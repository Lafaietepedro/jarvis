import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .cli_format import (
    format_command_result,
    format_diagnostics,
    format_history,
    format_panel,
    format_presence,
    format_privacy,
)


DEFAULT_BASE_URL = "http://127.0.0.1:8000"


class JarvisCliError(Exception):
    pass


class JarvisHttpClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._url(path, params)
        request = urllib.request.Request(url, method="GET")
        return self._open(request)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(payload or {}).encode("utf-8")
        request = urllib.request.Request(
            self._url(path),
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._open(request)

    def _url(self, path: str, params: dict[str, Any] | None = None) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        return url

    def _open(self, request: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise JarvisCliError(f"Could not reach JARVIS API at {self.base_url}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise JarvisCliError("JARVIS API returned invalid JSON.") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JARVIS local CLI")
    parser.add_argument("--url", default=os.environ.get("JARVIS_URL", DEFAULT_BASE_URL), help="JARVIS API URL")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("panel", help="Show presence, privacy and recent history")
    watch = subparsers.add_parser("watch", help="Refresh the local panel")
    watch.add_argument("--interval", type=float, default=2.0)
    watch.add_argument("--iterations", type=int, default=0, help="0 means run until Ctrl+C")

    subparsers.add_parser("presence", help="Show presence state")
    subparsers.add_parser("privacy", help="Show privacy panel")
    subparsers.add_parser("diagnostics", help="Show local diagnostics")

    history = subparsers.add_parser("history", help="Show recent command history")
    history.add_argument("--limit", type=int, default=10)

    ask = subparsers.add_parser("ask", help="Send a text command")
    ask.add_argument("text", nargs="+")
    ask.add_argument("--confirm", action="store_true", help="Confirm sensitive actions")
    ask.add_argument("--private", action="store_true", help="Do not store this command in local history")
    ask.add_argument("--speak", action="store_true", help="Speak the response")

    subparsers.add_parser("pause", help="Pause JARVIS session")
    subparsers.add_parser("resume", help="Resume JARVIS session")
    subparsers.add_parser("start", help="Start voice loop")
    subparsers.add_parser("stop", help="Stop voice loop")

    return parser


def run(args: argparse.Namespace) -> str:
    client = JarvisHttpClient(args.url)
    command = args.command or "panel"

    if command == "panel":
        return format_panel(
            client.get("/presence"),
            client.get("/privacy"),
            client.get("/history", {"limit": 5}),
            client.get("/diagnostics"),
        )
    if command == "watch":
        return watch_panel(client, interval=args.interval, iterations=args.iterations)
    if command == "presence":
        return format_presence(client.get("/presence"))
    if command == "privacy":
        return format_privacy(client.get("/privacy"))
    if command == "diagnostics":
        return format_diagnostics(client.get("/diagnostics"))
    if command == "history":
        return format_history(client.get("/history", {"limit": args.limit}))
    if command == "ask":
        payload = {
            "text": " ".join(args.text),
            "confirm_actions": args.confirm,
            "private": args.private,
            "speak_response": args.speak,
        }
        return format_command_result(client.post("/command", payload))
    if command in {"pause", "resume", "start", "stop"}:
        return json.dumps(client.post(f"/{command}"), indent=2, ensure_ascii=True)

    raise JarvisCliError(f"Unknown command: {command}")


def fetch_panel(client: JarvisHttpClient) -> str:
    return format_panel(
        client.get("/presence"),
        client.get("/privacy"),
        client.get("/history", {"limit": 5}),
        client.get("/diagnostics"),
    )


def watch_panel(client: JarvisHttpClient, interval: float, iterations: int = 0) -> str:
    frames = []
    count = 0
    try:
        while True:
            frame = fetch_panel(client)
            count += 1
            if iterations:
                frames.append(frame)
                if count >= iterations:
                    return "\n\n--- refresh ---\n\n".join(frames)
            else:
                print("\033[2J\033[H" + frame, flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        return "Stopped."


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(run(args))
        return 0
    except JarvisCliError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
