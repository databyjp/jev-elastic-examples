"""Check whether supplied passages support atomic claims, without generating an answer."""

import os

from dotenv import load_dotenv
from typesafe_sdk import Choice, TypeSafeClient

CLAIM_AND_CITATION_PAIRS = [
    {
        "claim": "Unopened items can be returned within 30 days.",
        "citation": "Unopened items may be returned within 30 days of delivery.",
    },
    {
        "claim": "Opened items can be returned within 30 days.",
        "citation": "Opened items are not eligible for return.",
    },
    {
        "claim": "Return shipping is always free.",
        "citation": "Unopened items may be returned within 30 days of delivery.",
    },
]

QUESTION = Choice(
    instructions="What is the relationship between `citation` and the atomic `claim`?",
    criteria={
        "supports": "The citation provides direct evidence for the claim.",
        "contradicts": "The citation states something incompatible with the claim.",
        "not_addressed": "The citation does not establish or refute the claim.",
    },
)


def main() -> None:
    load_dotenv()
    api_key = os.getenv("TYPESAFE_AI_API_KEY") or os.environ["TYPESAFE_API_KEY"]

    with TypeSafeClient(api_key=api_key, model="jev-latest") as client:
        for pair in CLAIM_AND_CITATION_PAIRS:
            response = client.system_one(
                state=pair,
                questions={"citation_support": QUESTION},
            )
            answer = response.choices["citation_support"]

            print(f"\nClaim: {pair['claim']}")
            print(f"Citation: {pair['citation']}")
            print(f"Verdict: {answer.choice}")
            print(f"Probabilities: {answer.probabilities}")


if __name__ == "__main__":
    main()
