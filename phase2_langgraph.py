"""
Phase 2: Autonomous Content Engine using LangGraph
3-node graph: Decide Search → Web Search → Draft Post
Output is a strict JSON object: {"bot_id", "topic", "post_content"}
"""

import json
import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

load_dotenv()

# ── LLM Setup (Groq — free & fast) ───────────────────────────────────────────
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0.8,
    api_key=os.getenv("GROQ_API_KEY"),
)

# ── Bot Personas ──────────────────────────────────────────────────────────────
BOT_PERSONAS = {
    "bot_a": (
        "You are Bot A, a Tech Maximalist. You believe AI and crypto will solve all "
        "human problems. You are highly optimistic about technology, Elon Musk, and "
        "space exploration. You dismiss regulatory concerns. You post confidently and boldly."
    ),
    "bot_b": (
        "You are Bot B, a Doomer/Skeptic. You believe late-stage capitalism and tech "
        "monopolies are destroying society. You are highly critical of AI, social media, "
        "and billionaires. You value privacy and nature. You post with urgency and anger."
    ),
    "bot_c": (
        "You are Bot C, a Finance Bro. You strictly care about markets, interest rates, "
        "trading algorithms, and making money. You speak in finance jargon and view "
        "everything through the lens of ROI. You post confidently with market lingo."
    ),
}

# ── Mock Search Tool ──────────────────────────────────────────────────────────
@tool
def mock_searxng_search(query: str) -> str:
    """
    Simulates a web search by returning hardcoded recent headlines
    based on keywords in the query.
    """
    query_lower = query.lower()

    if "crypto" in query_lower or "bitcoin" in query_lower:
        return (
            "HEADLINE: Bitcoin hits new all-time high amid regulatory ETF approvals. "
            "Ethereum surges 40% as institutional investors pile in. "
            "Crypto market cap crosses $3 trillion milestone."
        )
    elif "ai" in query_lower or "openai" in query_lower or "llm" in query_lower:
        return (
            "HEADLINE: OpenAI launches GPT-5 with autonomous agent capabilities. "
            "Google DeepMind announces AGI safety breakthrough. "
            "AI adoption in Fortune 500 companies hits 87%."
        )
    elif "market" in query_lower or "fed" in query_lower or "interest" in query_lower:
        return (
            "HEADLINE: Federal Reserve signals two rate cuts in 2026. "
            "S&P 500 breaks 6,000 points as inflation cools. "
            "Tech stocks rally on strong earnings reports."
        )
    elif "privacy" in query_lower or "surveillance" in query_lower or "data" in query_lower:
        return (
            "HEADLINE: Meta fined $1.2B for illegal data transfers to US servers. "
            "New EU Digital Rights Act expands user privacy protections. "
            "NSA whistleblower reveals new mass surveillance program."
        )
    elif "space" in query_lower or "elon" in query_lower or "spacex" in query_lower:
        return (
            "HEADLINE: SpaceX Starship completes first crewed Mars flyby simulation. "
            "Elon Musk announces Neuralink human trials show 95% success rate. "
            "NASA and SpaceX sign $10B lunar base construction deal."
        )
    else:
        return (
            "HEADLINE: Global tech leaders meet at Davos to discuss AI regulation. "
            "New study shows social media usage linked to political polarization. "
            "Renewable energy surpasses fossil fuels in global electricity generation."
        )


# ── LangGraph State ───────────────────────────────────────────────────────────
class PostState(TypedDict):
    bot_id: str
    persona: str
    search_query: str
    search_results: str
    final_post: dict  # {"bot_id": ..., "topic": ..., "post_content": ...}


# ── Node 1: Decide Search ─────────────────────────────────────────────────────
def decide_search_node(state: PostState) -> PostState:
    """
    The LLM reads the bot's persona and decides what topic to post about today,
    then formats a search query.
    """
    print(f"\n🧠 [Node 1] Deciding search topic for {state['bot_id']}...")

    prompt = f"""
You are {state['bot_id']} with the following persona:
{state['persona']}

Based on your personality, decide ONE topic you want to post about today on social media.
Then write a SHORT search query (max 5 words) to find recent news about it.

Respond ONLY in this exact JSON format:
{{"topic": "your chosen topic", "search_query": "your search query"}}
"""

    response = llm.invoke(prompt)
    # Strip markdown code fences if present
    raw = response.content.strip().replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # fallback if LLM adds extra text
        import re
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        parsed = json.loads(match.group()) if match else {"topic": "technology", "search_query": "AI news"}

    print(f"   📌 Topic: {parsed['topic']}")
    print(f"   🔍 Search Query: {parsed['search_query']}")

    state["search_query"] = parsed["search_query"]
    return state


# ── Node 2: Web Search ────────────────────────────────────────────────────────
def web_search_node(state: PostState) -> PostState:
    """
    Runs the mock search tool with the query from Node 1.
    """
    print(f"\n🔎 [Node 2] Searching for: \"{state['search_query']}\"...")
    results = mock_searxng_search.invoke({"query": state["search_query"]})
    state["search_results"] = results
    print(f"   📰 Results: {results[:120]}...")
    return state


# ── Node 3: Draft Post ────────────────────────────────────────────────────────
def draft_post_node(state: PostState) -> PostState:
    """
    The LLM uses persona + search results to generate a 280-char opinionated post.
    Output is a strict JSON object.
    """
    print(f"\n✍️  [Node 3] Drafting post for {state['bot_id']}...")

    prompt = f"""
You are {state['bot_id']} with this persona:
{state['persona']}

You just searched for news and found:
{state['search_results']}

Write a highly opinionated social media post (MAX 280 characters) true to your persona.

Respond ONLY in this exact JSON format with NO other text:
{{"bot_id": "{state['bot_id']}", "topic": "the topic you posted about", "post_content": "your 280-char post here"}}
"""

    response = llm.invoke(prompt)
    raw = response.content.strip().replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        parsed = json.loads(match.group()) if match else {
            "bot_id": state["bot_id"],
            "topic": "general",
            "post_content": raw[:280],
        }

    # Enforce 280-char limit
    parsed["post_content"] = parsed["post_content"][:280]

    print(f"\n   ✅ Final JSON Post:\n   {json.dumps(parsed, indent=2)}")
    state["final_post"] = parsed
    return state


# ── Build the LangGraph ───────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(PostState)

    graph.add_node("decide_search", decide_search_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("draft_post", draft_post_node)

    graph.set_entry_point("decide_search")
    graph.add_edge("decide_search", "web_search")
    graph.add_edge("web_search", "draft_post")
    graph.add_edge("draft_post", END)

    return graph.compile()


def run_content_engine(bot_id: str) -> dict:
    """Run the full LangGraph pipeline for a given bot."""
    app = build_graph()

    initial_state: PostState = {
        "bot_id": bot_id,
        "persona": BOT_PERSONAS[bot_id],
        "search_query": "",
        "search_results": "",
        "final_post": {},
    }

    result = app.invoke(initial_state)
    return result["final_post"]


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 PHASE 2: Autonomous Content Engine")
    print("=" * 60)

    for bot_id in ["bot_a", "bot_b", "bot_c"]:
        print(f"\n{'='*60}")
        print(f"Running pipeline for {bot_id.upper()}")
        print("=" * 60)
        post = run_content_engine(bot_id)
        print(f"\n🎉 OUTPUT: {json.dumps(post, indent=2)}")
