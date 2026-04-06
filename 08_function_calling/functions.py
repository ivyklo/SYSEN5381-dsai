# functions.py
# Function Calling Helper Functions
# Pairs with functions.R
# Tim Fraser

# This script contains functions used for multi-agent orchestration with function calling in Python.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import inspect  # to resolve tool functions defined in the caller script
import requests  # for HTTP requests
import json      # for working with JSON
import pandas as pd  # for data manipulation

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
    
    # If the agent has NO tools, perform a standard chat
    if tools is None:
        body = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(CHAT_URL, json=body, timeout=90)
        response.raise_for_status()
        result = response.json()
        
        return result["message"]["content"]
    else:
        # If the agent has tools, perform a tool call
        body = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "stream": False
        }
        
        response = requests.post(CHAT_URL, json=body, timeout=90)
        response.raise_for_status()
        result = response.json()
        
        # For any given tool call, execute the tool call
        if "tool_calls" in result.get("message", {}):
            tool_calls = result["message"]["tool_calls"]
            for tool_call in tool_calls:
                # Execute the tool function
                # Note: Tool functions must be defined in the global scope
                func_name = tool_call["function"]["name"]
                raw_args = tool_call["function"]["arguments"]
                # Ollama may return arguments as a JSON string or as an object
                func_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                # Prefer the caller script's globals (where tools are defined), then this module
                func = None
                frame = inspect.currentframe()
                try:
                    back = frame.f_back if frame else None
                    if back is not None:
                        func = back.f_globals.get(func_name)
                finally:
                    del frame
                if func is None:
                    func = globals().get(func_name)
                if func:
                    output = func(**func_args)
                    tool_call["output"] = output
        
        if all:
            return result
        else:
            # When output="tools", return the tool_calls list with outputs
            # When output="text", return the last tool call output or message content
            if "tool_calls" in result.get("message", {}):
                if output == "tools":
                    return tool_calls
                else:
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
        A cleaned DataFrame of Disney characters
    """

    # Disney API endpoint (REST)
    url = "https://api.disneyapi.dev/character"

    # The API is paginated with `page` and `pageSize`.
    # Loop through pages until we collect `limit` rows.
    characters = []
    page = 1

    while len(characters) < limit:
        page_size = min(50, max(1, limit - len(characters)))
        params = {"page": page, "pageSize": page_size}

        response = requests.get(
            url,
            params=params,
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        page_items = data.get("data", [])
        if not page_items:
            break

        characters.extend(page_items)

        # Stop if API reports no next page
        if not data.get("info", {}).get("nextPage"):
            break
        page += 1

    characters = characters[:limit]

    # Keep a compact, analysis-friendly schema
    cleaned = []
    for item in characters:
        cleaned.append(
            {
                "id": item.get("_id"),
                "name": item.get("name", ""),
                "alignment": item.get("alignment", ""),
                "n_films": len(item.get("films", [])),
                "n_tv_shows": len(item.get("tvShows", [])),
                "n_video_games": len(item.get("videoGames", [])),
            }
        )

    return pd.DataFrame(cleaned)
