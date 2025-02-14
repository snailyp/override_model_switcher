from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx

from app.log_config import setup_logger
from app.openai import get_allowed_models, get_current_model
from app.config import ConfigManager
from app.exceptions import OpenAIError

logger = setup_logger("misc")
config_manager = ConfigManager()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    models = await get_allowed_models()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "models": models,
            "current_model": get_current_model(),
            "current_channel": config_manager.config.current_channel,
        },
    )

@router.get("/health_check")
async def health_check():
    return {"status": "healthy", "message": "服务正在运行"}

@router.get("/wallpaper")
async def get_wallpaper():
    wallpaper_api_url = "https://api.suyanw.cn/api/comic/api.php"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(wallpaper_api_url, follow_redirects=True)
            
        if response.status_code == 200:
            final_url = str(response.url)
            async with httpx.AsyncClient() as client:
                img_response = await client.get(final_url)
                
            if img_response.status_code == 200:
                return StreamingResponse(
                    img_response.iter_bytes(),
                    media_type=img_response.headers.get("content-type"),
                )
            raise OpenAIError("获取图片内容失败")
        raise OpenAIError("获取壁纸URL失败")
    except httpx.RequestError as e:
        raise OpenAIError(f"获取壁纸失败: {str(e)}")
