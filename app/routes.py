from http.client import HTTPException
from fastapi import APIRouter, Request
import os
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from app.log_config import setup_logger
from app.openai import fetch_models, get_allowed_models
from app.openai import base_url
from app.openai import api_key
import httpx
from fastapi import HTTPException
import json


override_model = os.getenv("OVERRIDE_MODEL")
logger = setup_logger("routes")
allowed_models = []
router = APIRouter()


async def initialize_allowed_models():
    global allowed_models
    allowed_models = await get_allowed_models()


class OverrideModelRequest(BaseModel):
    model: str


templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    models = allowed_models
    return templates.TemplateResponse(
        "index.html", {"request": request, "models": models}
    )


@router.get("/v1/models")
async def list_models():
    return await fetch_models()


@router.post("/switch/override_models")
async def switch_override_model(request: OverrideModelRequest):
    global override_model

    if request.model not in allowed_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Allowed models are: {', '.join(allowed_models)}",
        )

    override_model = request.model
    logger.info(f"OVERRIDE_MODEL switched to: {override_model}")
    return {"message": f"OVERRIDE_MODEL successfully switched to {override_model}"}


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Request body is empty")

        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        if override_model:
            body["model"] = override_model

        stream = body.get("stream", False)

        async def event_stream():
            try:
                async with httpx.AsyncClient() as client:
                    async with client.stream(
                        "POST",
                        f"{base_url}/v1/chat/completions",
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
                                print(line)
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
                    f"{base_url}/v1/chat/completions", json=body, headers=headers
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
