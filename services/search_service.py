import json
import pickle
import re
import os
import unicodedata
from collections import defaultdict
from typing import List, Dict, Any, Optional
import threading

class OptimizedSongIndex:
    """Motor de cautare ultra-rapid pentru versuri de cantari"""
    
    def __init__(self):
        self.index = {}
        self.songs = {}
        self.word_set = set()
        self._ready = False
        # Cache pentru normalizare
        self._norm_cache = {}
        self._token_cache = {}
        
    def _normalize(self, text):
        if not text:
            return ""
        if text in self._norm_cache:
            return self._norm_cache[text]
        
        result = text.lower()
        result = unicodedata.normalize('NFKD', result)
        result = ''.join(c for c in result if not unicodedata.combining(c))
        result = re.sub(r'[^\w\s]', ' ', result)
        result = ' '.join(result.split())
        
        self._norm_cache[text] = result
        return result
    
    def _tokenize(self, text):
        if text in self._token_cache:
            return self._token_cache[text]
        result = self._normalize(text).split()
        self._token_cache[text] = result
        return result
    
    def _clear_cache(self):
        self._norm_cache.clear()
        self._token_cache.clear()
    
    def load_or_build(self, json_path, index_path):
        if os.path.exists(index_path):
            try:
                with open(index_path, 'rb') as f:
                    data = pickle.load(f)
                self.index = data["index"]
                self.songs = data["songs"]
                self.word_set = set(self.index.keys())
                self._ready = True
                return True
            except:
                pass
        
        if not os.path.exists(json_path):
            return False
            
        with open(json_path, 'r', encoding='utf-8') as f:
            songs_data = json.load(f)
        
        # Build index
        index = defaultdict(list)
        for fisier, data in songs_data.items():
            versuri = data.get("versuri", [])
            for idx_strofa, strofa in enumerate(versuri):
                words = self._tokenize(strofa)
                for pozitie, cuvant in enumerate(words):
                    index[cuvant].append((fisier, idx_strofa, pozitie))
        
        self.index = dict(index)
        self.songs = songs_data
        self.word_set = set(self.index.keys())
        
        with open(index_path, 'wb') as f:
            pickle.dump({"index": self.index, "songs": self.songs}, f)
        
        self._ready = True
        return True
    
    def search(self, query, limit=20):
        if not query or not self._ready or len(query) < 2:
            return []
        
        query_words = self._tokenize(query)
        if not query_words:
            return []
        
        query_len = len(query_words)
        query_norm = self._normalize(query)
        
        # FAZA 1: Colectare candidati rapida
        candidates = {}
        
        for qw in query_words:
            if qw in self.index:
                postings = self.index[qw]
                for fisier, idx_strofa, _ in postings:
                    key = (fisier, idx_strofa)
                    if key not in candidates:
                        candidates[key] = 0
                    candidates[key] += 1
        
        if not candidates:
            return []
        
        # Sortam candidatii dupa numarul de match-uri si luam top 200
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:200]
        
        # FAZA 2: Calcul scor pentru top candidati
        results = []
        query_word_set = set(query_words)
        
        for (fisier, idx_strofa), match_count in sorted_candidates:
            if fisier not in self.songs:
                continue
            
            song_data = self.songs[fisier]
            versuri = song_data.get("versuri", [])
            if idx_strofa >= len(versuri):
                continue
            
            strofa = versuri[idx_strofa]
            words = self._tokenize(strofa)
            
            # 1. Phrase match rapid
            phrase_score = 0.0
            if query_len <= len(words):
                # Cautam match exact de fraza
                for i in range(len(words) - query_len + 1):
                    if words[i:i+query_len] == query_words:
                        phrase_score = 1.0
                        break
                
                # Daca nu e match exact, calculam consecutivitatea
                if phrase_score == 0.0:
                    max_cons = 0
                    cur_cons = 0
                    q_idx = 0
                    for w in words:
                        if q_idx < query_len and w == query_words[q_idx]:
                            cur_cons += 1
                            q_idx += 1
                            if cur_cons > max_cons:
                                max_cons = cur_cons
                        elif w == query_words[0]:
                            cur_cons = 1
                            q_idx = 1
                        else:
                            cur_cons = 0
                            q_idx = 0
                    
                    if max_cons > 0:
                        phrase_score = (max_cons / query_len) * 0.8
            
            # 2. Word coverage rapid
            word_set = set(words)
            matches = sum(1 for qw in query_word_set if qw in word_set)
            word_score = matches / query_len if query_len > 0 else 0
            
            # 3. Titlu match simplu
            titlu = song_data.get("titlu", "")
            titlu_norm = self._normalize(titlu)
            titlu_score = 0.0
            
            # Verificam daca toate cuvintele din query sunt in titlu
            titlu_words = set(titlu_norm.split())
            titlu_matches = sum(1 for qw in query_word_set if qw in titlu_words)
            titlu_score = titlu_matches / query_len if query_len > 0 else 0
            
            # Verificam si fuzzy pe titlu daca e scurt
            if len(query) < 50 and len(titlu_norm) < 100:
                # Simplu: cate caractere consecutive match-uiesc
                if query_norm in titlu_norm:
                    titlu_score = max(titlu_score, 0.9)
            
            # 4. Coverage ratio
            coverage = min(match_count / query_len, 1.0)
            
            # Scor final
            final_score = (
                phrase_score * 0.50 +
                word_score * 0.20 +
                titlu_score * 0.25 +
                coverage * 0.05
            )
            
            # Boost pentru phrase match perfect
            if phrase_score >= 0.9:
                final_score = min(final_score + 0.10, 1.0)
            elif phrase_score >= 0.7:
                final_score = min(final_score + 0.05, 1.0)
            
            results.append({
                "titlu": titlu or "Fara titlu",
                "fisier": fisier,
                "vers": strofa.strip(),
                "scor": round(final_score, 4)
            })
        
        # Sortare rapida
        results.sort(key=lambda x: x["scor"], reverse=True)
        return results[:limit]
    
    def get_stats(self):
        return {
            "total_songs": len(self.songs),
            "total_verses": sum(len(s.get("versuri", [])) for s in self.songs.values()),
            "total_words": len(self.index)
        }


class SearchService:
    """Serviciu de cautare pentru integrare in aplicatia FLET"""
    
    def __init__(self, search_dir: Optional[str] = None):
        self.index = OptimizedSongIndex()
        self.search_dir = search_dir
        self.json_path = None
        self.index_path = None
        self._loaded = False
        self._lock = threading.Lock()
        
        if search_dir:
            self.set_search_directory(search_dir)
    
    def set_search_directory(self, search_dir: str):
        """Seteaza directorul de cautare si incarca indexul"""
        self.search_dir = search_dir
        base_dir = os.path.dirname(search_dir)
        self.json_path = os.path.join(base_dir, "cantari_index.json")
        self.index_path = os.path.join(base_dir, "search_index.pkl")
        self._loaded = False
        
        # Incarca indexul
        return self._load_index()
    
    def _load_index(self):
        """Incarca sau construieste indexul"""
        if not self.json_path or not self.index_path:
            return False
            
        try:
            success = self.index.load_or_build(self.json_path, self.index_path)
            self._loaded = success
            return success
        except Exception as e:
            print(f"[SearchService] Eroare la incarcarea indexului: {e}")
            self._loaded = False
            return False
    
    def is_ready(self):
        """Verifica daca serviciul este pregatit pentru cautare"""
        return self._loaded and self.index._ready
    
    def search_by_title(self, title: str, limit: int = 10):
        """Cauta dupa titlu"""
        if not self.is_ready():
            return []
        return self.index.search(title, limit=limit)
    
    def search_by_lyrics(self, lyrics: str, limit: int = 10):
        """Cauta dupa versuri (prima strofa)"""
        if not self.is_ready():
            return []
        
        # Ia primele 2-3 randuri pentru cautare
        lines = lyrics.strip().split('\n')[:3]
        query = ' '.join(lines)
        return self.index.search(query, limit=limit)
    
    def search_by_url(self, url: str, title: str, lyrics: str, limit: int = 10):
        """Cauta dupa URL - foloseste titlul si versurile"""
        results = []
        
        # Cauta dupa titlu intai
        if title:
            title_results = self.search_by_title(title, limit=limit)
            results.extend(title_results)
        
        # Daca nu gaseste destule, cauta si dupa versuri
        if len(results) < limit and lyrics:
            lyrics_results = self.search_by_lyrics(lyrics, limit=limit)
            # Adauga doar rezultate noi (fisiere diferite)
            existing_files = {r['fisier'] for r in results}
            for r in lyrics_results:
                if r['fisier'] not in existing_files:
                    results.append(r)
        
        # Sorteaza dupa scor
        results.sort(key=lambda x: x['scor'], reverse=True)
        return results[:limit]
    
    def get_file_path(self, filename: str):
        """Returneaza calea completa catre fisier"""
        if self.search_dir:
            return os.path.join(self.search_dir, filename)
        return filename
    
    def get_stats(self):
        """Returneaza statistici despre index"""
        if not self.is_ready():
            return {"total_songs": 0, "total_verses": 0, "total_words": 0}
        return self.index.get_stats()


# Singleton instance
_search_service = None

def get_search_service(search_dir: Optional[str] = None) -> SearchService:
    """Returneaza instanta singleton a serviciului de cautare"""
    global _search_service
    if _search_service is None:
        _search_service = SearchService(search_dir)
    elif search_dir:
        _search_service.set_search_directory(search_dir)
    return _search_service
