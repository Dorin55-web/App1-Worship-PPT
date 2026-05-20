from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Song:
    title: str
    stanzas: Dict[str, str] = field(default_factory=dict)
    refrains: Dict[str, str] = field(default_factory=dict)
    bridges: Dict[str, str] = field(default_factory=dict)
    codas: Dict[str, str] = field(default_factory=dict)
    order: List[str] = field(default_factory=list)
    raw_text: str = ""

    def get_text_for_key(self, key: str) -> str:
        """Returnează textul pentru o cheie din order (ex: '1', 'R', 'B')."""
        if key in self.stanzas:
            return self.stanzas[key]
        if key in self.refrains:
            return self.refrains[key]
        if key in self.bridges:
            return self.bridges[key]
        if key in self.codas:
            return self.codas[key]
        return ""

    def get_label_for_key(self, key: str) -> str:
        """Returnează o etichetă descriptivă (ex: 'Strofa 1', 'Refren R')."""
        if key in self.stanzas:
            return f"Strofa {key}"
        if key in self.refrains:
            return "Refren"
        if key in self.bridges:
            return f"Bridge {key}"
        if key in self.codas:
            return f"Coda {key}"
        return f"Necunoscut ({key})"

    def get_effective_order(self) -> List[str]:
        """Returnează order-ul efectiv. Dacă order e gol, generează automat."""
        if self.order:
            return self.order
        # Generare automată: alternare strofă-refren
        result = []
        refrain_key = next(iter(self.refrains), None) if self.refrains else None
        for key in sorted(self.stanzas.keys(), key=int):
            result.append(key)
            if refrain_key:
                result.append(refrain_key)
        # Adaugă bridge la final dacă există
        for key in self.bridges:
            result.append(key)
            if refrain_key:
                result.append(refrain_key)
        return result


@dataclass
class FontCalculation:
    size_pt: int
    is_minimized: bool = False
    is_maximized: bool = False
    longest_slide: str = ""
    reason: str = ""


@dataclass
class HistoryEntry:
    title: str
    url: str
    filename: str
    timestamp: str = ""
