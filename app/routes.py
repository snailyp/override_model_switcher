from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.security import APIKeyHeader
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List
import httpx
import json

from app.log_config import setup_logger
from app.openai import (
    openai_client,
    get_allowed_models,
    get_api_key,
    get_current_model,
)
from app.config import ConfigManager, ChannelConfig
from app.exceptions import (
    InvalidRequestError,
    AuthenticationError,
    NotFoundError,
    OpenAIError,
)

logger = setup_logger("routes")
config_manager = ConfigManager()
router = APIRouter()
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
templates = Jinja2Templates(directory="templates")

# 数据模型
class ChannelInfo(BaseModel):
    channel_name: str
    base_url: str
    api_key: str

class OverrideModelRequest(BaseModel):
    model: str

class ExportChannelInfo(BaseModel):
    channel_name: str
    base_url: str
    api_key: str

# 辅助函数
def merge_consecutive_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not messages:
        return []
    merged_messages = [messages[0]]
    for msg in messages[1:]:
        if msg["role"] == merged_messages[-1]["role"]:
            merged_messages[-1]["content"] += "\n\n" + msg["content"]
        else:
            merged_messages.append(msg)
    return merged_messages

# 认证依赖
async def verify_api_key(req_api_key: str = Depends(api_key_header)):
    if req_api_key is None:
        raise AuthenticationError("缺少API密钥")
    if req_api_key.startswith("Bearer "):
        req_api_key = req_api_key[7:]
    if req_api_key != get_api_key():
        raise AuthenticationError("无效的API密钥")
    return get_api_key()

# 初始化函数
async def initialize_allowed_models():
    return await get_allowed_models()

# 路由处理
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

@router.get("/v1/models")
async def list_models():
    return await openai_client.fetch_models()

@router.post("/switch/override_model")
async def switch_override_model(request: OverrideModelRequest):
    allowed_models = await get_allowed_models()
    if request.model not in allowed_models:
        raise InvalidRequestError(f"无效的模型。允许的模型有: {', '.join(allowed_models)}")
    
    openai_client.update_current_model(request.model)
    logger.info(f"已切换到模型: {request.model}")
    return {"message": f"成功切换到模型 {request.model}"}

@router.post("/v1/chat/completions")
async def chat_completions(request: Request, api_key: str = Depends(verify_api_key)):
    try:
        body = await request.body()
        if not body:
            raise InvalidRequestError("请求体为空")

        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            raise InvalidRequestError("无效的JSON格式")

        current_config = config_manager.get_current_channel_config()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        if body["model"] == "override":
            body["model"] = get_current_model()

        if any(model_type in body["model"] for model_type in ["c35s", "c3o", "claude"]):
            messages = body.get("messages", [])
            body["messages"] = merge_consecutive_messages(messages)

        stream = body.get("stream", False)
        
        async def event_stream():
            try:
                timeout = httpx.Timeout(timeout=10, read=120)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream(
                        "POST",
                        f"{current_config.base_url}/v1/chat/completions",
                        json=body,
                        headers=headers,
                    ) as response:
                        if response.status_code != 200:
                            logger.warning(f"API请求失败，状态码: {response.status_code}")
                            yield f"data: {json.dumps({'error': 'API请求失败'})}\n\n"
                            return
                        async for line in response.aiter_lines():
                            if line:
                                yield f"{line}\n\n"
            except Exception as e:
                logger.error(f"流处理错误: {str(e)}")
                yield f"data: {json.dumps({'error': '流处理错误'})}\n\n"

        if stream:
            return StreamingResponse(event_stream(), media_type="text/event-stream")
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=10, read=120)) as client:
            response = await client.post(
                f"{current_config.base_url}/v1/chat/completions",
                json=body,
                headers=headers,
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
            
    except Exception as e:
        logger.error(f"处理聊天完成请求时出错: {str(e)}")
        raise OpenAIError(str(e))

@router.get("/get_channels", response_model=List[str])
async def get_channels():
    return list(config_manager.config.channels.keys())

@router.get("/get_channel_config/{channel_name}")
async def get_channel_config(channel_name: str):
    if channel_name not in config_manager.config.channels:
        raise NotFoundError(f"通道 {channel_name} 不存在")
    return config_manager.config.channels[channel_name]

@router.delete("/delete_channel/{channel_name}")
async def delete_channel(channel_name: str):
    if channel_name not in config_manager.config.channels:
        raise NotFoundError(f"通道 {channel_name} 不存在")
    if channel_name == "default":
        raise InvalidRequestError("不能删除默认通道")
    
    if channel_name == config_manager.config.current_channel:
        config_manager.update_current_channel("default")
        openai_client.update_current_model("gpt-4o")
    
    channels = config_manager.config.channels
    del channels[channel_name]
    config_manager.save_config()
    
    return {"message": f"成功删除通道 {channel_name}"}

@router.post("/add_channel")
async def add_channel(channel_info: ChannelInfo):
    if channel_info.channel_name in config_manager.config.channels:
        raise InvalidRequestError("通道已存在")
    
    config_manager.config.channels[channel_info.channel_name] = ChannelConfig(
        base_url=channel_info.base_url,
        api_key=channel_info.api_key
    )
    config_manager.save_config()
    
    return {"message": f"成功添加通道 {channel_info.channel_name}"}

@router.post("/bulk_add_channels")
async def bulk_add_channels(channels: List[ChannelInfo]):
    added_channels = []
    existing_channels = []
    
    for channel in channels:
        if channel.channel_name not in config_manager.config.channels:
            config_manager.config.channels[channel.channel_name] = ChannelConfig(
                base_url=channel.base_url,
                api_key=channel.api_key
            )
            added_channels.append(channel.channel_name)
        else:
            existing_channels.append(channel.channel_name)
    
    config_manager.save_config()
    
    return {
        "message": f"成功添加 {len(added_channels)} 个通道",
        "added_channels": added_channels,
        "existing_channels": existing_channels,
    }

@router.post("/switch_channel")
async def switch_channel(request: Request):
    try:
        body = await request.json()
        channel_name = body.get("channel_name")
        
        if not channel_name:
            raise InvalidRequestError("缺少 channel_name 参数")
            
        if channel_name not in config_manager.config.channels:
            raise NotFoundError(f"通道 {channel_name} 不存在")
            
        config_manager.update_current_channel(channel_name)
        return JSONResponse({
            "success": True,
            "message": f"已切换到通道 {channel_name}",
        })
    except json.JSONDecodeError:
        raise InvalidRequestError("无效的JSON格式")
    except Exception as e:
        raise InvalidRequestError(str(e))

@router.get("/export_channels", response_model=List[ExportChannelInfo])
async def export_channels(api_key: str = Depends(verify_api_key)):
    channels = config_manager.config.channels
    export_data = [
        ExportChannelInfo(
            channel_name=name,
            base_url=info.base_url,
            api_key=info.api_key
        )
        for name, info in channels.items()
    ]
    return JSONResponse(content=[channel.model_dump() for channel in export_data])

@router.get("/export_models")
async def export_models():
    models = await get_allowed_models()
    return ",".join(models)

@router.post("/test_all_models")
async def test_all_models(channel_name: str):
    if channel_name not in config_manager.config.channels:
        raise NotFoundError(f"通道 {channel_name} 不存在")
    
    channel_config = config_manager.config.channels[channel_name]
    headers = {
        "Authorization": f"Bearer {channel_config.api_key}",
        "Content-Type": "application/json",
    }
    
    models_response = await openai_client.fetch_models()
    if not models_response:
        raise OpenAIError("获取模型列表失败")
    
    models = models_response["data"]
    test_results = {}
    
    async with httpx.AsyncClient() as client:
        for model in models:
            body = {
                "model": model["id"],
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
            }
            
            try:
                async with client.stream(
                    "POST",
                        f"{channel_config.base_url}/v1/chat/completions",
                    json=body,
                    headers=headers,
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                test_results[model["id"]] = "success"
                                break
                    else:
                        test_results[model["id"]] = f"failed: HTTP {response.status_code}"
            except Exception as e:
                test_results[model["id"]] = f"failed: {str(e)}"
    
    # 由于test_results不是ChannelConfig的一部分，我们需要将其存储在其他地方
    # 或者暂时移除这个功能，因为它不符合ChannelConfig的数据模型
    # TODO: 考虑创建一个单独的存储来保存测试结果
    config_manager.save_config()
    
    return JSONResponse({
        "success": True,
        "message": f"通道 {channel_name} 的测试结果",
        "results": test_results,
    })

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
