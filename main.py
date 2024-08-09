from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import initialize_allowed_models, router
import uvicorn
from starlette.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_allowed_models()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，您可以根据需要限制特定源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
