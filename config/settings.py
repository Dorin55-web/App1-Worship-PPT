import json
import os
import copy
from pathlib import Path


CONFIG_DIR = Path(__file__).parent
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "app": {
        "language": "ro",
        "max_history": 5,
        "default_output_dir": "./output"
    },
    "verses": {
        "font_family": "Calibri",
        "font_min_size": 24,
        "font_max_size": 44,
        "font_size_step": 4,
        "color": "#FFFFFF",
        "bg_color": "#000000",
        "margin_inches": 0.5,
        "safety_margin_percent": {
            "height": 10,
            "width": 15
        }
    },
    "amin_slide": {
        "font_size": 22,
        "font_family": "Calibri",
        "is_bold": False,
        "is_italic": False,
        "color": "#FFFFFF",
        "position": {
            "right_cm": 2,
            "bottom_cm": 2
        },
        "align": "right"
    },
    "refrain": {
        "start_marker": "/:",
        "end_marker": ":/"
    }
}

_config = None


def load_config() -> dict:
    """Încarcă configurația din config.json. Creează fișierul dacă nu există."""
    global _config
    if _config is not None:
        return _config
    
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        _config = copy.deepcopy(DEFAULT_CONFIG)
    else:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                _config = json.load(f)
        except (json.JSONDecodeError, IOError):
            save_config(DEFAULT_CONFIG)
            _config = copy.deepcopy(DEFAULT_CONFIG)
    
    return _config


def save_config(config: dict) -> None:
    """Salvează configurația în config.json."""
    global _config
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    _config = config


def get(section: str, key: str, default=None):
    """Acces rapid: get('verses', 'font_min_size') → 24"""
    config = load_config()
    return config.get(section, {}).get(key, default)


def get_section(section: str) -> dict:
    """Returnează o secțiune completă."""
    config = load_config()
    return config.get(section, {})


def ensure_directories():
    """Creează directoarele data/ și output/ dacă nu există."""
    config = load_config()
    output_dir = Path(config["app"]["default_output_dir"])
    data_dir = Path("data")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
