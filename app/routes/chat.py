from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
import json
import httpx
from typing import Dict, List

from app.log_config import setup_logger
from app.openai import get_current_model
from app.exceptions import InvalidRequestError, OpenAIError
from .auth import verify_api_key
from app.config import ConfigManager
from app.openai import openai_client


logger = setup_logger("chat")
config_manager = ConfigManager()
router = APIRouter()

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


@router.get("/v1/models")
async def list_models():
    return await openai_client.fetch_models()

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
