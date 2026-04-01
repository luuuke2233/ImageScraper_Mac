import requests
import re
import json
from typing import List, Dict
from urllib.parse import quote
from bs4 import BeautifulSoup
from scraper_base import ImageScraper


class BingScraper(ImageScraper):
    """Bing 图片爬虫"""
    
    def get_name(self) -> str:
        return "Bing"
    
    def search(self, keyword: str, limit: int = 20) -> List[Dict[str, str]]:
        """通过 Bing 搜索图片"""
        images = []
        first = 1
        
        while len(images) < limit:
            url = f"https://www.bing.com/images/search?q={quote(keyword)}&first={first}&count=35&form=IRFLTR"
            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 方法1: 从 iusc 属性中提取
                for a in soup.find_all('a', class_='iusc'):
                    if len(images) >= limit:
                        break
                    
                    m_attr = a.get('m')
                    if m_attr:
                        try:
                            data = json.loads(m_attr)
                            img_url = data.get('murl', '')
                            if img_url:
                                images.append({
                                    'url': img_url,
                                    'thumb': data.get('turl', ''),
                                    'title': data.get('t', '') or data.get('s', '') or keyword,
                                    'source': 'Bing',
                                    'source_url': data.get('purl', '') or data.get('murl', ''),
                                    'width': data.get('tsw', 0),
                                    'height': data.get('tsh', 0),
                                })
                        except json.JSONDecodeError as e:
                            print(f"Bing JSON 解析错误: {e}")
                            continue
                        except Exception as e:
                            print(f"Bing 数据处理错误: {e}")
                            continue
                
                # 方法2: 从 img 标签中提取
                if len(images) == 0:
                    for img in soup.find_all('img'):
                        if len(images) >= limit:
                            break
                        src = img.get('src') or img.get('data-src') or img.get('data-srcset', '').split(',')[0]
                        if src and (src.startswith('http') or src.startswith('//')):
                            if not src.startswith('http'):
                                src = 'https:' + src
                            images.append({
                                'url': src,
                                'thumb': src,
                                'title': img.get('alt', '') or keyword,
                                'source': 'Bing',
                                'width': img.get('width', 0),
                                'height': img.get('height', 0),
                            })
                
                if len(images) == 0:
                    break
                    
                first += 35
                
            except Exception as e:
                print(f"Bing 搜索错误: {e}")
                break
        
        return images[:limit]
