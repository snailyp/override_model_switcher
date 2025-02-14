from fastapi import APIRouter
from .auth import router as auth_router
from .channel import router as channel_router
from .chat import router as chat_router
from .model import router as model_router
from .misc import router as misc_router

router = APIRouter()

# 注册所有子路由
router.include_router(misc_router)  # 包含根路由 "/" 所以放在最前面
router.include_router(auth_router)
router.include_router(channel_router)
router.include_router(chat_router)
router.include_router(model_router)
