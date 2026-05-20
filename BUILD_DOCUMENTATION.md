# Worship PPT Generator - BUILD DOCUMENTATION
# PowerPoint Presentation Generator for Christian Worship Songs

## DESCRIPTION
FLET desktop application that generates PowerPoint (.pptx) presentations from lyrics extracted from resursecrestine.ro. Includes global URL capture via hotkey (F8) and inline text editing.

## TECHNOLOGIES
- Python 3.12
- FLET 0.80.5 (UI Framework)
- python-pptx (PowerPoint generation)
- pynput + pyperclip (Global F8 hotkey)
- Pillow (Image preview generation)
- BeautifulSoup4 + requests (Web scraping)

## PROJECT STRUCTURE

App1/
├── main.py                    # Entry point
├── build_windows.py           # PyInstaller build script
├── pyproject.toml             # Build configuration
├── requirements.txt           # Python dependencies
├── config/
│   ├── settings.py            # Configuration manager
│   └── config.json            # User settings
├── core/
│   ├── scraper.py             # Web scraping resursecrestine.ro
│   ├── parser.py              # Song structure parsing
│   ├── ppt_generator.py       # PowerPoint generation
│   ├── font_calculator.py     # Optimal font calculation
│   ├── models.py              # Data models
│   └── history_manager.py     # Song history
├── flet_ui/
│   └── app.py                 # Complete FLET interface
├── services/
│   ├── song_service.py        # API business logic
│   └── hotkey_manager.py      # Global F8 hotkey manager
├── interfaces/
│   └── __init__.py            # Package init
├── data/                      # Application data (history.json)
├── output/                    # Generated PPTs
└── start/
    ├── start-direct.vbs       # Hidden launcher (recommended)
    ├── start-ui.bat           # Visible CMD launcher
    ├── start-ui-debug.bat     # Debug launcher
    └── README.txt             # Run instructions

## BUILD METHODS

### METHOD 1: flet pack (RECOMMENDED) - PyInstaller
Uses PyInstaller to create a standalone executable.
Python runs as the main process, so `pynput` works correctly.

**Command:**
```bash
flet pack main.py \
  --onedir \
  --name "Worship PPT Generator" \
  --product-name "Worship PPT Generator" \
  --company-name "Worship App" \
  --add-data "config:config" \
  --add-data "core:core" \
  --add-data "flet_ui:flet_ui" \
  --add-data "services:services" \
  --add-data "interfaces:interfaces" \
  --hidden-import pynput \
  --hidden-import pyperclip \
  --hidden-import pynput.keyboard \
  --hidden-import pynput.mouse \
  --distpath "dist_pack" \
  -y
```

**Result:**
- Folder: `dist_pack/Worship PPT Generator/`
- Executable: `Worship PPT Generator.exe`
- Size: ~200MB
- pynput/pyperclip: Works (Python is the main process)

**Post-build (manual step):**
Copy `pynput` and `pyperclip` into `_internal/` if they are missing:
```bash
cp venv/Lib/site-packages/pynput "dist_pack/Worship PPT Generator/_internal/"
cp venv/Lib/site-packages/pyperclip "dist_pack/Worship PPT Generator/_internal/"
```

### METHOD 2: flet build windows (NATIVE FLUTTER)
Uses Flutter to compile the application natively for Windows.
Python runs in `serious_python` (background thread).

**Command:**
```bash
flet build windows --verbose
```

**Result:**
- Folder: `build/windows/`
- Executable: `worship_ppt_generator.exe`
- Size: ~100MB
- pynput/pyperclip: **DOES NOT WORK** (missing message loop)

**Known Issue:**
`serious_python` runs Python in a detached thread without a Windows message loop.
`pynput` requires `GetMessage()`/`PeekMessage()` to receive events from Windows hooks. Without a message loop, hooks are installed but never receive callbacks.

**Solution:** There is no Python workaround. The C++ code in `serious_python_windows_plugin.cpp` needs to be modified to add a message pump.

## COMPLETE BUILD COMMAND (with absolute Python path)

```powershell
# Activate venv
.\venv\Scripts\activate

# Set UTF-8 encoding
$env:PYTHONIOENCODING = "utf-8"

# Run flet pack
python -m flet pack main.py `
  --onedir `
  --name "Worship PPT Generator" `
  --product-name "Worship PPT Generator" `
  --company-name "Worship App" `
  --add-data "config:config" `
  --add-data "core:core" `
  --add-data "flet_ui:flet_ui" `
  --add-data "services:services" `
  --add-data "interfaces:interfaces" `
  --hidden-import pynput `
  --hidden-import pyperclip `
  --hidden-import pynput.keyboard `
  --hidden-import pynput.mouse `
  --distpath "dist_pack" `
  -y
```

## REQUIRED DEPENDENCIES

### Python packages (requirements.txt):
```
requests>=2.31.0
beautifulsoup4>=4.12.0
python-pptx>=0.6.21
rich>=13.0.0
pydantic>=2.0.0
flet>=0.10.0
Pillow>=10.0.0
pynput>=1.7.6
pyperclip>=1.8.2
```

### System dependencies:
- Windows 10/11
- Python 3.12 (for development)
- Flutter SDK (only for `flet build`, not required for `flet pack`)
- Microsoft Visual C++ Redistributable (automatically included in the build)

## KNOWN ISSUES AND SOLUTIONS

### 1. pynput doesn't work in flet build
**Cause:** `serious_python` doesn't have a Windows message loop
**Solution:** Use `flet pack` instead of `flet build`

### 2. pynput/pyperclip missing from PyInstaller build
**Cause:** PyInstaller fails to dynamically detect the imports
**Solution:** Manually copy from `venv/Lib/site-packages/` to `_internal/`

### 3. "Visual Studio toolchain" error during flet build
**Cause:** Incomplete Visual Studio installation or missing C++ components
**Solution:** Install the "Desktop development with C++" workload via the Visual Studio Installer

### 4. Calibri font missing on the target machine
**Cause:** Calibri is bundled with Microsoft Office
**Solution:** Fallback to Arial or `load_default()` implemented in the code

## BUILD CONFIGURATION (pyproject.toml)

```toml
[project]
name = "worship-ppt-generator"
version = "1.0.0"
description = "PowerPoint presentation generator for worship song lyrics"
dependencies = [
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "python-pptx>=0.6.21",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "flet>=0.10.0",
    "Pillow>=10.0.0",
    "pynput>=1.7.6",
    "pyperclip>=1.8.2"
]

[tool.flet]
main = "main.py"
product = "Worship PPT Generator"
company = "Worship App"

[tool.flet.windows]
build_number = 1
exclude = ["data", "output", "build", "venv", "__pycache__"]
```

## KEY IMPLEMENTED FEATURES

### Global F8 Hotkey
- `pynput` listener runs on a separate thread (daemon)
- Detects `vk=119` (F8) using virtual key codes
- Simulates `Ctrl+C` via Windows API (`ctypes`)
- Automatically saves/restores clipboard content
- Validates `resursecrestine.ro` URLs
- Injects URL into UI and triggers automatic scraping

### Edit Mode
- "Enable/Disable Editing" toggle
- `TextField` overlay over the image preview
- Auto-save on every change
- Cross-slide synchronization (all slides with the same key)
- Chorus markers `/: :/` editable manually

### PowerPoint Generation
- 16:9 slides (13.333" x 7.5")
- Auto-calculated font (20-72pt) based on text length
- Chorus markers automatically added on the first load
- "Amin" (Amen) positioned at bottom-right on the last slide
- 320x180 JPEG thumbnail embedded in the PPTX

## DISTRIBUTION

### For End Users:
1. Copy the `Worship PPT Generator/` folder to a USB drive/laptop
2. Run: Double-click on `Worship PPT Generator.exe`
3. No Python installation or dependencies required

### Available Launchers:
- `start-direct.vbs` - Runs without CMD window (recommended)
- `start-ui.bat` - CMD visible for 1 second
- `start-ui-debug.bat` - Permanent CMD for debugging

## AUTHOR
Personal project for rapidly generating PowerPoint presentations
with Christian worship song lyrics from resursecrestine.ro

## LICENSE
Personal project - Free to use for personal and church purposes
