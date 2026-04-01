# Changelog — Worship PPT Generator

---

## Sesiunea din 09 Martie 2026

### Bug Fix 1 — Secțiunea `I:` apărea în ultima strofă
**Fișier:** `core/parser.py`

**Problema:**
Pe resursecrestine.ro, cântările conțin la final o linie de tip `I:` (index/metadata),
de exemplu:
```
I: Cântările Harului, volumul 16, cântarea 335
- rugăciune fierbinte -
```
Linia `I:` era filtrată, dar conținutul de pe rândul următor (ex: `- rugăciune fierbinte -`)
era adăugat la ultima strofă a cântării.

**Fix:**
`I:` (și variantele `I1:`, `I2:`, etc.) sunt acum detectate ca marcaj de secțiune
de tip `"info"` în `_detect_section_marker`. Secțiunile de tip `"info"` sunt
complet ignorate în `_save_section`.
Acoperă toate formatele: `I:` pe linie separată, `I:` cu text pe aceeași linie,
multiple linii după `I:`, și `I:` în mijlocul cântării.

---

### Bug Fix 2 — Refrenul lipsea când era primul în cântare
**Fișier:** `core/scraper.py`

**Problema:**
Unele cântări (ex: [Vocea lui se aude](https://www.resursecrestine.ro/cantece/2761/vocea-lui-se-aude))
au structura: `R:` primul, apoi strofele (`1.`, `2.`).
Scraper-ul căuta markere de start în ordine, iar `"1."` era găsit **înainte** de `"R:"`.
Extracția începea de la prima strofă, **refrenul de dinainte era pierdut complet**.

**Fix:**
- `"R:"` adăugat în `start_markers` cu prioritate mai mare decât `"1."`
- `"r:"` adăugat în lista de verificare a contextului (`context_check`)
- Ordinea nouă: `Strofa X` → `R: /:` → `R:/:`→ `R:` → `Refren` → `1.` → ...

---

### Testare comprehensivă
**Fișier:** `test_parser_comprehensive.py` *(șters după validare)*

Au fost testate 22 de categorii, 57 de teste — toate trecute (PASS):
- Strofe simple, cu refren, refrene multiple (R1/R2/R3)
- Bridge (B:), Coda (C:), ordine explicită (O:)
- Secțiunea I: în 5 formate diferite
- COR:, REFREN:, format "Strofa 1" cu cuvânt
- Linii cu URL-uri, linii goale consecutive
- Text fără marcaje, refren fără strofă
- Marcaj + text pe aceeași linie, duplicate
- I: în mijlocul cântării

---

### Documentație adăugată
**Fișier:** `CANTARI_REFERINTA.md`

Listă cu toate PPT-urile generate și URL-urile corespunzătoare de pe resursecrestine.ro,
inclusiv nota că istoricul păstrează doar ultimele 5 intrări (setat în `config/config.json`).
