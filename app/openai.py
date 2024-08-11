from dotenv import load_dotenv
import os
import requests
import json

from app.log_config import setup_logger


logger = setup_logger("openai")
# 加载 .env 文件中的环境变量
load_dotenv()


# 加载配置
def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        config_json = {
            "channels": {
                "default": {
                    "base_url": os.getenv("DEFAULT_BASE_URL"),
                    "api_key": os.getenv("DEFAULT_API_KEY"),
                    "model": os.getenv("DEFAULT_MODEL"),
                }
            },
            "current_channel": "default",
            "current_model": "gpt-4o",
            "api_key": os.getenv("DEFAULT_API_KEY")
        }
        
        with open("config.json", "w") as f:
            json.dump(config_json, f, indent=2)
        return config_json
        


def config():
    return load_config()


def get_current_config():
    current_channel = config()["current_channel"]
    return config()["channels"][current_channel]

def get_api_key():
    return config()["api_key"]

def get_current_model():
    return config()["current_model"]


async def fetch_models():
    # 发送 GET 请求到 OpenAI API 以获取模型列表
    try:
        response = requests.get(
            f"{get_current_config()['base_url']}/v1/models",
            headers={"Authorization": f"Bearer {get_current_config()['api_key']}"},
        )
        response.raise_for_status()  # 检查请求是否成功
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        return None


async def get_allowed_models():
    models_data = await fetch_models()
    # 检查获取的数据是否有效
    if models_data and "data" in models_data:
        return [model["id"] for model in models_data["data"]]
    return []
