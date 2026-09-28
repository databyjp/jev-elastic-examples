"""Route each coding request with one serial Claude Haiku call through OpenRouter."""

import os
from time import perf_counter

import httpx

from routing_scenario import (
    BENCHMARK_RUNS,
    CODING_AGENT_REQUESTS,
    OPENROUTER_MODEL,
    OPENROUTER_URL,
    BenchmarkRun,
    load_project_env,
    openrouter_payload,
    parse_openrouter_response,
    print_summary,
)


def main() -> None:
    load_project_env()
    headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}

    with httpx.Client(headers=headers, timeout=60.0) as client:
        runs = []
        for _ in range(BENCHMARK_RUNS):
            started = perf_counter()
            results = []
            response_json = []
            for request in CODING_AGENT_REQUESTS:
                response = client.post(
                    OPENROUTER_URL,
                    json=openrouter_payload(request["prompt"]),
                )
                response.raise_for_status()
                data = response.json()
                results.append(parse_openrouter_response(data))
                response_json.append(data)
            runs.append(
                BenchmarkRun(
                    elapsed_seconds=perf_counter() - started,
                    results=results,
                    response_json=response_json,
                )
            )

    print_summary(
        mode="Haiku, serial requests",
        inference_model=OPENROUTER_MODEL,
        api_calls_per_run=len(CODING_AGENT_REQUESTS),
        runs=runs,
        cost_label="OpenRouter-reported cost",
    )


if __name__ == "__main__":
    main()
