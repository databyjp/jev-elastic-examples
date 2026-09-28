"""Route all coding requests as parallel Jev questions in one API call."""

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


def routing_question(index: int) -> Choice:
    return Choice(
        instructions=(
            f"{ROUTING_INSTRUCTION} Evaluate only "
            f"`coding_agent_requests[{index}].prompt`."
        ),
        criteria=ROUTE_CRITERIA,
    )


def main() -> None:
    load_project_env()
    api_key = os.getenv("TYPESAFE_AI_API_KEY") or os.environ["TYPESAFE_API_KEY"]
    questions = {
        f"request_{index}": routing_question(index)
        for index in range(len(CODING_AGENT_REQUESTS))
    }

    with TypeSafeClient(api_key=api_key, model=JEV_MODEL) as client:
        runs = []
        resolved_model = JEV_MODEL
        for _ in range(BENCHMARK_RUNS):
            started = perf_counter()
            response = client.system_one(
                state={"coding_agent_requests": CODING_AGENT_REQUESTS},
                questions=questions,
            )
            elapsed_seconds = perf_counter() - started
            resolved_model = response.model
            results = [
                RouteResult(
                    model_id=response.choices[f"request_{index}"].choice,
                    input_tokens=0,
                    output_tokens=0,
                )
                for index in range(len(CODING_AGENT_REQUESTS))
            ]
            input_tokens = response.usage.input_tokens or 0
            output_tokens = response.usage.output_tokens or 0
            runs.append(
                BenchmarkRun(
                    elapsed_seconds=elapsed_seconds,
                    results=results,
                    response_json=[response.model_dump(mode="json")],
                    request_input_tokens=input_tokens,
                    request_output_tokens=output_tokens,
                    request_cost_usd=jev_cost_usd(input_tokens, output_tokens),
                )
            )

    print_summary(
        mode="Jev, parallel questions in one request",
        inference_model=f"{JEV_MODEL} → {resolved_model}",
        api_calls_per_run=1,
        runs=runs,
        cost_label="Calculated Jev cost",
    )


if __name__ == "__main__":
    main()
