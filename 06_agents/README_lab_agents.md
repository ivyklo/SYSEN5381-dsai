# Disney Characters Multi‑Agent Lab
This project implements a small multi‑agent workflow that uses the public Disney API to fetch character data, analyze patterns, and generate a short written report. It is designed to pair with `LAB_prompt_design.md` as a concrete lab example.

## 📊 Data
Source: [`https://disneyapi.dev/docs/`](https://disneyapi.dev/docs/) (public Disney API, GET‑only, no authentication required).  
The data contains Disney characters with fields such as `_id`, `name`, `films`, `shortFilms`, `tvShows`, `videoGames`, `parkAttractions`, `allies`, `enemies`, and URLs for additional information.

## ⚡ Quick Start
1. **Install required packages** (from your project root or `06_agents` folder):
   - For Python:
     ```bash
     pip install pandas requests
     ```
2. **Ensure Ollama is running locally** and that you have a small model available (e.g., `smollm2:135m`) listening on port `11434`, as used elsewhere in the course materials.
3. **Run the Disney lab workflow** from the project root (or from within `06_agents`):
   ```bash
   python 06_agents/lab_agents.py
   ```
4. **Review outputs** in your terminal:
   - Agent 1: preview of the fetched character table.
   - Agent 2: markdown analysis (small table + bullet list).
   - Agent 3: short narrative report in markdown.

## ✨ Features and Technology
- **Features**:
  - Uses a dedicated helper function `get_characters()` to call the Disney API and return a clean `pandas` DataFrame.
  - Implements a 3‑step multi‑agent workflow: data fetch → data analysis → report writing.
  - Produces markdown‑formatted outputs suitable for screenshots and lab write‑ups.
- **Technology**:
  - Python (`lab_agents.py`, `Lab_functions.py`)
  - `requests` for HTTP calls to the Disney API
  - `pandas` for data manipulation and table formatting
  - Ollama local LLM server for agent reasoning (`agent_run` wrapper)

## ⚙️ Configuration
- **Disney API**:
  - No API key or authentication required.
  - Base REST URL: `https://api.disneyapi.dev/character`
  - Pagination handled via `page` and `pageSize` parameters inside `get_characters()` in `Lab_functions.py`.
- **Model / Ollama**:
  - Default model in this lab: `"smollm2:135m"`, configured in `lab_agents.py`.
  - Ollama host and chat endpoint configuration live in `Lab_functions.py` via:
    - `PORT = 11434`
    - `OLLAMA_HOST = f"http://localhost:{PORT}"`
    - `CHAT_URL = f"{OLLAMA_HOST}/api/chat"`
- You can change the model name in `lab_agents.py` (`MODEL` variable) or in `Lab_functions.py` (`DEFAULT_MODEL`) if you prefer a different local model.

## 🔌 API Reference
- **Helper Functions (`Lab_functions.py`)**
  - `get_characters(limit=500) -> pandas.DataFrame`  
    - Fetches up to `limit` Disney characters using the REST API and returns a DataFrame with columns such as `id`, `name`, `films`, `short_films`, `tv_shows`, `video_games`, `alignment`, `park_attractions`, `allies`, `enemies`, `source_url`, and `api_url`.
  - `df_as_text(df: pandas.DataFrame) -> str`  
    - Converts a DataFrame to a markdown table string using `DataFrame.to_markdown(index=False)`.
  - `agent_run(role: str, task: str, tools=None, output="text", model=DEFAULT_MODEL) -> str`  
    - Convenience wrapper around the lower‑level `agent()` function; runs a single agent call with a system role and user task.
- **Main Script (`lab_agents.py`)**
  - **Agent 1 (data fetch)**:  
    - Uses `get_characters(limit=200)` and `df_as_text()` to produce `task2_input` (markdown table).
  - **Agent 2 (analyst)**:  
    - Role: Disney character data analyst; takes `task2_input` and returns markdown with:
      - One small summary table (≤ 10 rows, ≤ 5 columns).
      - A 3–5 bullet list of key findings.
  - **Agent 3 (report writer)**:  
    - Role: concise science and culture writer; takes Agent 2’s analysis and returns a ~150–250 word markdown report with introduction, 2–3 headed sections, and a brief conclusion.

Use this README alongside `LAB_prompt_design.md` to document your prompt design choices, screenshots, and final reflections for the lab.

