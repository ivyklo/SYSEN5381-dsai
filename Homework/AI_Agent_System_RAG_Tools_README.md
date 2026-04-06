# AI Agent System + RAG + Tools
Documentation for a multi-agent workflow, semantic RAG pipeline, and local tool-calling system that work together to fetch data, analyze patterns, and generate concise reports.

## 📊 Data
Source files and APIs:
- Disney character data via `get_characters` in [`lab_functions.py`](../06_agents/lab_functions.py) (API-backed).
  - What the data is about: Disney character metadata (films, TV shows, alignment, and related fields).
- Long Beach NYRCR Plan text in [`long_beach_nyrcr_plan.txt`](../07_rag/data/plans/long_beach_nyrcr_plan.txt).
  - What the data is about: a resilience planning document used for semantic search and retrieval.

## ⚡ Quick Start
Install required packages:
```
pip install pandas requests sentence-transformers sqlite-vec python-dotenv
```
Run the workflows:
```
python ../06_agents/lab_agents.py
python ../07_rag/lab_embed_rag.py
python ../08_function_calling/Lab_multi_agent_with_tools.py
```

## ✨ Features and Technology
- Features: multi-agent role pipeline, semantic RAG retrieval, local tool calling, fact-checking output.
- Technology: Python, `sentence-transformers`, `sqlite-vec`, SQLite, Ollama Cloud API.

## ⚙️ Configuration
Required environment variable:
- `OLLAMA_API_KEY`: Ollama Cloud API key for `lab_embed_rag.py`.

Where to set it:
- Create a `.env` file in `07_rag/` with:
```
OLLAMA_API_KEY=your_key_here
```

## 🔌 API Reference
### System Architecture (Agent Roles and Workflow)
- **`lab_agents.py`**: 3-step workflow — data fetch → analyst summary → report writer.
- **`lab_embed_rag.py`**: RAG workflow — chunk → embed → store → search → answer + optional fact-check.
- **`Lab_multi_agent_with_tools.py`**: tool-calling workflow — summarize → identify patterns → format text.

### RAG Data Source and Search
- **Document**: `07_rag/data/plans/long_beach_nyrcr_plan.txt`
- **Chunking**: sentence-level split on periods.
- **Embedding model**: `all-MiniLM-L6-v2` (384-dim vectors).
- **Search function**: `search_embed_sql(conn, query, k=3)` (KNN search in SQLite).

### Tool Functions (Local)
**`summarize_dataset(dataset_json, top_n=5)`**
- Purpose: summarize row/column counts and top alignment categories.
- Parameters: `dataset_json` (str, required), `top_n` (int, optional).
- Returns: plain-language summary string.

**`identify_patterns(dataset_json, top_n=5)`**
- Purpose: identify appearance patterns across films/TV/games.
- Parameters: `dataset_json` (str, required), `top_n` (int, optional).
- Returns: plain-language pattern summary string.

**`format_text(text, style)`**
- Purpose: apply `upper`, `lower`, or `title` formatting.
- Parameters: `text` (str, required), `style` (str, required).
- Returns: formatted text string.

### Technical Details
- **Ollama Cloud endpoint**: `https://ollama.com/api/chat`
- **DB file**: `07_rag/data/embed.db` (created at runtime).
- **Models**:
  - Embeddings: `all-MiniLM-L6-v2`
  - LLM (RAG): `gpt-oss:20b-cloud`
  - Local model for agent demos: `smollm2:135m`

### Usage Instructions
1. **Install dependencies** (see Quick Start).
2. **Configure API key** in `07_rag/.env`.
3. **Run the scripts**:
   - Agents: `python ../06_agents/lab_agents.py`
   - RAG: `python ../07_rag/lab_embed_rag.py`
   - Agents + Tools: `python ../08_function_calling/Lab_multi_agent_with_tools.py`
4. **Confirm data** exists at `07_rag/data/plans/long_beach_nyrcr_plan.txt`.
