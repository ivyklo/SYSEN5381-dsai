# Lab_multi_agent_with_tools.py
# Multi-Agent Workflow with Local Tools
# Pairs with LAB_multi_agent_with_tools.md
# Tim Fraser
#
# This script demonstrates a 3-agent workflow with function calling:
# 1) Fetch Disney character data, 2) summarize with a custom tool,
# 3) identify patterns with a second custom tool, 4) format text with a third tool.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import json  # for parsing tool inputs and outputs
import pandas as pd  # for data manipulation
import time  # for timing each workflow step
import requests  # for handling agent call exceptions

## 0.2 Load Functions #################################

from functions import agent_run, get_characters


# 1. CONFIGURATION ###################################

# Select model of interest
MODEL = "smollm2:135m"


# 2. DEFINE TOOL FUNCTIONS ###################################

def summarize_dataset(dataset_json, top_n=5):
    """
    Summarize a dataset encoded as JSON records.

    Parameters:
    -----------
    dataset_json : str
        JSON string in records format (list of objects)
    top_n : int
        Number of top alignment categories to include

    Returns:
    --------
    str
        Plain-language summary text
    """
    records = json.loads(dataset_json)
    df = pd.DataFrame(records)

    n_rows = int(df.shape[0])
    n_columns = int(df.shape[1])
    columns = list(df.columns)
    col_text = ", ".join(columns) if columns else "none"

    # Disney-specific alignment summary if available
    alignment_lines = []
    if "alignment" in df.columns:
        alignment_counts = (
            df["alignment"]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("", "unknown")
            .value_counts()
            .head(int(top_n))
            .reset_index()
        )
        alignment_counts.columns = ["alignment", "count"]
        if len(alignment_counts) > 0:
            for row in alignment_counts.itertuples(index=False):
                alignment_lines.append(f"- {row.alignment}: {int(row.count)} characters")
        else:
            alignment_lines.append("- No alignment values found.")
    else:
        alignment_lines.append("- Alignment column is not present in this dataset.")

    summary_text = (
        "Dataset Summary\n"
        f"- This dataset has {n_rows} rows and {n_columns} columns.\n"
        f"- Columns included: {col_text}\n"
        "- Top alignment categories:\n"
        f"{chr(10).join(alignment_lines)}"
    )
    return summary_text


def format_text(text, style):
    """
    Format text as uppercase, lowercase, or title case.

    Parameters:
    -----------
    text : str
        The text to format
    style : str
        One of 'upper', 'lower', or 'title'

    Returns:
    --------
    str
        Formatted text
    """
    s = str(text)
    key = str(style).lower().strip()
    if key == "upper":
        return s.upper()
    if key == "lower":
        return s.lower()
    if key == "title":
        return s.title()
    return s


def identify_patterns(dataset_json, top_n=5):
    """
    Identify simple patterns in the Disney dataset.

    Parameters:
    -----------
    dataset_json : str
        JSON string in records format (list of objects)
    top_n : int
        Number of top names to list for each appearance metric

    Returns:
    --------
    str
        Plain-language pattern summary
    """
    records = json.loads(dataset_json)
    df = pd.DataFrame(records)

    if df.empty:
        return "Pattern Summary\n- No rows are available in this dataset sample."

    # Make sure expected columns exist and are numeric where needed
    for col in ["n_films", "n_tv_shows", "n_video_games"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "name" not in df.columns:
        df["name"] = "unknown"

    # Add total media appearances to find broad visibility patterns
    df["total_appearances"] = df["n_films"] + df["n_tv_shows"] + df["n_video_games"]

    top_total = df.nlargest(int(top_n), "total_appearances")[["name", "total_appearances"]]
    top_films = df.nlargest(int(top_n), "n_films")[["name", "n_films"]]
    top_tv = df.nlargest(int(top_n), "n_tv_shows")[["name", "n_tv_shows"]]

    avg_films = float(df["n_films"].mean())
    avg_tv = float(df["n_tv_shows"].mean())
    avg_games = float(df["n_video_games"].mean())

    lines = [
        "Pattern Summary",
        (
            f"- Average appearances per character: films={avg_films:.2f}, "
            f"tv_shows={avg_tv:.2f}, video_games={avg_games:.2f}."
        ),
        "- Most visible characters by total appearances:",
    ]
    for row in top_total.itertuples(index=False):
        lines.append(f"  - {row.name}: {int(row.total_appearances)} total appearances")

    lines.append("- Most appearances in films:")
    for row in top_films.itertuples(index=False):
        lines.append(f"  - {row.name}: {int(row.n_films)} films")

    lines.append("- Most appearances in TV shows:")
    for row in top_tv.itertuples(index=False):
        lines.append(f"  - {row.name}: {int(row.n_tv_shows)} TV shows")

    return "\n".join(lines)


# 3. DEFINE TOOL METADATA ###################################

# Tool metadata for summarize_dataset
tool_summarize_dataset = {
    "type": "function",
    "function": {
        "name": "summarize_dataset",
        "description": (
            "Create a plain-language dataset summary that reports row/column "
            "counts, column names, and top alignment categories."
        ),
        "parameters": {
            "type": "object",
            "required": ["dataset_json"],
            "properties": {
                "dataset_json": {
                    "type": "string",
                    "description": "Dataset encoded as a JSON records string.",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of top alignment categories to return.",
                    "default": 5,
                },
            },
        },
    },
}

# Tool metadata for format_text
tool_format_text = {
    "type": "function",
    "function": {
        "name": "format_text",
        "description": "Format text as uppercase, lowercase, or title case.",
        "parameters": {
            "type": "object",
            "required": ["text", "style"],
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to format.",
                },
                "style": {
                    "type": "string",
                    "description": "One of: upper, lower, title.",
                },
            },
        },
    },
}

# Tool metadata for identify_patterns
tool_identify_patterns = {
    "type": "function",
    "function": {
        "name": "identify_patterns",
        "description": (
            "Analyze Disney character media appearance fields and return a short "
            "plain-language summary of key patterns."
        ),
        "parameters": {
            "type": "object",
            "required": ["dataset_json"],
            "properties": {
                "dataset_json": {
                    "type": "string",
                    "description": "Dataset encoded as a JSON records string.",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of top characters to report per pattern.",
                    "default": 5,
                },
            },
        },
    },
}


# 4. TASK 1: FETCH DISNEY DATA ###################################


# Match the lab_agents.py workflow pattern:
# 1) fetch a larger dataset, 2) random sample, 3) keep a smaller subset for model context.
print("Starting Task 1: fetching Disney data...", flush=True)
task1_start = time.perf_counter()
data = get_characters(limit=500)
random_sample = data.sample(n=min(200, len(data)), random_state=42)
summary_table = random_sample.head(15)
task1_output = summary_table.to_json(orient="records")
task1_elapsed = time.perf_counter() - task1_start
print(f"Finished Task 1 in {task1_elapsed:.2f}s", flush=True)


# 5. TASK 2: AGENT 1 CALLS summarize_dataset ###################################

role_agent_1 = (
    "You are a data analyst assistant. "
    "Always call the summarize_dataset tool exactly once using the user's dataset_json. "
    "Return only the tool result."
)

task_agent_1 = (
    "Use summarize_dataset on this Disney character dataset and include top_n=6.\n\n"
    f"{task1_output}"
)

print("Starting Task 2: agent calls summarize_dataset...", flush=True)
task2_start = time.perf_counter()
try:
    agent1_resp = agent_run(
        role=role_agent_1,
        task=task_agent_1,
        tools=[tool_summarize_dataset],
        output="tools",
        model=MODEL,
    )
    task2_output = (
        agent1_resp[0].get("output", "")
        if isinstance(agent1_resp, list) and len(agent1_resp) > 0
        else str(agent1_resp)
    )
except (requests.exceptions.RequestException, ValueError) as e:
    # Fallback keeps the workflow moving when a local model does not support tools
    print(f"Agent tool call failed in Task 2. Falling back to direct tool call. Error: {e}", flush=True)
    task2_output = summarize_dataset(dataset_json=task1_output, top_n=6)
task2_elapsed = time.perf_counter() - task2_start
print(f"Finished Task 2 in {task2_elapsed:.2f}s", flush=True)


# 6. TASK 3: AGENT 2 CALLS identify_patterns ###################################

role_agent_2 = (
    "You are a Disney data analyst. "
    "Always call the identify_patterns tool exactly once using the user's dataset_json. "
    "Return only the tool output."
)

task_agent_2 = (
    "Use identify_patterns on this Disney character dataset and include top_n=5.\n\n"
    f"{task1_output}"
)

print("Starting Task 3: agent calls identify_patterns...", flush=True)
task3_start = time.perf_counter()
try:
    agent2_resp = agent_run(
        role=role_agent_2,
        task=task_agent_2,
        tools=[tool_identify_patterns],
        output="tools",
        model=MODEL,
    )
    task3_output = (
        agent2_resp[0].get("output", "")
        if isinstance(agent2_resp, list) and len(agent2_resp) > 0
        else str(agent2_resp)
    )
except (requests.exceptions.RequestException, ValueError) as e:
    print(f"Agent tool call failed in Task 3. Falling back to direct tool call. Error: {e}", flush=True)
    task3_output = identify_patterns(dataset_json=task1_output, top_n=5)
task3_elapsed = time.perf_counter() - task3_start
print(f"Finished Task 3 in {task3_elapsed:.2f}s", flush=True)


# 7. TASK 4: AGENT 3 CALLS format_text ###################################

role_agent_3 = (
    "You are a formatting assistant. "
    "Always call the format_text tool exactly once. "
    "Format the given summary using style='title' and return only the tool output."
)

task_agent_3 = (
    "Format this summary text with the tool using title case:\n\n"
    f"{task3_output}"
)

print("Starting Task 4: agent calls format_text...", flush=True)
task4_start = time.perf_counter()
try:
    agent3_resp = agent_run(
        role=role_agent_3,
        task=task_agent_3,
        tools=[tool_format_text],
        output="tools",
        model=MODEL,
    )
    task4_output = (
        agent3_resp[0].get("output", "")
        if isinstance(agent3_resp, list) and len(agent3_resp) > 0
        else str(agent3_resp)
    )
except (requests.exceptions.RequestException, ValueError) as e:
    print(f"Agent tool call failed in Task 4. Falling back to direct tool call. Error: {e}", flush=True)
    task4_output = format_text(text=task3_output, style="title")
task4_elapsed = time.perf_counter() - task4_start
print(f"Finished Task 4 in {task4_elapsed:.2f}s", flush=True)


# 8. VIEW RESULTS ###################################

print("=== Task 1: Disney Data (first 10 rows) ===")
print(data.head(10))
print()

print("=== Task 2: summarize_dataset output ===")
print(task2_output)
print()

print("=== Task 3: identify_patterns output ===")
print(task3_output)
print()

print("=== Task 4: format_text output ===")
print(task4_output)
print()

print("=== Runtime by Task (seconds) ===")
print(f"Task 1 (Fetch + sample): {task1_elapsed:.2f}s")
print(f"Task 2 (Agent + summarize_dataset tool): {task2_elapsed:.2f}s")
print(f"Task 3 (Agent + identify_patterns tool): {task3_elapsed:.2f}s")
print(f"Task 4 (Agent + format_text tool): {task4_elapsed:.2f}s")
