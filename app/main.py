"""
CDL Gateway 애플리케이션 진입점
FastAPI 애플리케이션 초기화 및 실행
"""
import os
import sys
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

# AWS Secrets Manager에서 환경변수 로드 (config 임포트 전에 실행)
try:
    from app.core.secrets import load_secrets_to_env
    print("🔐 AWS Secrets Manager 환경변수 로드 시도...")
    if load_secrets_to_env():
        print("✅ Secrets Manager 환경변수 로드 성공")
    else:
        print("⚠️ Secrets Manager 로드 실패 - 로컬 환경변수 사용")
except Exception as e:
    print(f"⚠️ Secrets Manager 모듈 로드 실패: {e}")
    print("로컬 환경변수(.env) 사용")

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.api.routes import router


def create_app() -> FastAPI:
    """
    FastAPI 애플리케이션 팩토리
    
    - 로깅 설정
    - 미들웨어 등록
    - 라우터 등록
    - 예외 핸들러 등록
    - OpenAPI 스키마 커스터마이징
    """
    # 로깅 설정
    configure_logging(settings.log_level)
    
    # FastAPI 앱 생성
    app = FastAPI(
        title=settings.app_name,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 미들웨어 등록 (순서 중요: Request ID → Request Logging)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    # 라우터 포함
    app.include_router(router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """요청 유효성 검사 예외 처리"""
        errors = []
        for error in exc.errors():
            if error["msg"] == "field required":
                errors.append({
                    "loc": error["loc"],
                    "msg": "is missing",
                    "type": error["type"]
                })
            else:
                errors.append({
                    "loc": error["loc"],
                    "msg": error["msg"],
                    "type": error["type"]
                })

        error_message = f'{errors[0]["loc"][1]} {errors[0]["msg"]}' if errors else "Validation error"
        
        return JSONResponse(
            content={
                "detail": "Validation error",
                "message": error_message,
                "status": 422,
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def custom_openapi():
        """커스텀 OpenAPI 스키마"""
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=settings.app_name,
            version="1.0.0",
            description="크디랩 통합 AI 분석 게이트웨이 - 클라이언트 서비스용 API",
            routes=app.routes,
        )
        
        # 커스텀 로고 추가
        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png",
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    return app


# 애플리케이션 인스턴스 생성
app = create_app()