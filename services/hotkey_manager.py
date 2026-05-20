# -*- coding: utf-8 -*-
"""
Modul Global Hotkey URL Capture

Permite capturarea automată a URL-urilor din browser folosind
o combinație de taste globală, chiar dacă aplicația nu are focus.

Flux:
1. User selectează text (URL) în browser
2. Apasă combinația configurată (default: Ctrl+K)
3. Modulul salvează clipboard, injectează Ctrl+C, citește, restaurează
4. Validează URL-ul (trebuie să fie de la resursecrestine.ro)
5. Pune URL-ul într-o queue thread-safe
6. UI-ul Flet citește din queue și declanșează scraping automat
"""

import ctypes
import queue
import threading
import time
import re
from typing import Optional, Callable
from urllib.parse import urlparse

import pyperclip
from pynput import keyboard


class ClipboardManager:
    """Gestionează clipboard-ul: salvare, captură, restaurare."""
    
    # Windows virtual key codes
    VK_CONTROL = 0x11
    VK_C = 0x43
    KEYEVENTF_KEYUP = 0x0002
    
    def __init__(self):
        self._original_clipboard: Optional[str] = None
    
    def capture(self) -> str:
        """
        Capturează textul selectat fără să deranjeze userul.
        
        Returns:
            Textul capturat din clipboard după simularea Ctrl+C
        """
        # Pas 1: Salvează clipboard-ul original
        self._save_original()
        
        # Pas 2: Simulează Ctrl+C
        self._send_ctrl_c()
        
        # Pas 3: Așteaptă procesarea (Windows are nevoie de timp)
        time.sleep(0.15)
        
        # Pas 4: Citește clipboard-ul
        captured_text = self._read_clipboard()
        
        # Pas 5: Restaurează clipboard-ul original imediat
        self._restore_original()
        
        return captured_text
    
    def _save_original(self):
        """Salvează conținutul actual al clipboard-ului."""
        try:
            self._original_clipboard = pyperclip.paste()
        except Exception:
            self._original_clipboard = ""
    
    def _read_clipboard(self) -> str:
        """Citește conținutul clipboard-ului."""
        try:
            return pyperclip.paste() or ""
        except Exception:
            return ""
    
    def _restore_original(self):
        """Restaurează clipboard-ul la valoarea originală."""
        if self._original_clipboard is not None:
            try:
                # Dacă originalul era gol, șterge clipboard-ul
                if self._original_clipboard == "":
                    pyperclip.copy("")
                else:
                    pyperclip.copy(self._original_clipboard)
            except Exception:
                pass
    
    def _send_ctrl_c(self):
        """Simulează apăsarea Ctrl+C folosind Windows API (ctypes)."""
        # Apasă Ctrl
        ctypes.windll.user32.keybd_event(self.VK_CONTROL, 0, 0, 0)
        # Apasă C
        ctypes.windll.user32.keybd_event(self.VK_C, 0, 0, 0)
        # Eliberează C
        ctypes.windll.user32.keybd_event(self.VK_C, 0, self.KEYEVENTF_KEYUP, 0)
        # Eliberează Ctrl
        ctypes.windll.user32.keybd_event(self.VK_CONTROL, 0, self.KEYEVENTF_KEYUP, 0)


class URLValidator:
    """Validează URL-uri de la resursecrestine.ro."""
    
    # Domenii acceptate
    ALLOWED_DOMAINS = [
        'resursecrestine.ro',
        'www.resursecrestine.ro',
    ]
    
    # Pattern-uri URL valide
    URL_PATTERNS = [
        r'^https?://(?:www\.)?resursecrestine\.ro/.+',
    ]
    
    @classmethod
    def is_valid(cls, text: str) -> bool:
        """
        Verifică dacă textul este un URL valid de la resursecrestine.ro.
        
        Args:
            text: Textul de validat
            
        Returns:
            True dacă e URL valid, False altfel
        """
        if not text or not isinstance(text, str):
            return False
        
        text = text.strip()
        
        # Trebuie să înceapă cu http
        if not text.startswith('http'):
            return False
        
        # Verifică pattern-ul URL
        for pattern in cls.URL_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # Verificare fallback: parsează domeniul
        try:
            parsed = urlparse(text)
            domain = parsed.netloc.lower()
            if any(domain.endswith(allowed.lower()) for allowed in cls.ALLOWED_DOMAINS):
                return True
        except Exception:
            pass
        
        return False
    
    @classmethod
    def clean_url(cls, text: str) -> str:
        """
        Curăță URL-ul de eventuale caractere extra.
        
        Args:
            text: URL-ul brut
            
        Returns:
            URL-ul curățat
        """
        text = text.strip()
        # Elimină spații din interior (uneori copierea selectează și spații)
        text = text.replace(' ', '')
        return text


class GlobalHotkeyListener:
    """
    Ascultător global de taste folosind pynput.
    Detectează combinația configurată și declanșează captura.
    Folosește coduri taste virtuale (vk) pentru detectare robustă.
    """
    
    # VK codes pentru taste comune
    VK_CTRL = 162  # VK_LCONTROL
    VK_SHIFT = 160  # VK_LSHIFT
    VK_ALT = 164  # VK_LMENU
    VK_K = 75
    VK_W = 87
    VK_C = 67
    VK_F8 = 119  # VK_F8
    
    def __init__(self, url_queue: queue.Queue, combination_vk=None):
        """
        Inițializează ascultătorul.
        
        Args:
            url_queue: Coadă thread-safe pentru comunicare cu UI
            combination_vk: Listă de vk codes pentru hotkey (default: [VK_F8])
        """
        self.url_queue = url_queue
        self.combination_vk = combination_vk or [self.VK_F8]
        self.current_vks = set()  # Set de vk codes apăsate
        self.listener: Optional[keyboard.Listener] = None
        self.clipboard_manager = ClipboardManager()
        self.validator = URLValidator()
        self._running = False
        self._last_capture_time = 0
        self._debounce_seconds = 1.0  # Previne dubla captură
    
    def start(self):
        """Pornește ascultătorul pe un thread separat."""
        if self._running:
            return
        
        self._running = True
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,  # Nu bloca tastele, doar ascultă
        )
        self.listener.start()
        vk_names = [f"vk={vk}" for vk in self.combination_vk]
        print(f"[HOTKEY] Global hotkey listener started (F8)")
        print(f"[HOTKEY DEBUG] Waiting for vk codes: {vk_names}")
    
    def stop(self):
        """Oprește ascultătorul."""
        self._running = False
        if self.listener:
            self.listener.stop()
            self.listener = None
        print("[HOTKEY] Global hotkey listener stopped")
    
    def is_alive(self) -> bool:
        """Verifică dacă ascultătorul rulează."""
        return self.listener is not None and self.listener.is_alive()
    
    def _get_vk(self, key):
        """Extrage vk code dintr-o tastă pynput."""
        if hasattr(key, 'vk') and key.vk:
            return key.vk
        # Mapare specială pentru Key.ctrl, Key.shift etc.
        if key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_l:
            return self.VK_CTRL
        if key == keyboard.Key.ctrl_r:
            return self.VK_CTRL
        if key == keyboard.Key.shift or key == keyboard.Key.shift_l:
            return self.VK_SHIFT
        if key == keyboard.Key.shift_r:
            return self.VK_SHIFT
        if key == keyboard.Key.alt or key == keyboard.Key.alt_l:
            return self.VK_ALT
        if key == keyboard.Key.alt_r:
            return self.VK_ALT
        # Tastele funcționale
        if hasattr(keyboard.Key, 'f9') and key == keyboard.Key.f9:
            return self.VK_F8
        if hasattr(keyboard.Key, 'f1') and key == keyboard.Key.f1:
            return 112
        if hasattr(keyboard.Key, 'f2') and key == keyboard.Key.f2:
            return 113
        if hasattr(keyboard.Key, 'f3') and key == keyboard.Key.f3:
            return 114
        if hasattr(keyboard.Key, 'f4') and key == keyboard.Key.f4:
            return 115
        if hasattr(keyboard.Key, 'f5') and key == keyboard.Key.f5:
            return 116
        if hasattr(keyboard.Key, 'f6') and key == keyboard.Key.f6:
            return 117
        if hasattr(keyboard.Key, 'f7') and key == keyboard.Key.f7:
            return 118
        if hasattr(keyboard.Key, 'f8') and key == keyboard.Key.f8:
            return 119
        if hasattr(keyboard.Key, 'f10') and key == keyboard.Key.f10:
            return 121
        if hasattr(keyboard.Key, 'f11') and key == keyboard.Key.f11:
            return 122
        if hasattr(keyboard.Key, 'f12') and key == keyboard.Key.f12:
            return 123
        return None
    
    def _on_press(self, key):
        """Handler pentru apăsarea unei taste."""
        if not self._running:
            return
        
        vk = self._get_vk(key)
        if vk is None:
            return
        
        # DEBUG: Afișează tastele relevante
        if vk in self.combination_vk:
            print(f"[HOTKEY DEBUG] Key pressed: vk={vk}")
            self.current_vks.add(vk)
            print(f"[HOTKEY DEBUG] Active vk codes: {self.current_vks}")
            
            # Verifică combinația
            if self._is_combination_active():
                print(f"[HOTKEY DEBUG] Combination COMPLETE! Triggering capture...")
                self._on_hotkey_triggered()
    
    def _on_release(self, key):
        """Handler pentru eliberarea unei taste."""
        vk = self._get_vk(key)
        if vk and vk in self.current_vks:
            self.current_vks.discard(vk)
            print(f"[HOTKEY DEBUG] Key released: vk={vk}")
    
    def _is_combination_active(self) -> bool:
        """Verifică dacă toate tastele din combinație sunt apăsate."""
        return all(vk in self.current_vks for vk in self.combination_vk)
    
    def _on_hotkey_triggered(self):
        """Executat când combinația este detectată."""
        # Debounce: nu captura mai des de o dată pe secundă
        current_time = time.time()
        if current_time - self._last_capture_time < self._debounce_seconds:
            return
        self._last_capture_time = current_time
        
        print("[HOTKEY] Combination detected! Capturing clipboard...")
        
        try:
            # Capturează textul selectat
            captured_text = self.clipboard_manager.capture()
            
            if not captured_text:
                print("[HOTKEY] No text captured (nothing selected)")
                return
            
            print(f"[HOTKEY] Captured: {captured_text[:80]}...")
            
            # Curăță URL-ul
            cleaned_url = self.validator.clean_url(captured_text)
            
            # Validează URL-ul
            if self.validator.is_valid(cleaned_url):
                print(f"[HOTKEY] Valid URL detected: {cleaned_url}")
                # Pune în coadă pentru UI
                self.url_queue.put({
                    'type': 'url',
                    'url': cleaned_url,
                    'timestamp': current_time,
                })
            else:
                print(f"[HOTKEY] Invalid URL (ignored): {cleaned_url[:80]}...")
                
        except Exception as e:
            print(f"[HOTKEY] Error during capture: {e}")


class HotkeyManager:
    """
    Manager principal pentru sistemul de hotkey global.
    Leagă toate componentele împreună.
    """
    
    def __init__(self):
        self.url_queue: queue.Queue = queue.Queue()
        self.listener = GlobalHotkeyListener(self.url_queue)
        self._callback: Optional[Callable] = None
    
    def start(self):
        """Pornește sistemul de hotkey."""
        self.listener.start()
    
    def stop(self):
        """Oprește sistemul de hotkey."""
        self.listener.stop()
    
    def has_url(self) -> bool:
        """Verifică dacă există URL-uri noi în coadă."""
        return not self.url_queue.empty()
    
    def get_url(self) -> Optional[dict]:
        """
        Extrage un URL din coadă.
        
        Returns:
            Dict cu 'url', 'timestamp' sau None dacă coada e goală
        """
        try:
            return self.url_queue.get_nowait()
        except queue.Empty:
            return None
    
    def set_callback(self, callback: Callable):
        """Setează callback-ul pentru când un URL este capturat."""
        self._callback = callback
    
    def check_and_process(self):
        """
        Verifică coada și procesează URL-urile.
        Apelează această metodă periodic din UI (ex: la fiecare 100ms).
        """
        while self.has_url():
            data = self.get_url()
            if data and self._callback:
                self._callback(data['url'])


# Singleton pentru acces ușor
_hotkey_manager: Optional[HotkeyManager] = None


def get_hotkey_manager() -> HotkeyManager:
    """Returnează instanța singleton a HotkeyManager."""
    global _hotkey_manager
    if _hotkey_manager is None:
        _hotkey_manager = HotkeyManager()
    return _hotkey_manager
