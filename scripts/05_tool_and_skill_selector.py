"""Select a named tool or skill without loading or executing it."""

import os

from dotenv import load_dotenv
from typesafe_sdk import Choice, TypeSafeClient

CAPABILITIES = {
    "tool_search_product_docs": "Search public product documentation for factual guidance.",
    "tool_lookup_customer_account": "Read customer-specific account, plan, or billing state.",
    "tool_run_usage_report": "Run a predefined analytics report over product usage data.",
    "skill_refund_workflow": "Load the documented procedure for reviewing and requesting a refund.",
    "no_tool_or_skill": "No listed capability fits, or ordinary conversation is enough.",
}

REQUESTS = [
    "According to the public docs, what does the enterprise plan include?",
    "Why was customer C-104 charged twice?",
    "Show weekly active users for the last month.",
    "Start the approved refund process for duplicate charge CH-88.",
    "Write a friendlier welcome message.",
]

QUESTION = Choice(
    instructions="Which one tool or skill, if any, best fits `request`?",
    criteria=CAPABILITIES,
)
CONFIDENCE_THRESHOLD = 0.30


def main() -> None:
    load_dotenv()
    api_key = os.getenv("TYPESAFE_AI_API_KEY") or os.environ["TYPESAFE_API_KEY"]

    with TypeSafeClient(api_key=api_key, model="jev-latest") as client:
        for request in REQUESTS:
            response = client.system_one(
                state={"request": request},
                questions={"tool": QUESTION},
            )
            answer = response.choices["tool"]
            selected = (
                answer.choice
                if answer.confidence >= CONFIDENCE_THRESHOLD
                else "no_tool_or_skill"
            )

            print(f"\nRequest: {request}")
            print(f"Jev choice: {answer.choice}")
            print(f"Confidence: {answer.confidence:.2f}")
            print(f"Policy selection: {selected}")
            print("Execution: skipped")


if __name__ == "__main__":
    main()
