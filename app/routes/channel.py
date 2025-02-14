from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from typing import List
import json
import httpx

from app.exceptions import InvalidRequestError, NotFoundError, OpenAIError

from app.log_config import setup_logger
from app.models import ChannelInfo, ExportChannelInfo
from app.config import ConfigManager, ChannelConfig
from app.openai import openai_client
from .auth import verify_api_key

logger = setup_logger("channel")
config_manager = ConfigManager()
router = APIRouter()

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
    
    return JSONResponse({
        "success": True,
        "message": f"通道 {channel_name} 的测试结果",
        "results": test_results,
    })
