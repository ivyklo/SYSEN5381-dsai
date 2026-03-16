"""
lab_agents.py
Multi-Agent Workflow for Disney Characters
Pairs with LAB_prompt_design.md

This script demonstrates a 3-step workflow using Disney character data:
1) Fetch characters from the Disney API, 2) analyze patterns, and 3) write a short report.
"""

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import pandas as pd  # for data manipulation

# If you haven't already, install these packages...
# pip install pandas requests

## 0.2 Load Functions ##################################

from lab_functions import get_characters, df_as_text, agent_run


# 1. CONFIGURATION ###################################

# Select model of interest
MODEL = "smollm2:135m"


# 2. WORKFLOW EXECUTION ###################################

# Task 1 - Data Fetch Function -------------------------
# Get a sample of Disney characters from the API
data = get_characters(limit=500)
random_sample = data.sample(n=200, random_state=42)  # 200 random rows to analyze

# For the analyst, keep a smaller table to fit comfortably into the model context
summary_table = random_sample.head(40)

# Convert the data to a markdown table string
task2_input = df_as_text(summary_table)


# Task 2 - Analyst Agent -------------------------
# This agent analyzes the character table and returns a concise markdown summary
role_analyst = (
    "You are a data analyst who studies Disney characters.\n"
    "The user will give you a markdown table with columns like name, films, "
    "short_films, tv_shows, video_games, alignment, allies, and enemies.\n"
    "Your job is to:\n"
    "1) Identify interesting patterns (for example: characters that appear in many films, "
    "common franchises, or notable heroes vs villains).\n"
    "2) Return a short markdown section that includes:\n"
    "   - One small markdown table (no more than 10 rows, 5 columns) summarizing key statistics.\n"
    "   - A short bullet list (2–4 bullets) highlighting the most interesting findings.\n"
    "Be concise and stay focused on what can be inferred from the table only."
)

analysis_text = agent_run(
    role=role_analyst,
    task=task2_input,
    model=MODEL,
    output="text",
)


# Task 3 - Report Writer Agent -------------------------
# This agent takes the analysis and writes a short report
role_reporter = (
    "You are a concise science and culture writer.\n"
    "The user will give you an analysis of Disney character data.\n"
    "Write a short, clearly structured report (about 150–250 words) in markdown that:\n"
    "- Start with a concise headline (max 50 characters)\n"
    "- Explains the main patterns in an accessible way for a general audience.\n"
    "- Includes an introduction, 2–3 key insights sections with headings\n"
    "- Does not repeat full tables, but may reference them descriptively.\n"
    "- Includes a brief concluding remark.\n"
    "Keep the tone neutral and informative."
)

report_text = agent_run(
    role=role_reporter,
    task=analysis_text,
    model=MODEL,
    output="text",
)


# 3. VIEW RESULTS ###################################

print("=== Agent 1 Result (Data Fetch: first 10 rows) ===")
print(summary_table.head(10))
print()

print("=== Agent 2 Result (Analysis) ===")
print(analysis_text)
print()

print("=== Agent 3 Result (Report) ===")
print(report_text)

