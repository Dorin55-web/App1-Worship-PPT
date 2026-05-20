import json
from pathlib import Path
from datetime import datetime
from typing import List
from core.models import HistoryEntry
from config import settings


HISTORY_DIR = Path("data")
HISTORY_FILE = HISTORY_DIR / "history.json"


def load_history() -> List[HistoryEntry]:
    """Încarcă istoricul din fișier. Returnează listă goală dacă nu există."""
    if not HISTORY_FILE.exists():
        return []
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return [
            HistoryEntry(
                title=entry["title"],
                url=entry["url"],
                filename=entry["filename"],
                timestamp=entry.get("timestamp", "")
            )
            for entry in data.get("entries", [])
        ]
    except (json.JSONDecodeError, KeyError):
        return []


def save_history(entries: List[HistoryEntry]) -> None:
    """Salvează istoricul în fișier."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    data = {
        "entries": [
            {
                "title": entry.title,
                "url": entry.url,
                "filename": entry.filename,
                "timestamp": entry.timestamp
            }
            for entry in entries
        ]
    }
    
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_entry(title: str, url: str, filename: str) -> None:
    """
    Adaugă o intrare nouă în istoric.
    Păstrează doar ultimele N intrări (din config).
    """
    max_history = settings.get("app", "max_history", 5)
    
    entries = load_history()
    
    new_entry = HistoryEntry(
        title=title,
        url=url,
        filename=filename,
        timestamp=datetime.now().isoformat(timespec="seconds")
    )
    
    entries.insert(0, new_entry)
    
    entries = entries[:max_history]
    
    save_history(entries)


def get_recent(count: int = 5) -> List[HistoryEntry]:
    """Returnează ultimele N intrări din istoric."""
    entries = load_history()
    return entries[:count]


def clear_history() -> None:
    """Șterge tot istoricul."""
    save_history([])
