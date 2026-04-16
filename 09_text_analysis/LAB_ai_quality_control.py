# LAB_ai_quality_control.py
# AI-Assisted Text Quality Control (Lab Version)
# Tim Fraser
#
# This lab script mirrors 02_ai_quality_control.py and is designed for prompt
# iteration practice. It adds a modified quality control prompt with stricter
# scoring guidance and JSON formatting rules so students can compare outcomes.

# 0. Setup #################################

## 0.1 Load Packages #################################

# If you have not already, install required packages:
# pip install pandas requests python-dotenv

import json  # for JSON operations
import os  # for environment variables
import re  # for text processing
import time  # for small delay in batch checks

import pandas as pd  # for data wrangling
import requests  # for HTTP requests
from dotenv import load_dotenv  # for loading .env file

## 0.2 Configuration #################################

# Choose your AI provider: "ollama" or "openai"
AI_PROVIDER = "ollama"  # Change to "openai" if using OpenAI

# Ollama configuration
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"
OLLAMA_MODEL = "llama3.2:latest"  # Use a model that supports JSON output

# OpenAI configuration
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"  # Low-cost model

## 0.3 Load Sample Data #################################

# Load sample report text for quality control
with open("09_text_analysis/data/sample_reports.txt", "r", encoding="utf-8") as f:
    sample_text = f.read()

# Split text into individual reports
reports = [r.strip() for r in sample_text.split("\n\n") if r.strip()]
report = reports[0]

# Load source data (if available) for accuracy checking
source_data = """White County, IL | 2015 | PM10 | Time Driven | hours
|type        |label_value |label_percent |
|:-----------|:-----------|:-------------|
|Light Truck |2.7 M       |51.8%         |
|Car/ Bike   |1.9 M       |36.1%         |
|Combo Truck |381.3 k     |7.3%          |
|Heavy Truck |220.7 k     |4.2%          |
|Bus         |30.6 k      |0.6%          |"""

print("📝 Report for Quality Control:")
print("---")
print(report)
print("---\n")

# 1. AI Quality Control Function #################################

## 1.1 Create Quality Control Prompt #################################

# This modified prompt is designed for lab iteration in Task 4.
# It adds stricter scoring anchors and asks for evidence-based notes.
def create_quality_control_prompt(report_text, source_data=None):
    instructions = """
You are a strict quality control validator for AI-generated reports.
Evaluate the report and return ONLY valid JSON (no markdown, no extra text).
Use conservative scoring: only give 5 when the criterion is fully met.
"""

    data_context = ""
    if source_data is not None:
        data_context = f"""

Source Data for Fact Checking:
{source_data}
"""

    criteria = """

Quality Control Criteria:

1) accurate (boolean)
- true only if there are NO factual errors, NO unsupported numeric claims, and NO contradictions with source data.
- false if any single factual or numerical issue exists.

2) accuracy (1-5)
- 1 = major factual errors
- 2 = several factual issues
- 3 = mostly correct with minor issues
- 4 = accurate with only trivial ambiguity
- 5 = fully accurate and consistent with source data

3) formality (1-5)
- 1 = casual or conversational
- 3 = mixed tone
- 5 = polished professional/government-report style

4) faithfulness (1-5)
- 1 = makes unsupported or exaggerated claims
- 3 = mostly tied to data but some overreach
- 5 = all claims clearly tied to provided data

5) clarity (1-5)
- 1 = confusing
- 3 = understandable but uneven
- 5 = clear, precise, and easy to follow

6) succinctness (1-5)
- 1 = wordy or repetitive
- 3 = moderate concision
- 5 = concise with no unnecessary text

7) relevance (1-5)
- 1 = mostly off-topic
- 3 = somewhat focused
- 5 = fully focused on the data and task

Return JSON in exactly this schema:
{
  "accurate": true,
  "accuracy": 1,
  "formality": 1,
  "faithfulness": 1,
  "clarity": 1,
  "succinctness": 1,
  "relevance": 1,
  "details": "<=50 words total summary",
  "issues_found": [
    "Short evidence-based issue 1",
    "Short evidence-based issue 2"
  ]
}

Rules:
- Use double-quoted JSON keys and strings.
- Keep "details" at 50 words or fewer.
- Include at least 1 issue in "issues_found" if accurate=false.
- If accurate=true, "issues_found" may be an empty list.
"""

    full_prompt = f"""
{instructions}
{data_context}

Report Text to Validate:
{report_text}
{criteria}
"""
    return full_prompt

## 1.2 Query AI Function #################################

def query_ai_quality_control(prompt, provider=AI_PROVIDER):
    if provider == "ollama":
        url = f"{OLLAMA_HOST}/api/chat"
        body = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "format": "json",
            "stream": False,
        }

        response = requests.post(url, json=body)
        response.raise_for_status()
        response_data = response.json()
        output = response_data["message"]["content"]

    elif provider == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in .env file. Please set it up first.")

        url = "https://api.openai.com/v1/chat/completions"
        body = {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a strict quality control validator. Return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        response_data = response.json()
        output = response_data["choices"][0]["message"]["content"]
    else:
        raise ValueError("Invalid provider. Use 'ollama' or 'openai'.")

    return output

## 1.3 Parse Quality Control Results #################################

def parse_quality_control_results(json_response):
    # Some models still return wrapper text, so we recover JSON if needed.
    json_match = re.search(r"\{.*\}", json_response, re.DOTALL)
    if json_match:
        json_response = json_match.group(0)

    quality_data = json.loads(json_response)

    results = pd.DataFrame(
        {
            "accurate": [quality_data.get("accurate", False)],
            "accuracy": [quality_data.get("accuracy", None)],
            "formality": [quality_data.get("formality", None)],
            "faithfulness": [quality_data.get("faithfulness", None)],
            "clarity": [quality_data.get("clarity", None)],
            "succinctness": [quality_data.get("succinctness", None)],
            "relevance": [quality_data.get("relevance", None)],
            "details": [quality_data.get("details", "")],
            "issues_found": [quality_data.get("issues_found", [])],
        }
    )

    return results

# 2. Run Quality Control #################################

## 2.1 Create Quality Control Prompt #################################

quality_prompt = create_quality_control_prompt(report, source_data)
print("🤖 Querying AI for quality control...\n")

## 2.2 Query AI #################################

ai_response = query_ai_quality_control(quality_prompt, provider=AI_PROVIDER)
print("📥 AI Response (raw):")
print(ai_response)
print()

## 2.3 Parse and Display Results #################################

quality_results = parse_quality_control_results(ai_response)
print("✅ Quality Control Results:")
print(quality_results)
print()

## 2.4 Calculate Overall Score #################################

likert_scores = quality_results[["accuracy", "formality", "faithfulness", "clarity", "succinctness", "relevance"]]
overall_score = likert_scores.mean(axis=1).values[0]
quality_results["overall_score"] = round(overall_score, 2)

print(f"📊 Overall Quality Score (average of Likert scales): {overall_score:.2f} / 5.0")
print(f"📊 Accuracy Check: {'✅ PASS' if quality_results['accurate'].values[0] else '❌ FAIL'}")
print(f"📊 Issues Found: {quality_results['issues_found'].values[0]}\n")

# 3. Quality Control Multiple Reports #################################

## 3.1 Batch Quality Control Function #################################

def check_multiple_reports(reports, source_data=None):
    print(f"🔄 Performing quality control on {len(reports)} reports...\n")
    all_results = []

    for i, report_text in enumerate(reports, 1):
        print(f"Checking report {i} of {len(reports)}...")

        prompt = create_quality_control_prompt(report_text, source_data)

        try:
            response = query_ai_quality_control(prompt, provider=AI_PROVIDER)
            results = parse_quality_control_results(response)
            results["report_id"] = i
            all_results.append(results)
        except Exception as e:
            print(f"❌ Error checking report {i}: {e}")

        time.sleep(1)

    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        return combined_results

    return pd.DataFrame()

## 3.2 Run Batch Quality Control (Optional) #################################

# Uncomment to check all reports:
# if len(reports) > 1:
#     batch_results = check_multiple_reports(reports, source_data)
#     print("\n📊 Batch Quality Control Results:")
#     print(batch_results)

print("✅ AI quality control complete!")
print("💡 For the lab, iterate on create_quality_control_prompt() and compare score changes.")
