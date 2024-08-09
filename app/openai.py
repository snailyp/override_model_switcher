from dotenv import load_dotenv
import os
import requests

from app.log_config import setup_logger

# 加载 .env 文件中的环境变量
load_dotenv()
# 从 .env 文件中获取 API URL 和 API 密钥
base_url = os.getenv("BASE_URL")
api_key = os.getenv("API_KEY")
logger = setup_logger("openai")

async def fetch_models():
    # 发送 GET 请求到 OpenAI API 以获取模型列表
    try:
        response = requests.get(
            f"{base_url}/v1/models", headers={"Authorization": f"Bearer {api_key}"}
        )
        response.raise_for_status()  # 检查请求是否成功
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        return None

async def get_allowed_models():
    models_data = await fetch_models()
    # 检查获取的数据是否有效
    if models_data and 'data' in models_data:
        return [model['id'] for model in models_data['data']]
    return []
