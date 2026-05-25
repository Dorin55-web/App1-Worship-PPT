import flet as ft
import sys
import os
import time
import threading
import tempfile
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import load_config, ensure_directories, save_config
from services.song_service import SongService
from services.hotkey_manager import HotkeyManager
from services.search_service import get_search_service
from core.scraper import scrape_song
from core.parser import parse_song
from core.font_calculator import calculate_font_size
from core.ppt_generator import generate_pptx, generate_filename
from core.models import Song, FontCalculation


class WorshipPPTApp:
    """Aplicația Worship PPT Generator cu UI FLET Modern."""
    
    # Culori tema moderna
    COLOR_BG_DARK = "#0d1117"
    COLOR_BG_CARD = "#161b22"
    COLOR_CYAN = "#00d4ff"
    COLOR_PURPLE = "#7c3aed"
    COLOR_TEXT_GRAY = "#8b949e"
    COLOR_TEXT_WHITE = "#ffffff"
    COLOR_BORDER = "#30363d"
    COLOR_GREEN = "#4caf50"
    COLOR_RED = "#f44336"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_song = None
        self.current_font_size = 20
        self.slides_data = []
        self.current_slide_index = 0
        self.history = []
        self.active_tab = "home"
        
        # Încarcă configurația
        self.config = load_config()
        self.output_dir = self.config.get("app", {}).get("default_output_dir", "./output")
        
        # Mod editare toggle
        self.editing_mode = False
        self.edit_text_field = None
        
        # Hotkey manager pentru captură globală URL
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.set_callback(self._on_hotkey_url)
        self._hotkey_check_running = False
        self._pending_hotkey_url = None  # URL primit prin hotkey, procesat în UI loop
        
        # Search service pentru cautare locala
        search_dir = self.config.get("app", {}).get("search_directory", "")
        self.search_service = get_search_service(search_dir if search_dir else None)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configurează interfața utilizator modernă."""
        # Configurare pagină
        self.page.title = "Worship PPT Generator"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.bgcolor = self.COLOR_BG_DARK
        
        # Layout principal - 3 coloane
        self.main_layout = ft.Row(
            expand=True,
            spacing=0,
        )
        
        # Sidebar (80px)
        self.sidebar = self._create_sidebar()
        
        # Lista slide-uri (100px) - NOU
        self.slide_list_panel = self._create_slide_list_panel()
        
        # Content principal
        self.content_area = self._create_content_area()
        
        self.main_layout.controls = [self.sidebar, self.slide_list_panel, self.content_area]
        self.page.add(self.main_layout)
        
        # Porneste sistemul de hotkey global
        self._start_hotkey_system()
    
    def _start_hotkey_system(self):
        """Porneste ascultatorul de hotkey global si verificarea periodica."""
        try:
            self.hotkey_manager.start()
            self._hotkey_check_running = True
            
            # Porneste thread-ul de verificare a cozii
            import threading
            self._hotkey_thread = threading.Thread(
                target=self._hotkey_queue_loop,
                daemon=True
            )
            self._hotkey_thread.start()
            
            print("[UI] Hotkey system started - Press F8 to capture URL")
        except Exception as e:
            print(f"[UI] Failed to start hotkey system: {e}")
    
    def _hotkey_queue_loop(self):
        """Loop care verifica periodic coada de URL-uri (ruleaza pe thread separat)."""
        while self._hotkey_check_running:
            try:
                self.hotkey_manager.check_and_process()
                
                # Verifica daca exista un URL pending si il proceseaza pe main thread
                if self._pending_hotkey_url:
                    url = self._pending_hotkey_url
                    self._pending_hotkey_url = None  # Clear immediately to prevent loop
                    # Proceseaza pe main thread folosind run_task
                    self.page.run_task(self._process_hotkey_async, url)
                        
            except Exception as e:
                print(f"[UI] Hotkey queue error: {e}")
            time.sleep(0.2)  # Verifica la fiecare 200ms
    
    async def _process_hotkey_async(self, url):
        """Proceseaza URL-ul primit prin hotkey (ruleaza pe main thread)."""
        try:
            print(f"[UI] Processing hotkey URL on main thread: {url}")
            
            # Reset UI
            self.slides_data = []
            self.current_slide_index = 0
            self.current_song = None
            self.slide_list_panel.visible = False
            self.slide_list_view.controls = []
            self.slide_info.value = "Slide 0/0"
            self.preview_image.content = ft.Container(
                width=640,
                height=360,
                bgcolor=self.COLOR_BG_DARK,
                border_radius=16,
            )
            
            # Seteaza URL-ul
            self.url_input.value = url
            self.status_text.value = "URL captured via hotkey! Processing..."
            self.status_text.color = self.COLOR_CYAN
            self.page.update()
            
            # Declanseaza automat scraping-ul (ruleaza pe main thread)
            self.on_fetch_click(None)
            
        except Exception as ex:
            print(f"[UI] Error processing hotkey URL: {ex}")
    
    def _process_hotkey_url(self, url):
        """Proceseaza URL-ul primit prin hotkey (metoda veche, pastrata pentru compatibilitate)."""
        pass
    
    def _on_hotkey_url(self, url: str):
        """Handler apelat cand un URL este capturat prin hotkey.
        
        NU actualizeaza UI direct - doar salveaza URL-ul pentru procesare
        in UI loop-ul principal.
        """
        self._pending_hotkey_url = url
        print(f"[UI] URL received via hotkey: {url}")
    
    def _create_sidebar(self):
        """Creează sidebar-ul modern (80px)."""
        # Logo
        logo = ft.Container(
            content=ft.Text("🎵", size=32),
            padding=20,
        )
        
        # Buton HOME (activ by default)
        self.home_btn = ft.Container(
            content=ft.Column(
                [
                    ft.Text("🏠", size=24),
                    ft.Text("HOME", size=10, color=self.COLOR_TEXT_GRAY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=10,
            bgcolor=self.COLOR_BG_CARD,
            border=ft.border.only(left=ft.border.BorderSide(3, self.COLOR_CYAN)),
            on_click=self.on_home_click,
        )
        
        # Buton SEARCH
        self.search_btn = ft.Container(
            content=ft.Column(
                [
                    ft.Text("🔍", size=24),
                    ft.Text("Search", size=10, color=self.COLOR_TEXT_GRAY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=10,
            on_click=self.on_search_click,
        )
        
        # Buton Setări (jos) - doar iconiță
        settings_btn = ft.Container(
            content=ft.Text("⚙️", size=24),
            padding=15,
            on_click=self.on_settings_click,
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    logo,
                    ft.Divider(height=1, color=self.COLOR_BORDER),
                    ft.Container(height=20),
                    self.home_btn,
                    ft.Container(height=10),
                    self.search_btn,
                    ft.Container(expand=True),
                    settings_btn,
                    ft.Container(height=10),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=80,
            bgcolor=self.COLOR_BG_DARK,
            border=ft.border.only(right=ft.border.BorderSide(1, self.COLOR_BORDER)),
        )
    
    def _create_slide_list_panel(self):
        """Creează panelul cu lista slide-urilor (225px)."""
        self.slide_list_view = ft.ListView(
            expand=True,
            spacing=6,
            padding=10,
        )
        
        return ft.Container(
            content=self.slide_list_view,
            width=250,
            bgcolor=self.COLOR_BG_DARK,
            border=ft.border.only(right=ft.border.BorderSide(1, self.COLOR_BORDER)),
            visible=False,  # Vizibil doar când e cantare încărcată
        )
    
    def update_slide_list(self):
        """Actualizează lista slide-urilor."""
        if not self.slides_data:
            self.slide_list_panel.visible = False
            return
        
        self.slide_list_view.controls = []
        
        for i, slide_data in enumerate(self.slides_data):
            # Folosește tot textul din slide
            full_text = slide_data['text']
            
            # Container pentru item cu tot textul
            is_active = (i == self.current_slide_index)
            
            item = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    full_text,
                                    size=8,
                                    color=self.COLOR_TEXT_WHITE if is_active else self.COLOR_TEXT_GRAY,
                                    text_align=ft.TextAlign.CENTER,
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True,
                ),
                padding=10,
                bgcolor=self.COLOR_BG_CARD if is_active else None,
                border=ft.border.only(
                    left=ft.border.BorderSide(4, self.COLOR_CYAN if is_active else self.COLOR_BORDER)
                ),
                border_radius=8,
                on_click=lambda e, idx=i: self.on_slide_list_click(idx),
            )
            
            self.slide_list_view.controls.append(item)
        
        self.slide_list_panel.visible = True
    
    def on_slide_list_click(self, index):
        """Handler pentru click pe item din listă."""
        self.current_slide_index = index
        self.update_preview()
        self.update_slide_list()
        self.page.update()
    
    def _create_content_area(self):
        """Creează zona principală de conținut cu suport pentru multiple views."""
        # Creează views separate
        self.home_view = self._create_home_view()
        self.search_view = self._create_search_view()
        
        # Container principal care va afișa view-ul activ
        self.content_container = ft.Container(
            content=self.home_view,
            expand=True,
            bgcolor=self.COLOR_BG_DARK,
        )
        
        return self.content_container
    
    def _create_home_view(self):
        """Creează view-ul principal (HOME)."""
        # Header cu input URL
        header = self._create_header()
        
        # Zona de preview
        preview_section = self._create_preview_section()
        
        # Bottom toolbar
        toolbar = self._create_toolbar()
        
        # Status bar
        status_bar = self._create_status_bar()
        
        return ft.Column(
            [
                header,
                preview_section,
                toolbar,
                status_bar,
            ],
            spacing=0,
            expand=True,
        )
    
    def _create_search_view(self):
        """Creează view-ul de căutare (SEARCH) - design modern integrat."""
        
        # Header compact cu search input (similar cu home header)
        self.search_input = ft.TextField(
            hint_text="Search songs...",
            border_color=self.COLOR_BORDER,
            focused_border_color=self.COLOR_CYAN,
            text_size=12,
            expand=True,
            height=35,
            on_submit=self._on_search_submit,
        )
        
        search_btn = ft.ElevatedButton(
            "Search",
            on_click=self._on_search_submit,
            style=ft.ButtonStyle(
                bgcolor=self.COLOR_CYAN,
                color="#000000",
                padding=12,
                text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
            ),
            height=35,
        )
        
        search_header = ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=10),
                    self.search_input,
                    ft.Container(width=8),
                    search_btn,
                    ft.Container(width=10),
                ],
            ),
            padding=10,
            bgcolor=self.COLOR_BG_DARK,
            border=ft.border.only(bottom=ft.border.BorderSide(1, self.COLOR_BORDER)),
        )
        
        # Status bar (similar cu home status)
        self.search_status = ft.Text(
            "Ready",
            size=12,
            color=self.COLOR_TEXT_WHITE,
            width=200,
            text_align=ft.TextAlign.CENTER,
        )
        
        status_row = ft.Container(
            content=ft.Row(
                [
                    ft.Text("●", size=10, color=self.COLOR_GREEN),
                    ft.Container(width=5),
                    self.search_status,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=250,
        )
        
        # Info header
        info_header = ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=40),
                    ft.Column(
                        [
                            ft.Text("SEARCH", size=10, color=self.COLOR_TEXT_GRAY),
                            ft.Text("Local Collection", size=12, color=self.COLOR_TEXT_WHITE),
                        ],
                        spacing=2,
                    ),
                    ft.Container(expand=True),
                    status_row,
                    ft.Container(width=40),
                ],
            ),
            padding=15,
            bgcolor=self.COLOR_BG_CARD,
            border=ft.border.only(bottom=ft.border.BorderSide(1, self.COLOR_BORDER)),
        )
        
        # Results list
        self.search_results = ft.ListView(
            expand=True,
            spacing=6,
            padding=15,
        )
        
        return ft.Column(
            [
                search_header,
                info_header,
                self.search_results,
            ],
            spacing=0,
            expand=True,
        )
    
    def _create_header(self):
        """Creează header-ul compact cu input URL."""
        self.url_input = ft.TextField(
            hint_text="Paste URL...",
            border_color=self.COLOR_BORDER,
            focused_border_color=self.COLOR_CYAN,
            text_size=12,
            expand=True,
            height=35,
            on_submit=self.on_fetch_click,
            autofocus=True,
        )
        
        fetch_btn = ft.ElevatedButton(
            "Run",
            on_click=self.on_fetch_click,
            style=ft.ButtonStyle(
                bgcolor=self.COLOR_CYAN,
                color="#000000",
                padding=12,
                text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
            ),
            height=35,
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=10),
                    self.url_input,
                    ft.Container(width=8),
                    fetch_btn,
                    ft.Container(width=10),
                ],
            ),
            padding=10,
            bgcolor=self.COLOR_BG_DARK,
        )
    
    def _create_preview_section(self):
        """Creează secțiunea de preview."""
        # Info slide
        self.slide_info = ft.Text(
            "Slide 0/0",
            size=14,
            color=self.COLOR_TEXT_GRAY,
            weight=ft.FontWeight.BOLD,
        )
        
        # Preview image - placeholder gol când nu e imagine
        self.preview_image = ft.Container(
            width=640,
            height=360,
            bgcolor=self.COLOR_BG_DARK,
            border_radius=16,
        )
        
        # Container preview cu border subtil
        preview_container = ft.Container(
            content=self.preview_image,
            width=680,
            height=400,
            bgcolor=self.COLOR_BG_DARK,
            border_radius=16,
            padding=20,
            border=ft.border.all(1, self.COLOR_BORDER),
        )
        
        # Navigation buttons - aliniate perfect
        prev_btn = ft.Container(
            content=ft.Row(
                [ft.Text("◀ Previous", color=self.COLOR_TEXT_WHITE, weight=ft.FontWeight.BOLD, size=14)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=self.COLOR_BG_CARD,
            border_radius=8,
            width=120,
            height=40,
            on_click=self.on_prev_slide,
        )
        
        next_btn = ft.Container(
            content=ft.Row(
                [ft.Text("Next ▶", color=self.COLOR_TEXT_WHITE, weight=ft.FontWeight.BOLD, size=14)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=self.COLOR_BG_CARD,
            border_radius=8,
            width=120,
            height=40,
            on_click=self.on_next_slide,
        )
        
        # Fixam dimensiunea pentru slide_info ca sa fie simetric
        self.slide_info.width = 150
        self.slide_info.text_align = ft.TextAlign.CENTER
        
        nav_row = ft.Row(
            [
                prev_btn,
                ft.Container(width=30),
                self.slide_info,
                ft.Container(width=30),
                next_btn,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    preview_container,
                    ft.Container(height=15),
                    nav_row,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
        )
    
    def _create_toolbar(self):
        """Creează toolbar-ul de jos."""
        # Font size control
        self.font_label = ft.Text(
            "20pt",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=self.COLOR_CYAN,
            width=60,
            text_align=ft.TextAlign.CENTER,
        )
        
        font_control = ft.Row(
            [
                ft.ElevatedButton(
                    "−",
                    on_click=self.on_font_minus,
                    style=ft.ButtonStyle(
                        bgcolor=self.COLOR_BG_CARD,
                        color=self.COLOR_TEXT_WHITE,
                    ),
                ),
                self.font_label,
                ft.ElevatedButton(
                    "+",
                    on_click=self.on_font_plus,
                    style=ft.ButtonStyle(
                        bgcolor=self.COLOR_BG_CARD,
                        color=self.COLOR_TEXT_WHITE,
                    ),
                ),
            ],
            spacing=10,
        )
        
        # Toggle Edit button
        self.edit_toggle_btn = ft.ElevatedButton(
            on_click=self.on_toggle_edit_mode,
            content=ft.Text("Enable Editing", weight=ft.FontWeight.BOLD),
            style=ft.ButtonStyle(
                bgcolor=self.COLOR_CYAN,
                color="#000000",
                padding=15,
            ),
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=40),
                    font_control,
                    ft.Container(expand=True),
                    self.edit_toggle_btn,
                    ft.Container(width=40),
                ],
            ),
            padding=15,
            bgcolor=self.COLOR_BG_DARK,
        )
    
    def _create_status_bar(self):
        """Creează status bar-ul."""
        # Stânga - Format și Aspect Ratio
        left_section = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("FORMAT", size=10, color=self.COLOR_TEXT_GRAY),
                        ft.Text("PowerPoint (.pptx)", size=12, color=self.COLOR_TEXT_WHITE),
                    ],
                    spacing=2,
                ),
                ft.VerticalDivider(width=20, color=self.COLOR_BORDER),
                ft.Column(
                    [
                        ft.Text("ASPECT RATIO", size=10, color=self.COLOR_TEXT_GRAY),
                        ft.Text("Widescreen 16:9", size=12, color=self.COLOR_TEXT_WHITE),
                    ],
                    spacing=2,
                ),
            ],
            spacing=15,
        )
        
        # Centru - Status cu width fix ca să nu mute butonul
        self.status_text = ft.Text(
            "Ready",
            size=12,
            color=self.COLOR_TEXT_WHITE,
            width=200,
            text_align=ft.TextAlign.CENTER,
        )
        
        status_center = ft.Container(
            content=ft.Row(
                [
                    ft.Text("●", size=10, color=self.COLOR_GREEN),
                    ft.Container(width=5),
                    self.status_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=250,
        )
        
        # Dreapta - Generate button flexibil (ca Edit)
        generate_btn = ft.ElevatedButton(
            "Generate",
            on_click=self.on_generate_click,
            style=ft.ButtonStyle(
                bgcolor=self.COLOR_PURPLE,
                color=self.COLOR_TEXT_WHITE,
                padding=15,
                text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            ),
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=40),
                    left_section,
                    ft.Container(width=50),
                    status_center,
                    ft.Container(expand=True),
                    generate_btn,
                    ft.Container(width=40),
                ],
            ),
            padding=15,
            bgcolor=self.COLOR_BG_CARD,
            border=ft.border.only(top=ft.border.BorderSide(1, self.COLOR_BORDER)),
        )
    
    # Handler methods
    def on_home_click(self, e):
        """Handler pentru click pe HOME."""
        self.active_tab = "home"
        self.home_btn.bgcolor = self.COLOR_BG_CARD
        self.home_btn.border = ft.border.only(left=ft.border.BorderSide(3, self.COLOR_CYAN))
        self.search_btn.bgcolor = None
        self.search_btn.border = None
        
        # Comuta la home view
        self.content_container.content = self.home_view
        
        # Arata slide list panel daca sunt slide-uri incarcate
        if self.slides_data:
            self.slide_list_panel.visible = True
        
        self.page.update()
    
    def on_search_click(self, e):
        """Handler pentru click pe SEARCH - comuta la view-ul de cautare."""
        self.active_tab = "search"
        self.home_btn.bgcolor = None
        self.home_btn.border = None
        self.search_btn.bgcolor = self.COLOR_BG_CARD
        self.search_btn.border = ft.border.only(left=ft.border.BorderSide(3, self.COLOR_CYAN))
        
        # Comuta la search view
        self.content_container.content = self.search_view
        
        # Ascunde slide list panel in modul search
        self.slide_list_panel.visible = False
        
        self.page.update()
    
    def _get_background_type(self, filepath: str) -> str:
        """Analizeaza tipul de fundal al unui fisier PowerPoint.
        
        Returns:
            'black' - fundal negru (generat de aplicatia noastra)
            'white' - fundal alb
            'color' - fundal colorat sau imagini
            'unknown' - nu s-a putut determina
        """
        try:
            from pptx import Presentation
            
            # Pentru .ppt (format vechi) - python-pptx nu il poate citi
            if filepath.lower().endswith('.ppt'):
                # Scanam continutul binar dupa semnaturi de imagini
                with open(filepath, 'rb') as f:
                    content = f.read()
                
                # Semnaturi imagini comune
                has_png = b'\x89PNG' in content
                has_jpeg = b'\xff\xd8\xff' in content
                has_gif = b'GIF8' in content
                
                if has_png or has_jpeg or has_gif:
                    return 'color'  # Contine imagini = fundal colorat
                
                # Daca nu are imagini, verificam dimensiunea
                file_size = os.path.getsize(filepath)
                if file_size < 30 * 1024:  # Mai putin de 30KB - probabil text simplu
                    return 'white'
                else:
                    return 'color'  # Fisierele mai mari fara imagini detectate - presupunem color
            
            # Pentru .pptx folosim python-pptx
            prs = Presentation(filepath)
            
            black_count = 0
            white_count = 0
            color_count = 0
            image_count = 0
            
            for slide in prs.slides:
                background = slide.background
                fill = background.fill
                
                if fill.type is None:
                    continue
                elif fill.type == 1:  # SOLID
                    try:
                        color = fill.fore_color.rgb
                        if color:
                            r, g, b = color[0], color[1], color[2]
                            if r < 50 and g < 50 and b < 50:
                                black_count += 1
                            elif r > 200 and g > 200 and b > 200:
                                white_count += 1
                            else:
                                color_count += 1
                    except:
                        pass
                elif fill.type == 6:  # PICTURE
                    image_count += 1
                else:
                    color_count += 1
            
            # Determina tipul predominant
            total = black_count + white_count + color_count + image_count
            if total == 0:
                return 'unknown'
            
            if image_count > 0:
                return 'color'  # Imagini = color
            elif black_count > white_count and black_count > color_count:
                return 'black'
            elif white_count > black_count and white_count > color_count:
                return 'white'
            else:
                return 'color'
                
        except Exception as e:
            return 'unknown'
    
    def _on_search_submit(self, e=None):
        """Handler pentru submit in search view."""
        query = self.search_input.value.strip() if self.search_input else ""
        if len(query) < 2:
            self.search_status.value = "Type at least 2 characters"
            self.search_status.color = self.COLOR_TEXT_GRAY
            self.search_results.controls = []
            self.page.update()
            return
        
        if not self.search_service.is_ready():
            self.search_status.value = "Search service unavailable. Check settings."
            self.search_status.color = self.COLOR_RED
            self.search_results.controls = []
            self.page.update()
            return
        
        self.search_status.value = "Searching..."
        self.search_status.color = self.COLOR_CYAN
        self.page.update()
        
        results = self.search_service.search_by_title(query, limit=20)
        
        if not results:
            self.search_status.value = "No results found"
            self.search_status.color = self.COLOR_TEXT_GRAY
            self.search_results.controls = []
            self.page.update()
            return
        
        self.search_status.value = f"{len(results)} results"
        self.search_status.color = self.COLOR_GREEN
        
        # Analizeaza fundalurile si sorteaza
        self.search_status.value = f"Analyzing {len(results)} results..."
        self.page.update()
        
        # Adauga tipul de fundal la fiecare rezultat
        for r in results:
            filepath = self.search_service.get_file_path(r['fisier'])
            r['bg_type'] = self._get_background_type(filepath)
        
        # Sorteaza: black first, then white, then color
        bg_priority = {'black': 0, 'white': 1, 'color': 2, 'unknown': 3}
        results.sort(key=lambda x: (bg_priority.get(x.get('bg_type', 'unknown'), 3), -x['scor']))
        
        self.search_status.value = f"{len(results)} results"
        
        self.search_results.controls = []
        for r in results:
            scor_pct = int(r['scor'] * 100)
            scor_color = '#00aa00' if scor_pct >= 80 else '#00d4ff' if scor_pct >= 50 else self.COLOR_TEXT_GRAY
            
            # Badge pentru tipul de fundal
            bg_type = r.get('bg_type', 'unknown')
            bg_label = {
                'black': 'Dark BG',
                'white': 'Light BG', 
                'color': 'Color/Image',
                'unknown': '?'
            }.get(bg_type, '?')
            
            bg_badge_color = {
                'black': '#333333',
                'white': '#ffffff',
                'color': '#ff6b6b',
                'unknown': '#666666'
            }.get(bg_type, '#666666')
            
            bg_text_color = '#ffffff' if bg_type == 'black' else '#000000' if bg_type == 'white' else '#ffffff'
            
            # Score badge
            score_badge = ft.Container(
                content=ft.Text(
                    f"{scor_pct}%",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color="#000000" if scor_pct >= 50 else self.COLOR_TEXT_WHITE,
                ),
                bgcolor=self.COLOR_CYAN if scor_pct >= 50 else self.COLOR_BORDER,
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=8, vertical=2),
            )
            
            # Background type badge
            bg_badge = ft.Container(
                content=ft.Text(
                    bg_label,
                    size=9,
                    weight=ft.FontWeight.BOLD,
                    color=bg_text_color,
                ),
                bgcolor=bg_badge_color,
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
            )
            
            result_card = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            r['titlu'][:70] + ('...' if len(r['titlu']) > 70 else ''),
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                            color=self.COLOR_TEXT_WHITE,
                                        ),
                                        ft.Text(
                                            r['fisier'],
                                            size=10,
                                            color=self.COLOR_TEXT_GRAY,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Row(
                                    [bg_badge, score_badge],
                                    spacing=5,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=1, color=self.COLOR_BORDER),
                        ft.Text(
                            r['vers'][:150] + ('...' if len(r['vers']) > 150 else ''),
                            size=11,
                            color=self.COLOR_TEXT_GRAY,
                        ),
                    ],
                    spacing=8,
                ),
                padding=15,
                bgcolor=self.COLOR_BG_CARD,
                border=ft.border.all(1, self.COLOR_BORDER),
                border_radius=8,
                on_click=lambda e, f=r['fisier']: self._open_search_result(f),
                ink=True,
            )
            self.search_results.controls.append(result_card)
        
        self.page.update()
    
    def _open_search_result(self, filename: str):
        """Deschide fisierul PowerPoint din rezultatele cautarii si il aduce in prim-plan."""
        filepath = self.search_service.get_file_path(filename)
        if os.path.exists(filepath):
            try:
                import subprocess
                import time
                
                self.search_status.value = f"Opening: {filename}..."
                self.page.update()
                
                # Foloseste subprocess cu 'start' pentru a deschide in modul Windows standard
                # 'start "" "filepath"' deschide fisierul cu aplicatia asociata
                subprocess.Popen(
                    f'start "" "{filepath}"',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                self.search_status.value = f"Deschis: {filename}"
                self.search_status.color = self.COLOR_GREEN
                
            except Exception as e:
                self.search_status.value = f"Eroare la deschidere: {e}"
                self.search_status.color = self.COLOR_RED
        else:
            self.search_status.value = f"Fisier negasit: {filename}"
            self.search_status.color = self.COLOR_RED
        self.page.update()
    
    def _check_local_song(self, title: str, lyrics: str = ""):
        """Verifica daca cantarea exista in colectia locala."""
        if not self.search_service.is_ready():
            return []
        
        # Cauta dupa titlu
        results = self.search_service.search_by_title(title, limit=5)
        
        # Daca nu gaseste sau scorul e mic, cauta si dupa versuri
        if (not results or results[0]['scor'] < 0.7) and lyrics:
            lyrics_results = self.search_service.search_by_lyrics(lyrics, limit=5)
            # Adauga doar rezultate noi
            existing_files = {r['fisier'] for r in results}
            for r in lyrics_results:
                if r['fisier'] not in existing_files:
                    results.append(r)
            
            # Sorteaza dupa scor
            results.sort(key=lambda x: x['scor'], reverse=True)
        
        return results[:5]
    
    def _show_local_results(self, title: str, results: list):
        """Arata dialog cu rezultatele cautarii locale cand se incarca o cantare."""
        def close_dlg(e):
            dlg.open = False
            self.page.update()
        
        def open_file(e, filename):
            self._open_search_result(filename)
            dlg.open = False
            self.page.update()
        
        def continue_generate(e):
            dlg.open = False
            self.page.update()
        
        results_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=6,
            height=250,
        )
        
        for r in results:
            scor_pct = int(r['scor'] * 100)
            
            # Score badge
            score_badge = ft.Container(
                content=ft.Text(
                    f"{scor_pct}%",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color="#000000" if scor_pct >= 50 else self.COLOR_TEXT_WHITE,
                ),
                bgcolor=self.COLOR_CYAN if scor_pct >= 50 else self.COLOR_BORDER,
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=8, vertical=2),
            )
            
            result_card = ft.Container(
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    r['titlu'][:50] + ('...' if len(r['titlu']) > 50 else ''),
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=self.COLOR_TEXT_WHITE,
                                ),
                                ft.Text(
                                    r['fisier'],
                                    size=9,
                                    color=self.COLOR_TEXT_GRAY,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        score_badge,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=12,
                bgcolor=self.COLOR_BG_CARD,
                border=ft.border.all(1, self.COLOR_BORDER),
                border_radius=8,
                on_click=lambda e, f=r['fisier']: open_file(e, f),
                ink=True,
            )
            results_column.controls.append(result_card)
        
        dlg = ft.AlertDialog(
            title=ft.Text(
                "Song Found in Local Collection",
                color=self.COLOR_TEXT_WHITE,
                weight=ft.FontWeight.BOLD,
                size=16,
            ),
            bgcolor=self.COLOR_BG_CARD,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"'{title[:40]}{'...' if len(title) > 40 else ''}'",
                            size=13,
                            color=self.COLOR_CYAN,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(color=self.COLOR_BORDER),
                        ft.Text(
                            f"Found {len(results)} result(s) in your local collection:",
                            size=12,
                            color=self.COLOR_TEXT_GRAY,
                        ),
                        ft.Container(
                            content=results_column,
                            border=ft.border.all(1, self.COLOR_BORDER),
                            border_radius=8,
                            padding=8,
                            bgcolor=self.COLOR_BG_DARK,
                        ),
                        ft.Text(
                            "Or generate a new version:",
                            size=11,
                            color=self.COLOR_TEXT_GRAY,
                            italic=True,
                        ),
                    ],
                    spacing=10,
                    tight=True,
                ),
                bgcolor=self.COLOR_BG_CARD,
                width=500,
                height=420,
            ),
            actions=[
                ft.TextButton(
                    "Generate New",
                    on_click=continue_generate,
                    style=ft.ButtonStyle(color=self.COLOR_CYAN),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            open=True,
        )
        
        self.page.overlay.append(dlg)
        self.page.update()
    
    def on_settings_click(self, e):
        """Deschide dialogul de setări."""
        def save_settings(e):
            new_path = path_input.value.strip()
            
            if new_path:
                try:
                    os.makedirs(new_path, exist_ok=True)
                    self.output_dir = new_path
                    self.config["app"]["default_output_dir"] = new_path
                except Exception as ex:
                    self.status_text.value = f"Error: {str(ex)}"
                    self.status_text.color = self.COLOR_RED
                    self.page.update()
                    return
            else:
                self.output_dir = "./output"
                self.config["app"]["default_output_dir"] = "./output"

            # Save search directory setting
            search_dir = search_dir_input.value.strip()
            if search_dir:
                self.config["app"]["search_directory"] = search_dir
                self.search_service.set_search_directory(search_dir)
            
            # Save auto open setting
            self.config["app"]["auto_open_ppt"] = auto_open_switch.value
            save_config(self.config)

            self.status_text.value = "Settings saved"
            self.status_text.color = self.COLOR_GREEN
            dlg.open = False
            self.page.update()
        
        def close_dlg(e):
            dlg.open = False
            self.page.update()
        
        path_input = ft.TextField(
            label="Save Location",
            value=self.output_dir if self.output_dir != "./output" else "",
            hint_text="e.g. C:\\Users\\Name\\Documents\\Songs (leave empty for default)",
            border_color=self.COLOR_BORDER,
            focused_border_color=self.COLOR_CYAN,
            text_size=14,
            expand=True,
        )
        
        # Auto Open toggle în setări
        auto_open_value = self.config.get("app", {}).get("auto_open_ppt", True)
        auto_open_switch = ft.Switch(
            label="Auto Open PowerPoint after generation",
            value=auto_open_value,
            active_color=self.COLOR_CYAN,
            inactive_track_color=self.COLOR_BORDER,
        )
        
        # Search directory input
        search_dir_value = self.config.get("app", {}).get("search_directory", "")
        search_dir_input = ft.TextField(
            label="Search Directory (Local Songs)",
            value=search_dir_value,
            hint_text="Path to folder containing .ppt/.pptx files",
            border_color=self.COLOR_BORDER,
            focused_border_color=self.COLOR_CYAN,
            text_size=14,
            expand=True,
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text("Settings", color=self.COLOR_TEXT_WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=self.COLOR_BG_CARD,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Choose where to save songs:", size=14, color=self.COLOR_TEXT_WHITE),
                        ft.Text(f"Current: {self.output_dir}", size=12, color=self.COLOR_TEXT_GRAY),
                        ft.Divider(color=self.COLOR_BORDER),
                        path_input,
                        ft.Text(
                            "Note: Leave empty to use default 'output' folder",
                            size=11,
                            color=self.COLOR_TEXT_GRAY,
                            italic=True,
                        ),
                        ft.Divider(color=self.COLOR_BORDER),
                        ft.Text("Export Options:", size=14, color=self.COLOR_TEXT_WHITE, weight=ft.FontWeight.BOLD),
                        auto_open_switch,
                        ft.Divider(color=self.COLOR_BORDER),
                        ft.Text("Search Settings:", size=14, color=self.COLOR_TEXT_WHITE, weight=ft.FontWeight.BOLD),
                        search_dir_input,
                        ft.Text(
                            "Path to folder with PowerPoint songs for local search",
                            size=11,
                            color=self.COLOR_TEXT_GRAY,
                            italic=True,
                        ),
                    ],
                    tight=True,
                    spacing=15,
                    width=500,
                ),
                bgcolor=self.COLOR_BG_CARD,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", 
                    on_click=close_dlg,
                    style=ft.ButtonStyle(color=self.COLOR_TEXT_GRAY),
                ),
                ft.ElevatedButton(
                    "Save", 
                    on_click=save_settings,
                    style=ft.ButtonStyle(
                        bgcolor=self.COLOR_CYAN,
                        color="#000000",
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            open=True,
        )
        
        self.page.overlay.append(dlg)
        self.page.update()
    
    def on_fetch_click(self, e):
        """Handler pentru butonul Fetch."""
        url = self.url_input.value.strip()
        if not url:
            self.status_text.value = "Please enter a URL first!"
            self.status_text.color = self.COLOR_RED
            self.page.update()
            return
        
        try:
            # Resetare date vechi înainte de încărcare
            # Curăță imaginile vechi din temp
            import glob
            for old_file in glob.glob(os.path.join(tempfile.gettempdir(), "worship_preview_*.png")):
                try:
                    os.remove(old_file)
                except:
                    pass
            
            self.slides_data = []
            self.current_slide_index = 0
            self.current_song = None
            self.preview_image.content = ft.Container(
                width=640,
                height=360,
                bgcolor=self.COLOR_BG_DARK,
                border_radius=16,
            )
            self.slide_info.value = "Slide 0/0"
            
            self.status_text.value = "Loading..."
            self.status_text.color = self.COLOR_CYAN
            self.page.update()
            
            # Scrape și parse
            title, raw_text = scrape_song(url)
            self.current_song = parse_song(title, raw_text)
            
            # Verifica daca cantarea exista in colectia locala
            local_results = self._check_local_song(title, raw_text[:200])
            if local_results:
                self._show_local_results(title, local_results)
            
            # Calculează fontul optim
            font_calc = calculate_font_size(self.current_song, use_caps=False)
            self.current_font_size = font_calc.size_pt
            
            # Pregătește datele slide-urilor
            self.slides_data = []
            order = self.current_song.get_effective_order()
            for key in order:
                text = self.current_song.get_text_for_key(key)
                if text:
                    label = self.current_song.get_label_for_key(key)
                    self.slides_data.append({
                        'key': key,
                        'label': label,
                        'text': text,
                    })
            
            self.current_slide_index = 0
            self.song_counter = getattr(self, 'song_counter', 0) + 1

            # Actualizează UI
            self.font_label.value = f"{self.current_font_size}pt"
            self.status_text.value = f"✓ {title} - {len(self.slides_data)} slides"
            self.status_text.color = self.COLOR_GREEN
            
            # Generează preview și lista
            self.update_preview()
            self.update_slide_list()
            
        except Exception as ex:
            self.status_text.value = f"✗ Error: {str(ex)}"
            self.status_text.color = self.COLOR_RED
        
        self.page.update()
    
    def update_preview(self):
        """Actualizează imaginea de preview sau text field în mod editare."""
        if not self.slides_data:
            return
        
        slide_data = self.slides_data[self.current_slide_index]
        self.slide_info.value = f"Slide {self.current_slide_index + 1}/{len(self.slides_data)} - {slide_data['label']}"
        
        if self.editing_mode:
            # Mod editare - TextField identic cu imaginea preview
            # Scalez fontul din PowerPoint pentru a arata bine in UI
            # PowerPoint foloseste puncte, dar in Flet trebuie scalat pentru preview
            edit_font_size = int(self.current_font_size * 0.6)  # Scalez la 60% pentru UI
            
            # Verific daca e ultimul slide pentru a adauga "Amin" separat
            is_last_slide = (self.current_slide_index == len(self.slides_data) - 1)
            
            # Calculez padding pentru centrare verticala exacta
            lines = slide_data['text'].split('\n')
            num_lines = len(lines)
            line_height = edit_font_size * 1.4
            text_height = num_lines * line_height
            vertical_padding = max(20, (340 - text_height) / 2)
            
            # TextField principal pentru textul versurilor - OCUPA TOT CONTAINERUL
            self.edit_text_field = ft.TextField(
                value=slide_data['text'],
                multiline=True,
                border=ft.InputBorder.NONE,
                text_size=edit_font_size,
                text_align=ft.TextAlign.CENTER,
                color=self.COLOR_TEXT_WHITE,
                bgcolor="#000000",
                on_change=self.on_edit_text_change,
                cursor_color=self.COLOR_CYAN,
                selection_color=self.COLOR_CYAN,
                content_padding=ft.padding.only(top=vertical_padding, left=10, right=10, bottom=20),
                min_lines=15,
                max_lines=15,
                height=360,
                width=640,
            )
            
            # Construiesc containerul
            if is_last_slide:
                # Pentru ultimul slide, folosesc Stack cu "Amin" pozitionat DEASUPRA TextField
                amin_text = ft.Text(
                    "Amin",
                    size=13,  # 22pt * 0.6 = ~13px pentru UI
                    color=self.COLOR_TEXT_WHITE,
                    text_align=ft.TextAlign.RIGHT,
                )
                
                self.preview_image.content = ft.Container(
                    content=ft.Stack(
                        [
                            # TextField pe toata suprafata
                            self.edit_text_field,
                            # "Amin" pozitionat in coltul dreapta-jos PESTE TextField
                            ft.Container(
                                content=amin_text,
                                right=40,  # 1cm ~ 40px din dreapta
                                bottom=30,  # 1cm ~ 30px de jos
                                width=120,
                                height=30,
                                alignment=ft.alignment.Alignment(1.0, 1.0),
                            ),
                        ]
                    ),
                    width=640,
                    height=360,
                    bgcolor="#000000",
                    border_radius=16,
                    border=ft.border.all(1, self.COLOR_BORDER),
                )
            else:
                # Pentru celelalte slide-uri, doar TextField in container
                self.preview_image.content = ft.Container(
                    content=self.edit_text_field,
                    width=640,
                    height=360,
                    bgcolor="#000000",
                    border_radius=16,
                    border=ft.border.all(1, self.COLOR_BORDER),
                )
        else:
            # Mod normal - generează imagine preview
            is_last = (self.current_slide_index == len(self.slides_data) - 1)
            is_refrain = bool(self.current_song and slide_data['key'] in self.current_song.refrains)
            img = self._generate_slide_preview(
                slide_data['text'],
                self.current_font_size,
                slide_data['label'],
                is_last,
                is_refrain
            )
            
            # Salvează temporar cu nume unic (include timestamp pentru a evita cache-ul)
            import time
            timestamp = int(time.time() * 1000)
            temp_path = os.path.join(tempfile.gettempdir(), f"worship_preview_{self.song_counter}_{self.current_slide_index}_{timestamp}.png")
            img.save(temp_path)
            
            # Actualizează preview-ul cu imaginea generată
            self.preview_image.content = ft.Image(
                src=temp_path,
                width=640,
                height=360,
                border_radius=16,
            )
            self.preview_image.bgcolor = None  # Eliminăm background-ul placeholder
    
    def _generate_slide_preview(self, text: str, font_size: int, label: str, is_last: bool = False, is_refrain: bool = False):
        """Generează o imagine preview a slide-ului folosind Pillow."""
        # Procesează textul pentru refren - normalizează spațierea marcajelor
        if is_refrain:
            lines = text.split('\n')
            for line_idx in range(len(lines)):
                lines[line_idx] = lines[line_idx].replace(': /', ':/')
            text = '\n'.join(lines)

        # Convertește în imagine
        preview_width, preview_height = 1280, 720
        img = Image.new('RGB', (preview_width, preview_height), color='black')
        draw = ImageDraw.Draw(img)
        
        scale_x = preview_width / 13.333
        scale_y = preview_height / 7.5
        scaled_font_size = int(font_size * scale_y / 72)
        
        try:
            font = ImageFont.truetype("calibri.ttf", scaled_font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", scaled_font_size)
            except:
                font = ImageFont.load_default()
        
        lines = text.split("\n")
        line_height = scaled_font_size * 1.2
        total_text_height = len(lines) * line_height
        start_y = (preview_height - total_text_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (preview_width - text_width) // 2
            y = start_y + i * line_height
            draw.text((x, y), line, fill='white', font=font)
        
        if is_last:
            try:
                amin_font = ImageFont.truetype("calibri.ttf", int(22 * scale_y / 72))
            except:
                amin_font = font
            
            amin_bbox = draw.textbbox((0, 0), "Amin", font=amin_font)
            amin_width = amin_bbox[2] - amin_bbox[0]
            amin_x = preview_width - amin_width - int(0.4 * scale_x)
            amin_y = preview_height - int(1.0 * scale_y)
            draw.text((amin_x, amin_y), "Amin", fill='white', font=amin_font)
        
        img = img.resize((640, 360), Image.Resampling.LANCZOS)
        return img
    
    def on_prev_slide(self, e):
        """Handler pentru slide anterior."""
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            self.update_preview()
            self.update_slide_list()
            self.page.update()
    
    def on_next_slide(self, e):
        """Handler pentru slide următor."""
        if self.current_slide_index < len(self.slides_data) - 1:
            self.current_slide_index += 1
            self.update_preview()
            self.update_slide_list()
            self.page.update()
    
    def on_font_minus(self, e):
        """Scade fontul cu 2pt."""
        if self.current_font_size > 20:
            self.current_font_size -= 2
            self.font_label.value = f"{self.current_font_size}pt"
            self.update_preview()
            self.page.update()
    
    def on_font_plus(self, e):
        """Crește fontul cu 2pt."""
        if self.current_font_size < 72:
            self.current_font_size += 2
            self.font_label.value = f"{self.current_font_size}pt"
            self.update_preview()
            self.page.update()
    
    def on_edit_click(self, e):
        """Deschide dialog de editare text."""
        if not self.slides_data:
            return
        
        slide_data = self.slides_data[self.current_slide_index]
        
        # Procesează textul pentru refren (adaugă marcajele /: :/)
        display_text = slide_data['text']
        is_refrain = bool(self.current_song and slide_data['key'] in self.current_song.refrains)
        
        if is_refrain:
            lines = display_text.split('\n')
            # Normalizează marcajele
            for line_idx in range(len(lines)):
                lines[line_idx] = lines[line_idx].replace(': /', ':/')
            
            # Adaugă marcaj la început dacă nu există
            first_line = lines[0].strip()
            if '/:' not in first_line:
                lines[0] = f"/: {lines[0]}"
            
            # Adaugă marcaj la final dacă nu există
            last_line = lines[-1].strip()
            if ':/' not in last_line:
                lines[-1] = f"{lines[-1]} :/"
            
            display_text = '\n'.join(lines)
        
        def save_edit(e):
            slide_data['text'] = edit_field.value
            dlg.open = False
            self.update_preview()
            self.page.update()
        
        def close_dlg(e):
            dlg.open = False
            self.page.update()
        
        edit_field = ft.TextField(
            value=display_text,
            multiline=True,
            border_color=self.COLOR_BORDER,
            focused_border_color=self.COLOR_CYAN,
            text_size=14,
            text_align=ft.TextAlign.CENTER,
            expand=True,
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"Edit {slide_data['label']}", color=self.COLOR_TEXT_WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=self.COLOR_BG_CARD,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Container(expand=True),
                        ft.Row(
                            [edit_field],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True,
                        ),
                        ft.Container(expand=True),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                bgcolor=self.COLOR_BG_DARK,
                width=640,
                height=360,
                border_radius=16,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=close_dlg,
                    style=ft.ButtonStyle(color=self.COLOR_TEXT_GRAY),
                ),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_edit,
                    style=ft.ButtonStyle(
                        bgcolor=self.COLOR_CYAN,
                        color="#000000",
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            open=True,
        )
        
        self.page.overlay.append(dlg)
        self.page.update()
    
    def on_toggle_edit_mode(self, e):
        """Comută între modul normal și modul editare."""
        if not self.slides_data:
            return
        
        self.editing_mode = not self.editing_mode
        
        if self.editing_mode:
            # Intră în mod editare
            self.edit_toggle_btn.content = ft.Text("Disable Editing", weight=ft.FontWeight.BOLD)
            self.edit_toggle_btn.style = ft.ButtonStyle(
                bgcolor=self.COLOR_RED,
                color=self.COLOR_TEXT_WHITE,
                padding=15,
            )
            self.status_text.value = "Editing mode ON - type to auto-save"
            self.status_text.color = self.COLOR_CYAN
        else:
            # Ieși din mod editare - SALVEZ textul înainte de a curăța
            if self.edit_text_field and self.slides_data:
                slide_data = self.slides_data[self.current_slide_index]
                saved_text = self.edit_text_field.value
                slide_data['text'] = saved_text
            
            self.edit_toggle_btn.content = ft.Text("Enable Editing", weight=ft.FontWeight.BOLD)
            self.edit_toggle_btn.style = ft.ButtonStyle(
                bgcolor=self.COLOR_CYAN,
                color="#000000",
                padding=15,
            )
            self.status_text.value = "Editing mode OFF - changes saved"
            self.status_text.color = self.COLOR_GREEN
            # Curăță referința la text field
            self.edit_text_field = None
        
        self.update_preview()
        self.page.update()
    
    def on_edit_text_change(self, e):
        """Auto-save la fiecare modificare în mod editare."""
        if self.editing_mode and self.slides_data and self.edit_text_field:
            current_slide_data = self.slides_data[self.current_slide_index]
            edited_key = current_slide_data['key']
            new_text = self.edit_text_field.value
            
            # Updatez TOATE slide-urile cu acelasi key (pentru consistenta)
            # Deoarece in PowerPoint toate aparitiile aceluiasi refren folosesc acelasi text
            for slide_data in self.slides_data:
                if slide_data['key'] == edited_key:
                    slide_data['text'] = new_text
    
    def on_generate_click(self, e):
        """Generează PowerPoint."""
        if not self.current_song:
            self.status_text.value = "No song loaded!"
            self.status_text.color = self.COLOR_RED
            self.page.update()
            return
        
        try:
            # Update current_song cu textele editate din slides_data
            # Salvez textele editate înapoi în song
            if self.slides_data:
                for slide_data in self.slides_data:
                    key = slide_data['key']
                    edited_text = slide_data['text']
                    
                    if key in self.current_song.stanzas:
                        self.current_song.stanzas[key] = edited_text
                    elif key in self.current_song.refrains:
                        self.current_song.refrains[key] = edited_text
                    elif key in self.current_song.bridges:
                        self.current_song.bridges[key] = edited_text
                    elif key in self.current_song.codas:
                        self.current_song.codas[key] = edited_text
            
            font_calc = FontCalculation(size_pt=self.current_font_size)
            
            output_path = generate_pptx(
                self.current_song,
                font_calc,
                os.path.join(self.output_dir, generate_filename(self.current_song.title)),
                use_caps=False
            )
            
            self.status_text.value = f"✓ Saved: {output_path}"
            self.status_text.color = self.COLOR_GREEN
            
            # Deschide automat dacă toggle-ul e ON
            if self.config.get("app", {}).get("auto_open_ppt", True):
                try:
                    os.startfile(output_path)
                except Exception as open_error:
                    print(f"Could not open file: {open_error}")
            
        except Exception as ex:
            self.status_text.value = f"✗ Error: {str(ex)}"
            self.status_text.color = self.COLOR_RED
        
        self.page.update()


def main(page: ft.Page):
    """Entry point pentru aplicația FLET."""
    WorshipPPTApp(page)


if __name__ == "__main__":
    ft.run(main)
