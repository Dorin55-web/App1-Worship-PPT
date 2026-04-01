from core.models import Song, FontCalculation
from config import settings


# Dimensiuni slide PowerPoint (16:9)
SLIDE_WIDTH_INCHES = 13.333
SLIDE_HEIGHT_INCHES = 7.5

# Margine de 0.4 inch pe fiecare parte
MARGIN_INCHES = 0.4


def calculate_font_size(song: Song, use_caps: bool = False) -> FontCalculation:
    """
    Calculează dimensiunea optimă a fontului pentru fiecare slide în parte,
    începând de la 20pt și crescând până când textul atinge limita de 0.5" de margine.
    
    Algoritm:
    1. Pentru fiecare slide, începe cu font = 20pt
    2. Crește fontul cu 1pt la fiecare pas
    3. Verifică dacă textul încape în slide (cu 0.5" margini pe toate părțile)
    4. Când textul depășește limita, oprește și salvează fontul maxim pentru acel slide
    5. La final, returnează cel mai mic font dintre toate slide-urile
    
    Args:
        song: Obiect Song cu structura completă
        use_caps: True dacă ALL CAPS este activat
    
    Returns:
        FontCalculation: Cel mai mic font calculat pentru toate slide-urile
    """
    config = settings.get_section("verses")
    font_max = 72  # Maxim 72pt
    
    refrain_markers = settings.get_section("refrain")
    start_marker = refrain_markers.get("start_marker", "/:")
    end_marker = refrain_markers.get("end_marker", ":/")
    
    # Dimensiuni disponibile (cu 0.4\" margini pe toate părțile)
    available_w = SLIDE_WIDTH_INCHES - (2 * MARGIN_INCHES)  # 12.533"
    available_h = SLIDE_HEIGHT_INCHES - (2 * MARGIN_INCHES)  # 6.7"
    
    order = song.get_effective_order()
    
    # Calculează fontul maxim pentru fiecare slide în parte
    slide_fonts = []
    
    for key in order:
        text = song.get_text_for_key(key)
        if not text:
            continue
        
        label = song.get_label_for_key(key)
        
        # Transformare ALL CAPS dacă e activ
        if use_caps:
            text = text.upper()
        
        # Adaugă marcaje pentru refren dacă e necesar
        is_refrain = key in song.refrains
        if is_refrain:
            lines = text.split('\n')
            # Normalizează marcajele
            for i in range(len(lines)):
                lines[i] = lines[i].replace(': /', ':/')
            
            # Adaugă marcaje
            first_line = lines[0].strip()
            if not first_line.startswith(start_marker):
                lines[0] = f"{start_marker} {lines[0]}"
            
            last_line = lines[-1].strip()
            if not last_line.endswith(end_marker):
                lines[-1] = f"{lines[-1]} {end_marker}"
            
            text = '\n'.join(lines)
        
        # Calculează fontul maxim pentru acest slide (începând de la 20pt)
        lines = text.split("\n")
        num_lines = len(lines)
        max_line_length = max(len(line) for line in lines) if lines else 0
        
        if max_line_length == 0 or num_lines == 0:
            continue
        
        # Începe de la 20pt și crește până când textul atinge limita
        optimal_font = 20  # Font minim de pornire
        
        for font_size in range(20, font_max + 1):
            # Estimează lățimea textului la acest font
            # Aproximare: un caracter Calibri are ~0.42 din înălțimea fontului la 72pt
            # Factor ajustat (0.42) pentru font optim
            char_width_at_72pt = 0.42  # inch
            char_width = (font_size / 72) * char_width_at_72pt
            text_width = max_line_length * char_width
            
            # Estimează înălțimea textului
            line_height = font_size * 1.2  # puncte (pt)
            total_height = num_lines * line_height
            total_height_inches = total_height / 72
            
            # Verifică dacă textul încape în slide (cu 5% margine de siguranță)
            if text_width <= available_w * 0.95 and total_height_inches <= available_h * 0.95:
                optimal_font = font_size  # Acceptabil, continuă
            else:
                break  # Depășește limita, oprește
        
        slide_fonts.append((optimal_font, label, max_line_length, num_lines))
    
    if not slide_fonts:
        return FontCalculation(
            size_pt=40,
            is_minimized=False,
            is_maximized=False,
            longest_slide="",
            reason="Font 40pt — nu s-a putut calcula"
        )
    
    # Găsește cel mai mic font dintre toate slide-urile
    min_font = min(font for font, _, _, _ in slide_fonts)
    
    # Găsește slide-ul care determină fontul minim
    determining_slide = next(label for font, label, _, _ in slide_fonts if font == min_font)
    
    # Generare reason
    reason = (f"Font {min_font}pt — "
              f"determinat de {determining_slide} (cel mai restrictiv)")
    
    return FontCalculation(
        size_pt=min_font,
        is_minimized=False,
        is_maximized=(min_font >= font_max),
        longest_slide=determining_slide,
        reason=reason
    )


def get_slide_analysis(song: Song, font_calc: FontCalculation, 
                       use_caps: bool = False) -> list:
    """
    Returnează o listă de dicționare cu analiza per slide.
    Folosit de CLI pentru afișare tabel preview.
    """
    order = song.get_effective_order()
    analysis = []
    
    for i, key in enumerate(order):
        text = song.get_text_for_key(key)
        if not text:
            continue
        
        lines = text.split("\n")
        is_refrain = key in song.refrains
        
        analysis.append({
            "index": i + 1,
            "label": song.get_label_for_key(key),
            "key": key,
            "font_size": font_calc.size_pt,
            "num_lines": len(lines),
            "max_chars": max(len(l) for l in lines) if lines else 0,
            "has_markers": is_refrain,
            "is_determining": song.get_label_for_key(key) == font_calc.longest_slide
        })
    
    # Adaugă slide-ul Amin
    amin_config = settings.get_section("amin_slide")
    analysis.append({
        "index": len(analysis) + 1,
        "label": "Amin",
        "key": "AMIN",
        "font_size": amin_config.get("font_size", 22),
        "num_lines": 1,
        "max_chars": 4,
        "has_markers": False,
        "is_determining": False
    })
    
    return analysis
