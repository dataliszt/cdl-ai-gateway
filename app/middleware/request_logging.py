import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    요청/응답 로깅 미들웨어
    
    모든 HTTP 요청에 대한 상세 로그를 기록:
    - 메소드, 경로, 쿼리
    - 상태코드, 응답시간
    - 클라이언트 IP, User-Agent 등
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("request")

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        # 클라이언트 정보 수집
        client_ip = request.client.host if request.client else None
        fwd_for = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")
        user_agent = request.headers.get("User-Agent")
        referer = request.headers.get("Referer")

        # Request ID 가져오기
        request_id = getattr(request.state, "request_id", "unknown")

        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            self.logger.error(
                "Exception during request processing",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "exception": str(exc)
                },
                exc_info=True
            )
            raise exc
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.logger.info(
                f"{request.method} {request.url.path} - {status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.url.query),
                    "status": status_code,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "client_ip": client_ip,
                    "x_forwarded_for": fwd_for,
                    "x_real_ip": real_ip,
                    "user_agent": user_agent,
                    "referer": referer,
                },
            )

        return response