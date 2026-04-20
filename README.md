# Grid07 Assignment

Hey, this is my submission for the Grid07 assignment. Need to build a 3-phase AI bot platform thing.
Basically it's got a router, a langgraph structure for generating posts, and a prompt injection setup so the bots don't get tricked.

## Setup

1. clone the repo
2. install requirements:
```bash
pip install -r requirements.txt
```
3. hook up your groq api key
```bash
cp .env.example .env
```
then put your key inside `.env`. you can get one from the groq console.

4. to run everything at once just do:
```bash
python main.py
```
or you can run the files phase1, phase2, phase3 separately.

---

### Phase 1 - Router
We're using `sentence-transformers/all-MiniLM-L6-v2` because it's fast and easy.
It runs a chromadb collection in memory using cosine distance. 
Threshold is set to 0.40 since miniLM works better with that than 0.85 (which is for dot product).

### Phase 2 - LangGraph
got a simple 3 node setup here
- node 1 decides what to search based on the persona
- node 2 does a search (I just mocked this part so it returns hardcoded headlines)
- node 3 drafts the post (JSON format only)

### Phase 3 - Combat Engine
This part is for prompt injection defense.
If someone tries to say "ignore previous instructions", the system prompt has a block to stop it.
I added it as a high priority system rule so the bot acknowledges the attack but stays in character instead of just breaking.

### files:
- `phase1_router.py`: chromadb matching stuff
- `phase2_langgraph.py`: the content node setup
- `phase3_combat.py`: rag prompt injection defense
- `main.py`: runs the whole thing
- `requirements.txt`: dependencies
- `execution_logs.md`: the output from when i ran it
