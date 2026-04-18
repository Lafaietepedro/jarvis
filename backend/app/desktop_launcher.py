from pathlib import Path


DEFAULT_APP_NAME = "JARVIS Local"
DEFAULT_UI_PATH = "/ui"
DEFAULT_DESKTOP_FILE = "jarvis-local.desktop"


def build_desktop_entry(
    ui_url: str,
    app_name: str = DEFAULT_APP_NAME,
    icon_path: str | None = None,
) -> str:
    safe_name = _clean_value(app_name)
    safe_url = _clean_value(ui_url)
    icon = _clean_value(icon_path or str(default_icon_path()))
    return "\n".join(
        [
            "[Desktop Entry]",
            "Type=Application",
            f"Name={safe_name}",
            "Comment=Assistente JARVIS local-first",
            f"Exec=xdg-open {safe_url}",
            f"Icon={icon}",
            "Terminal=false",
            "Categories=Utility;",
            "StartupNotify=false",
            "",
        ]
    )


def write_desktop_entry(output_path: str, content: str) -> Path:
    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def install_desktop_launcher(ui_url: str, output_path: str | None = None) -> Path:
    target = Path(output_path).expanduser() if output_path else default_user_launcher_path()
    return write_desktop_entry(str(target), build_desktop_entry(ui_url=ui_url))


def default_user_launcher_path() -> Path:
    return Path.home() / ".local" / "share" / "applications" / DEFAULT_DESKTOP_FILE


def default_icon_path() -> Path:
    return Path(__file__).with_name("ui") / "icon.svg"


def default_ui_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{DEFAULT_UI_PATH}"


def _clean_value(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ").strip()
