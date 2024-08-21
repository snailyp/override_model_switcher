from http.client import HTTPException
from fastapi import APIRouter, Request, Depends
from fastapi.responses import (
    PlainTextResponse,
    StreamingResponse,
    JSONResponse,
    HTMLResponse,
)
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


# 添加这个新的模型用于导出
class ExportChannelInfo(BaseModel):
    channel_name: str
    base_url: str
    api_key: str


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
            test_results = config["channels"][channel_name].get("test_results", {})
            return {"success": True, "test_results": test_results}

    return {"success": False, "message": "Invalid channel"}


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
                timeout = httpx.Timeout(timeout=10, read=120)
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
    global override_model
    if channel_name not in current_config["channels"]:
        raise HTTPException(status_code=404, detail="Channel not found")

    if channel_name == "default":
        raise HTTPException(status_code=400, detail="Cannot delete the default channel")
    if channel_name == current_config["current_channel"]:
        current_config["current_channel"] = "default"
        current_config["current_model"] = "gpt-4o"
        override_model = "gpt-4o"

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
    switch_result = await switch_api_channel(channel)
    if switch_result["success"]:
        return JSONResponse(
            {
                "success": True,
                "message": f"Switched to channel {channel}",
                "data": switch_result["test_results"],
            },
        )
    return JSONResponse(
        {"success": False, "message": "Invalid channel"}, status_code=400
    )


@router.get("/export_channels", response_model=List[ExportChannelInfo])
async def export_channels(api_key: str = Depends(verify_api_key)):
    current_config = config()
    channels = current_config["channels"]

    export_data = [
        ExportChannelInfo(
            channel_name=name, base_url=info["base_url"], api_key=info["api_key"]
        )
        for name, info in channels.items()
    ]

    return JSONResponse(content=[channel.dict() for channel in export_data])


@router.get("/export_models", response_class=PlainTextResponse)
async def export_models():
    models = await get_allowed_models()
    models_str = ",".join(models)
    return models_str


@router.post("/test_all_models")
async def test_all_models(request: Request):
    data = await request.json()
    channel = data.get("channel")

    # 检查渠道是否存在
    current_config = config()
    if channel not in current_config["channels"]:
        return JSONResponse(
            {"success": False, "message": "Invalid channel"}, status_code=400
        )

    # 获取渠道配置信息
    channel_config = current_config["channels"][channel]
    headers = {
        "Authorization": f"Bearer {channel_config['api_key']}",
        "Content-Type": "application/json",
    }

    # 假设我们获取模型列表的 API
    models_response = await fetch_models()
    if not models_response:
        return JSONResponse(
            {"success": False, "message": "Failed to fetch models"}, status_code=500
        )

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
                    f"{channel_config['base_url']}/v1/chat/completions",
                    json=body,
                    headers=headers,
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                test_results[model["id"]] = "success"
                                break
                    else:
                        test_results[model["id"]] = (
                            f"failed: HTTP {response.status_code}"
                        )
            except Exception as e:
                test_results[model["id"]] = f"failed: {str(e)}"

    # 保存测试结果到 config.json
    current_config["channels"][channel]["test_results"] = test_results
    with open("config.json", "w") as f:
        json.dump(current_config, f, indent=2)

    return JSONResponse(
        {
            "success": True,
            "message": f"Test results for channel {channel}",
            "results": test_results,
        }
    )


@router.get("/wallpaper")
async def get_wallpaper():
    wallpaper_api_url = "https://api.suyanw.cn/api/comic/api.php"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(wallpaper_api_url, follow_redirects=True)

        if response.status_code == 200:
            # 获取最终重定向后的URL
            final_url = str(response.url)

            # 创建一个新的请求来获取实际的图片内容
            async with httpx.AsyncClient() as client:
                img_response = await client.get(final_url)

            if img_response.status_code == 200:
                # 返回图片内容，而不是重定向
                return StreamingResponse(
                    img_response.iter_bytes(),
                    media_type=img_response.headers.get("content-type"),
                )
            else:
                raise HTTPException(
                    status_code=img_response.status_code,
                    detail="Failed to fetch image content",
                )
        else:
            raise HTTPException(
                status_code=response.status_code, detail="Failed to fetch wallpaper URL"
            )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching wallpaper: {str(e)}"
        )
