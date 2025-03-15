import json
import os
from typing import Dict, List, Any, Optional

class DataLoader:
    def __init__(self, data_dir: str = None):
        """初始化数据加载器，加载所有JSON文件中的景点数据"""
        if data_dir is None:
            data_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.data_dir = data_dir
        self.data = self._load_all_data()
        
    def _load_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载所有JSON文件的数据"""
        data_files = {
            "scenic": os.path.join(self.data_dir, "scenic_spots.json"),
            "romantic": os.path.join(self.data_dir, "romantic_spots.json"),
            "family": os.path.join(self.data_dir, "family_attractions.json")
        }
        
        all_data = {}
        
        for category, file_path in data_files.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_data[category] = data.get("景点列表", [])
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                all_data[category] = []
                
        return all_data
    
    def search_spots(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """简单搜索功能，根据关键词查找相关景点"""
        results = []
        
        for category, spots in self.data.items():
            for spot in spots:
                if query in spot.get("景点名称", ""):
                    # 添加分类标签
                    spot_with_category = spot.copy()
                    spot_with_category["分类"] = self._get_category_name(category)
                    results.append(spot_with_category)
                    
        return results[:limit]
    
    def get_all_spots(self) -> List[Dict[str, Any]]:
        """获取所有景点的基本信息"""
        all_spots = []
        
        for category, spots in self.data.items():
            for spot in spots:
                spot_info = {
                    "景点名称": spot.get("景点名称", ""),
                    "分类": self._get_category_name(category)
                }
                all_spots.append(spot_info)
                
        return all_spots
    
    def get_spot_details(self, spot_name: str) -> Optional[Dict[str, Any]]:
        """根据景点名称获取详细信息"""
        for category, spots in self.data.items():
            for spot in spots:
                if spot.get("景点名称", "") == spot_name:
                    spot_with_category = spot.copy()
                    spot_with_category["分类"] = self._get_category_name(category)
                    return spot_with_category
        
        return None
    
    def _get_category_name(self, category_code: str) -> str:
        """获取分类的中文名称"""
        categories = {
            "scenic": "经典景点",
            "romantic": "浪漫景点",
            "family": "亲子景点"
        }
        return categories.get(category_code, "其他景点")
