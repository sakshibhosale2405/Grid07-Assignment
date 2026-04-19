"""
Phase 1: Vector-Based Persona Matching (The Router)
Uses ChromaDB + sentence-transformers to match posts to bot personas via cosine similarity.
"""

import chromadb
from chromadb.utils import embedding_functions
import numpy as np

# ── Bot personas ──────────────────────────────────────────────────────────────
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

# ── Setup ChromaDB with sentence-transformers embeddings ──────────────────────
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"   # small, fast, free — no API key needed
)

client = chromadb.Client()  # in-memory
collection = client.get_or_create_collection(
    name="bot_personas",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"},   # use cosine distance
)

# Store all personas in the vector DB
collection.add(
    ids=list(BOT_PERSONAS.keys()),
    documents=list(BOT_PERSONAS.values()),
)
print("✅ Bot personas stored in ChromaDB\n")


def route_post_to_bots(post_content: str, threshold: float = 0.40) -> list[dict]:
    """
    Embed the incoming post and return bots whose persona vector
    has cosine similarity > threshold with the post.

    Note: ChromaDB returns *distance* (0 = identical, 1 = opposite),
    so similarity = 1 - distance.
    The default threshold of 0.40 works well with all-MiniLM-L6-v2.
    """
    results = collection.query(
        query_texts=[post_content],
        n_results=len(BOT_PERSONAS),   # check all bots
        include=["distances", "documents"],
    )

    matched_bots = []
    print(f"📨 Post: \"{post_content}\"\n")
    print("📊 Similarity Scores:")

    for bot_id, distance in zip(results["ids"][0], results["distances"][0]):
        similarity = 1 - distance   # convert distance → similarity
        print(f"   {bot_id}: {similarity:.4f}", end="")

        if similarity >= threshold:
            print(f"  ✅ MATCHED (≥ {threshold})")
            matched_bots.append({"bot_id": bot_id, "similarity": round(similarity, 4)})
        else:
            print(f"  ❌ skipped (< {threshold})")

    print(f"\n🎯 Routed to: {[b['bot_id'] for b in matched_bots] or 'No bots matched'}\n")
    return matched_bots


# ── Quick demo ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_posts = [
        "OpenAI just released a new model that might replace junior developers.",
        "Bitcoin hits a new all-time high as ETF approvals surge.",
        "Big Tech companies are collecting your data without consent.",
        "The Federal Reserve raised interest rates by 25 basis points today.",
    ]

    for post in test_posts:
        route_post_to_bots(post)
        print("-" * 60)
