# ImageScraper Mac

A powerful macOS image scraping tool that supports keyword search (via Bing) and image extraction from arbitrary web URLs.

## Features

- **Keyword Search**: Search and download images using Bing.
- **URL Extraction**: Extract images from any webpage.
- **Thumbnail Preview**: Visually select images to download.
- **Batch Download**: Download selected or all images.
- **Search History**: Quickly repeat previous searches (keeps last 5).
- **Responsive UI**: Dynamic thumbnail grid that adapts to window size.
- **Horizontal Scrolling**: Hold Shift + Scroll to scroll horizontally.

## Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:luuuke2233/ImageScraper_Mac.git
   cd ImageScraper_Mac
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

## Usage

**Option 1: Using the run script**
```bash
bash run.sh
```

**Option 2: Using Python directly**
```bash
python3 main.py
```

## Project Structure

```
├── main.py            # Main GUI application
├── scraper_bing.py    # Bing image search implementation
├── scraper_base.py    # Base scraper class
├── downloader.py      # Image downloader
├── run.sh             # One-click run script
└── requirements.txt   # Python dependencies
```

## Requirements

- Python 3.8+
- requests
- beautifulsoup4
- Pillow

## License

MIT
