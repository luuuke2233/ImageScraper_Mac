# ImageScraper Mac

适用于M芯片系列的macbook 图片爬虫工具，支持关键词搜索（Bing）和网页图片提取。

## 功能

- **关键词搜索**：通过 Bing 搜索并下载图片
- **网址提取**：从任意网页提取图片
- **缩略图预览**：可视化选择要下载的图片
- **批量下载**：支持选中/全部下载
- **搜索历史**：快速重复之前的搜索（保留5个搜索历史）

## 安装

```bash
git clone git@github.com:luuuke2233/ImageScraper_Mac.git
cd ImageScraper_Mac
pip3 install requests beautifulsoup4 Pillow
```

## 运行

**方式一**：终端运行 `run.sh`

**方式二**：终端执行
```bash
python3 main.py
```

## 项目结构

```
├── main.py            # 主程序 GUI
├── scraper_bing.py    # Bing 图片搜索
├── scraper_base.py    # 爬虫基类
├── downloader.py      # 图片下载器
├── run.sh             # 一键运行脚本
└── requirements.txt   # 依赖列表
```

## 依赖

- Python 3.8+
- requests
- beautifulsoup4
- Pillow

## License

MIT
