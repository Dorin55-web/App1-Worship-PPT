#!/usr/bin/env python3
"""
Worship PPT Generator - Flet Build Version
"""

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Entry point pentru aplicatia FLET."""
    try:
        import flet as ft
        from config.settings import load_config, ensure_directories
        from flet_ui.app import WorshipPPTApp
        
        def app_main(page: ft.Page):
            try:
                load_config()
                ensure_directories()
                WorshipPPTApp(page)
            except Exception as e:
                page.add(ft.Text(f"Eroare la initializare: {str(e)}", color="red"))
                page.add(ft.Text(traceback.format_exc(), color="red", size=10))
        
        ft.run(app_main)
        
    except Exception as e:
        print(f"EROARE CRITICA: {str(e)}")
        print(traceback.format_exc())
        
        # Daca flet nu se poate importa, incercam sa afisam in consola
        try:
            import flet as ft
            def error_page(page: ft.Page):
                page.add(ft.Text(f"Eroare la pornire: {str(e)}", color="red", size=20))
                page.add(ft.Text(traceback.format_exc(), color="red", size=10))
            ft.app(target=error_page)
        except:
            pass

if __name__ == "__main__":
    main()
