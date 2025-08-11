"""
API 라우터 모듈
통합된 API 엔드포인트 및 라우팅 정의
"""
import logging
import time
from fastapi import APIRouter, Request, Body, status
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError

from app.models.requests import SokindRequest
from app.services.message_service import MessageService
from app.services.rabbitmq import get_rabbitmq_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status/")
def health_check() -> Response:
    """서비스 상태 확인"""
    return Response(
        content="<html><body><h1>CDL Gateway - Health Check OK</h1></body></html>", 
        media_type="text/html"
    )


@router.get("/status/rabbitmq")
def rabbitmq_status():
    """RabbitMQ 클러스터 상태 확인"""
    try:
        client = get_rabbitmq_client()
        cluster_status = client.get_cluster_status()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "cluster": cluster_status,
                "timestamp": int(time.time())
            }
        )
    except Exception as e:
        logger.error(f"Failed to get RabbitMQ cluster status: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": int(time.time())
            }
        )




@router.post(
    "/",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "message": "success",
                        "status": 200,
                        "request_id": "12345678-1234-1234-1234-123456789012"
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Validation error",
                        "message": "edu_type is missing",
                        "status": 422
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error",
                        "message": "An unexpected error occurred",
                        "status": 500
                    }
                }
            }
        },
    },
    tags=["sokind_analysis"],
    summary="Sokind 분석 요청 처리",
    description="다양한 교육 타입의 Sokind 분석 요청을 처리하고 RabbitMQ로 전송합니다."
)
async def sokind(request: Request, request_body: SokindRequest = Body()):
    """
    Sokind 분석 요청 엔드포인트
    
    - 교육 타입별 특화 모델로 변환하여 처리
    - Request ID 추적 지원
    - 클라이언트 IP 추출 및 포함
    """
    try:
        # 클라이언트 IP 추출
        client_ip = request.client.host if request.client else None
        fwd_for = request.headers.get("X-Forwarded-For")
        if fwd_for:
            client_ip = fwd_for.split(",")[0].strip()

        # Request ID 가져오기
        request_id = getattr(request.state, "request_id", None)
        
        # 특화 모델로 변환 (자동 검증 포함)
        specialized_model = request_body.to_specialized_model()
        
        # 메시지 서비스를 통해 전송
        message_service = MessageService()
        result = message_service.send_message_with_model(
            model=specialized_model,
            client_ip=client_ip,
            request_id=request_id
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Error processing sokind request: {str(e)}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "edu_type": getattr(request_body, "edu_type", None),
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "message": str(e),
                "status": 500
            },
        )