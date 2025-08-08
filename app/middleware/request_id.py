import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    각 요청에 고유한 ID를 할당하는 미들웨어
    
    X-Request-ID 헤더가 있으면 사용하고, 없으면 새로 생성
    응답에도 X-Request-ID 헤더 추가
    """
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response