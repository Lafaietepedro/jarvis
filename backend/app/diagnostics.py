import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any


OPTIONAL_BINARIES = (
    "pactl",
    "playerctl",
    "xdg-open",
    "code",
    "firefox",
    "google-chrome",
    "x-terminal-emulator",
    "espeak",
)


def collect_diagnostics(context: dict[str, Any]) -> dict[str, Any]:
    model_path = os.environ.get("VOSK_MODEL_PATH")
    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "python": sys.version.split()[0],
        },
        "project": context["project"],
        "privacy": context["privacy"],
        "audio": {
            "vosk_model_path": model_path,
            "vosk_model_available": bool(model_path and Path(model_path).exists()),
        },
        "binaries": {
            binary: {
                "available": shutil.which(binary) is not None,
                "path": shutil.which(binary),
            }
            for binary in OPTIONAL_BINARIES
        },
        "environment": {
            "JARVIS_ENABLE_CLOUD": os.environ.get("JARVIS_ENABLE_CLOUD") == "1",
            "JARVIS_ENABLE_DESKTOP_ACTIONS": os.environ.get("JARVIS_ENABLE_DESKTOP_ACTIONS") == "1",
            "JARVIS_ENABLE_SHELL": os.environ.get("JARVIS_ENABLE_SHELL") == "1",
            "JARVIS_ENABLE_MEDIA_ACTIONS": os.environ.get("JARVIS_ENABLE_MEDIA_ACTIONS") == "1",
            "JARVIS_DISABLE_MEMORY": os.environ.get("JARVIS_DISABLE_MEMORY") == "1",
        },
    }
