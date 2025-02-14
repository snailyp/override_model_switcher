from fastapi import APIRouter, Depends
from fastapi.security import APIKeyHeader
from app.log_config import setup_logger
from app.openai import get_api_key
from app.exceptions import AuthenticationError
from app.config import ConfigManager

logger = setup_logger("auth")
config_manager = ConfigManager()
router = APIRouter()
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def verify_api_key(req_api_key: str = Depends(api_key_header)):
    if req_api_key is None:
        raise AuthenticationError("缺少API密钥")
    if req_api_key.startswith("Bearer "):
        req_api_key = req_api_key[7:]
    if req_api_key != get_api_key():
        raise AuthenticationError("无效的API密钥")
    return config_manager.get_current_channel_config().api_key
