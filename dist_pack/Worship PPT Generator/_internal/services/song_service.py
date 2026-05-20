import os
from typing import List, Tuple, Optional
from core.scraper import scrape_song, ScraperError
from core.parser import parse_song
from core.font_calculator import calculate_font_size, get_slide_analysis
from core.ppt_generator import generate_pptx, generate_filename, PPTGeneratorError
from core.history_manager import add_entry, get_recent, clear_history
from core.models import Song, FontCalculation, HistoryEntry
from config import settings


class SongService:
    """
    API principal pentru manipularea cântărilor.
    Expune metode clare pentru fiecare acțiune majoră.
    """
    
    def __init__(self):
        self.current_song: Optional[Song] = None
        self.current_font_calc: Optional[FontCalculation] = None
        self.use_caps: bool = False
    
    def analyze_url(self, url: str, use_caps: bool = False) -> Tuple[Song, FontCalculation]:
        """
        Procesează complet un URL: extrage, parsează, calculează font.
        
        Args:
            url: URL-ul paginii cu versuri
            use_caps: True pentru ALL CAPS
        
        Returns:
            Tuple[Song, FontCalculation]
        
        Raises:
            ScraperError: Eroare la extragere
            Exception: Eroare la parsare
        """
        self.use_caps = use_caps
        
        title, raw_text = scrape_song(url)
        
        song = parse_song(title, raw_text)
        
        font_calc = calculate_font_size(song, use_caps)
        
        self.current_song = song
        self.current_font_calc = font_calc
        
        return song, font_calc
    
    def preview_structure(self) -> list:
        """
        Returnează analiza slide-by-slide a cântării curente.
        Apelează get_slide_analysis() din font_calculator.
        
        Returns:
            Lista de dict-uri cu info per slide
        """
        if not self.current_song or not self.current_font_calc:
            return []
        
        return get_slide_analysis(
            self.current_song, 
            self.current_font_calc, 
            self.use_caps
        )
    
    def export_ppt(self, url: str = "", custom_path: str = "") -> str:
        """
        Generează fișierul PowerPoint și adaugă în istoric.
        
        Args:
            url: URL-ul sursă (pentru istoric)
            custom_path: Cale personalizată (opțional)
        
        Returns:
            str: Calea absolută a fișierului generat
        """
        if not self.current_song or not self.current_font_calc:
            raise ValueError("Nu există o cântare analizată. Apelează analyze_url() mai întâi.")
        
        if custom_path:
            output_path = custom_path
        else:
            output_dir = settings.get("app", "default_output_dir", "./output")
            filename = generate_filename(self.current_song.title)
            output_path = os.path.join(output_dir, filename)
        
        abs_path = generate_pptx(
            self.current_song,
            self.current_font_calc,
            output_path,
            self.use_caps
        )
        
        add_entry(
            title=self.current_song.title,
            url=url,
            filename=os.path.basename(abs_path)
        )
        
        return abs_path
    
    def edit_stanza(self, key: str, new_text: str) -> FontCalculation:
        """
        Editează o strofă/refren și recalculează fontul.
        
        Args:
            key: Cheia secțiunii (ex: '1', 'R', 'B')
            new_text: Textul nou
        
        Returns:
            FontCalculation: Font recalculat
        """
        if not self.current_song:
            raise ValueError("Nu există o cântare încărcată.")
        
        if key in self.current_song.stanzas:
            self.current_song.stanzas[key] = new_text
        elif key in self.current_song.refrains:
            self.current_song.refrains[key] = new_text
        elif key in self.current_song.bridges:
            self.current_song.bridges[key] = new_text
        elif key in self.current_song.codas:
            self.current_song.codas[key] = new_text
        else:
            raise ValueError(f"Cheia '{key}' nu există în cântare.")
        
        self.current_font_calc = calculate_font_size(
            self.current_song, self.use_caps
        )
        
        return self.current_font_calc
    
    def get_history(self) -> List[HistoryEntry]:
        """Returnează ultimele intrări din istoric."""
        return get_recent()
    
    def clear_all_history(self) -> None:
        """Șterge tot istoricul."""
        clear_history()
