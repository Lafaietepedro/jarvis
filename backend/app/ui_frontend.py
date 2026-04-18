from pathlib import Path


UI_DIR = Path(__file__).with_name("ui")

ASSET_TYPES = {
    "app.js": "text/javascript",
    "styles.css": "text/css",
}


def read_ui_index() -> str:
    return _read_ui_file("index.html")


def read_ui_asset(asset_name: str) -> tuple[str, str] | None:
    media_type = ASSET_TYPES.get(asset_name)
    if media_type is None:
        return None
    return _read_ui_file(asset_name), media_type


def _read_ui_file(file_name: str) -> str:
    return (UI_DIR / file_name).read_text(encoding="utf-8")
