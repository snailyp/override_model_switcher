from fastapi import APIRouter
from app.log_config import setup_logger
from app.openai import openai_client, get_allowed_models
from app.exceptions import InvalidRequestError
from app.models import OverrideModelRequest

# 初始化函数
async def initialize_allowed_models():
    return await get_allowed_models()

logger = setup_logger("model")
router = APIRouter()

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
