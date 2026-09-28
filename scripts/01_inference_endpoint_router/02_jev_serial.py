"""Route each coding request with one serial Jev call."""

import os
from time import perf_counter

from typesafe_sdk import Choice, TypeSafeClient

from routing_scenario import (
    BENCHMARK_RUNS,
    CODING_AGENT_REQUESTS,
    JEV_MODEL,
    BenchmarkRun,
    ROUTE_CRITERIA,
    ROUTING_INSTRUCTION,
    RouteResult,
    jev_cost_usd,
    load_project_env,
    print_summary,
)

MODEL_ROUTING_QUESTION = Choice(
    instructions=ROUTING_INSTRUCTION,
    criteria=ROUTE_CRITERIA,
)


def main() -> None:
    load_project_env()
    api_key = os.getenv("TYPESAFE_AI_API_KEY") or os.environ["TYPESAFE_API_KEY"]

    with TypeSafeClient(api_key=api_key, model=JEV_MODEL) as client:
        runs = []
        resolved_model = JEV_MODEL
        for _ in range(BENCHMARK_RUNS):
            started = perf_counter()
            results = []
            response_json = []
            for request in CODING_AGENT_REQUESTS:
                response = client.system_one(
                    state={"coding_agent_request": request["prompt"]},
                    questions={"model": MODEL_ROUTING_QUESTION},
                )
                resolved_model = response.model
                input_tokens = response.usage.input_tokens or 0
                output_tokens = response.usage.output_tokens or 0
                response_json.append(response.model_dump(mode="json"))
                results.append(
                    RouteResult(
                        model_id=response.choices["model"].choice,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost_usd=jev_cost_usd(input_tokens, output_tokens),
                    )
                )
            runs.append(
                BenchmarkRun(
                    elapsed_seconds=perf_counter() - started,
                    results=results,
                    response_json=response_json,
                )
            )

    print_summary(
        mode="Jev, serial requests",
        inference_model=f"{JEV_MODEL} → {resolved_model}",
        api_calls_per_run=len(CODING_AGENT_REQUESTS),
        runs=runs,
        cost_label="Calculated Jev cost",
    )


if __name__ == "__main__":
    main()
