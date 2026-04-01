# Worship PPT Generator

## General Description

**Worship PPT Generator** is a modern desktop application for Windows that transforms Christian worship song lyrics from the internet into professional PowerPoint presentations, ready to be used in churches or worship groups.

## 🎯 Application Goal

The application automatically extracts song lyrics from the website **resursecrestine.ro** and converts them into professionally formatted PowerPoint (.pptx) files, featuring:
- Centered and optimally sized text
- Black background (ideal for projection)
- Fonts adapted for readability
- Logically organized slides (verses, choruses)

## ✨ Main Features

### 1. **Automatic Extraction**
- Fetches songs from resursecrestine.ro using the URL
- Automatically parses the structure: verses, choruses, bridges, codas
- Detects and handles multiple choruses (C1, C2, etc.)

### 2. **Real-Time Preview**
- Preview of all slides before generation
- Navigate with Previous/Next between slides
- Full list of slides in the left panel
- Preview image generated identically to the final PowerPoint

### 3. **Flexible Editing**
- Edit text directly in the application
- Font size adjustment (±2pt)
- Automatic detection of the optimal font for each slide
- Smart processing for choruses (/: :/ markers)

### 4. **PowerPoint Generation**
- Create professional .pptx files
- 16:9 format (widescreen)
- Calibri font, white text on black background
- Automatic "Amin" (Amen) on the last slide
- Thumbnail preview in Windows Explorer

### 5. **Song Management**
- History of generated songs (saved locally)
- Auto-open after generation (optional)
- Save in a configurable folder
- Smart filename generation (no diacritics, max 4 words)

### 6. **Customizable Settings**
- Custom location for saving files
- "Auto Open" toggle - automatically opens PowerPoint after generation
- Persistent configurations between sessions

## 🖥️ User Interface

### Modern Design (Dark Theme)
- **Sidebar** (80px): Quick navigation (Home, Settings)
- **Slide List** (250px): All slides visible and clickable
- **Main Area**:
  - URL Input + Run button
  - Image preview (640x360px)
  - Previous/Next navigation with counter
  - Font control (+/-)
  - Edit Text button
  - Status bar with information

### Color Theme
- Background: `#0d1117` (GitHub dark)
- Cards: `#161b22`
- Cyan accent: `#00d4ff`
- Purple accent: `#7c3aed`
- White and gray text for optimal contrast

## 🔄 Typical Workflow

```
1. Open Application
   └─► Modern interface loads instantly

2. Enter URL
   └─► User pastes the song URL

3. Click "Run"
   └─► App extracts and parses the song (2-3 seconds)
   └─► Displays preview of the first slide
   └─► Lists all slides in the left panel

4. Navigate and Edit (optional)
   └─► Previous/Next to view all slides
   └─► Adjust font if necessary
   └─► Edit text directly if needed

5. Generate PowerPoint
   └─► Click "Generate" button
   └─► .pptx file is created in the output folder
   └─► Auto-opens in PowerPoint (if enabled)

6. Use in Projection
   └─► PowerPoint ready to present in church
```

## 🛠️ Used Technologies

### Technical Stack
- **Python 3.12** - Programming language
- **Flet 0.80.5** - Modern UI framework (Flutter-based)
- **python-pptx** - PowerPoint file generation
- **BeautifulSoup4** - Web scraping and HTML parsing
- **Pillow** - Preview image and thumbnail generation
- **Flutter** - Native Windows build

### Modular Architecture
```
App1/
├── core/          # Application engine (scraper, parser, generator)
├── flet_ui/       # Modern graphical interface
├── services/      # Business logic
├── config/        # Configurations and settings
├── data/          # Local history and data
└── output/        # Generated PowerPoint files
```

## 📦 Distribution and Installation

### For End Users
- **Windows Executable** (.exe) - 71 MB
- **No installation required** - runs directly
- **No Python required** or other dependencies
- **Portable** - can run from a USB drive or any location

### For Developers
```bash
# Clone repository
git clone <repo-url>
cd App1

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py

# Or build executable
python build_windows.py
```

## 🎨 Advanced Technical Features

### 1. **Smart Text Processing**
- Automatic detection of verses vs choruses
- Handling multiple choruses (C1, C2 at the end)
- Automatic chorus markers (/::/)
- Diacritics removal from filenames

### 2. **Font Optimization**
- Automatic calculation of optimal font size
- Smart scaling based on text length
- Limit 20-72pt for readability
- Optimal line spacing

### 3. **Thumbnail Generation**
- Automatic thumbnail creation for Windows Explorer
- Size 320x180px (16:9 aspect ratio)
- Consistent scalable font
- Black background with white text

### 4. **Error Handling**
- Catch and display errors in the interface
- URL validation before processing
- Fallbacks for missing fonts
- Detailed logging for debugging

## 📋 System Requirements

### Minimum
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB
- **Disk**: 100 MB free space
- **Internet**: Connection for downloading songs

### Recommended
- **OS**: Windows 11
- **RAM**: 8 GB
- **Disk**: 500 MB (for generated files)
- **Microsoft PowerPoint**: For viewing (optional)

## 🎯 Target Audience

- **Worship leaders** in churches
- **Audio-visual technicians** responsible for projection
- **Youth groups** using projected songs
- **Anyone** who wants to create professional presentations quickly

## 🚀 Competitive Advantages

✅ **Fast**: Generates PowerPoint in 5-10 seconds  
✅ **Easy**: Intuitive interface, no training required  
✅ **Professional**: Quality results, ready to present  
✅ **Free**: Open source, no costs  
✅ **Modern**: Contemporary UI, dark theme  
✅ **Portable**: No complex installation required  

## 📝 Use Case Examples

### Scenario 1: Sunday Morning
> "I need the song 'Great Are You Lord' for the service. I copy the URL from the site, paste it in the app, click Run, check the slides, click Generate. Done in 10 seconds!"

### Scenario 2: Conference Preparation
> "I need to prepare 20 songs for the conference. I use the app for each one, save them in the conference folder, then load them onto the presentation laptop."

### Scenario 3: Urgent Modification
> "I noticed a mistake in a verse. I open the app, load the song, edit the text directly in the interface, regenerate. Fixed in 30 seconds!"

## 🏆 Conclusion

**Worship PPT Generator** is a complete, modern, and efficient solution for creating PowerPoint presentations with Christian worship song lyrics. It combines the power of Python with a modern Flet interface to deliver a superior user experience, saving valuable time when preparing worship materials.

---

**Version**: 1.0.0  
**Platform**: Windows 10/11  
**Technologies**: Python, Flet, Flutter  
**License**: Open Source
