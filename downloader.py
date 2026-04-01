import os
import re
import time
import hashlib
import requests
from typing import Dict, Callable, Optional
from urllib.parse import urlparse


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """清理文件名，移除非法字符"""
    # 移除非法字符
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    # 替换空格和连字符
    name = re.sub(r'\s+', '_', name)
    # 截断过长名称
    if len(name) > max_length:
        name = name[:max_length]
    return name.strip('_')


def get_extension_from_url(url: str, content_type: str = None) -> str:
    """从 URL 或 content-type 获取文件扩展名"""
    ext_map = {
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
        'image/bmp': '.bmp',
        'image/svg+xml': '.svg',
    }
    
    if content_type and content_type in ext_map:
        return ext_map[content_type]
    
    parsed = urlparse(url)
    path = parsed.path.lower()
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']:
        if path.endswith(ext):
            return ext
    
    return '.jpg'


class ImageDownloader:
    """图片下载器"""
    
    def __init__(self, output_dir: str = "downloaded_images"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def download(
        self,
        image_info: Dict,
        keyword: str,
        index: int,
        callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        下载单张图片
        
        Args:
            image_info: 图片信息字典
            keyword: 搜索关键词
            index: 图片序号
            callback: 进度回调函数
            
        Returns:
            保存的文件路径，失败返回 None
        """
        url = image_info.get('url', '')
        if not url:
            return None
        
        try:
            resp = self.session.get(url, timeout=15, stream=True)
            resp.raise_for_status()
            
            content_type = resp.headers.get('Content-Type', '')
            ext = get_extension_from_url(url, content_type)
            
            # 生成文件名（使用哈希避免重名冲突）
            title = sanitize_filename(image_info.get('title', '') or keyword)
            url_hash = hashlib.md5(url.encode()).hexdigest()[:6]
            filename = f"{keyword}_{title}_{index:03d}_{url_hash}{ext}"
            
            # 确保文件名不太长
            if len(filename) > 100:
                filename = f"{keyword}_{index:03d}_{url_hash}{ext}"
            
            # 创建输出目录
            os.makedirs(self.output_dir, exist_ok=True)
            filepath = os.path.join(self.output_dir, filename)
            
            # 写入文件
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if callback:
                callback(f"已下载: {os.path.basename(filepath)}")
            
            return filepath
            
        except Exception as e:
            if callback:
                callback(f"下载失败: {str(e)[:50]}")
            return None
    
    def download_batch(
        self,
        images: list,
        keyword: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, int]:
        """
        批量下载图片
        
        Args:
            images: 图片信息列表
            keyword: 搜索关键词
            progress_callback: 进度回调函数
            
        Returns:
            统计信息 {'success': int, 'failed': int}
        """
        stats = {'success': 0, 'failed': 0}
        
        for i, img in enumerate(images, 1):
            if progress_callback:
                progress_callback(i, len(images), img.get('title', ''))
            
            result = self.download(img, keyword, i, progress_callback)
            if result:
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            time.sleep(0.3)  # 避免请求过快
        
        return stats
