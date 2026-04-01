import requests
from abc import ABC, abstractmethod
from typing import List, Dict
from urllib.parse import quote


class ImageScraper(ABC):
    """图片爬虫基类"""
    
    def __init__(self, headers: dict = None):
        self.session = requests.Session()
        self.session.headers.update(headers or {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    @abstractmethod
    def search(self, keyword: str, limit: int = 20) -> List[Dict[str, str]]:
        """搜索图片，返回图片信息列表"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """返回爬虫名称"""
        pass
