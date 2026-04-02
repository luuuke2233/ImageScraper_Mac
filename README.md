# ImageScraper Mac

[English](#english) | [中文](#中文)

---

<a id="english"></a>
## English

A powerful macOS image scraping tool that supports keyword search (via Bing) and image extraction from arbitrary web URLs.

### Features

- **Keyword Search**: Search and download images using Bing.
- **URL Extraction**: Extract images from any webpage.
- **Thumbnail Preview**: Visually select images to download.
- **Batch Download**: Download selected or all images.
- **Search History**: Quickly repeat previous searches (keeps last 5).
- **Responsive UI**: Dynamic thumbnail grid that adapts to window size.
- **Horizontal Scrolling**: Hold Shift + Scroll to scroll horizontally.
- **Multi-language**: Supports English and Chinese (switch in Settings).

### Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:luuuke2233/ImageScraper_Mac.git
   cd ImageScraper_Mac
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

### Usage

**Option 1: Using the run script**
```bash
bash run.sh
```

**Option 2: Using Python directly**
```bash
python3 main.py
```

### Project Structure

```
├── main.py            # Main GUI application
├── scraper_bing.py    # Bing image search implementation
├── scraper_base.py    # Base scraper class
├── downloader.py      # Image downloader
├── run.sh             # One-click run script
└── requirements.txt   # Python dependencies
```

### Requirements

- Python 3.8+
- requests
- beautifulsoup4
- Pillow

### License

MIT

---

<a id="中文"></a>
## 中文

适用于 macOS 的图片爬虫工具，支持关键词搜索（Bing）和网页图片提取。

### 功能

- **关键词搜索**：通过 Bing 搜索并下载图片
- **网址提取**：从任意网页提取图片
- **缩略图预览**：可视化选择要下载的图片
- **批量下载**：支持选中/全部下载
- **搜索历史**：快速重复之前的搜索（保留5个搜索历史）
- **响应式界面**：缩略图网格根据窗口大小动态调整
- **水平滚动**：按住 Shift + 滚轮可左右滚动
- **中英文切换**：在设置中可切换中英文界面

### 安装

1. 克隆仓库：
   ```bash
   git clone git@github.com:luuuke2233/ImageScraper_Mac.git
   cd ImageScraper_Mac
   ```

2. 安装依赖：
   ```bash
   pip3 install -r requirements.txt
   ```

### 运行

**方式一**：终端运行
```bash
bash run.sh
```

**方式二**：Python 直接运行
```bash
python3 main.py
```

### 项目结构

```
├── main.py            # 主程序 GUI
├── scraper_bing.py    # Bing 图片搜索
├── scraper_base.py    # 爬虫基类
├── downloader.py      # 图片下载器
├── run.sh             # 一键运行脚本
└── requirements.txt   # 依赖列表
```

### 依赖

- Python 3.8+
- requests
- beautifulsoup4
- Pillow

### 许可证

MIT
