# Worship PPT Generator

A modern desktop application built with Python and FLET that generates PowerPoint presentations from web content, designed specifically for **worship services**. Features real-time preview, inline editing, local content search, and global hotkey support.

[![GitHub Repo](https://img.shields.io/badge/GitHub-App1--Worship--PPT-181717?logo=github)](https://github.com/Dorin55-web/App1-Worship-PPT)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FLET](https://img.shields.io/badge/FLET-0.80+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4?logo=windows)

## Features

### Content Acquisition
- **URL Scraping**: Extract structured content from web pages
- **Global Hotkey (F8)**: Capture URLs directly from your browser without switching windows
- **Clipboard Integration**: Automatic URL detection and validation

### Content Processing
- **Smart Parsing**: Automatic detection of sections (verses, choruses, bridges)
- **Text Normalization**: Handles diacritics and special characters
- **Structure Recognition**: Identifies repeating patterns and refrains

### Presentation Generation
- **Auto-scaling Fonts**: Dynamically calculates optimal font size (20-72pt) based on content length
- **16:9 Widescreen**: Standard widescreen format (13.333" x 7.5")
- **Visual Preview**: Real-time slide preview before generation
- **Inline Editing**: Toggle edit mode to modify text directly with auto-save
- **Cross-slide Sync**: Changes to repeated sections update all instances

### Local Search
- **Full-text Search**: Search through your local PowerPoint collection
- **Background Detection**: Automatically categorizes presentations by background type:
  - Dark backgrounds (solid black)
  - Light backgrounds (solid white)
  - Rich content (images, gradients, colors)
- **Smart Sorting**: Results sorted by background type for easier selection
- **Instant Opening**: Click to open presentations directly in PowerPoint

### User Interface
- **Modern Dark Theme**: Built with a sleek dark interface (#0d1117 base)
- **Tabbed Navigation**: Separate tabs for Home and Search
- **Settings**: Configurable output directory and search paths
- **History Tracking**: Recently processed items

## Installation

### Prerequisites
- Windows 10/11
- Python 3.12+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Dorin55-web/App1-Worship-PPT.git
cd App1-Worship-PPT
```

2. Create and activate virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running

#### Development Mode
```bash
python main.py
```

#### Production Build
Build a standalone Windows executable using PyInstaller:

```bash
flet pack main.py \
  --onedir \
  --name "PPT Generator" \
  --add-data "config:config" \
  --add-data "core:core" \
  --add-data "flet_ui:flet_ui" \
  --add-data "services:services" \
  --add-data "interfaces:interfaces" \
  --hidden-import pynput \
  --hidden-import pyperclip \
  --distpath "dist"
```

**Note**: After building, manually copy `pynput` and `pyperclip` from `venv/Lib/site-packages/` to `dist/PPT Generator/_internal/`.

## Usage

### Basic Workflow

1. **Enter URL**: Paste a content URL in the input field or press F8 to capture from browser
2. **Fetch**: Click "Run" to scrape and process the content
3. **Preview**: Review slides in the preview panel with navigation controls
4. **Edit** (Optional): Enable editing mode to modify text inline
5. **Generate**: Click "Generate" to create the PowerPoint file

### Local Search

1. Configure your local presentations directory in Settings
2. Switch to the Search tab
3. Enter keywords to find existing presentations
4. Results are sorted by background type (dark → light → rich content)
5. Click any result to open it directly

### Global Hotkey

- Press **F8** while a URL is selected in your browser
- The application will automatically capture the URL and start processing

### Settings

- **Output Directory**: Where generated presentations are saved
- **Search Directory**: Path to your existing presentation collection
- **Auto-open**: Automatically open presentations after generation

## Project Structure

```
.
├── config/              # Configuration management
│   ├── settings.py      # Config loader/saver
│   └── config.json      # User settings
├── core/                # Core business logic
│   ├── scraper.py       # Web scraping engine
│   ├── parser.py        # Content parser
│   ├── ppt_generator.py # PowerPoint generation
│   ├── font_calculator.py # Dynamic font sizing
│   ├── models.py        # Data models
│   └── history_manager.py # Usage history
├── flet_ui/             # User interface
│   └── app.py           # Main FLET application
├── services/            # External services
│   ├── song_service.py  # Content API
│   ├── search_service.py # Local search engine
│   └── hotkey_manager.py # Global hotkey handler
├── interfaces/          # Package interfaces
├── data/                # Application data
├── output/              # Generated presentations
├── start/               # Launcher scripts
├── main.py              # Entry point
├── pyproject.toml       # Project configuration
└── requirements.txt     # Python dependencies
```

## Tech Stack

- **Python 3.12**: Core language
- **FLET**: Cross-platform UI framework (Flutter-based)
- **python-pptx**: PowerPoint file generation
- **BeautifulSoup4**: HTML parsing
- **Requests**: HTTP client
- **Pillow**: Image processing for previews
- **pynput**: Global hotkey listener
- **PyInstaller**: Executable bundling

## Configuration

The application stores user preferences in `config/config.json`:

```json
{
  "app": {
    "default_output_dir": "./output",
    "search_directory": "",
    "auto_open_ppt": true
  },
  "verses": {
    "font_family": "Calibri",
    "font_min_size": 24,
    "font_max_size": 44,
    "color": "#FFFFFF",
    "bg_color": "#000000"
  }
}
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| F8 | Capture URL from browser |
| Enter | Submit URL / Search |
| ← → | Navigate slides |

## Search Engine

The local search uses an inverted index for fast full-text search:
- **Indexing**: Scans presentations and builds a word index
- **Search**: Supports multi-word queries with relevance scoring
- **Background Detection**: Analyzes .pptx files for solid colors and .ppt files for image signatures
- **Performance**: Sub-100ms search times for collections of 6000+ files

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- Built with [FLET](https://flet.dev/) - a Flutter-based Python UI framework
- Uses [python-pptx](https://python-pptx.readthedocs.io/) for PowerPoint generation
- Inspired by the needs of worship teams managing song lyrics for Sunday services
