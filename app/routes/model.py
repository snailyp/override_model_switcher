from fastapi import APIRouter
from fastapi.responses import JSONResponse
import httpx
from app.log_config import setup_logger
from app.openai import openai_client, get_allowed_models
from app.exceptions import InvalidRequestError
from app.models import OverrideModelRequest
from app.config import ConfigManager

# 初始化函数
async def initialize_allowed_models():
    return await get_allowed_models()

logger = setup_logger("model")
router = APIRouter()

@router.get("/get_current_model")
async def get_current_model():
    return {"current_model": openai_client.get_current_model()}

@router.post("/switch/override_model")
async def switch_override_model(request: OverrideModelRequest):
    allowed_models = await get_allowed_models()
    if request.model not in allowed_models:
        raise InvalidRequestError(f"无效的模型。允许的模型有: {', '.join(allowed_models)}")
    
    openai_client.update_current_model(request.model)
    logger.info(f"已切换到模型: {request.model}")
    return {"message": f"成功切换到模型 {request.model}"}

@router.get("/export_models")
async def export_models():
    models = await get_allowed_models()
    return ",".join(models)

@router.post("/test_model")
async def test_model(request: OverrideModelRequest):
    config_manager = ConfigManager()
    channel_name = config_manager.config.current_channel
    channel_config = config_manager.config.channels[channel_name]
    
    headers = {
        "Authorization": f"Bearer {channel_config.api_key}",
        "Content-Type": "application/json",
    }
    
    body = {
        "model": request.model,
        "messages": [{"role": "user", "content": "hi"}],
        "stream": True,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{channel_config.base_url}/v1/chat/completions",
                json=body,
                headers=headers,
            ) as response:
                if response.status_code == 200:
                    async for line in response.aiter_lines():
                        if line:
                            return JSONResponse({
                                "available": True,
                                "message": f"模型 {request.model} 可用"
                            })
                            break
                else:
                    return JSONResponse({
                        "available": False,
                        "message": f"HTTP错误: {response.status_code}"
                    })
    except Exception as e:
        return JSONResponse({
            "available": False,
            "message": str(e)
        })
