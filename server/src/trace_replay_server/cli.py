from __future__ import annotations

import argparse
import threading
import time
import webbrowser

import uvicorn


def serve() -> None:
    parser = argparse.ArgumentParser(prog="trace-replay")
    parser.add_argument("command", nargs="?", default="serve")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if args.command != "serve":
        raise SystemExit(f"unsupported command: {args.command}")

    if not args.no_browser:
        threading.Thread(
            target=lambda: (time.sleep(0.8), webbrowser.open(f"http://{args.host}:{args.port}")),
            daemon=True,
        ).start()

    uvicorn.run("trace_replay_server.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    serve()
