import requests
from typing import List, Dict, Any
from app.config import ConfigManager
from app.exceptions import OpenAIError, ConfigurationError
from app.log_config import setup_logger

logger = setup_logger("openai")
config_manager = ConfigManager()

class OpenAIClient:
    def __init__(self):
        self.config = config_manager.config
    async def fetch_models(self) -> Dict[str, Any]:
        """获取可用的模型列表"""
        try:
            response = requests.get(
                f"{config_manager.get_current_channel_config().base_url}/v1/models",
                headers={"Authorization": f"Bearer {config_manager.get_current_channel_config().api_key}"},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"获取模型列表失败: {e}")
            raise OpenAIError(f"获取模型列表失败: {str(e)}")

    async def get_allowed_models(self) -> List[str]:
        """获取允许使用的模型ID列表"""
        try:
            models_data = await self.fetch_models()
            if not models_data or "data" not in models_data:
                raise OpenAIError("无效的模型数据响应")
            return [model["id"] for model in models_data["data"]]
        except Exception as e:
            logger.error(f"处理模型列表失败: {e}")
            return []

    def get_api_key(self) -> str:
        """获取当前API密钥"""
        return self.config.api_key

    def get_current_model(self) -> str:
        """获取当前使用的模型"""
        return self.config.current_model

    def update_current_model(self, model: str) -> None:
        """更新当前使用的模型"""
        try:
            config_manager.update_current_model(model)
            self.config = config_manager.config
        except Exception as e:
            raise ConfigurationError(f"更新模型失败: {str(e)}")

    def update_current_channel(self, channel: str) -> None:
        """更新当前使用的通道"""
        try:
            config_manager.update_current_channel(channel)
            self.config = config_manager.config
        except Exception as e:
            raise ConfigurationError(f"更新通道失败: {str(e)}")

# 创建全局OpenAI客户端实例
openai_client = OpenAIClient()

# 导出便捷函数
async def fetch_models() -> Dict[str, Any]:
    return await openai_client.fetch_models()

async def get_allowed_models() -> List[str]:
    return await openai_client.get_allowed_models()

def get_api_key() -> str:
    return openai_client.get_api_key()

def get_current_model() -> str:
    return openai_client.get_current_model()

def update_current_model(model: str) -> None:
    openai_client.update_current_model(model)

def update_current_channel(channel: str) -> None:
    openai_client.update_current_channel(channel)
