from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 添加CORS中间件
from fastapi.responses import HTMLResponse, FileResponse  # Add this import
from fastapi import requests
from pydantic import BaseModel
import json
import os
from typing import Dict, Any
import httpx
from fastapi.staticfiles import StaticFiles
import uvicorn
from rag.data_loader import DataLoader

app = FastAPI()

# 添加CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],   # 允许所有方法（包括OPTIONS）
    allow_headers=["*"],   # 允许所有头
)

# 添加静态文件配置
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

# 修改根路由返回HTML页面
@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("templates/index.html")

# 加载本地JSON数据
def load_rag_data() -> Dict[str, Any]:
    loader = DataLoader()
    return {
        'all_spots': loader.get_all_spots(),
        'search_func': loader.search_spots,
        'detail_func': loader.get_spot_details
    }

# 高德地图配置
class GaodeConfig:
    def __init__(self):
        self.api_key = os.getenv('GAODE_API_KEY')
        # 添加环境变量检查
        if not self.api_key:
            raise ValueError("GAODE_API_KEY 环境变量未设置")
        self.base_url = "https://restapi.amap.com/v3"

    def get_location_url(self, city: str, poi: str = None) -> str:
        if poi:
            return f"https://uri.amap.com/search?keywords={poi}&city={city}&callnative=1"
        return f"https://uri.amap.com/search?keywords={city}&city={city}&callnative=1"

# 深度求索模型交互
# async def query_deepseek(prompt: str, context: str) -> str:
#     try:
#         async with httpx.AsyncClient(proxies=os.getenv('HTTP_PROXY')) as client:
#             # 添加调试日志
#             print(f"[DEBUG] 正在请求DeepSeek API，prompt长度: {len(prompt)}，context长度: {len(context)}")
#             print(f"[DEBUG] API_KEY前6位: {os.getenv('DEEPSEEK_API_KEY', '未设置')[:6]}...")
            
#             response = await client.post(
#                 "https://api.deepseek.com/v1/chat/completions",
#                 headers={
#                     "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}", 
#                     "Content-Type": "application/json"
#                 },
#                 json={
#                     "model": "deepseek-reasoner",
#                     "messages": [
#                         {"role": "system", "content": "你是一个旅游助手，需要根据以下数据回答问题：" + context},
#                         {"role": "user", "content": prompt}
#                     ]
#                 },
#                 timeout=30
#             )
#             print(response)

#             # 增强响应日志
#             print(f"[DEBUG] 收到响应状态码: {response.status_code}")
#             print(f"[DEBUG] 响应头: {response.headers}")
            
#             # 检查响应状态
#             if response.status_code != 200:
#                 error_msg = f"API请求失败，状态码：{response.status_code}，响应：{response.text}"
#                 print(f"DeepSeek API Error: {error_msg}")
#                 return f"服务暂时不可用，错误代码：{response.status_code}"

#             response_data = response.json()
#             if 'choices' not in response_data or len(response_data['choices']) == 0:
#                 return "未能生成有效回答，请尝试重新提问"
            
#             return response_data['choices'][0]['message']['content']
            
#     except httpx.RequestError as e:  # 捕获网络请求错误
#         error_detail = f"网络请求失败: {str(e)}" if str(e) else "未知网络错误"
#         print(f"DeepSeek API调用异常：{error_detail}")
#         return "网络连接异常，请检查网络后重试"
#     except json.JSONDecodeError as e:  # 捕获JSON解析错误
#         print(f"响应解析失败: {str(e)}")
#         return "服务响应异常，请稍后再试"
#     except Exception as e:  # 捕获其他未知异常
#         error_type = type(e).__name__
#         print(f"未预期错误 [{error_type}]: {str(e)}")
#         return "系统服务繁忙，请稍后重试"

async def query_deepseek(prompt: str, context: str) -> str:
    async with httpx.AsyncClient() as client:
        print(prompt)
        print(context)
        response = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-reasoner",
                "messages": [
                    {"role": "system", "content": f'你是一个旅游助手，这是已知的参考数据：{context},判断问题合法性，并给用户作出回答'},
                    {"role": "user", "content": f"请根据提供的参考数据回答问题，问题：{prompt}"}
                ]
            },
            timeout=120
        )
        response_data = response.json()
        print(response_data)
        return response_data['choices'][0]['message']['content']
# 添加请求体模型
class QueryRequest(BaseModel):
    prompt: str  # 严格匹配前端发送的JSON字段名

# 修改接口参数接收方式
@app.post("/query")
async def handle_query(request: QueryRequest):  # 使用QueryRequest模型接收请求体
    print(f"收到请求：{request.prompt}")  # 添加请求日志
    rag_data = load_rag_data()
    gaode = GaodeConfig()
    
    # 调用深度求索模型（改用 request.prompt）
    # 动态生成精简上下文
    context = json.dumps({
        'prompt': request.prompt,
        'related_spots': rag_data['search_func'](request.prompt)
    }, ensure_ascii=False)
    answer = await query_deepseek(request.prompt, context)
    
    # 解析地图标记
    while '@map' in answer:
        parts = answer.split('@map', 1)
        before = parts[0]
        remaining = parts[1]
        
        # 提取位置信息
        if ':' in remaining:
            location_part = remaining.split(':', 1)[1]
            if ' ' in location_part:
                location_part = location_part.split(' ', 1)[0]
            city, _, poi = location_part.partition(':')
            city = city.strip()
            poi = poi.strip() if poi else None
        else:
            city = remaining.split(' ', 1)[0].strip()
            poi = None
        
        map_url = gaode.get_location_url(city, poi)
        answer = f"{before}🔍 地图跳转：{map_url} {remaining.split(' ', 1)[1] if ' ' in remaining else ''}"
    
    # 确保最终返回格式包含answer字段
    print(map_url)
    print(f"生成回答：{answer}")  # 添加响应日志
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)