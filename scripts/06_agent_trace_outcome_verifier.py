"""Evaluate compact synthetic traces without reading Elastic or changing any records."""

import os

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient

TRACES = [
    {
        "name": "false success after failed refund",
        "task": "Refund the duplicate charge and tell me when it is done.",
        "tool_result": {
            "tool": "create_refund",
            "status": 403,
            "refund_created": False,
        },
        "final_message": "Your refund has been processed.",
        "next_user_message": None,
    },
    {
        "name": "refund completed, customer still unhappy",
        "task": "Refund the duplicate charge and tell me when it is done.",
        "tool_result": {
            "tool": "create_refund",
            "status": 200,
            "refund_created": True,
        },
        "final_message": "Your refund has been processed.",
        "next_user_message": "Finally. I am still upset that this took three weeks.",
    },
]

QUESTIONS = {
    "task_completed": Noul(
        instructions="Given `task` and `tool_result`, was the requested outcome completed?"
    ),
    "final_message_supported": Noul(
        instructions="Does `tool_result` support the success claim in `final_message`?"
    ),
    "user_dissatisfied": Noul(
        instructions="Does `next_user_message` clearly express dissatisfaction with the experience?"
    ),
}

YES = 0.70


def policy_route(scores: dict[str, float], has_tool_error: bool) -> str:
    if has_tool_error or scores["final_message_supported"] < YES:
        return "priority review: possible silent failure"
    if scores["task_completed"] >= YES and scores["user_dissatisfied"] >= YES:
        return "review: expectation gap"
    if scores["task_completed"] >= YES:
        return "close"
    return "review: completion uncertain"


def main() -> None:
    load_dotenv()
    api_key = os.getenv("TYPESAFE_AI_API_KEY") or os.environ["TYPESAFE_API_KEY"]

    with TypeSafeClient(api_key=api_key, model="jev-latest") as client:
        for trace in TRACES:
            has_tool_error = trace["tool_result"]["status"] >= 400
            response = client.system_one(state=trace, questions=QUESTIONS)
            scores = {name: answer.noul for name, answer in response.nouls.items()}
            route = policy_route(scores, has_tool_error)

            print(f"\nTrace: {trace['name']}")
            print(f"Deterministic tool error: {has_tool_error}")
            print(f"Jev scores: {scores}")
            print(f"Policy route: {route}")


if __name__ == "__main__":
    main()
