import aiohttp
import asyncio
from typing import Dict, Any, Optional, List, Tuple
import re

class GeocodingService:
    def __init__(self, api_key: str):
        """初始化地理编码服务"""
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/geocode/geo"
        self.search_url = "https://restapi.amap.com/v3/place/text"
        
    async def geocode(self, address: str, city: str = "烟台") -> Optional[Dict[str, float]]:
        """获取地址的经纬度坐标"""
        try:
            params = {
                "key": self.api_key,
                "address": address,
                "city": city
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("geocodes"):
                            location = data["geocodes"][0]["location"]
                            lng, lat = location.split(",")
                            return {
                                "longitude": float(lng),
                                "latitude": float(lat)
                            }
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    async def search_city(self, city_name: str) -> Optional[Dict[str, Any]]:
        """搜索城市信息，获取中心坐标"""
        try:
            params = {
                "key": self.api_key,
                "keywords": city_name,
                "types": "190100", # 城市类型编码
                "city": city_name,
                "offset": 1,  # 仅返回一条结果
                "page": 1,
                "extensions": "all"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("pois"):
                            poi = data["pois"][0]
                            location = poi["location"]
                            lng, lat = location.split(",")
                            return {
                                "name": city_name,
                                "longitude": float(lng),
                                "latitude": float(lat),
                                "adcode": poi.get("adcode", "")
                            }
            return None
        except Exception as e:
            print(f"City search error: {e}")
            return None
    
    async def extract_locations(self, text: str, default_city: str = "烟台") -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """从文本中提取位置信息，返回城市和相关地点"""
        # 简单的城市名称提取
        city_pattern = r"(?:在|位于|去|到|游览|参观|游玩)?(\w+?(?:市|县|区))(?:的|是|有|旅游|景点|玩什么)"
        city_match = re.search(city_pattern, text)
        
        city_name = default_city
        if city_match:
            city_name = city_match.group(1)
            if city_name.endswith(("县", "市", "区")):
                city_name = city_name[:-1]  # 移除"市"、"县"或"区"后缀
        
        # 获取城市信息
        city_info = await self.search_city(city_name) or {
            "name": city_name,
            "longitude": 121.391382,  # 烟台默认经度
            "latitude": 37.539297,    # 烟台默认纬度
            "adcode": "370600"       # 烟台市默认编码
        }
        
        # 提取景点名称（这是简化版，实际情况可能需要更复杂的NLP处理）
        # 这里假设数据中的景点已经包含了坐标信息
        
        return city_info, []  # 第二个列表将由模型和数据加载器提供实际景点
