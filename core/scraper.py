import requests
import re
from bs4 import BeautifulSoup
from typing import Tuple, Optional


class ScraperError(Exception):
    """Excepție personalizată pentru erori de scraping."""
    pass


def scrape_song(url: str) -> Tuple[str, str]:
    """
    Extrage titlul și textul brut al versurilor de pe URL-ul dat.
    
    Args:
        url: URL-ul complet al paginii cu versurile
    
    Returns:
        Tuple[str, str]: (title, raw_text)
        
    Raises:
        ScraperError: Dacă URL-ul e invalid, site-ul inaccesibil,
                      sau nu se găsesc versuri
    """
    # 1. Validare URL
    if not url.startswith(("http://", "https://")):
        raise ScraperError("URL invalid — trebuie să înceapă cu http:// sau https://")
    
    # 2. Request HTTP
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"
    except requests.ConnectionError:
        raise ScraperError("Nu se poate conecta la server. Verifică conexiunea la internet.")
    except requests.Timeout:
        raise ScraperError("Timeout — serverul nu a răspuns în 15 secunde.")
    except requests.HTTPError as e:
        raise ScraperError(f"Eroare HTTP: {e.response.status_code}")
    
    # 3. Parsare HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 4. Extragere titlu
    title = _extract_title(soup, url)
    
    # 5. Extragere text versuri
    raw_text = _extract_lyrics(soup)
    
    if not raw_text or len(raw_text.strip()) < 20:
        raise ScraperError(
            "Nu am putut extrage versurile. Structura HTML necunoscută."
        )
    
    return title, raw_text


def _extract_title(soup: BeautifulSoup, url: str) -> str:
    """Extrage titlul cântării din pagina HTML."""
    # Strategie 1: Tag <h1> sau <h2>
    for tag in ["h1", "h2"]:
        heading = soup.find(tag)
        if heading and heading.get_text(strip=True):
            return heading.get_text(strip=True)

    # Strategie 2: Tag <title> (elimină sufixul site-ului după " - ")
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        if ' - ' in title:
            title = title.split(' - ')[0].strip()
        return title

    # Strategie 3: din URL
    return url.split("/")[-1].replace("-", " ").replace("_", " ").title()


def _extract_lyrics(soup: BeautifulSoup) -> Optional[str]:
    """Extrage textul versurilor din HTML."""
    
    # STRATEGIA 1: Cauta containerul principal cu versuri (formatat)
    # Acest div contine versurile deja structurate
    resized_container = soup.find("div", class_="resized-text")
    if resized_container:
        # Extrage textul pastrand structura cu newline-uri
        lyrics = resized_container.get_text(separator="\n", strip=True)
        cleaned = _clean_lyrics_text(lyrics)
        if cleaned and len(cleaned) > 50:
            return cleaned
    
    # STRATEGIA 2: Cauta strofe individuale (strofa-text)
    strofa_divs = soup.find_all("div", class_="strofa-text")
    if strofa_divs:
        parts = []
        for div in strofa_divs:
            text = div.get_text(separator="\n", strip=True)
            if text:
                parts.append(text)
        if parts:
            lyrics = "\n\n".join(parts)
            cleaned = _clean_lyrics_text(lyrics)
            if cleaned and len(cleaned) > 50:
                return cleaned
    
    # STRATEGIA 3 (fallback): Parseaza tot textul paginii
    # Folosit doar daca strategiile de mai sus nu functioneaza
    all_text = soup.get_text(separator="\n", strip=True)
    
    # Cauta unde incep versurile
    start_markers = [
        "Strofă 1", "Strofă 2", "Strofă 3",
        "Strofa 1", "Strofa 2", "Strofa 3",
        "R: /:", "R:/:", "R:", "Refren", "REFREN",
        "1. ", "1.",
        "Paradis", "Doamne", "Isus", "Dumnezeu"
    ]
    
    # Gaseste cel mai devreme marker valid (nu primul din lista)
    idx_start = -1
    best_marker = None
    for marker in start_markers:
        idx = all_text.find(marker)
        if idx != -1:
            # Verifica daca e intr-un context de versuri (nu in meniu)
            context = all_text[max(0, idx-50):idx+100]
            # Verificare mai permisiva - daca gasim "1." sau "strofa" sau versuri tipice
            if any(v in context.lower() for v in ["strofa", "strofă", "refren", "r:", "1.", "2.", "3.", "/:", ":/", "când", "cum", "de unde"]):
                if idx_start == -1 or idx < idx_start:
                    idx_start = idx
                    best_marker = marker
    
    if idx_start == -1:
        return None
    
    # Cauta unde se termina versurile
    end_markers = [
        "Statistici", "Vizualizari", "Comentarii", 
        "Resurse inrudite", "De acelasi autor", "Din acelasi album",
        "Psalmii", "Un gand", "Pasajul zilei",
        "Termeni si conditii", "Politica de confidentialitate",
        "Adauga comentariu", "Raporteaza o problema",
        "Pentru a adauga comentarii", "Pentru a semnala o problema"
    ]
    
    idx_end = len(all_text)
    for marker in end_markers:
        idx = all_text.find(marker, idx_start)
        if idx != -1 and idx < idx_end:
            idx_end = idx
    
    # Extrage versurile
    lyrics = all_text[idx_start:idx_end]
    
    # Curata versurile
    cleaned = _clean_lyrics_text(lyrics)
    
    return cleaned if cleaned else None


def _clean_lyrics_text(text: str) -> str:
    """Curata textul versurilor de elemente nedorite."""
    lines = text.split("\n")
    cleaned_lines = []
    
    # Elemente UI de ignorat
    ui_patterns = [
        "autentificare", "meniu", "adauga", "voteaza",
        "resurse crestine", "text", "cantece", "audio", "video", "biblia",
        "mai multe", "doneaza", "toate resursele", "titlu", "autor", "album",
        "continut", "acorduri", "partitura", "powerpoint",
        "⛶", "▲", "|", "fara album", "tematica:", "diverse",
        "resursa adaugata de", "media", "voturi",
        "confirmata de", "orchestra", "1 / 1", "1/1"
    ]
    
    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        # Ignora linii goale multiple
        if not line_stripped:
            if cleaned_lines and cleaned_lines[-1] == "":
                continue
            cleaned_lines.append(line_stripped)
            continue
        
        # Ignora liniile care sunt doar elemente UI
        if any(pattern in line_lower for pattern in ui_patterns):
            continue
        
        # Ignora liniile care sunt doar numere mici (voturi, pagini)
        if line_stripped.isdigit() and len(line_stripped) <= 3:
            continue
        
        # Ignora liniile care contin doar caractere speciale
        if all(c in "|⛶▲xX/\\-" for c in line_stripped):
            continue
        
        # Ignora liniile care sunt doar data (ex: "05/06/2018")
        if len(line_stripped) == 10 and line_stripped.count("/") == 2:
            continue
        
        # Elimina indicatori de repetare muzicala de la finalul liniei
        # Ex: "x2", "x3", "2x", "(bis)", "(2x)" etc.
        line_stripped = re.sub(r'\s*x\s*\d+\s*$', '', line_stripped, flags=re.IGNORECASE)  # " x2", "x2"
        line_stripped = re.sub(r'\s*\d+\s*x\s*$', '', line_stripped, flags=re.IGNORECASE)  # "2x", "3x"
        line_stripped = re.sub(r'\s*\(\s*(?:bis|\d+x?)\s*\)\s*$', '', line_stripped, flags=re.IGNORECASE)  # "(bis)", "(2x)"
        
        # Dupa curatare, daca linia a ramas goala, o ignoram
        if not line_stripped.strip():
            continue
        
        cleaned_lines.append(line_stripped)
    
    # Eliminarea duplicatelor - doar daca textul apare de 2 ori complet identic
    # (o data formatat, o data plain text)
    # Nu elimina strofele care se repeta in cantece
    result = []
    seen_hashes = set()
    
    for line in cleaned_lines:
        # Cream un hash normalizat pentru linie
        line_hash = line.lower().strip()
        
        # Verificam daca am vazut deja aceasta linie in mod consecutiv
        if line_hash in seen_hashes:
            # Verificam daca urmatoarele linii sunt si ele identice (posibil duplicat)
            # Doar daca avem multe linii identice consecutive, e duplicat
            last_3_lines = [l.lower().strip() for l in result[-3:]] if len(result) >= 3 else []
            current_and_next = [line_hash]
            
            # Daca ultimele 3 linii sunt identice cu ce avem acum, e duplicat
            if len(last_3_lines) >= 3 and all(l == line_hash for l in last_3_lines):
                # Posibil duplicat, verificam daca restul textului e identic
                remaining_original = '\n'.join(cleaned_lines[len(result):])
                remaining_current = '\n'.join(cleaned_lines[cleaned_lines.index(line):])
                if remaining_original == remaining_current:
                    # E duplicat complet, oprim aici
                    break
        
        result.append(line)
        seen_hashes.add(line_hash)
    
    return "\n".join(result).strip()


def _clean_text(element) -> str:
    """Curăță textul extras din HTML."""
    # Înlocuiește <br> cu newline
    for br in element.find_all("br"):
        br.replace_with("\n")
    
    text = element.get_text(separator="\n")
    
    # Curățare rânduri goale consecutive (max 2)
    lines = text.split("\n")
    cleaned = []
    empty_count = 0
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            empty_count += 1
            if empty_count <= 2:
                cleaned.append("")
        else:
            empty_count = 0
            cleaned.append(stripped)
    
    return "\n".join(cleaned).strip()
