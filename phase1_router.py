import chromadb
from chromadb.utils import embedding_functions
import numpy as np

# bot personas for the router phase
BOT_PERSONAS = {
    "bot_a": (
        "I believe AI and crypto will solve all human problems. "
        "I am highly optimistic about technology, Elon Musk, and space exploration. "
        "I dismiss regulatory concerns."
    ),
    "bot_b": (
        "I believe late-stage capitalism and tech monopolies are destroying society. "
        "I am highly critical of AI, social media, and billionaires. "
        "I value privacy and nature."
    ),
    "bot_c": (
        "I strictly care about markets, interest rates, trading algorithms, and making money. "
        "I speak in finance jargon and view everything through the lens of ROI."
    ),
}

# setting up chromadb with sentence-transformers 
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2" # using this because it's fast and no api key needed
)

client = chromadb.Client() # memory only
collection = client.get_or_create_collection(
    name="bot_personas",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}, # cosine distance
)

# put all personas in the db
collection.add(
    ids=list(BOT_PERSONAS.keys()),
    documents=list(BOT_PERSONAS.values()),
)
print("bot personas stored in chromadb\n")


def route_post_to_bots(post_content: str, threshold: float = 0.40) -> list[dict]:
    # embed the post and return bots that cross the threshold
    # chromadb returns distance so similarity is 1 - distance
    results = collection.query(
        query_texts=[post_content],
        n_results=len(BOT_PERSONAS),
        include=["distances", "documents"],
    )

    matched_bots = []
    print(f"post: \"{post_content}\"\n")
    print("similarity scores:")

    for bot_id, distance in zip(results["ids"][0], results["distances"][0]):
        similarity = 1 - distance
        print(f"   {bot_id}: {similarity:.4f}", end="")

        if similarity >= threshold:
            print(f"  matched (>={threshold})")
            matched_bots.append({"bot_id": bot_id, "similarity": round(similarity, 4)})
        else:
            print(f"  skipped (<{threshold})")

    assigned = [b['bot_id'] for b in matched_bots] or 'none'
    print(f"\nrouted to: {assigned}\n")
    return matched_bots


if __name__ == "__main__":
    test_posts = [
        "OpenAI just released a new model that might replace junior developers.",
        "Bitcoin hits a new all-time high as ETF approvals surge.",
        "Big Tech companies are collecting your data without consent.",
        "The Federal Reserve raised interest rates by 25 basis points today.",
    ]

    for post in test_posts:
        route_post_to_bots(post)
        print("-" * 50)
