# Worship PPT Generator

## Descriere Generală

**Worship PPT Generator** este o aplicație desktop modernă pentru Windows care transformă versurile cântărilor creștine de pe internet în prezentări PowerPoint profesionale, gata de utilizat în biserici sau grupuri de închinare.

## 🎯 Scopul Aplicației

Aplicația extrage automat versurile cântărilor de pe site-ul **resursecrestine.ro** și le convertește în fișiere PowerPoint (.pptx) formatate profesional, cu:
- Text centrat și dimensionat optim
- Background negru (ideal pentru proiecție)
- Fonturi adaptate pentru lizibilitate
- Slide-uri organizate logic (strofe, refrene)

## ✨ Funcționalități Principale

### 1. **Extragere Automată**
- Preia cântece de pe resursecrestine.ro folosind URL-ul
- Parsează automat structura: strofe, refrene, punți, code
- Detectează și gestionează multiple refrene (R1, R2, etc.)

### 2. **Preview în Timp Real**
- Vizualizare a tuturor slide-urilor înainte de generare
- Navigare cu Previous/Next între slide-uri
- Lista completă de slide-uri în panoul stâng
- Imagine preview generată identic cu PowerPoint-ul final

### 3. **Editare Flexibilă**
- Editare text direct în aplicație
- Ajustare dimensiune font (±2pt)
- Detectare automată font optim pentru fiecare slide
- Procesare inteligentă a refrenelor (marcaje /: :/)

### 4. **Generare PowerPoint**
- Creare fișiere .pptx profesionale
- Format 16:9 (widescreen)
- Font Calibri, text alb pe fundal negru
- "Amin" automat pe ultimul slide
- Thumbnail preview în Windows Explorer

### 5. **Management Cântece**
- Istoric al cântecelor generate (salvat local)
- Deschidere automată după generare (opțional)
- Salvare în folder configurabil
- Generare nume fișier inteligentă (fără diacritice, max 4 cuvinte)

### 6. **Setări Personalizabile**
- Locație customizată pentru salvare fișiere
- Toggle "Auto Open" - deschide automat PowerPoint după generare
- Configurații persistente între sesiuni

## 🖥️ Interfața Utilizator

### Design Modern (Dark Theme)
- **Sidebar** (80px): Navigare rapidă (Home, Setări)
- **Lista Slide-uri** (250px): Toate slide-urile vizibile, clicabile
- **Zona Principală**:
  - Input URL + buton Run
  - Preview imagine (640x360px)
  - Navigare Previous/Next cu counter
  - Control font (+/-)
  - Buton Edit Text
  - Status bar cu informații

### Temă de Culori
- Fundal: `#0d1117` (GitHub dark)
- Carduri: `#161b22`
- Accent cyan: `#00d4ff`
- Accent purple: `#7c3aed`
- Text alb și gri pentru contrast optim

## 🔄 Fluxul de Lucru Tipic

```
1. Deschidere aplicație
   └─► Interfața modernă se încarcă instant

2. Introducere URL
   └─► Utilizatorul lipește URL-ul cântării

3. Apăsare "Run"
   └─► Aplicația extrage și parsează cântarea (2-3 secunde)
   └─► Afișează preview primului slide
   └─► Listează toate slide-urile în panoul stâng

4. Navigare și Editare (opțional)
   └─► Previous/Next pentru vizualizare toate slide-urile
   └─► Ajustare font dacă e necesar
   └─► Editare text direct dacă e cazul

5. Generare PowerPoint
   └─► Apăsare buton "Generate"
   └─► Fișierul .pptx este creat în folderul output
   └─► Deschide automat în PowerPoint (dacă e activat)

6. Utilizare în Proiecție
   └─► PowerPoint gata de prezentat în biserică
```

## 🛠️ Tehnologii Utilizate

### Stack Tehnic
- **Python 3.12** - Limbaj de programare
- **Flet 0.80.5** - Framework UI modern (Flutter-based)
- **python-pptx** - Generare fișiere PowerPoint
- **BeautifulSoup4** - Web scraping și parsing HTML
- **Pillow** - Generare imagini preview și thumbnails
- **Flutter** - Build nativ Windows

### Arhitectură Modulară
```
App1/
├── core/          # Motorul aplicației (scraper, parser, generator)
├── flet_ui/       # Interfața grafică modernă
├── services/      # Logica de business
├── config/        # Configurări și setări
├── data/          # Istoric și date locale
└── output/        # Fișiere PowerPoint generate
```

## 📦 Distribuție și Instalare

### Pentru Utilizatori Finali
- **Executabil Windows** (.exe) - 71 MB
- **Nu necesită instalare** - rulează direct
- **Nu necesită Python** sau alte dependențe
- **Portable** - poate fi rulat de pe USB sau orice locație

### Pentru Dezvoltatori
```bash
# Clonare repository
git clone <repo-url>
cd App1

# Creare mediu virtual
python -m venv venv
venv\Scripts\activate

# Instalare dependențe
pip install -r requirements.txt

# Rulare aplicație
python main.py

# Sau build executabil
python build_windows.py
```

## 🎨 Caracteristici Tehnice Avansate

### 1. **Procesare Text Inteligentă**
- Detectare automată strofe vs refrene
- Gestionare refrene multiple (R1, R2 la final)
- Marcaje refren automate (/::/)
- Eliminare diacritice din nume fișiere

### 2. **Optimizare Font**
- Calculare automată dimensiune font optimă
- Scalare inteligentă bazată pe lungimea textului
- Limitare 20-72pt pentru lizibilitate
- Spațiere optimă între linii

### 3. **Thumbnail Generation**
- Creare automată thumbnail pentru Windows Explorer
- Dimensiune 320x180px (aspect ratio 16:9)
- Font scalabil consistent
- Fundal negru cu text alb

### 4. **Error Handling**
- Prindere și afișare erori în interfață
- Validare URL înainte de procesare
- Fallback-uri pentru fonturi lipsă
- Logging detaliat pentru debugging

## 📋 Cerințe Sistem

### Minime
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB
- **Disk**: 100 MB spațiu liber
- **Internet**: Conexiune pentru descărcare cântece

### Recomandate
- **OS**: Windows 11
- **RAM**: 8 GB
- **Disk**: 500 MB (pentru fișiere generate)
- **Microsoft PowerPoint**: Pentru vizualizare (opțional)

## 🎯 Públic Țintă

- **Lideri de închinare** din biserici
- **Tehnicieni audio-video** responsabili cu proiecția
- **Grupuri de tineret** care folosesc cântece proiectate
- **Orice persoană** care vrea să creeze prezentări profesionale rapid

## 🚀 Avantaje Competitiv

✅ **Rapid**: Generează PowerPoint în 5-10 secunde  
✅ **Ușor**: Interfață intuitivă, fără training necesar  
✅ **Profesional**: Rezultate de calitate, gata de prezentare  
✅ **Gratuit**: Open source, fără costuri  
✅ **Modern**: UI contemporary, dark theme  
✅ **Portabil**: Nu necesită instalare complexă  

## 📝 Exemple de Utilizare

### Scenariu 1: Duminică Dimineața
> "Am nevoie de cântarea 'Mare Ești Tu' pentru serviciu. Copiez URL-ul din site, dau paste în aplicație, apăs Run, verific slide-urile, apăs Generate. Gata în 10 secunde!"

### Scenariu 2: Pregătire Conferință
> "Trebuie să pregătesc 20 de cântece pentru conferință. Folosesc aplicația pentru fiecare, le salvez în folderul conferinței, apoi le încarc pe laptop-ul de prezentare."

### Scenariu 3: Modificare Urgentă
> "Am observat o greșeală într-un vers. Deschid aplicația, încarc cântarea, editez textul direct în interfață, regenerez. Corectat în 30 de secunde!"

## 🏆 Concluzie

**Worship PPT Generator** este o soluție completă, modernă și eficientă pentru crearea prezentărilor PowerPoint cu versuri de cântece creștine. Combină puterea Python cu o interfață modernă Flet pentru a oferi o experiență utilizator superioară, economisind timp prețios în pregătirea materialelor pentru închinare.

---

**Versiune**: 1.0.0  
**Platformă**: Windows 10/11  
**Tehnologii**: Python, Flet, Flutter  
**Licență**: Open Source
