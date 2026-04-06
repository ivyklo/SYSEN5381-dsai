# ACTIVITY_agents_with_tools.py
# Agents with Tools — format_text activity
# Pairs with ACTIVITY_agents_with_tools.md
# updated script using 03_agents_with_function_calling.py by Tim Fraser

# Load helper functions for agent orchestration
from functions import agent

## 0.3 Configuration #################################

# Select model of interest
MODEL = "smollm2:1.7b"

# 1. DEFINE FUNCTIONS TO BE USED AS TOOLS ###################################

# Define a function to be used as a tool
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

# 2. DEFINE TOOL METADATA ###################################

# Define the tool metadata for format_text
tool_format_text = {
    "type": "function",
    "function": {
        "name": "format_text",
        "description": "Format text as uppercase, lowercase, or title case",
        "parameters": {
            "type": "object",
            "required": ["text", "style"],
            "properties": {
                "text": {
                    "type": "string",
                    "description": "the text to format"
                },
                "style": {
                    "type": "string",
                    "description": "one of: upper, lower, title"
                }
            }
        }
    }
}

# 3. EXAMPLE 1: STANDARD CHAT (NO TOOLS) ###################################

# Trying to call a standard chat without tools
# The agent() function from functions.py handles this automatically
messages = [
    {"role": "user", "content": "Write a haiku about cheese."}
]

# Keep this in its own variable — tool examples below need this string
resp_chat = agent(messages=messages, model=MODEL, output="text")
print("📝 Standard Chat Response:")
print(resp_chat)
print()

# 4. EXAMPLE 2: TOOL CALL #1 ###################################

# Format the prior chat response (haiku) with the tool — not a hardcoded phrase
messages = [
    {
        "role": "user",
        "content": (
            "Format the following text in uppercase using the tool.\n\n"
            + resp_chat
        ),
    }
]

resp = agent(messages=messages, model=MODEL, output="tools", tools=[tool_format_text])
print("🔧 Tool Call #1 Result:")
print(resp)
print()

# Access the output from the tool call
if isinstance(resp, list) and len(resp) > 0:
    print(f"Tool output: {resp[0].get('output', 'No output')}")
    print()

# 5. EXAMPLE 3: TOOL CALL #2 ###################################

# Chain a second formatting step using the first tool output
# Second tool call builds on the first tool's output (uppercase haiku)
formatted = resp[0].get("output", resp_chat) if isinstance(resp, list) else resp_chat

messages = [
    {
        "role": "user",
        "content": (
            f"Using the tool, format this exact string in title case: {formatted!r}"
        ),
    }
]

resp2 = agent(messages=messages, model=MODEL, output="tools", tools=[tool_format_text])
print("🔧 Tool Call #2 Result:")
print(resp2)
print()

# Compare against manual approach
print("📊 Manual Format (title case):")
manual = str(formatted).title()
print(manual)
print()

# Note: We can use the agent() function to rapidly build and test out agents with or without tools.
