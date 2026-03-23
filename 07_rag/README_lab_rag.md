# Lab Embed RAG
Semantic RAG demo that embeds a plan document, stores vectors in SQLite, and answers queries using Ollama Cloud.

## 📊 Data
The text source is the Long Beach NY Rising Community Reconstruction (NYRCR) Plan.
The script reads `data/plans/long_beach_nyrcr_plan.txt` and chunk-embeds it for search.

## ⚡ Quick Start
Install requirements:
`pip install sentence-transformers sqlite-vec requests python-dotenv`
Run the script:
`python lab_embed_rag.py`

## ✨ Features and Technology
Search query: asks how the Long Beach NYRCR Plan addresses coastal flood and storm surge risk after Superstorm Sandy, including shoreline, dunes, and boardwalk strategies, and how those connect to broader recovery and resilience priorities.
LLM prompt summary: the model is instructed to answer only using retrieved plan context, avoid inventing details, and return a markdown response with a title and clear bullet points.
- Features: text chunking, vector embedding, SQLite KNN search, RAG response, fact-check step
- Technology: Python, sentence-transformers, sqlite-vec, SQLite, Ollama Cloud API

## ⚙️ Configuration
Environment variables:
- `OLLAMA_API_KEY` in a `.env` file (required for Ollama Cloud calls).

Key parameters in `lab_embed_rag.py`:
- `DB_PATH` (default `data/embed.db`) for the vector database.
- `DOCUMENT` (default `data/plans/long_beach_nyrcr_plan.txt`) for the input text.
- `EMBED_MODEL` (default `all-MiniLM-L6-v2`) for embeddings.
- `MODEL` (default `gpt-oss:20b-cloud`) for the RAG answer step.

## 🔌 API Reference
Public helper functions used by the script:
- `agent_run(role, task, model=MODEL)` -> run an Ollama Cloud chat request.
- `get_text(document_path)` -> load and split text into sentence chunks.
- `build_index_from_document(conn, chunks)` -> embed chunks and populate SQLite tables.
- `search_embed_sql(conn, query, k=3)` -> KNN search for top-k relevant chunks.
- `connect_db(path=DB_PATH)` -> open SQLite and load sqlite-vec extension.
