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


class ImageScraperGUI:
    """图片爬虫 GUI 界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("图片爬虫工具")
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
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        search_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(search_tab, text="关键词搜索")
        self._setup_search_tab(search_tab)
        
        url_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(url_tab, text="网址提取")
        self._setup_url_tab(url_tab)
        
        settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_tab, text="设置")
        self._setup_settings_tab(settings_tab)
    
    def _setup_settings_tab(self, parent):
        """设置标签页"""
        # 保存目录
        dir_frame = ttk.LabelFrame(parent, text="保存目录", padding="10")
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dir_frame, text="默认保存目录:").pack(anchor=tk.W, pady=(0, 5))
        dir_entry_frame = ttk.Frame(dir_frame)
        dir_entry_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.output_var = tk.StringVar(value=self.config.get('default_output_dir', 'downloaded_images'))
        ttk.Entry(dir_entry_frame, textvariable=self.output_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(dir_entry_frame, text="浏览...", command=self._browse_output).pack(side=tk.LEFT)
        ttk.Button(dir_entry_frame, text="保存", command=self._save_default_dir).pack(side=tk.LEFT, padx=(5, 0))
        
        # 窗口设置
        win_frame = ttk.LabelFrame(parent, text="窗口设置", padding="10")
        win_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(win_frame, text="保存当前窗口大小", command=self._save_window_size).pack(anchor=tk.W, pady=2)
        ttk.Button(win_frame, text="恢复初始窗口大小", command=self._reset_window_size).pack(anchor=tk.W, pady=2)
        
        # 缓存管理
        cache_frame = ttk.LabelFrame(parent, text="缓存管理", padding="10")
        cache_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(cache_frame, text="清空缓存", command=self._clear_cache).pack(anchor=tk.W, pady=2)
        
        # 日志
        log_frame = ttk.LabelFrame(parent, text="日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def _setup_search_tab(self, parent):
        # 状态栏 - 必须最先初始化
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        self.selected_count_var = tk.StringVar(value="已选: 0 张")
        ttk.Label(status_frame, textvariable=self.selected_count_var).pack(side=tk.RIGHT)
        
        search_frame = ttk.LabelFrame(parent, text="搜索设置", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="关键词:").grid(row=0, column=0, sticky=tk.W, pady=5)
        keyword_entry_frame = ttk.Frame(search_frame)
        keyword_entry_frame.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)
        self.keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(keyword_entry_frame, textvariable=self.keyword_var, width=35)
        keyword_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        keyword_entry.bind('<Return>', lambda e: self.search())
        ttk.Button(keyword_entry_frame, text="清空", command=self._clear_search, width=6).pack(side=tk.LEFT, padx=(5, 0))
        
        history_frame = ttk.Frame(search_frame)
        history_frame.grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(history_frame, text="历史", command=self._show_history, width=6).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(search_frame, text="下载数量:").grid(row=2, column=0, sticky=tk.W, pady=5)
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
        
        self.search_btn = ttk.Button(button_frame, text="搜索图片", command=self.search)
        self.search_btn.pack(side=tk.LEFT, padx=5, ipadx=30, ipady=10)
        
        self.download_btn = ttk.Button(button_frame, text="下载选中", command=self.download_selected, state=tk.DISABLED)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_all_btn = ttk.Button(button_frame, text="下载全部", command=self.download_all, state=tk.DISABLED)
        self.download_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_source_btn = ttk.Button(button_frame, text="前往来源", command=self._open_selected_source, state=tk.DISABLED)
        self.open_source_btn.pack(side=tk.LEFT, padx=5)
        
        self.deselect_all_btn = ttk.Button(button_frame, text="取消选中", command=self._deselect_all)
        self.deselect_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="停止", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=5)
        
        # 状态栏
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        self.selected_count_var = tk.StringVar(value="已选: 0 张")
        ttk.Label(status_frame, textvariable=self.selected_count_var).pack(side=tk.RIGHT)
        
        self._setup_preview_area(parent)
    
    def _setup_url_tab(self, parent):
        url_frame = ttk.LabelFrame(parent, text="网址设置", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="网页 URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)
        url_entry.bind('<Return>', lambda e: self.extract_from_url())
        
        ttk.Label(url_frame, text="过滤格式:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.filter_var = tk.StringVar(value="jpg,jpeg,png,gif,webp")
        filter_entry = ttk.Entry(url_frame, textvariable=self.filter_var, width=40)
        filter_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(url_frame, text="(逗号分隔)").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        url_frame.columnconfigure(1, weight=1)
        
        url_button_frame = ttk.Frame(parent)
        url_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.url_extract_btn = ttk.Button(url_button_frame, text="提取图片", command=self.extract_from_url)
        self.url_extract_btn.pack(side=tk.LEFT, padx=5, ipadx=30, ipady=10)
        
        self.url_download_btn = ttk.Button(url_button_frame, text="下载选中", command=self.url_download_selected, state=tk.DISABLED)
        self.url_download_btn.pack(side=tk.LEFT, padx=5)
        
        self.url_download_all_btn = ttk.Button(url_button_frame, text="下载全部", command=self.url_download_all, state=tk.DISABLED)
        self.url_download_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.url_stop_btn = ttk.Button(url_button_frame, text="停止", command=self.stop, state=tk.DISABLED)
        self.url_stop_btn.pack(side=tk.RIGHT, padx=5)
        
        self._setup_url_preview_area(parent)
    
    def _setup_preview_area(self, parent):
        preview_frame = ttk.LabelFrame(parent, text="搜索结果", padding="5")
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
        self.preview_inner.bind("<MouseWheel>", self._on_preview_mousewheel)
        self.preview_inner.bind("<Button-4>", self._on_preview_mousewheel)
        self.preview_inner.bind("<Button-5>", self._on_preview_mousewheel)
        self.preview_canvas.bind("<Configure>", self._on_resize)
    
    def _setup_url_preview_area(self, parent):
        url_preview_frame = ttk.LabelFrame(parent, text="网页图片", padding="5")
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
        self.url_preview_inner.bind("<MouseWheel>", self._on_url_mousewheel)
        self.url_preview_inner.bind("<Button-4>", self._on_url_mousewheel)
        self.url_preview_inner.bind("<Button-5>", self._on_url_mousewheel)
        self.url_preview_canvas.bind("<Configure>", self._on_url_resize)
        
        self.url_thumbnails = []
        self.url_thumb_widgets = []
        self.url_images = []
        self._url_preview_loaded = False
        self._url_resize_timer = None
        self._url_cols = 3
    
    def _on_preview_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.preview_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.preview_canvas.yview_scroll(1, "units")
        return "break"
    
    def _on_url_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.url_preview_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
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
        new_cols = 5
        
        if new_cols == self._cols:
            return
        
        self._cols = new_cols
        for i, widget in enumerate(self.thumb_widgets):
            row = i // new_cols
            col = i % new_cols
            widget.grid(row=row, column=col, padx=8, pady=8, sticky=tk.NSEW)
        
        for c in range(new_cols):
            self.preview_inner.columnconfigure(c, weight=1)
    
    def _reflow_url_preview(self):
        new_cols = 5
        
        if new_cols == self._url_cols:
            return
        
        self._url_cols = new_cols
        for i, widget in enumerate(self.url_thumb_widgets):
            row = i // new_cols
            col = i % new_cols
            widget.grid(row=row, column=col, padx=8, pady=8, sticky=tk.NSEW)
        
        for c in range(new_cols):
            self.url_preview_inner.columnconfigure(c, weight=1)
    
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
            self._log(f"已保存默认目录: {current_dir}")
            messagebox.showinfo("成功", f"已保存默认目录:\n{current_dir}")
    
    def _save_window_size(self):
        geom = self.root.geometry()
        self.config['window_geometry'] = geom
        self._save_config()
        self._log(f"已保存窗口大小: {geom}")
        messagebox.showinfo("成功", f"已保存当前窗口大小:\n{geom}")
    
    def _reset_window_size(self):
        self.root.geometry("900x650")
        self.config.pop('window_geometry', None)
        self._save_config()
        self._log("已恢复初始窗口大小: 900x650")
    
    def _get_scraper(self):
        return BingScraper()
    
    def _clear_search(self):
        self.images = []
        self.keyword_var.set("")
        self._clear_preview()
        self.download_btn.config(state=tk.DISABLED)
        self.download_all_btn.config(state=tk.DISABLED)
        self.status_var.set("就绪")
        self._log("已清空搜索")
    
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
            messagebox.showinfo("搜索历史", "暂无搜索历史")
            return
        
        win = tk.Toplevel(self.root)
        win.title("搜索历史")
        win.geometry("450x500")
        win.transient(self.root)
        win.grab_set()
        
        ttk.Label(win, text="搜索历史", font=('Arial', 12, 'bold')).pack(pady=10)
        
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
            if messagebox.askyesno("确认", "确定要清空所有搜索历史吗？"):
                self.search_history.clear()
                self._save_config()
                win.destroy()
        
        ttk.Button(btn_frame, text="清空全部", command=clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=win.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _do_search_from_history(self, keyword):
        self.keyword_var.set(keyword)
        self.search()
    
    # ========== 搜索功能 ==========
    
    def search(self):
        keyword = self.keyword_var.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
        
        self.is_running = True
        self.stop_btn.config(state=tk.NORMAL)
        self.search_btn.config(state=tk.DISABLED)
        self.status_var.set("正在搜索...")
        
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
        self.selected_count_var.set("已选: 0 张")
    
    def _search_thread(self, keyword):
        self._add_to_history(keyword)
        try:
            self.scraper = self._get_scraper()
            if not self.scraper:
                self.root.after(0, lambda: self._log("错误: 无法创建爬虫"))
                return
            
            self.root.after(0, lambda: self._log(f"正在从 {self.scraper.get_name()} 搜索: {keyword}"))
            
            limit = self.limit_var.get()
            self.images = self.scraper.search(keyword, limit=limit)
            
            def on_search_done():
                self._log(f"搜索完成，找到 {len(self.images)} 张图片")
                self._update_preview()
                self.download_btn.config(state=tk.NORMAL if self.images else tk.DISABLED)
                self.download_all_btn.config(state=tk.NORMAL if self.images else tk.DISABLED)
                self.status_var.set(f"搜索完成，找到 {len(self.images)} 张图片")
            
            self.root.after(0, on_search_done)
            
        except Exception as e:
            self.root.after(0, lambda: self._log(f"搜索错误: {e}"))
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
        
        canvas_width = self.preview_canvas.winfo_width()
        if canvas_width > 1:
            thumb_size = max(50, (canvas_width - 16) // 5)
        else:
            thumb_size = 155
        thumb_dim = (thumb_size, thumb_size)
        cols = 5
        
        for i, img in enumerate(self.images):
            row = i // cols
            col = i % cols
            
            is_selected = i in selected_indices
            border_color = '#0078d4' if is_selected else 'white'
            
            frame = tk.Frame(self.preview_inner, bg=border_color, bd=3, relief=tk.RAISED,
                             cursor="hand2", width=thumb_size, height=thumb_size)
            frame.grid(row=row, column=col, padx=8, pady=8, sticky=tk.NSEW)
            frame.grid_propagate(False)
            
            thumb_label = tk.Label(frame, bg='white',
                                   text="加载中...", fg='#999', compound=tk.CENTER,
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
        
        for c in range(cols):
            self.preview_inner.columnconfigure(c, weight=1)
        
        self._cols = cols
        self._preview_loaded = True
        self._update_selected_count()
    
    def _load_thumbnail(self, index, url, size):
        try:
            resp = requests.get(url, timeout=1, stream=True)
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
            self.selected_count_var.set(f"已选: {self._selected_count} 张")
            self.open_source_btn.config(state=tk.NORMAL if self._selected_count > 0 else tk.DISABLED)
    
    def _update_selected_count(self):
        count = sum(1 for t in self.thumbnails if t['selected'].get())
        self.selected_count_var.set(f"已选: {count} 张")
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
            messagebox.showwarning("警告", "请先选中至少一张图片")
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
                self._log(f"已在浏览器中打开: {url[:80]}...")
            except Exception as e:
                self._log(f"打开浏览器失败: {e}")
        else:
            img_url = img.get('url', '')
            if img_url:
                try:
                    import platform
                    if platform.system() == 'Darwin':
                        os.system(f'open "{img_url}"')
                    else:
                        webbrowser.open(img_url)
                    self._log(f"无来源链接，已打开图片 URL: {img_url[:80]}...")
                except Exception as e:
                    self._log(f"打开图片 URL 失败: {e}")
            else:
                messagebox.showwarning("警告", "无法获取来源链接或图片 URL")
    
    def _deselect_all(self):
        for i, t in enumerate(self.thumbnails):
            if t['selected'].get():
                t['selected'].set(False)
                t['frame'].config(bg='white')
                t['check_icon'].config(text="", bg='white')
        self._selected_count = 0
        self._last_selected_index = -1
        self.selected_count_var.set("已选: 0 张")
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
        self._log("已清空缓存")
    
    def download_selected(self):
        images = self._get_selected_images()
        if not images:
            messagebox.showwarning("警告", "请先选中要下载的图片")
            return
        self._start_download(images)
    
    def download_all(self):
        if not self.images:
            messagebox.showwarning("警告", "没有可下载的图片")
            return
        self._start_download(self.images.copy())
    
    def _start_download(self, images):
        keyword = self.keyword_var.get().strip() or "images"
        output_dir = self.output_var.get()
        
        self.is_running = True
        self.stop_btn.config(state=tk.NORMAL)
        self.download_btn.config(state=tk.DISABLED)
        self.download_all_btn.config(state=tk.DISABLED)
        self.status_var.set("正在下载...")
        
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
                    self.root.after(0, lambda: self._log("下载已停止"))
                    break
                
                self.root.after(0, lambda idx=i, tot=total: self.status_var.set(f"正在下载 {idx}/{tot}..."))
                
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
            
            self.root.after(0, lambda: self._log(f"下载完成: 成功 {success} 张，失败 {failed} 张"))
            self.root.after(0, lambda: self.status_var.set(f"下载完成: 成功 {success} 张，失败 {failed} 张"))
            
            if success > 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    "完成",
                    f"下载完成!\n成功: {success} 张\n失败: {failed} 张\n\n保存目录: {self.downloader.output_dir}"
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
        self.status_var.set("正在停止...")
    
    def _on_close(self):
        self.is_running = False
        self._thumb_pool.shutdown(wait=False)
        self.root.destroy()
    
    # ========== URL 提取功能 ==========
    
    def extract_from_url(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入网页 URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_var.set(url)
        
        self.is_running = True
        self.url_stop_btn.config(state=tk.NORMAL)
        self.url_extract_btn.config(state=tk.DISABLED)
        self.status_var.set("正在提取图片...")
        
        self.url_images = []
        self._clear_url_preview()
        
        thread = threading.Thread(target=self._extract_thread, args=(url,), daemon=True)
        thread.start()
    
    def _clear_url_preview(self):
        for widget in self.url_thumb_widgets:
            widget.destroy()
        self.url_thumb_widgets = []
        self.url_thumbnails = []
        self.selected_count_var.set("已选: 0 张")
    
    def _extract_thread(self, url):
        try:
            self.root.after(0, lambda: self._log(f"正在获取网页: {url}"))
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            
            self.root.after(0, lambda: self._log(f"网页获取成功，大小: {len(resp.text)} 字节"))
            
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
            
            self.root.after(0, lambda: self._log(f"提取完成，找到 {len(images)} 张图片"))
            self.root.after(0, self._update_url_preview)
            self.root.after(0, lambda: self.url_download_btn.config(state=tk.NORMAL if images else tk.DISABLED))
            self.root.after(0, lambda: self.url_download_all_btn.config(state=tk.NORMAL if images else tk.DISABLED))
            self.root.after(0, lambda: self.status_var.set(f"提取完成，找到 {len(images)} 张图片"))
            
        except Exception as e:
            self.root.after(0, lambda: self._log(f"提取错误: {e}"))
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
        
        canvas_width = self.url_preview_canvas.winfo_width()
        if canvas_width > 1:
            thumb_size = max(50, (canvas_width - 16) // 5)
        else:
            thumb_size = 155
        thumb_dim = (thumb_size, thumb_size)
        cols = 5
        
        for i, img in enumerate(self.url_images):
            row = i // cols
            col = i % cols
            
            frame = tk.Frame(self.url_preview_inner, bg='white', bd=3, relief=tk.RAISED,
                             cursor="hand2", width=thumb_size, height=thumb_size)
            frame.grid(row=row, column=col, padx=8, pady=8, sticky=tk.NSEW)
            frame.grid_propagate(False)
            
            thumb_label = tk.Label(frame, bg='white',
                                   text="加载中...", fg='#999', compound=tk.CENTER,
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
        
        for c in range(cols):
            self.url_preview_inner.columnconfigure(c, weight=1)
        
        self._url_cols = cols
        self._url_preview_loaded = True
        self._update_url_selected_count()
    
    def _load_url_thumbnail(self, index, url, size):
        try:
            resp = requests.get(url, timeout=1, stream=True)
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
        self.selected_count_var.set(f"已选: {count} 张")
    
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
            messagebox.showwarning("警告", "请先选中要下载的图片")
            return
        self._start_url_download(images)
    
    def url_download_all(self):
        if not self.url_images:
            messagebox.showwarning("警告", "没有可下载的图片")
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
        self.status_var.set("正在下载...")
        
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
                    self.root.after(0, lambda: self._log("下载已停止"))
                    break
                
                self.root.after(0, lambda idx=i, tot=total: self.status_var.set(f"正在下载 {idx}/{tot}..."))
                
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
            
            self.root.after(0, lambda: self._log(f"下载完成: 成功 {success} 张，失败 {failed} 张"))
            self.root.after(0, lambda: self.status_var.set(f"下载完成: 成功 {success} 张，失败 {failed} 张"))
            
            if success > 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    "完成",
                    f"下载完成!\n成功: {success} 张\n失败: {failed} 张\n\n保存目录: {self.downloader.output_dir}"
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
