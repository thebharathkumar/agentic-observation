from trace_replay import trace


@trace(capture_prompt_arg="prompt")
def call_tool(prompt: str) -> str:
    return f"[mcp-tool-mock] lookup({prompt})"


if __name__ == "__main__":
    print(call_tool("weather sf"))
