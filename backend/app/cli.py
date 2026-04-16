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
    format_checkpoints,
    format_command_result,
    format_diagnostics,
    format_history,
    format_history_export,
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
    subparsers.add_parser("checkpoints", help="Show pending automation checkpoints")
    subparsers.add_parser("privacy", help="Show privacy panel")
    subparsers.add_parser("diagnostics", help="Show local diagnostics")

    history = subparsers.add_parser("history", help="Show recent command history")
    history.add_argument("--limit", type=int, default=10)

    export_history = subparsers.add_parser("export-history", help="Export local command history")
    export_history.add_argument("--limit", type=int, default=None)
    export_history.add_argument("--output", help="Write JSON export to a file")

    clear_history = subparsers.add_parser("clear-history", help="Clear local command history")
    clear_history.add_argument("--confirm", action="store_true", help="Confirm history deletion")

    ask = subparsers.add_parser("ask", help="Send a text command")
    ask.add_argument("text", nargs="+")
    ask.add_argument("--confirm", action="store_true", help="Confirm sensitive actions")
    ask.add_argument("--private", action="store_true", help="Do not store this command in local history")
    ask.add_argument("--speak", action="store_true", help="Speak the response")

    subparsers.add_parser("chat", help="Start an interactive text session")
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
    if command == "checkpoints":
        return format_checkpoints(client.get("/presence"))
    if command == "privacy":
        return format_privacy(client.get("/privacy"))
    if command == "diagnostics":
        return format_diagnostics(client.get("/diagnostics"))
    if command == "history":
        return format_history(client.get("/history", {"limit": args.limit}))
    if command == "export-history":
        export = client.get("/history/export", {"limit": args.limit} if args.limit is not None else None)
        if args.output:
            write_json_file(args.output, export)
            return f"History exported to {args.output}"
        return json.dumps(export, indent=2, ensure_ascii=True)
    if command == "clear-history":
        result = client.post("/history/clear", {"confirm": args.confirm})
        return json.dumps(result, indent=2, ensure_ascii=True)
    if command == "ask":
        payload = {
            "text": " ".join(args.text),
            "confirm_actions": args.confirm,
            "private": args.private,
            "speak_response": args.speak,
        }
        return format_command_result(client.post("/command", payload))
    if command == "chat":
        return chat_loop(client)
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


CHAT_HELP = """Commands:
/help - show this help
/exit - leave chat
/panel - show local panel
/presence - show presence
/checkpoints - show pending automation checkpoints
/privacy - show privacy panel
/diagnostics - show local diagnostics
/history - show recent commands
/export-history - summarize a local history export
/clear-history - clear local command history
/pause - pause JARVIS
/resume - resume JARVIS
/start - start voice loop
/stop - stop voice loop
/private <text> - send without storing history
/confirm <text> - confirm sensitive action
/speak <text> - speak the response
"""


def parse_chat_line(line: str) -> tuple[str, dict[str, Any]]:
    text = line.strip()
    if not text:
        return "empty", {}
    if text in {"/exit", "/quit"}:
        return "exit", {}
    if text == "/help":
        return "help", {}
    if text in {
        "/panel",
        "/presence",
        "/checkpoints",
        "/privacy",
        "/diagnostics",
        "/history",
        "/export-history",
        "/clear-history",
        "/pause",
        "/resume",
        "/start",
        "/stop",
    }:
        return text.lstrip("/"), {}

    options = {"confirm_actions": False, "private": False, "speak_response": False}
    for prefix, key in (("/private ", "private"), ("/confirm ", "confirm_actions"), ("/speak ", "speak_response")):
        if text.startswith(prefix):
            options[key] = True
            text = text[len(prefix):].strip()
            break

    return "ask", {"text": text, **options}


def handle_chat_action(client: JarvisHttpClient, action: str, payload: dict[str, Any]) -> str:
    if action == "empty":
        return ""
    if action == "help":
        return CHAT_HELP
    if action == "panel":
        return fetch_panel(client)
    if action == "presence":
        return format_presence(client.get("/presence"))
    if action == "checkpoints":
        return format_checkpoints(client.get("/presence"))
    if action == "privacy":
        return format_privacy(client.get("/privacy"))
    if action == "diagnostics":
        return format_diagnostics(client.get("/diagnostics"))
    if action == "history":
        return format_history(client.get("/history", {"limit": 10}))
    if action == "export-history":
        return format_history_export(client.get("/history/export"))
    if action == "clear-history":
        return json.dumps(client.post("/history/clear", {"confirm": True}), indent=2, ensure_ascii=True)
    if action in {"pause", "resume", "start", "stop"}:
        return json.dumps(client.post(f"/{action}"), indent=2, ensure_ascii=True)
    if action == "ask":
        return format_command_result(client.post("/command", payload))
    raise JarvisCliError(f"Unknown chat action: {action}")


def chat_loop(
    client: JarvisHttpClient,
    input_func=input,
    output_func=print,
) -> str:
    output_func("JARVIS chat active. Type /help for commands, /exit to leave.")
    while True:
        try:
            line = input_func("jarvis> ")
        except EOFError:
            return "Chat closed."

        action, payload = parse_chat_line(line)
        if action == "exit":
            return "Chat closed."

        output = handle_chat_action(client, action, payload)
        if output:
            output_func(output)


def write_json_file(path: str, payload: dict[str, Any]):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=True)
        file.write("\n")


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
