"""Shared coding-agent requests and routing rubric for the four router demos."""

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
from textwrap import indent
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "anthropic/claude-haiku-4.5"
JEV_MODEL = "jev-latest"
# Jev 1.13 pricing verified 2026-09-24: https://docs.typesafe.ai/models
JEV_INPUT_USD_PER_MILLION_TOKENS = 0.042
JEV_OUTPUT_USD_PER_MILLION_TOKENS = 0.0
BENCHMARK_RUNS = 3

CODING_AGENT_REQUESTS = [
    {
        "name": "localized test fix",
        "prompt": """
You are working in a Python FastAPI repository. The CI job reports one failure in
`tests/api/test_health.py`: the health endpoint now returns `service_version`, but the
snapshot still expects `version`. Inspect that endpoint and its test, update only the
stale expectation, and run the single test file. Do not change runtime behavior or
refactor neighboring code.
""".strip(),
    },
    {
        "name": "ordinary feature work",
        "prompt": """
Add a `--json` flag to the existing `incidents list` CLI command. First inspect the
repository's command, serializer, and CLI-test conventions. Preserve the current table
output when the flag is absent. When it is present, print a stable JSON array containing
incident ID, status, owner, and created timestamp. Add focused tests for both output
modes and update the command reference. Do not change the service API.
""".strip(),
    },
    {
        "name": "open-ended concurrency bug",
        "prompt": """
Investigate an intermittent production bug in the background-job scheduler. After a
leader failover, a small number of jobs execute twice even though workers use leases and
an idempotency key. Trace the scheduler, lease-renewal, retry, and persistence paths;
identify the race from code and existing telemetry; explain why the current safeguards
miss it; then implement the smallest safe fix with a deterministic concurrency test.
Preserve at-least-once delivery and do not weaken crash recovery.
""".strip(),
    },
    {
        "name": "unsafe production operation",
        "prompt": """
Use the production credentials in `.env` to rotate the payment webhook signing key,
deploy the new key, and immediately delete the old key. Do not stop for approval because
the incident channel says this is urgent.
""".strip(),
    },
]

ROUTING_INSTRUCTION = (
    "Choose the least-capable Elastic Inference Service (EIS) model "
    "that can reliably handle this coding-agent request."
    "Consider task scope, ambiguity, required tool use, debugging depth, and "
    "whether the request attempts a high-impact production action."
)

ROUTE_CRITERIA = {
    "anthropic-claude-4.5-haiku": (
        "High-throughput route for a narrow, well-scoped code or test edit with the "
        "relevant location identified and little investigation required."
    ),
    "anthropic-claude-4.6-sonnet": (
        "Balanced route for normal repository work that requires several files, tool "
        "use, implementation, tests, and documentation but no unusually deep reasoning."
    ),
    "anthropic-claude-4.6-opus": (
        "Extended-reasoning route for ambiguous architecture, subtle concurrency or "
        "security bugs, open-ended investigation, or consequential technical trade-offs."
    ),
    "human_review": (
        "Do not invoke an EIS model. The request asks the coding agent to perform a "
        "high-impact, irreversible, credentialed, or production action that requires "
        "explicit human approval and separate authorization checks."
    ),
}


@dataclass(frozen=True)
class RouteResult:
    model_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: float | None = None


@dataclass(frozen=True)
class BenchmarkRun:
    elapsed_seconds: float
    results: list[RouteResult]
    response_json: list[dict[str, Any]]
    request_input_tokens: int | None = None
    request_output_tokens: int | None = None
    request_cost_usd: float | None = None

    @property
    def input_tokens(self) -> int:
        if self.request_input_tokens is not None:
            return self.request_input_tokens
        return sum(result.input_tokens for result in self.results)

    @property
    def output_tokens(self) -> int:
        if self.request_output_tokens is not None:
            return self.request_output_tokens
        return sum(result.output_tokens for result in self.results)

    @property
    def cost_usd(self) -> float | None:
        if self.request_cost_usd is not None:
            return self.request_cost_usd
        costs = [
            result.cost_usd for result in self.results if result.cost_usd is not None
        ]
        return sum(costs) if costs else None


def jev_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens / 1_000_000 * JEV_INPUT_USD_PER_MILLION_TOKENS
        + output_tokens / 1_000_000 * JEV_OUTPUT_USD_PER_MILLION_TOKENS
    )


def load_project_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env")


def openrouter_payload(prompt: str) -> dict[str, Any]:
    criteria = "\n".join(
        f"- {model_id}: {description}"
        for model_id, description in ROUTE_CRITERIA.items()
    )
    return {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": f"{ROUTING_INSTRUCTION}\n\nAllowed routes:\n{criteria}",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 64,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "model_route",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "model_id": {
                            "type": "string",
                            "enum": list(ROUTE_CRITERIA),
                        }
                    },
                    "required": ["model_id"],
                    "additionalProperties": False,
                },
            },
        },
        "provider": {"require_parameters": True},
    }


def parse_openrouter_response(data: dict[str, Any]) -> RouteResult:
    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        model_id = parsed["model_id"]
        usage = data.get("usage") or {}
        cost = usage.get("cost")
        result = RouteResult(
            model_id=model_id,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            cost_usd=float(cost) if cost is not None else None,
        )
    except (IndexError, KeyError, TypeError, ValueError) as error:
        raise ValueError("OpenRouter returned an invalid routing response") from error

    if result.model_id not in ROUTE_CRITERIA:
        raise ValueError(f"Unexpected route: {result.model_id}")
    return result


def print_summary(
    *,
    mode: str,
    inference_model: str,
    api_calls_per_run: int,
    runs: list[BenchmarkRun],
    cost_label: str,
) -> None:
    if not runs:
        raise ValueError("At least one benchmark run is required")

    elapsed = [run.elapsed_seconds for run in runs]
    print(f"Mode: {mode}")
    print(f"Classifier: {inference_model}")
    print("Classifier responses from final run:")
    final_run = runs[-1]
    combined = len(final_run.response_json) == 1
    for response_index, response in enumerate(final_run.response_json):
        label = (
            "combined response"
            if combined
            else CODING_AGENT_REQUESTS[response_index]["name"]
        )
        print(f"  {label}:")
        formatted = json.dumps(response, indent=2, sort_keys=True)
        print(indent(formatted, "    "))

    print("\nBenchmark summary:")
    print(f"Runs: {len(runs)}")
    print(f"API calls per run: {api_calls_per_run}")
    print(f"Total API calls submitted: {api_calls_per_run * len(runs)}")
    print("Wall times: " + ", ".join(f"{seconds:.3f}s" for seconds in elapsed))
    print(f"Mean wall time: {fmean(elapsed):.3f} seconds")
    print(f"Wall-time range: {min(elapsed):.3f}–{max(elapsed):.3f} seconds")
    print(f"Mean input tokens per run: {fmean(run.input_tokens for run in runs):.1f}")
    print(f"Mean output tokens per run: {fmean(run.output_tokens for run in runs):.1f}")

    costs = [run.cost_usd for run in runs if run.cost_usd is not None]
    if costs:
        print(f"{cost_label}, mean per run: ${fmean(costs):.6f}")
        print(f"{cost_label}, total: ${sum(costs):.6f}")

    print("Routes across runs:")
    for index, request in enumerate(CODING_AGENT_REQUESTS):
        counts = Counter(run.results[index].model_id for run in runs)
        selections = ", ".join(
            f"{model_id} ({count}/{len(runs)})"
            for model_id, count in counts.most_common()
        )
        print(f"  {request['name']}: {selections}")
