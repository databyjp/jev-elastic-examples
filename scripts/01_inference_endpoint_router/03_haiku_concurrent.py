"""Route coding requests with concurrent Claude Haiku calls through OpenRouter."""

import asyncio
import os
from time import perf_counter

import httpx

from routing_scenario import (
    BENCHMARK_RUNS,
    CODING_AGENT_REQUESTS,
    OPENROUTER_MODEL,
    BenchmarkRun,
    OPENROUTER_URL,
    RouteResult,
    load_project_env,
    openrouter_payload,
    parse_openrouter_response,
    print_summary,
)


async def classify(
    client: httpx.AsyncClient,
    prompt: str,
) -> RouteResult:
    response = await client.post(OPENROUTER_URL, json=openrouter_payload(prompt))
    response.raise_for_status()
    return parse_openrouter_response(response.json())


async def run() -> None:
    load_project_env()
    headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}

    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        runs = []
        for _ in range(BENCHMARK_RUNS):
            started = perf_counter()
            results = await asyncio.gather(
                *(
                    classify(client, request["prompt"])
                    for request in CODING_AGENT_REQUESTS
                )
            )
            runs.append(
                BenchmarkRun(
                    elapsed_seconds=perf_counter() - started,
                    results=results,
                )
            )

    print_summary(
        mode="Haiku, concurrent requests",
        inference_model=OPENROUTER_MODEL,
        api_calls_per_run=len(CODING_AGENT_REQUESTS),
        runs=runs,
        cost_label="OpenRouter-reported cost",
    )


if __name__ == "__main__":
    asyncio.run(run())
