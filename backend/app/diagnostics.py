import os
import platform
import shutil
import sys
from importlib.util import find_spec
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

OPTIONAL_BINARY_PACKAGES = {
    "pactl": "pulseaudio-utils",
    "playerctl": "playerctl",
    "xdg-open": "xdg-utils",
    "code": "code",
    "firefox": "firefox",
    "google-chrome": "google-chrome-stable",
    "x-terminal-emulator": "x-terminal-emulator",
    "espeak": "espeak",
}

OPTIONAL_PYTHON_MODULES = {
    "vosk": "vosk",
    "sounddevice": "sounddevice",
    "soundfile": "soundfile",
    "pyttsx3": "pyttsx3",
}


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
        "python_modules": {
            name: {
                "available": find_spec(module) is not None,
                "module": module,
            }
            for name, module in OPTIONAL_PYTHON_MODULES.items()
        },
        "environment": {
            "JARVIS_ENABLE_CLOUD": os.environ.get("JARVIS_ENABLE_CLOUD") == "1",
            "JARVIS_ENABLE_DESKTOP_ACTIONS": os.environ.get("JARVIS_ENABLE_DESKTOP_ACTIONS") == "1",
            "JARVIS_ENABLE_SHELL": os.environ.get("JARVIS_ENABLE_SHELL") == "1",
            "JARVIS_ENABLE_MEDIA_ACTIONS": os.environ.get("JARVIS_ENABLE_MEDIA_ACTIONS") == "1",
            "JARVIS_DISABLE_MEMORY": os.environ.get("JARVIS_DISABLE_MEMORY") == "1",
        },
    }


def build_optional_dependency_report(diagnostics: dict[str, Any]) -> dict[str, Any]:
    missing_binaries = [
        name
        for name, item in diagnostics.get("binaries", {}).items()
        if not item.get("available")
    ]
    missing_python_modules = [
        name
        for name, item in diagnostics.get("python_modules", {}).items()
        if not item.get("available")
    ]
    vosk_model_missing = not diagnostics.get("audio", {}).get("vosk_model_available")
    install_hints = _build_install_hints(missing_binaries, missing_python_modules, vosk_model_missing)
    status = "ready"
    if missing_binaries or missing_python_modules or vosk_model_missing:
        status = "missing_optional"

    return {
        "status": status,
        "missing": {
            "binaries": missing_binaries,
            "python_modules": missing_python_modules,
            "vosk_model": vosk_model_missing,
        },
        "install_hints": install_hints,
    }


def _build_install_hints(
    missing_binaries: list[str],
    missing_python_modules: list[str],
    vosk_model_missing: bool,
) -> list[dict[str, str]]:
    hints = []
    packages = sorted(
        {
            OPTIONAL_BINARY_PACKAGES[name]
            for name in missing_binaries
            if name in OPTIONAL_BINARY_PACKAGES
        }
    )
    if packages:
        hints.append(
            {
                "label": "Linux packages",
                "command": f"sudo apt install {' '.join(packages)}",
            }
        )

    if missing_python_modules:
        hints.append(
            {
                "label": "Python packages",
                "command": "cd backend && .venv/bin/pip install -r requirements.txt",
            }
        )

    if vosk_model_missing:
        hints.append(
            {
                "label": "Vosk model",
                "command": "export VOSK_MODEL_PATH=/caminho/para/modelo",
            }
        )

    return hints
