from trace_replay import trace


@trace(capture_prompt_arg="prompt")
def run(prompt: str) -> str:
    return f"[openai-mock] {prompt}"


if __name__ == "__main__":
    print(run("hello from openai example"))
