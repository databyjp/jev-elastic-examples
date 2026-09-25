"""Judge hard-coded retrieval results without querying Elasticsearch or an LLM."""

import os

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient

QUERY = "How long do I have to return an unopened item?"
RETRIEVED_CHUNKS = [
    {
        "id": "returns-30-days",
        "text": "Unopened items may be returned within 30 days of delivery.",
    },
    {
        "id": "shipping-30-days",
        "text": "International shipping estimates can extend to 30 days.",
    },
    {
        "id": "refund-timing",
        "text": "Approved refunds appear on the original payment method within five days.",
    },
]

QUESTION = Noul(
    instructions="Does `chunk.text` directly help answer `query`? Judge the pair, not topic similarity alone."
)
RELEVANCE_THRESHOLD = 0.60


def main() -> None:
    load_dotenv()
    api_key = os.getenv("TYPESAFE_AI_API_KEY") or os.environ["TYPESAFE_API_KEY"]

    with TypeSafeClient(api_key=api_key, model="jev-latest") as client:
        for chunk in RETRIEVED_CHUNKS:
            state = {"query": QUERY, "chunk": chunk}
            response = client.system_one(
                state=state,
                questions={"is_relevant": QUESTION},
            )
            probability = response.nouls["is_relevant"].noul
            route = "include" if probability >= RELEVANCE_THRESHOLD else "exclude"

            print(f"\nChunk: {chunk['id']}")
            print(f"Relevance probability: {probability:.2f}")
            print(f"Policy route: {route}")


if __name__ == "__main__":
    main()
