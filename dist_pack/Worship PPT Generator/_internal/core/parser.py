import re
from typing import Tuple, List
from core.models import Song


def parse_song(title: str, raw_text: str) -> Song:
    """
    Parsează textul brut al unei cântări și returnează un obiect Song
    cu structura completă.
    
    Args:
        title: Titlul cântării
        raw_text: Text brut extras de scraper
    
    Returns:
        Song: Obiect cu strofe, refrene, bridge-uri, ordine
    """
    stanzas = {}
    refrains = {}
    bridges = {}
    codas = {}
    order = []
    
    current_section = None
    current_key = None
    current_lines = []
    
    lines = raw_text.split("\n")
    
    for line in lines:
        stripped = line.strip()
        
        # Detectare linie de ordine
        order_match = re.match(r'^(?:O|ORDINE)\s*:\s*(.*)', stripped, re.IGNORECASE)
        if order_match:
            order = _parse_order_line(order_match.group(1))
            continue
        
        # Detectare marcaj secțiune nouă
        section_type, section_key = _detect_section_marker(stripped)
        
        if section_type is not None:
            # Salvează secțiunea anterioară
            _save_section(current_section, current_key, current_lines,
                         stanzas, refrains, bridges, codas)
            
            # Inițiază secțiunea nouă
            current_section = section_type
            current_key = section_key
            current_lines = []
            
            # Verifică dacă pe aceeași linie cu marcajul există text
            remaining = _remove_marker(stripped, section_type, section_key)
            if remaining:
                current_lines.append(remaining)
        else:
            # Linie obișnuită — adaugă la secțiunea curentă
            if current_section is not None:
                current_lines.append(stripped)
            elif stripped:
                # Text fără secțiune explicită → tratează ca strofă 1
                if current_section is None:
                    current_section = "stanza"
                    current_key = "1"
                current_lines.append(stripped)
    
    # Salvează ultima secțiune
    _save_section(current_section, current_key, current_lines,
                 stanzas, refrains, bridges, codas)
    
    # Generare ordine implicită dacă lipsește
    if not order:
        order = _generate_default_order(stanzas, refrains, bridges, codas, raw_text)
    
    return Song(
        title=title,
        stanzas=stanzas,
        refrains=refrains,
        bridges=bridges,
        codas=codas,
        order=order,
        raw_text=raw_text
    )


def _detect_section_marker(line: str) -> Tuple:
    """
    Detectează dacă o linie este un marcaj de secțiune nouă.
    
    Returns:
        (section_type, section_key) sau (None, None) dacă nu e marcaj
    """
    line_lower = line.lower().strip()
    
    # Refren: R:, R1:, R2:, COR, REFREN, sau formatul "Strofa X" când e de fapt refren
    refrain_match = re.match(
        r'^(R(\d?):|COR|REFREN)\s*', line, re.IGNORECASE
    )
    if refrain_match:
        num = refrain_match.group(2) if refrain_match.group(2) else ""
        key = f"R{num}" if num else "R"
        return ("refrain", key)
    
    # Bridge: B:, B1:, PUNTE
    bridge_match = re.match(
        r'^(B(\d?):|PUNTE)\s*', line, re.IGNORECASE
    )
    if bridge_match:
        num = bridge_match.group(2) if bridge_match.group(2) else ""
        key = f"B{num}" if num else "B"
        return ("bridge", key)
    
    # Coda: C:, C1:, C2: (dar NU COR)
    coda_match = re.match(r'^C(\d*):\s*', line, re.IGNORECASE)
    if coda_match and not re.match(r'^COR', line, re.IGNORECASE):
        num = coda_match.group(1) if coda_match.group(1) else ""
        key = f"C{num}" if num else "C"
        return ("coda", key)
    
    # Strofă: 1., 2., 3., etc. sau "Strofa 1", "Strofă 1"
    stanza_match = re.match(r'^(?:strofa|strofă)\s*(\d+)\s*', line_lower)
    if stanza_match:
        return ("stanza", stanza_match.group(1))

    # Si formatul simplu: 1., 2., 3.
    stanza_match = re.match(r'^(\d+)\.\s*', line)
    if stanza_match:
        return ("stanza", stanza_match.group(1))

    # Informații: I:, I1:, etc. — secțiune de metadata/indice, se ignoră
    info_match = re.match(r'^I\d*:\s*', line, re.IGNORECASE)
    if info_match:
        return ("info", "I")

    return (None, None)


def _remove_marker(line: str, section_type: str, section_key: str) -> str:
    """Elimină marcajul de la începutul liniei și returnează restul textului."""
    if section_type == "stanza":
        # Acceptă "1.", "Strofa 1", "Strofă 1"
        pattern = rf'^(?:strofa|strofă)?\s*{section_key}\.?\s*'
    elif section_type == "refrain":
        if section_key == "R":
            pattern = r'^(R:|COR|REFREN)\s*'
        else:
            pattern = rf'^{section_key}:\s*'
    elif section_type == "bridge":
        if section_key == "B":
            pattern = r'^(B:|PUNTE)\s*'
        else:
            pattern = rf'^{section_key}:\s*'
    elif section_type == "coda":
        if section_key == "C":
            pattern = r'^C:\s*'
        else:
            pattern = rf'^{section_key}:\s*'
    else:
        return line
    
    return re.sub(pattern, '', line, flags=re.IGNORECASE).strip()


def _save_section(section_type, key, lines, stanzas, refrains, bridges, codas):
    """Salvează liniile acumulate în dicționarul corespunzător."""
    if section_type is None or not lines:
        return

    # Secțiunile de tip "info" (I:) sunt metadata — se ignoră complet
    if section_type == "info":
        return
    
    # Elimină linii goale de la început și sfârșit
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()
    
    # Elimină linii cu URL-uri sau informații (I:)
    filtered_lines = []
    for line in lines:
        line_stripped = line.strip()
        # Ignoră linii care încep cu I: sau conțin http
        if line_stripped.startswith('I:') or 'http' in line_stripped.lower():
            continue
        filtered_lines.append(line)
    
    if not filtered_lines:
        return
    
    text = "\n".join(filtered_lines)
    
    if section_type == "stanza":
        stanzas[key] = text
    elif section_type == "refrain":
        # Adaugă marcajele de repetare pentru refren (la încărcare inițială)
        lines_list = text.split('\n')
        if lines_list:
            # Adaugă /: la prima linie dacă nu există deja
            first_line = lines_list[0].strip()
            if not first_line.startswith('/:'):
                lines_list[0] = f"/: {lines_list[0]}"
            elif not first_line.startswith('/: '):
                # Marcajul există dar e lipit de text — adaugă spațiu
                lines_list[0] = '/: ' + lines_list[0][2:].lstrip()

            # Adaugă marcaj de sfârșit la ultima linie dacă nu există deja
            last_line = lines_list[-1].strip()
            # Verifică ambele formate: :/ (standard) sau /: (format resursecrestine.ro)
            has_end_marker = last_line.endswith(':/') or last_line.endswith('/:')
            if not has_end_marker:
                lines_list[-1] = f"{lines_list[-1]} :/"
            elif last_line.endswith('/:'):
                # Site-ul folosește /: la sfârșit în loc de :/ - normalizează
                lines_list[-1] = last_line[:-2] + ' :/'
            
            text = '\n'.join(lines_list)
        
        # Dacă refrenul există deja și cel nou e mai scurt, păstrează cel vechi
        if key in refrains and len(refrains[key].split('\n')) > len(lines):
            pass  # Păstrează refrenul existent (mai lung)
        else:
            refrains[key] = text
    elif section_type == "bridge":
        bridges[key] = text
    elif section_type == "coda":
        codas[key] = text


def _generate_default_order(stanzas, refrains, bridges, codas, raw_text="") -> list:
    """
    Generează ordine implicită când lipsește O: sau când ordinea e incompletă.
    
    Reguli:
    - Dacă sunt multiple refrene (R1, R2, R3...), fiecare strofă N folosește refrenul RN
    - Dacă e un singur refren (R), toate strofele folosesc același refren
    - Bridge-urile și Coda se adaugă la final
    """
    order = []
    
    # Sortează strofele numeric
    sorted_stanzas = sorted(stanzas.keys(), key=lambda x: int(x))
    
    # Găsește toate refrenele care apar la final (după ultima strofă)
    # Acestea sunt refrene finale (R2, R3, R4, etc.)
    final_refrains = []
    if sorted_stanzas:
        raw_lower = raw_text.lower()
        last_stanza_pos = -1
        
        # Găsește poziția ultimei strofe în text
        for i in range(len(sorted_stanzas) - 1, -1, -1):
            stanza_num = sorted_stanzas[i]
            patterns = [
                f"{stanza_num}.",
                f"strofa {stanza_num}",
                f"strofă {stanza_num}"
            ]
            for pattern in patterns:
                pos = raw_lower.find(pattern)
                if pos > last_stanza_pos:
                    last_stanza_pos = pos
        
        # Verifică fiecare refren să vedem dacă apare după ultima strofă
        for refrain_key in refrains:
            if refrain_key.startswith('R') and refrain_key != 'R':
                refrain_num = refrain_key[1:]  # Extrage numărul (2, 3, 4...)
                refrain_pos = raw_lower.find(f'r{refrain_num}:')
                if refrain_pos > last_stanza_pos and last_stanza_pos > 0:
                    final_refrains.append(refrain_key)
        
        # Sortează refrenele finale (R2, R3, R4...)
        final_refrains.sort(key=lambda x: int(x[1:]))
    
    # Pentru fiecare strofă, găsește refrenul corespunzător
    for idx, stanza_key in enumerate(sorted_stanzas):
        order.append(stanza_key)
        
        # Caută refrenul specific pentru această strofă (R1 pentru strofa 1, etc.)
        stanza_num = int(stanza_key)
        specific_refrain = f"R{stanza_num}"
        
        # Dacă suntem la ultima strofă și avem refrene finale, nu adăugăm refren aici
        is_last_stanza = (idx == len(sorted_stanzas) - 1)
        if is_last_stanza and final_refrains:
            # Nu adăugăm niciun refren aici, refrenele finale vor fi adăugate la final
            pass
        elif specific_refrain in final_refrains:
            # Refrenul specific e un refren final, nu-l punem după strofa lui
            # În schimb, folosim R1 (primul refren disponibil)
            if 'R1' in refrains:
                order.append('R1')
            elif refrains:
                generic_refrain = next(iter(refrains))
                order.append(generic_refrain)
        elif specific_refrain in refrains:
            # Folosește refrenul specific (R1, R2, R3...)
            order.append(specific_refrain)
        elif refrains:
            # Dacă nu există refren specific, folosește primul disponibil (R)
            generic_refrain = next(iter(refrains))
            order.append(generic_refrain)
    
    # Adaugă refrenele finale la final (R2, R3, R4, etc.)
    for refrain_key in final_refrains:
        if refrain_key in refrains:
            order.append(refrain_key)
    
    # Adaugă bridge-urile la final
    for key in bridges:
        order.append(key)
        # Bridge-urile folosesc ultimul refren sau primul disponibil
        if refrains:
            last_refrain = sorted(refrains.keys())[-1] if len(refrains) > 1 else next(iter(refrains))
            order.append(last_refrain)
    
    # Adaugă coda la final (fără refren după)
    for key in codas:
        order.append(key)
    
    return order


def _parse_order_line(order_text: str) -> list:
    """
    Parsează linia de ordine. Exemplu: '1 R 2 R 3 B R' → ['1', 'R', '2', 'R', '3', 'B', 'R']
    """
    parts = order_text.strip().split()
    return [p.strip() for p in parts if p.strip()]
