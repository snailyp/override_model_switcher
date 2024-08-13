from http.client import HTTPException
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from app.log_config import setup_logger
from app.openai import (
    fetch_models,
    get_allowed_models,
    get_api_key,
    get_current_config,
    get_current_model,
)
import httpx
from fastapi import HTTPException
import json
from starlette.status import HTTP_403_FORBIDDEN
from typing import List
from app.openai import config

override_model = get_current_model()
logger = setup_logger("routes")
allowed_models = []
router = APIRouter()
# 创建 API 密钥头部验证器
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
templates = Jinja2Templates(directory="templates")


class OverrideModelRequest(BaseModel):
    model: str


class ChannelInfo(BaseModel):
    channel_name: str
    base_url: str
    api_key: str


async def switch_api_channel(channel_name):
    global allowed_models
    with open("config.json", "r+") as f:
        config = json.load(f)
        if channel_name in config["channels"]:
            config["current_channel"] = channel_name
            f.seek(0)
            json.dump(config, f, indent=2)
            f.truncate()
            allowed_models = await get_allowed_models()
            return True
    return False


# 验证 API 密钥的函数
async def verify_api_key(req_api_key: str = Depends(api_key_header)):
    if req_api_key is None:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Missing API Key")

    # 移除 "Bearer " 前缀（如果存在）
    if req_api_key.startswith("Bearer "):
        req_api_key = req_api_key[7:]

    if req_api_key != get_api_key():
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key")
    return get_current_config()["api_key"]


async def initialize_allowed_models():
    global allowed_models
    allowed_models = await get_allowed_models()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    models = allowed_models
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "models": models,
            "current_model": config()["current_model"],
            "current_channel": config()["current_channel"],
        },
    )


@router.get("/health_check")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}


@router.get("/v1/models")
async def list_models():
    return await fetch_models()


@router.post("/switch/override_model")
async def switch_override_model(request: OverrideModelRequest):
    global override_model

    if request.model not in allowed_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Allowed models are: {', '.join(allowed_models)}",
        )

    override_model = request.model
    with open("config.json", "r+") as f:
        config = json.load(f)
        config["current_model"] = request.model
        f.seek(0)
        json.dump(config, f, indent=2)
        f.truncate()
    logger.info(f"OVERRIDE_MODEL switched to: {override_model}")
    return {"message": f"OVERRIDE_MODEL successfully switched to {override_model}"}


@router.post("/v1/chat/completions")
async def chat_completions(request: Request, api_key: str = Depends(verify_api_key)):
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Request body is empty")

        try:
            body = json.loads(body)
            logger.info(f"Request body: {body}")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        if body["model"] == "override" and override_model:
            body["model"] = override_model

        stream = body.get("stream", False)

        async def event_stream():
            try:
                timeout = httpx.Timeout(timeout=10,read=120)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream(
                        "POST",
                        f"{get_current_config()['base_url']}/v1/chat/completions",
                        json=body,
                        headers=headers,
                    ) as response:
                        if response.status_code != 200:
                            logger.warning(
                                f"API key {api_key} failed with status {response.status_code}"
                            )
                            yield f"data: {json.dumps({'error': 'API request failed'})}\n\n"
                            return
                        async for line in response.aiter_lines():
                            if line:
                                yield f"{line}\n\n"
            except Exception as e:
                logger.error(f"Error in event stream: {str(e)}")
                yield f"data: {json.dumps({'error': 'Stream processing error'})}\n\n"

        if stream:
            return StreamingResponse(event_stream(), media_type="text/event-stream")
        else:
            # 非流式处理逻辑
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{get_current_config()['base_url']}/v1/chat/completions",
                    json=body,
                    headers=headers,
                )

            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except httpx.RequestError as e:
        logger.error(f"Error proxying request to OpenAI: {str(e)}")
        raise HTTPException(status_code=502, detail="Error proxying request to OpenAI")
    except Exception as e:
        logger.error(f"Unexpected error in chat_completions: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/get_channels", response_model=List[str])
async def get_channels():
    return list(config()["channels"].keys())


@router.get("/get_channel_config/{channel_name}")
async def get_channel_config(channel_name: str):
    if channel_name in config()["channels"]:
        return config()["channels"][channel_name]
    raise HTTPException(status_code=404, detail="Channel not found")


@router.delete("/delete_channel/{channel_name}")
async def delete_channel(channel_name: str):
    current_config = config()
    if channel_name not in current_config["channels"]:
        raise HTTPException(status_code=404, detail="Channel not found")

    if channel_name == current_config["current_channel"]:
        raise HTTPException(
            status_code=400, detail="Cannot delete the current active channel"
        )

    del current_config["channels"][channel_name]

    # 保存更新后的配置
    with open("config.json", "w") as f:
        json.dump(current_config, f, indent=2)

    return {"message": f"Channel {channel_name} deleted successfully"}


@router.post("/add_channel")
async def add_channel(request: Request):
    data = await request.json()
    channel_name = data.get("channel_name")
    base_url = data.get("base_url")
    api_key = data.get("api_key")

    if not all([channel_name, base_url, api_key]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    if channel_name in config()["channels"]:
        raise HTTPException(status_code=400, detail="Channel already exists")
    current_config = config()
    current_config["channels"][channel_name] = {
        "base_url": base_url,
        "api_key": api_key,
    }

    # 保存更新后的配置
    with open("config.json", "w") as f:
        f.seek(0)
        json.dump(current_config, f, indent=2)
        f.truncate()

    return {"message": f"Channel {channel_name} added successfully"}


@router.post("/bulk_add_channels")
async def bulk_add_channels(channels: List[ChannelInfo]):
    current_config = config()
    added_channels = []
    existing_channels = []

    for channel in channels:
        if channel.channel_name not in current_config["channels"]:
            current_config["channels"][channel.channel_name] = {
                "base_url": channel.base_url,
                "api_key": channel.api_key,
            }
            added_channels.append(channel.channel_name)
        else:
            existing_channels.append(channel.channel_name)

    # 保存更新后的配置
    with open("config.json", "w") as f:
        json.dump(current_config, f, indent=2)

    return {
        "message": f"Added {len(added_channels)} channels successfully",
        "added_channels": added_channels,
        "existing_channels": existing_channels,
    }


@router.post("/switch_channel")
async def switch_channel(request: Request):
    data = await request.json()
    channel = data.get("channel")
    switch_flag = await switch_api_channel(channel)
    if switch_flag:
        return JSONResponse(
            {"success": True, "message": f"Switched to channel {channel}"}
        )
    return JSONResponse(
        {"success": False, "message": "Invalid channel"}, status_code=400
    )
