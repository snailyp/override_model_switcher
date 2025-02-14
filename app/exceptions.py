from typing import Any, Dict, Optional
from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

class AppBaseException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class InvalidRequestError(AppBaseException):
    def __init__(self, detail: str = "无效的请求"):
        super().__init__(status_code=HTTP_400_BAD_REQUEST, detail=detail)

class AuthenticationError(AppBaseException):
    def __init__(self, detail: str = "认证失败"):
        super().__init__(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class ForbiddenError(AppBaseException):
    def __init__(self, detail: str = "访问被拒绝"):
        super().__init__(status_code=HTTP_403_FORBIDDEN, detail=detail)

class NotFoundError(AppBaseException):
    def __init__(self, detail: str = "资源未找到"):
        super().__init__(status_code=HTTP_404_NOT_FOUND, detail=detail)

class InternalServerError(AppBaseException):
    def __init__(self, detail: str = "服务器内部错误"):
        super().__init__(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class OpenAIError(AppBaseException):
    def __init__(self, detail: str = "OpenAI API 调用失败"):
        super().__init__(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class ConfigurationError(AppBaseException):
    def __init__(self, detail: str = "配置错误"):
        super().__init__(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
