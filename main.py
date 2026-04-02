import os
import json
import re
import tkinter as tk
import webbrowser
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import requests
from io import BytesIO
from PIL import Image, ImageTk
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

from scraper_bing import BingScraper
from downloader import ImageDownloader

CONFIG_FILE = "config.json"

LANG = {
    'en': {
        'app_title': 'Image Scraper',
        'tab_search': 'Keyword Search',
        'tab_url': 'URL Extract',
        'tab_settings': 'Settings',
        'save_dir': 'Save Directory',
        'default_dir': 'Default directory:',
        'browse': 'Browse...',
        'save': 'Save',
        'window_settings': 'Window Settings',
        'save_window': 'Save Window Size',
        'reset_window': 'Reset Window Size',
        'cache': 'Cache',
        'clear_cache': 'Clear Cache',
        'log': 'Log',
        'language': 'Language',
        'search_settings': 'Search Settings',
        'keyword': 'Keyword:',
        'clear': 'Clear',
        'history': 'History',
        'download_count': 'Count:',
        'search': 'Search',
        'download_selected': 'Download Selected',
        'download_all': 'Download All',
        'go_source': 'Go to Source',
        'deselect_all': 'Deselect All',
        'stop': 'Stop',
        'ready': 'Ready',
        'selected': 'Selected: 0',
        'search_results': 'Search Results',
        'loading': 'Loading...',
        'url_settings': 'URL Settings',
        'web_url': 'Web URL:',
        'filter_format': 'Filter:',
        'comma_sep': '(comma separated)',
        'extract': 'Extract Images',
        'web_images': 'Web Images',
        'search_history': 'Search History',
        'no_history': 'No search history',
        'clear_all': 'Clear All',
        'close': 'Close',
        'confirm': 'Confirm',
        'confirm_clear_history': 'Clear all search history?',
        'warning': 'Warning',
        'enter_keyword': 'Please enter a keyword',
        'enter_url': 'Please enter a URL',
        'select_image': 'Please select at least one image',
        'no_images': 'No images to download',
        'select_download': 'Please select images to download',
        'success': 'Success',
        'saved_dir': 'Saved directory:',
        'saved_window': 'Saved window size:',
        'reset_done': 'Reset to initial size: 900x650',
        'cleared_cache': 'Cache cleared',
        'cleared_search': 'Search cleared',
        'searching': 'Searching...',
        'search_done': 'Found {0} images',
        'search_error': 'Search error: {0}',
        'downloading': 'Downloading {0}/{1}...',
        'download_done': 'Done: {0} success, {1} failed',
        'download_complete': 'Download complete!\nSuccess: {0}\nFailed: {1}\n\nSave dir: {2}',
        'download_stopped': 'Download stopped',
        'extracting': 'Extracting images...',
        'extract_done': 'Found {0} images',
        'extract_error': 'Extract error: {0}',
        'opened_browser': 'Opened in browser: {0}...',
        'open_browser_failed': 'Failed to open browser: {0}',
        'no_source_url': 'No source URL, opened image URL: {0}...',
        'no_url': 'Unable to get source URL',
        'from': 'From',
    },
    'zh': {
        'app_title': '图片爬虫工具',
        'tab_search': '关键词搜索',
        'tab_url': '网址提取',
        'tab_settings': '设置',
        'save_dir': '保存目录',
        'default_dir': '默认保存目录:',
        'browse': '浏览...',
        'save': '保存',
        'window_settings': '窗口设置',
        'save_window': '保存当前窗口大小',
        'reset_window': '恢复初始窗口大小',
        'cache': '缓存管理',
        'clear_cache': '清空缓存',
        'log': '日志',
        'language': '语言',
        'search_settings': '搜索设置',
        'keyword': '关键词:',
        'clear': '清空',
        'history': '历史',
        'download_count': '下载数量:',
        'search': '搜索图片',
        'download_selected': '下载选中',
        'download_all': '下载全部',
        'go_source': '前往来源',
        'deselect_all': '取消选中',
        'stop': '停止',
        'ready': '就绪',
        'selected': '已选: 0 张',
        'search_results': '搜索结果',
        'loading': '加载中...',
        'url_settings': '网址设置',
        'web_url': '网页 URL:',
        'filter_format': '过滤格式:',
        'comma_sep': '(逗号分隔)',
        'extract': '提取图片',
        'web_images': '网页图片',
        'search_history': '搜索历史',
        'no_history': '暂无搜索历史',
        'clear_all': '清空全部',
        'close': '关闭',
        'confirm': '确认',
        'confirm_clear_history': '确定要清空所有搜索历史吗？',
        'warning': '警告',
        'enter_keyword': '请输入搜索关键词',
        'enter_url': '请输入网页 URL',
        'select_image': '请先选中至少一张图片',
        'no_images': '没有可下载的图片',
        'select_download': '请先选中要下载的图片',
        'success': '成功',
        'saved_dir': '已保存默认目录:',
        'saved_window': '已保存当前窗口大小:',
        'reset_done': '已恢复初始窗口大小: 900x650',
        'cleared_cache': '已清空缓存',
        'cleared_search': '已清空搜索',
        'searching': '正在搜索...',
        'search_done': '搜索完成，找到 {0} 张图片',
        'search_error': '搜索错误: {0}',
        'downloading': '正在下载 {0}/{1}...',
        'download_done': '下载完成: 成功 {0} 张，失败 {1} 张',
        'download_complete': '下载完成!\n成功: {0} 张\n失败: {1} 张\n\n保存目录: {2}',
        'download_stopped': '下载已停止',
        'extracting': '正在提取图片...',
        'extract_done': '提取完成，找到 {0} 张图片',
        'extract_error': '提取错误: {0}',
        'opened_browser': '已在浏览器中打开: {0}...',
        'open_browser_failed': '打开浏览器失败: {0}',
        'no_source_url': '无来源链接，已打开图片 URL: {0}...',
        'no_url': '无法获取来源链接或图片 URL',
        'from': '正在从',
    }
}


class ImageScraperGUI:
    """图片爬虫 GUI 界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.resizable(True, True)
        
        self.scraper = None
        self.downloader = None
        self.images = []
        self.is_running = False
        self.thumbnails = []
        self.thumb_widgets = []
        self._preview_loaded = False
        self._resize_timer = None
        self._cols = 3
        self._selected_count = 0
        self._last_selected_index = -1
        
        self.config = self._load_config()
        self.search_history = self.config.get('search_history', [])
        self.lang = self.config.get('language', 'en')
        
        self.root.title(self.t('app_title'))
        
        self.tooltip = None
        self._thumb_pool = ThreadPoolExecutor(max_workers=4)
        self._pending_thumbs = set()
        
        self._setup_ui()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        saved_geom = self.config.get('window_geometry', None)
        if saved_geom:
            self.root.geometry(saved_geom)
        else:
            self.root.geometry("900x650")
    
    def t(self, key):
        return LANG.get(self.lang, LANG['en']).get(key, key)
    
    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'default_output_dir': 'downloaded_images'}
    
    def _save_config(self):
        self.config['search_history'] = self.search_history
        self.config['default_output_dir'] = self.output_var.get()
        self.config['language'] = self.lang
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def _switch_language(self, lang):
        self.lang = lang
        self._save_config()
        messagebox.showinfo(self.t('success'), 'Language changed. Please restart the app.' if lang == 'en' else '语言已更改，请重启应用。')
    
    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        search_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(search_tab, text=self.t('tab_search'))
        self._setup_search_tab(search_tab)
        
        url_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(url_tab, text=self.t('tab_url'))
        self._setup_url_tab(url_tab)
        
        settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_tab, text=self.t('tab_settings'))
        self._setup_settings_tab(settings_tab)
    
    def _setup_settings_tab(self, parent):
        # 保存目录
        dir_frame = ttk.LabelFrame(parent, text=self.t('save_dir'), padding="10")
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dir_frame, text=self.t('default_dir')).pack(anchor=tk.W, pady=(0, 5))
        dir_entry_frame = ttk.Frame(dir_frame)
        dir_entry_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.output_var = tk.StringVar(value=self.config.get('default_output_dir', 'downloaded_images'))
        ttk.Entry(dir_entry_frame, textvariable=self.output_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(dir_entry_frame, text=self.t('browse'), command=self._browse_output).pack(side=tk.LEFT)
        ttk.Button(dir_entry_frame, text=self.t('save'), command=self._save_default_dir).pack(side=tk.LEFT, padx=(5, 0))
        
        # 语言设置
        lang_frame = ttk.LabelFrame(parent, text=self.t('language'), padding="10")
        lang_frame.pack(fill=tk.X, pady=(0, 10))
        
        lang_btn_frame = ttk.Frame(lang_frame)
        lang_btn_frame.pack(anchor=tk.W)
        ttk.Button(lang_btn_frame, text="English", command=lambda: self._switch_language('en')).pack(side=tk.LEFT, padx=2)
        ttk.Button(lang_btn_frame, text="中文", command=lambda: self._switch_language('zh')).pack(side=tk.LEFT, padx=2)
        
        # 窗口设置
        win_frame = ttk.LabelFrame(parent, text=self.t('window_settings'), padding="10")
        win_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(win_frame, text=self.t('save_window'), command=self._save_window_size).pack(anchor=tk.W, pady=2)
        ttk.Button(win_frame, text=self.t('reset_window'), command=self._reset_window_size).pack(anchor=tk.W, pady=2)
        
        # 缓存管理
        cache_frame = ttk.LabelFrame(parent, text=self.t('cache'), padding="10")
        cache_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(cache_frame, text=self.t('clear_cache'), command=self._clear_cache).pack(anchor=tk.W, pady=2)
        
        # 日志
        log_frame = ttk.LabelFrame(parent, text=self.t('log'), padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def _setup_search_tab(self, parent):
        # 状态栏 - 必须最先初始化
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.status_var = tk.StringVar(value=self.t('ready'))
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        self.selected_count_var = tk.StringVar(value=self.t('selected'))
        ttk.Label(status_frame, textvariable=self.selected_count_var).pack(side=tk.RIGHT)
        
        search_frame = ttk.LabelFrame(parent, text=self.t('search_settings'), padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text=self.t('keyword')).grid(row=0, column=0, sticky=tk.W, pady=5)
        keyword_entry_frame = ttk.Frame(search_frame)
        keyword_entry_frame.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)
        self.keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(keyword_entry_frame, textvariable=self.keyword_var, width=35)
        keyword_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        keyword_entry.bind('<Return>', lambda e: self.search())
        ttk.Button(keyword_entry_frame, text=self.t('clear'), command=self._clear_search, width=6).pack(side=tk.LEFT, padx=(5, 0))
        
        history_frame = ttk.Frame(search_frame)
        history_frame.grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(history_frame, text=self.t('history'), command=self._show_history, width=6).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(search_frame, text=self.t('download_count')).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.limit_var = tk.IntVar(value=20)
        limit_frame = ttk.Frame(search_frame)
        limit_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        limit_spinbox = ttk.Spinbox(limit_frame, from_=1, to=100, textvariable=self.limit_var, width=10)
        limit_spinbox.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(limit_frame, text="▲", command=lambda: self.limit_var.set(min(100, self.limit_var.get() + 1)), width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(limit_frame, text="▼", command=lambda: self.limit_var.set(max(1, self.limit_var.get() - 1)), width=3).pack(side=tk.LEFT, padx=1)
        
        search_frame.columnconfigure(1, weight=1)
        
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.search_btn = ttk.Button(button_frame, text=self.t('search'), command=self.search)
        self.search_btn.pack(side=tk.LEFT, padx=5, ipadx=30, ipady=10)
        
        self.download_btn = ttk.Button(button_frame, text=self.t('download_selected'), command=self.download_selected, state=tk.DISABLED)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_all_btn = ttk.Button(button_frame, text=self.t('download_all'), command=self.download_all, state=tk.DISABLED)
        self.download_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_source_btn = ttk.Button(button_frame, text=self.t('go_source'), command=self._open_selected_source, state=tk.DISABLED)
        self.open_source_btn.pack(side=tk.LEFT, padx=5)
        
        self.deselect_all_btn = ttk.Button(button_frame, text=self.t('deselect_all'), command=self._deselect_all)
        self.deselect_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text=self.t('stop'), command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=5)
        
        # 状态栏
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_var = tk.StringVar(value=self.t('ready'))
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        self.selected_count_var = tk.StringVar(value=self.t('selected'))
        ttk.Label(status_frame, textvariable=self.selected_count_var).pack(side=tk.RIGHT)
        
        self._setup_preview_area(parent)
    
    def _setup_url_tab(self, parent):
        url_frame = ttk.LabelFrame(parent, text=self.t('url_settings'), padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text=self.t('web_url')).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)
        url_entry.bind('<Return>', lambda e: self.extract_from_url())
        
        ttk.Label(url_frame, text=self.t('filter_format')).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.filter_var = tk.StringVar(value="jpg,jpeg,png,gif,webp")
        filter_entry = ttk.Entry(url_frame, textvariable=self.filter_var, width=40)
        filter_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(url_frame, text=self.t('comma_sep')).grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        url_frame.columnconfigure(1, weight=1)
        
        url_button_frame = ttk.Frame(parent)
        url_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.url_extract_btn = ttk.Button(url_button_frame, text=self.t('extract'), command=self.extract_from_url)
        self.url_extract_btn.pack(side=tk.LEFT, padx=5, ipadx=30, ipady=10)
        
        self.url_download_btn = ttk.Button(url_button_frame, text=self.t('download_selected'), command=self.url_download_selected, state=tk.DISABLED)
        self.url_download_btn.pack(side=tk.LEFT, padx=5)
        
        self.url_download_all_btn = ttk.Button(url_button_frame, text=self.t('download_all'), command=self.url_download_all, state=tk.DISABLED)
        self.url_download_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.url_stop_btn = ttk.Button(url_button_frame, text=self.t('stop'), command=self.stop, state=tk.DISABLED)
        self.url_stop_btn.pack(side=tk.RIGHT, padx=5)
        
        self._setup_url_preview_area(parent)
    
    def _setup_preview_area(self, parent):
        preview_frame = ttk.LabelFrame(parent, text=self.t('search_results'), padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.preview_canvas = tk.Canvas(preview_frame, bg='#f0f0f0', highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        scrollbar_x = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_canvas.xview)
        
        self.preview_inner = ttk.Frame(self.preview_canvas)
        
        self.preview_inner.bind(
            "<Configure>",
            lambda e: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
        )
        
        self.preview_canvas.create_window((0, 0), window=self.preview_inner, anchor=tk.NW)
        self.preview_canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.preview_canvas.bind("<MouseWheel>", self._on_preview_mousewheel)
        self.preview_canvas.bind("<Button-4>", self._on_preview_mousewheel)
        self.preview_canvas.bind("<Button-5>", self._on_preview_mousewheel)
        self.preview_canvas.bind("<Shift-MouseWheel>", self._on_preview_mousewheel)
        self.preview_inner.bind("<MouseWheel>", self._on_preview_mousewheel)
        self.preview_inner.bind("<Button-4>", self._on_preview_mousewheel)
        self.preview_inner.bind("<Button-5>", self._on_preview_mousewheel)
        self.preview_inner.bind("<Shift-MouseWheel>", self._on_preview_mousewheel)
        self.preview_canvas.bind("<Configure>", self._on_resize)
    
    def _setup_url_preview_area(self, parent):
        url_preview_frame = ttk.LabelFrame(parent, text=self.t('web_images'), padding="5")
        url_preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.url_preview_canvas = tk.Canvas(url_preview_frame, bg='#f0f0f0', highlightthickness=0)
        url_scrollbar_y = ttk.Scrollbar(url_preview_frame, orient=tk.VERTICAL, command=self.url_preview_canvas.yview)
        url_scrollbar_x = ttk.Scrollbar(url_preview_frame, orient=tk.HORIZONTAL, command=self.url_preview_canvas.xview)
        
        self.url_preview_inner = ttk.Frame(self.url_preview_canvas)
        
        self.url_preview_inner.bind(
            "<Configure>",
            lambda e: self.url_preview_canvas.configure(scrollregion=self.url_preview_canvas.bbox("all"))
        )
        
        self.url_preview_canvas.create_window((0, 0), window=self.url_preview_inner, anchor=tk.NW)
        self.url_preview_canvas.configure(yscrollcommand=url_scrollbar_y.set, xscrollcommand=url_scrollbar_x.set)
        
        url_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        url_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.url_preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.url_preview_canvas.bind("<MouseWheel>", self._on_url_mousewheel)
        self.url_preview_canvas.bind("<Button-4>", self._on_url_mousewheel)
        self.url_preview_canvas.bind("<Button-5>", self._on_url_mousewheel)
        self.url_preview_canvas.bind("<Shift-MouseWheel>", self._on_url_mousewheel)
        self.url_preview_inner.bind("<MouseWheel>", self._on_url_mousewheel)
        self.url_preview_inner.bind("<Button-4>", self._on_url_mousewheel)
        self.url_preview_inner.bind("<Button-5>", self._on_url_mousewheel)
        self.url_preview_inner.bind("<Shift-MouseWheel>", self._on_url_mousewheel)
        self.url_preview_canvas.bind("<Configure>", self._on_url_resize)
        
        self.url_thumbnails = []
        self.url_thumb_widgets = []
        self.url_images = []
        self._url_preview_loaded = False
        self._url_resize_timer = None
        self._url_cols = 3
    
    def _on_preview_mousewheel(self, event):
        if event.state & 0x1:  # Shift键按下时水平滚动
            if event.delta > 0:
                self.preview_canvas.xview_scroll(-1, "units")
            elif event.delta < 0:
                self.preview_canvas.xview_scroll(1, "units")
        else:
            if event.delta > 0:
                self.preview_canvas.yview_scroll(-1, "units")
            elif event.delta < 0:
                self.preview_canvas.yview_scroll(1, "units")
        return "break"
    
    def _on_url_mousewheel(self, event):
        if event.state & 0x1:  # Shift键按下时水平滚动
            if event.delta > 0:
                self.url_preview_canvas.xview_scroll(-1, "units")
            elif event.delta < 0:
                self.url_preview_canvas.xview_scroll(1, "units")
        else:
            if event.delta > 0:
                self.url_preview_canvas.yview_scroll(-1, "units")
            elif event.delta < 0:
                self.url_preview_canvas.yview_scroll(1, "units")
        return "break"
    
    def _on_resize(self, event):
        if not self.images or not self._preview_loaded:
            return
        if self._resize_timer:
            self.root.after_cancel(self._resize_timer)
        self._resize_timer = self.root.after(300, self._reflow_preview)
    
    def _on_url_resize(self, event):
        if not self.url_images or not self._url_preview_loaded:
            return
        if self._url_resize_timer:
            self.root.after_cancel(self._url_resize_timer)
        self._url_resize_timer = self.root.after(150, self._reflow_url_preview)
    
    def _reflow_preview(self):
        thumb_size = 140
        canvas_width = self.preview_canvas.winfo_width()
        if canvas_width <= 1:
            return
        new_cols = max(1, canvas_width // (thumb_size + 20))
        
        if new_cols == self._cols:
            return
        
        self._cols = new_cols
        for i, widget in enumerate(self.thumb_widgets):
            row = i // new_cols
            col = i % new_cols
            widget.grid(row=row, column=col, padx=8, pady=8)
    
    def _reflow_url_preview(self):
        thumb_size = 140
        canvas_width = self.url_preview_canvas.winfo_width()
        if canvas_width <= 1:
            return
        new_cols = max(1, canvas_width // (thumb_size + 20))
        
        if new_cols == self._url_cols:
            return
        
        self._url_cols = new_cols
        for i, widget in enumerate(self.url_thumb_widgets):
            row = i // new_cols
            col = i % new_cols
            widget.grid(row=row, column=col, padx=8, pady=8)
            self.url_preview_inner.rowconfigure(r, weight=1)
    
    def _log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _browse_output(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_var.set(directory)
    
    def _save_default_dir(self):
        current_dir = self.output_var.get()
        if current_dir:
            self.config['default_output_dir'] = current_dir
            self._save_config()
            self._log(f"{self.t('saved_dir')} {current_dir}")
            messagebox.showinfo(self.t('success'), f"{self.t('saved_dir')}\n{current_dir}")
    
    def _save_window_size(self):
        geom = self.root.geometry()
        self.config['window_geometry'] = geom
        self._save_config()
        self._log(f"{self.t('saved_window')} {geom}")
        messagebox.showinfo(self.t('success'), f"{self.t('saved_window')}\n{geom}")
    
    def _reset_window_size(self):
        self.root.geometry("900x650")
        self.config.pop('window_geometry', None)
        self._save_config()
        self._log(self.t('reset_done'))
    
    def _get_scraper(self):
        return BingScraper()
    
    def _clear_search(self):
        self.images = []
        self.keyword_var.set("")
        self._clear_preview()
        self.download_btn.config(state=tk.DISABLED)
        self.download_all_btn.config(state=tk.DISABLED)
        self.status_var.set(self.t('ready'))
        self._log(self.t('cleared_search'))
    
    def _add_to_history(self, keyword):
        keyword = keyword.strip()
        if not keyword:
            return
        if keyword in self.search_history:
            self.search_history.remove(keyword)
        self.search_history.insert(0, keyword)
        if len(self.search_history) > 5:
            self.search_history = self.search_history[:5]
        self._save_config()
    
    def _show_history(self):
        if not self.search_history:
            messagebox.showinfo(self.t('search_history'), self.t('no_history'))
            return
        
        win = tk.Toplevel(self.root)
        win.title(self.t('search_history'))
        win.geometry("450x500")
        win.transient(self.root)
        win.grab_set()
        
        ttk.Label(win, text=self.t('search_history'), font=('Arial', 12, 'bold')).pack(pady=10)
        
        scroll_frame = ttk.Frame(win)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(scroll_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL, command=canvas.yview)
        inner = ttk.Frame(canvas)
        
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        def use_history(keyword):
            win.grab_release()
            win.destroy()
            self.root.after(100, lambda: self._do_search_from_history(keyword))
        
        def delete_item(keyword, btn):
            if keyword in self.search_history:
                self.search_history.remove(keyword)
                self._save_config()
            btn.destroy()
            if not self.search_history:
                win.destroy()
        
        for item in self.search_history:
            row = ttk.Frame(inner)
            row.pack(fill=tk.X, padx=5, pady=3)
            
            btn = ttk.Button(row, text=item, command=lambda k=item: use_history(k), width=35)
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            del_btn = ttk.Button(row, text="✕", width=3,
                                command=lambda k=item, b=btn: delete_item(k, b))
            del_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def clear_all():
            if messagebox.askyesno(self.t('confirm'), self.t('confirm_clear_history')):
                self.search_history.clear()
                self._save_config()
                win.destroy()
        
        ttk.Button(btn_frame, text=self.t('clear_all'), command=clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=self.t('close'), command=win.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _do_search_from_history(self, keyword):
        self.keyword_var.set(keyword)
        self.search()
    
    # ========== 搜索功能 ==========
    
    def search(self):
        keyword = self.keyword_var.get().strip()
        if not keyword:
            messagebox.showwarning(self.t('warning'), self.t('enter_keyword'))
            return
        
        self.is_running = True
        self.stop_btn.config(state=tk.NORMAL)
        self.search_btn.config(state=tk.DISABLED)
        self.status_var.set(self.t('searching'))
        
        self.images = []
        self._clear_preview()
        
        thread = threading.Thread(target=self._search_thread, args=(keyword,), daemon=True)
        thread.start()
    
    def _clear_preview(self):
        for widget in self.thumb_widgets:
            widget.destroy()
        self.thumb_widgets = []
        self.thumbnails = []
        self._pending_thumbs.clear()
        self.selected_count_var.set(self.t('selected'))
    
    def _search_thread(self, keyword):
        self._add_to_history(keyword)
        try:
            self.scraper = self._get_scraper()
            if not self.scraper:
                self.root.after(0, lambda: self._log("Error: Cannot create scraper" if self.lang == 'en' else "错误: 无法创建爬虫"))
                return
            
            self.root.after(0, lambda: self._log(f"{self.t('from')} {self.scraper.get_name()}: {keyword}"))
            
            limit = self.limit_var.get()
            self.images = self.scraper.search(keyword, limit=limit)
            
            def on_search_done():
                self._log(self.t('search_done').format(len(self.images)))
                self._update_preview()
                self.download_btn.config(state=tk.NORMAL if self.images else tk.DISABLED)
                self.download_all_btn.config(state=tk.NORMAL if self.images else tk.DISABLED)
                self.status_var.set(self.t('search_done').format(len(self.images)))
            
            self.root.after(0, on_search_done)
            
        except Exception as e:
            self.root.after(0, lambda: self._log(self.t('search_error').format(e)))
        finally:
            self.is_running = False
            def on_done():
                self.search_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
            self.root.after(0, on_done)
    
    def _update_preview(self):
        selected_indices = set()
        for i, t in enumerate(self.thumbnails):
            if t['selected'].get():
                selected_indices.add(i)
        
        self._clear_preview()
        
        thumb_size = 140
        thumb_dim = (thumb_size, thumb_size)
        
        canvas_width = self.preview_canvas.winfo_width()
        if canvas_width > 1:
            cols = max(1, canvas_width // (thumb_size + 20))
        else:
            cols = 5
        
        for i, img in enumerate(self.images):
            row = i // cols
            col = i % cols
            
            is_selected = i in selected_indices
            border_color = '#0078d4' if is_selected else 'white'
            
            frame = tk.Frame(self.preview_inner, bg=border_color, bd=3, relief=tk.RAISED,
                             cursor="hand2", width=thumb_size, height=thumb_size)
            frame.grid(row=row, column=col, padx=8, pady=8)
            frame.grid_propagate(False)
            
            thumb_label = tk.Label(frame, bg='white',
                                   text=self.t('loading'), fg='#999', compound=tk.CENTER,
                                   cursor="hand2")
            thumb_label.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            selected_var = tk.BooleanVar(value=is_selected)
            
            check_icon = tk.Label(frame, text="✓" if is_selected else "",
                                  bg='#0078d4', fg='white', font=('Arial', 10, 'bold'),
                                  cursor="hand2", width=2, height=1)
            check_icon.place(relx=1.0, y=0, anchor=tk.NE)
            
            def do_toggle(idx=i):
                self._toggle_select(idx)
            
            frame.bind("<Button-1>", lambda e, idx=i: do_toggle(idx))
            thumb_label.bind("<Button-1>", lambda e, idx=i: do_toggle(idx))
            check_icon.bind("<Button-1>", lambda e, idx=i: do_toggle(idx))
            
            frame.bind("<Enter>", lambda e, idx=i, f=frame: self._show_tooltip_for_frame(e, f, idx))
            frame.bind("<Leave>", lambda e: self._hide_tooltip())
            thumb_label.bind("<Enter>", lambda e, idx=i, f=frame: self._show_tooltip_for_frame(e, f, idx))
            thumb_label.bind("<Leave>", lambda e: self._hide_tooltip())
            
            for w in (frame, thumb_label):
                w.bind("<MouseWheel>", self._on_preview_mousewheel, add=True)
                w.bind("<Button-4>", self._on_preview_mousewheel, add=True)
                w.bind("<Button-5>", self._on_preview_mousewheel, add=True)
                w.bind("<Shift-MouseWheel>", self._on_preview_mousewheel, add=True)
            
            self.thumb_widgets.append(frame)
            self.thumbnails.append({
                'frame': frame,
                'label': thumb_label,
                'selected': selected_var,
                'check_icon': check_icon,
                'source_url': img.get('source_url', ''),
            })
            
            thumb_url = img.get('thumb', '')
            if thumb_url and i not in self._pending_thumbs:
                self._pending_thumbs.add(i)
                self._thumb_pool.submit(self._load_thumbnail, i, thumb_url, thumb_dim)
        
        self._cols = cols
        self._preview_loaded = True
        self._update_selected_count()
    
    def _load_thumbnail(self, index, url, size):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            resp = requests.get(url, timeout=3, headers=headers)
            resp.raise_for_status()
            
            img_data = BytesIO(resp.content)
            img = Image.open(img_data)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            self.root.after(0, lambda idx=index, im=img: self._set_thumbnail(idx, im))
            
        except Exception:
            self.root.after(0, lambda idx=index: self._set_thumbnail_error(idx))
        finally:
            self._pending_thumbs.discard(index)
    
    def _set_thumbnail(self, index, pil_image):
        if index < len(self.thumbnails):
            photo = ImageTk.PhotoImage(pil_image)
            widget = self.thumbnails[index]['label']
            widget.config(image=photo, text="")
            widget.image = photo
    
    def _set_thumbnail_error(self, index):
        if index < len(self.thumbnails):
            self.thumbnails[index]['frame'].grid_remove()
    
    def _toggle_select(self, index):
        if index < len(self.thumbnails):
            t = self.thumbnails[index]
            new_val = not t['selected'].get()
            t['selected'].set(new_val)
            color = '#0078d4' if new_val else 'white'
            t['frame'].config(bg=color)
            t['check_icon'].config(text="✓" if new_val else "", bg=color)
            if new_val:
                self._selected_count += 1
                self._last_selected_index = index
            else:
                self._selected_count -= 1
            self.selected_count_var.set(f"{self.t('selected').split(':')[0]}: {self._selected_count}")
            self.open_source_btn.config(state=tk.NORMAL if self._selected_count > 0 else tk.DISABLED)
    
    def _update_selected_count(self):
        count = sum(1 for t in self.thumbnails if t['selected'].get())
        self.selected_count_var.set(f"{self.t('selected').split(':')[0]}: {count}")
        self.open_source_btn.config(state=tk.NORMAL if count > 0 else tk.DISABLED)
    
    def _update_frame_border(self, index):
        if index >= len(self.thumbnails):
            return
        t = self.thumbnails[index]
        frame = t['frame']
        is_selected = t['selected'].get()
        color = '#0078d4' if is_selected else 'white'
        frame.config(bg=color)
    
    def _show_tooltip_for_frame(self, event, frame, index):
        if index >= len(self.thumbnails):
            return
        source_url = self.thumbnails[index].get('source_url', '')
        if not source_url:
            return
        
        self._hide_tooltip()
        
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root + 15}+{event.y_root + 15}")
        
        label = ttk.Label(self.tooltip, text=source_url, background="#ffffe0",
                         relief="solid", borderwidth=1, padding=(8, 4),
                         wraplength=400)
        label.pack()
    
    def _hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def _get_selected_images(self):
        selected = []
        for i, t in enumerate(self.thumbnails):
            if t['selected'].get() and i < len(self.images):
                selected.append(self.images[i])
        return selected
    
    def _open_selected_source(self):
        if self._selected_count == 0:
            messagebox.showwarning(self.t('warning'), self.t('select_image'))
            return
        
        if self._last_selected_index < 0 or self._last_selected_index >= len(self.images):
            return
        
        img = self.images[self._last_selected_index]
        url = img.get('source_url', '')
        
        if url:
            try:
                import platform
                if platform.system() == 'Darwin':
                    os.system(f'open "{url}"')
                else:
                    webbrowser.open(url)
                self._log(self.t('opened_browser').format(url[:80]))
            except Exception as e:
                self._log(self.t('open_browser_failed').format(e))
        else:
            img_url = img.get('url', '')
            if img_url:
                try:
                    import platform
                    if platform.system() == 'Darwin':
                        os.system(f'open "{img_url}"')
                    else:
                        webbrowser.open(img_url)
                    self._log(self.t('no_source_url').format(img_url[:80]))
                except Exception as e:
                    self._log(self.t('open_browser_failed').format(e))
            else:
                messagebox.showwarning(self.t('warning'), self.t('no_url'))
    
    def _deselect_all(self):
        for i, t in enumerate(self.thumbnails):
            if t['selected'].get():
                t['selected'].set(False)
                t['frame'].config(bg='white')
                t['check_icon'].config(text="", bg='white')
        self._selected_count = 0
        self._last_selected_index = -1
        self.selected_count_var.set(self.t('selected'))
        self.open_source_btn.config(state=tk.DISABLED)
    
    def _clear_cache(self):
        import gc
        self._pending_thumbs.clear()
        for t in self.thumbnails:
            try:
                t['label'].image = None
            except:
                pass
        gc.collect()
        self._log(self.t('cleared_cache'))
    
    def download_selected(self):
        images = self._get_selected_images()
        if not images:
            messagebox.showwarning(self.t('warning'), self.t('select_download'))
            return
        self._start_download(images)
    
    def download_all(self):
        if not self.images:
            messagebox.showwarning(self.t('warning'), self.t('no_images'))
            return
        self._start_download(self.images.copy())
    
    def _start_download(self, images):
        keyword = self.keyword_var.get().strip() or "images"
        output_dir = self.output_var.get()
        
        self.is_running = True
        self.stop_btn.config(state=tk.NORMAL)
        self.download_btn.config(state=tk.DISABLED)
        self.download_all_btn.config(state=tk.DISABLED)
        self.status_var.set(self.t('downloading'))
        
        self.downloader = ImageDownloader(output_dir=output_dir)
        
        thread = threading.Thread(
            target=self._download_thread,
            args=(images, keyword),
            daemon=True
        )
        thread.start()
    
    def _download_thread(self, images, keyword):
        success = 0
        failed = 0
        total = len(images)
        
        try:
            for i, img in enumerate(images, 1):
                if not self.is_running:
                    self.root.after(0, lambda: self._log(self.t('download_stopped')))
                    break
                
                self.root.after(0, lambda idx=i, tot=total: self.status_var.set(self.t('downloading').format(idx, tot)))
                
                result = self.downloader.download(
                    img,
                    keyword,
                    i,
                    callback=lambda msg: self.root.after(0, lambda m=msg: self._log(m))
                )
                
                if result:
                    success += 1
                else:
                    failed += 1
            
            self.root.after(0, lambda: self._log(self.t('download_done').format(success, failed)))
            self.root.after(0, lambda: self.status_var.set(self.t('download_done').format(success, failed)))
            
            if success > 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    self.t('success'),
                    self.t('download_complete').format(success, failed, self.downloader.output_dir)
                ))
                
        except Exception as e:
            self.root.after(0, lambda: self._log(f"下载错误: {e}"))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.download_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.download_all_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
    
    def stop(self):
        self.is_running = False
        self.status_var.set(self.t('stop'))
    
    def _on_close(self):
        self.is_running = False
        self._thumb_pool.shutdown(wait=False)
        self.root.destroy()
    
    # ========== URL 提取功能 ==========
    
    def extract_from_url(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(self.t('warning'), self.t('enter_url'))
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_var.set(url)
        
        self.is_running = True
        self.url_stop_btn.config(state=tk.NORMAL)
        self.url_extract_btn.config(state=tk.DISABLED)
        self.status_var.set(self.t('extracting'))
        
        self.url_images = []
        self._clear_url_preview()
        
        thread = threading.Thread(target=self._extract_thread, args=(url,), daemon=True)
        thread.start()
    
    def _clear_url_preview(self):
        for widget in self.url_thumb_widgets:
            widget.destroy()
        self.url_thumb_widgets = []
        self.url_thumbnails = []
        self.selected_count_var.set(self.t('selected'))
    
    def _extract_thread(self, url):
        try:
            self.root.after(0, lambda: self._log(f"Fetching: {url}" if self.lang == 'en' else f"正在获取网页: {url}"))
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            
            self.root.after(0, lambda: self._log(f"OK: {len(resp.text)} bytes" if self.lang == 'en' else f"网页获取成功，大小: {len(resp.text)} 字节"))
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            filter_str = self.filter_var.get().strip()
            formats = [f.strip().lower() for f in filter_str.split(',') if f.strip()]
            
            images = []
            seen_urls = set()
            
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
                if src:
                    full_url = urljoin(url, src)
                    if full_url not in seen_urls and self._is_image_url(full_url, formats):
                        seen_urls.add(full_url)
                        images.append({
                            'url': full_url,
                            'thumb': full_url,
                            'title': img.get('alt', '') or os.path.basename(urlparse(full_url).path),
                            'source': 'URL',
                            'width': img.get('width', 0),
                            'height': img.get('height', 0),
                        })
            
            for img in soup.find_all('img'):
                srcset = img.get('srcset', '')
                if srcset:
                    for part in srcset.split(','):
                        part = part.strip()
                        if part:
                            img_url = part.split()[0]
                            full_url = urljoin(url, img_url)
                            if full_url not in seen_urls and self._is_image_url(full_url, formats):
                                seen_urls.add(full_url)
                                images.append({
                                    'url': full_url,
                                    'thumb': full_url,
                                    'title': img.get('alt', '') or os.path.basename(urlparse(full_url).path),
                                    'source': 'URL',
                                    'width': 0,
                                    'height': 0,
                                })
            
            for source in soup.find_all('source'):
                srcset = source.get('srcset', '')
                if srcset:
                    for part in srcset.split(','):
                        part = part.strip()
                        if part:
                            img_url = part.split()[0]
                            full_url = urljoin(url, img_url)
                            if full_url not in seen_urls and self._is_image_url(full_url, formats):
                                seen_urls.add(full_url)
                                images.append({
                                    'url': full_url,
                                    'thumb': full_url,
                                    'title': os.path.basename(urlparse(full_url).path),
                                    'source': 'URL',
                                    'width': 0,
                                    'height': 0,
                                })
            
            for tag in soup.find_all(style=True):
                style = tag.get('style', '')
                bg_matches = re.findall(r'url\(["\']?(.*?)["\']?\)', style)
                for bg_url in bg_matches:
                    full_url = urljoin(url, bg_url)
                    if full_url not in seen_urls and self._is_image_url(full_url, formats):
                        seen_urls.add(full_url)
                        images.append({
                            'url': full_url,
                            'thumb': full_url,
                            'title': os.path.basename(urlparse(full_url).path),
                            'source': 'URL',
                            'width': 0,
                            'height': 0,
                        })
            
            self.url_images = images
            
            self.root.after(0, lambda: self._log(self.t('extract_done').format(len(images))))
            self.root.after(0, self._update_url_preview)
            self.root.after(0, lambda: self.url_download_btn.config(state=tk.NORMAL if images else tk.DISABLED))
            self.root.after(0, lambda: self.url_download_all_btn.config(state=tk.NORMAL if images else tk.DISABLED))
            self.root.after(0, lambda: self.status_var.set(self.t('extract_done').format(len(images))))
            
        except Exception as e:
            self.root.after(0, lambda: self._log(self.t('extract_error').format(e)))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.url_extract_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.url_stop_btn.config(state=tk.DISABLED))
    
    def _is_image_url(self, url, formats):
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if url.startswith('data:'):
            return False
        
        for fmt in formats:
            if path.endswith(f'.{fmt}'):
                return True
        
        if not formats:
            common_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'ico']
            for fmt in common_formats:
                if path.endswith(f'.{fmt}'):
                    return True
        
        if any(fmt in url.lower() for fmt in ['image', 'photo', 'pic', 'img']):
            return True
        
        return False
    
    def _update_url_preview(self):
        self._clear_url_preview()
        
        thumb_size = 140
        thumb_dim = (thumb_size, thumb_size)
        
        canvas_width = self.url_preview_canvas.winfo_width()
        if canvas_width > 1:
            cols = max(1, canvas_width // (thumb_size + 20))
        else:
            cols = 5
        
        for i, img in enumerate(self.url_images):
            row = i // cols
            col = i % cols
            
            frame = tk.Frame(self.url_preview_inner, bg='white', bd=3, relief=tk.RAISED,
                             cursor="hand2", width=thumb_size, height=thumb_size)
            frame.grid(row=row, column=col, padx=8, pady=8)
            frame.grid_propagate(False)
            
            thumb_label = tk.Label(frame, bg='white',
                                   text=self.t('loading'), fg='#999', compound=tk.CENTER,
                                   cursor="hand2")
            thumb_label.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            selected_var = tk.BooleanVar(value=False)
            
            check_icon = tk.Label(frame, text="",
                                  bg='white', fg='white', font=('Arial', 10, 'bold'),
                                  cursor="hand2", width=2, height=1)
            check_icon.place(relx=1.0, y=0, anchor=tk.NE)
            
            frame.bind("<Button-1>", lambda e, idx=i: self._url_toggle_select(idx))
            thumb_label.bind("<Button-1>", lambda e, idx=i: self._url_toggle_select(idx))
            check_icon.bind("<Button-1>", lambda e, idx=i: self._url_toggle_select(idx))
            
            frame.bind("<Enter>", lambda e, idx=i, f=frame: self._show_url_tooltip_for_frame(e, f, idx))
            frame.bind("<Leave>", lambda e: self._hide_tooltip())
            thumb_label.bind("<Enter>", lambda e, idx=i, f=frame: self._show_url_tooltip_for_frame(e, f, idx))
            thumb_label.bind("<Leave>", lambda e: self._hide_tooltip())
            
            for w in (frame, thumb_label):
                w.bind("<MouseWheel>", self._on_url_mousewheel, add=True)
                w.bind("<Button-4>", self._on_url_mousewheel, add=True)
                w.bind("<Button-5>", self._on_url_mousewheel, add=True)
                w.bind("<Shift-MouseWheel>", self._on_url_mousewheel, add=True)
            
            self.url_thumb_widgets.append(frame)
            self.url_thumbnails.append({
                'frame': frame,
                'label': thumb_label,
                'selected': selected_var,
                'check_icon': check_icon,
                'source_url': img.get('url', ''),
            })
            
            thumb_url = img.get('thumb', '')
            if thumb_url:
                self._thumb_pool.submit(self._load_url_thumbnail, i, thumb_url, thumb_dim)
        
        self._url_cols = cols
        self._url_preview_loaded = True
        self._update_url_selected_count()
    
    def _load_url_thumbnail(self, index, url, size):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            resp = requests.get(url, timeout=3, headers=headers)
            resp.raise_for_status()
            
            img_data = BytesIO(resp.content)
            img = Image.open(img_data)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            self.root.after(0, lambda idx=index, im=img: self._set_url_thumbnail(idx, im))
            
        except Exception:
            self.root.after(0, lambda idx=index: self._set_url_thumbnail_error(idx))
    
    def _set_url_thumbnail(self, index, photo):
        if index < len(self.url_thumbnails):
            self.url_thumbnails[index]['label'].config(image=photo, text="")
            self.url_thumbnails[index]['label'].image = photo
    
    def _set_url_thumbnail_error(self, index):
        if index < len(self.url_thumbnails):
            self.url_thumbnails[index]['frame'].grid_remove()
    
    def _url_toggle_select(self, index):
        if index < len(self.url_thumbnails):
            t = self.url_thumbnails[index]
            new_val = not t['selected'].get()
            t['selected'].set(new_val)
            color = '#0078d4' if new_val else 'white'
            t['frame'].config(bg=color)
            t['check_icon'].config(text="✓" if new_val else "", bg=color)
            self._update_url_selected_count()
    
    def _update_url_selected_count(self):
        count = sum(1 for t in self.url_thumbnails if t['selected'].get())
        self.selected_count_var.set(f"{self.t('selected').split(':')[0]}: {count}")
    
    def _show_url_tooltip_for_frame(self, event, frame, index):
        if index >= len(self.url_thumbnails):
            return
        source_url = self.url_thumbnails[index].get('source_url', '')
        if not source_url:
            return
        
        self._hide_tooltip()
        
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root + 15}+{event.y_root + 15}")
        
        label = ttk.Label(self.tooltip, text=source_url, background="#ffffe0",
                         relief="solid", borderwidth=1, padding=(8, 4),
                         wraplength=400)
        label.pack()
    
    def _get_url_selected_images(self):
        selected = []
        for i, t in enumerate(self.url_thumbnails):
            if t['selected'].get() and i < len(self.url_images):
                selected.append(self.url_images[i])
        return selected
    
    def url_download_selected(self):
        images = self._get_url_selected_images()
        if not images:
            messagebox.showwarning(self.t('warning'), self.t('select_download'))
            return
        self._start_url_download(images)
    
    def url_download_all(self):
        if not self.url_images:
            messagebox.showwarning(self.t('warning'), self.t('no_images'))
            return
        self._start_url_download(self.url_images.copy())
    
    def _start_url_download(self, images):
        url = self.url_var.get().strip()
        keyword = urlparse(url).netloc.replace('.', '_') or "web_images"
        output_dir = self.output_var.get()
        
        self.is_running = True
        self.url_stop_btn.config(state=tk.NORMAL)
        self.url_download_btn.config(state=tk.DISABLED)
        self.url_download_all_btn.config(state=tk.DISABLED)
        self.status_var.set(self.t('downloading'))
        
        self.downloader = ImageDownloader(output_dir=output_dir)
        
        thread = threading.Thread(
            target=self._url_download_thread,
            args=(images, keyword),
            daemon=True
        )
        thread.start()
    
    def _url_download_thread(self, images, keyword):
        success = 0
        failed = 0
        total = len(images)
        
        try:
            for i, img in enumerate(images, 1):
                if not self.is_running:
                    self.root.after(0, lambda: self._log(self.t('download_stopped')))
                    break
                
                self.root.after(0, lambda idx=i, tot=total: self.status_var.set(self.t('downloading').format(idx, tot)))
                
                result = self.downloader.download(
                    img,
                    keyword,
                    i,
                    callback=lambda msg: self.root.after(0, lambda m=msg: self._log(m))
                )
                
                if result:
                    success += 1
                else:
                    failed += 1
            
            self.root.after(0, lambda: self._log(self.t('download_done').format(success, failed)))
            self.root.after(0, lambda: self.status_var.set(self.t('download_done').format(success, failed)))
            
            if success > 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    self.t('success'),
                    self.t('download_complete').format(success, failed, self.downloader.output_dir)
                ))
                
        except Exception as e:
            self.root.after(0, lambda: self._log(f"下载错误: {e}"))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.url_download_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.url_download_all_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.url_stop_btn.config(state=tk.DISABLED))


def main():
    root = tk.Tk()
    app = ImageScraperGUI(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        app._thumb_pool.shutdown(wait=False)
        root.destroy()


if __name__ == "__main__":
    main()
