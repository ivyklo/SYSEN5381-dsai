# functions.py
# Multi-Agent Orchestration Functions
# Pairs with functions.R
# Tim Fraser

# This script contains functions used for multi-agent orchestration in Python.

# 0. SETUP ####################################

## 0.1 Load Packages #################################

import requests  # for HTTP requests
import json      # for working with JSON
import pandas as pd  # for data manipulation
from datetime import datetime  # for date parsing

# If you haven't already, install these packages...
# pip install requests pandas

## 0.2 Configuration #################################

# Default model and Ollama connection
DEFAULT_MODEL = "smollm2:1.7b"
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"
CHAT_URL = f"{OLLAMA_HOST}/api/chat"

# 1. AGENT FUNCTION ###################################

def agent(messages, model=DEFAULT_MODEL, output="text", tools=None, all=False):
    """
    Agent wrapper function that runs a single agent, with or without tools.
    
    Parameters:
    -----------
    messages : list
        List of message dictionaries with 'role' and 'content' keys.
        Must follow format: [{"role": "system", "content": "..."}, ...]
    model : str
        The model to be used for the agent (default: "smollm2:1.7b")
    output : str
        The output format (default: "text")
    tools : list, optional
        List of tool metadata dictionaries for function calling
    all : bool
        If True, return all responses. If False, return only the last response.
    
    Returns:
    --------
    str or list
        The agent's response(s)
    """
    
    # Options to reduce runaway/repetitive output (e.g. "**" spam) from small models
    options = {"num_predict": 1024, "repeat_penalty": 1.2}

    # If the agent has NO tools, perform a standard chat
    if tools is None:
        body = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options,
        }

        response = requests.post(CHAT_URL, json=body)
        response.raise_for_status()
        result = response.json()
        
        return result["message"]["content"]
    else:
        # If the agent has tools, perform a tool call
        body = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "options": options,
        }

        response = requests.post(CHAT_URL, json=body)
        response.raise_for_status()
        result = response.json()
        
        # For any given tool call, execute the tool call
        if "tool_calls" in result.get("message", {}):
            tool_calls = result["message"]["tool_calls"]
            for tool_call in tool_calls:
                # Execute the tool function
                # Note: Tool functions must be defined in the global scope
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                # Get the function from globals and execute it
                func = globals().get(func_name)
                if func:
                    output = func(**func_args)
                    tool_call["output"] = output
        
        if all:
            return result
        else:
            # Return the last tool call output or the message content
            if "tool_calls" in result.get("message", {}):
                return tool_calls[-1].get("output", result["message"]["content"])
            return result["message"]["content"]


def agent_run(role, task, tools=None, output="text", model=DEFAULT_MODEL):
    """
    Run an agent with a specific role and task.
    
    Parameters:
    -----------
    role : str
        The system prompt defining the agent's role
    task : str
        The user message/task for the agent
    tools : list, optional
        List of tool metadata for function calling
    output : str
        Output format (default: "text")
    model : str
        Model to use (default: DEFAULT_MODEL)
    
    Returns:
    --------
    str
        The agent's response
    """
    
    # Define the messages to be sent to the agent
    messages = [
        {"role": "system", "content": role},
        {"role": "user", "content": task}
    ]
    
    # Run the agent
    resp = agent(messages=messages, model=model, output=output, tools=tools)
    return resp


# 2. DATA CONVERSION FUNCTION ###################################

def df_as_text(df):
    """
    Convert a pandas DataFrame to a markdown table string.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The DataFrame to convert to text
    
    Returns:
    --------
    str
        A markdown-formatted table string
    """
    
    # Convert DataFrame to markdown table
    # pandas to_markdown() method creates markdown tables
    tab = df.to_markdown(index=False)
    return tab


# 3. API FUNCTION ###################################

def get_characters(limit=500):
    """
    Get data on characters from the Disney API.

    Parameters:
    -----------
    limit : int
        The maximum number of results to return (default: 500)

    Returns:
    --------
    pandas.DataFrame
        A DataFrame of characters
    """

    # Disney API endpoint (REST)
    url = "https://api.disneyapi.dev/character"

    # The API is paginated with `page` and `pageSize` query parameters.
    # We loop through pages until we collect `limit` characters or run out.
    characters = []
    page = 1

    while len(characters) < limit:
        # Page size should not exceed remaining requested rows
        page_size = min(50, max(1, limit - len(characters)))

        params = {
            "page": page,
            "pageSize": page_size,
        }

        response = requests.get(url, params=params, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()

        # Each page returns a list of character dicts under "data"
        page_items = data.get("data", [])
        if not page_items:
            break

        characters.extend(page_items)

        # Stop if there is no next page in the API
        info = data.get("info", {})
        next_page = info.get("nextPage")
        if not next_page:
            break

        page += 1

    # Trim to requested limit in case we fetched extra in the last page
    characters = characters[:limit]

    # Extract relevant fields for analysis
    processed_data = []
    for item in characters:
        processed_data.append(
            {
                "id": item.get("_id", None),
                "name": item.get("name", ""),
                "films": ", ".join(item.get("films", [])),
                "short_films": ", ".join(item.get("shortFilms", [])),
                "tv_shows": ", ".join(item.get("tvShows", [])),
                "video_games": ", ".join(item.get("videoGames", [])),
                "alignment": item.get("alignment", ""),
                "park_attractions": ", ".join(item.get("parkAttractions", [])),
                "allies": ", ".join(item.get("allies", [])),
                "enemies": ", ".join(item.get("enemies", [])),
                "source_url": item.get("sourceUrl", ""),
                "api_url": item.get("url", ""),
            }
        )

    df = pd.DataFrame(processed_data)
    return df
