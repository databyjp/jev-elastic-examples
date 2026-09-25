"""Classify zero-result searches without rewriting or rerunning the search."""

import os

from dotenv import load_dotenv
from typesafe_sdk import Choice, TypeSafeClient

ZERO_RESULT_SEARCHES = [
    {
        "query": "refnd polcy",
        "known_terms": ["refund policy", "return policy"],
        "active_filters": [],
    },
    {
        "query": "SLA",
        "known_terms": ["service level agreement"],
        "active_filters": [],
    },
    {
        "query": "enterprise audit logs",
        "known_terms": ["audit logs"],
        "active_filters": ["plan:free"],
    },
    {
        "query": "ZX-99118",
        "known_terms": [],
        "active_filters": [],
    },
    {
        "query": "mercury",
        "known_terms": ["Mercury payment service", "Mercury programming language"],
        "active_filters": [],
    },
    {
        "query": "quantum fax integration",
        "known_terms": [],
        "active_filters": [],
    },
]

QUESTION = Choice(
    instructions="What is the most likely reason this search returned no results?",
    criteria={
        "typo": "The query appears to misspell a known term.",
        "acronym": "The query uses an acronym whose expanded form may exist in the corpus.",
        "missing_filter": "An active filter likely excludes otherwise relevant content.",
        "ambiguous": "The query has multiple materially different meanings and needs clarification.",
        "exact_id": "The query looks like an identifier that should use an exact lookup path.",
        "corpus_gap": "The request appears clear, but the corpus likely has no matching content.",
    },
)

NEXT_STEPS = {
    "typo": "offer a spelling correction",
    "acronym": "retry with the known expansion",
    "missing_filter": "suggest removing the conflicting filter",
    "ambiguous": "ask a clarifying question",
    "exact_id": "try the exact-ID lookup path",
    "corpus_gap": "log a content gap",
}


def main() -> None:
    load_dotenv()
    api_key = os.getenv("TYPESAFE_AI_API_KEY") or os.environ["TYPESAFE_API_KEY"]

    with TypeSafeClient(api_key=api_key, model="jev-latest") as client:
        for search in ZERO_RESULT_SEARCHES:
            response = client.system_one(
                state=search,
                questions={"recovery_route": QUESTION},
            )
            answer = response.choices["recovery_route"]

            print(f"\nQuery: {search['query']}")
            print(f"Cause: {answer.choice}")
            print(f"Next step: {NEXT_STEPS[answer.choice]}")
            print(f"Probabilities: {answer.probabilities}")


if __name__ == "__main__":
    main()
