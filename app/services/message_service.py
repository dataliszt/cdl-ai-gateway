"""
통합 메시지 서비스
비즈니스 로직과 인프라 로직을 연결하는 단일 서비스
"""
import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from app.models.requests import SokindRequest
from app.models.education_models import SokindBaseModel
from app.services.rabbitmq import MessageSender

logger = logging.getLogger(__name__)


class MessageService:
    """
    통합 메시지 서비스
    - 비즈니스 우선순위를 시스템 우선순위로 매핑
    - 교육 타입별 큐 라우팅 규칙 관리
    - RabbitMQ 인프라 추상화
    """
    
    # 비즈니스 우선순위 → 시스템 우선순위 매핑
    PRIORITY_MAPPING = {
        "urgent": settings.priority_high,
        "high": settings.priority_high,
        "normal": settings.priority_medium,
        "medium": settings.priority_medium,
        "low": settings.priority_low,
    }
    
    # 교육 타입별 기본 큐 매핑
    QUEUE_MAPPING = {
        # 기본 교육 타입들 (1-6)
        1: settings.default_queue,
        2: settings.default_queue,
        3: settings.default_queue,
        4: settings.default_queue,
        5: settings.default_queue,
        6: settings.default_queue,
        
        # 정기 리포트
        9: "periodic_report",
    }
    
    def get_queue_for_model(self, model: SokindBaseModel) -> str:
        """모델의 비즈니스 특성에 따라 적절한 큐 결정"""
        edu_type = getattr(model, 'edu_type', None)
        
        if edu_type in self.QUEUE_MAPPING:
            return self.QUEUE_MAPPING[edu_type]
        
        # 동적 큐 결정
        if edu_type == 7:
            request_type = getattr(model, 'request_type', 0)
            if request_type in [1, 2]:
                return "sokind_conversation_generate_response"
            else:
                return "sokind_conversation"
                
        elif edu_type == 8:
            request_type = getattr(model, 'request_type', 0)
            if request_type in [1, 2]:
                return "sokind_demo_generate_response"
            elif request_type in [3, 4]:
                return "sokind_demo_analyze_response"
            else:
                return settings.default_queue
                
        elif edu_type == 10:
            generation_type = getattr(model, 'generation_type', '')
            queue_map = {
                "AUGMENTATION": "V3_PERSONA_GENERATION",
                "QUESTION": "V3_RESPONSE_GENERATION", 
                "REPORT": "V3_CONVERSATION_ANALYSIS_REPORT",
            }
            return queue_map.get(generation_type, settings.default_queue)
        
        return settings.default_queue
    
    def get_priority_for_model(self, model: SokindBaseModel) -> int:
        """모델의 비즈니스 우선순위를 시스템 우선순위로 변환"""
        if hasattr(model, 'get_business_priority'):
            business_priority = model.get_business_priority()
            return self.PRIORITY_MAPPING.get(business_priority, settings.priority_medium)
        
        # 기본값: 교육 타입별 우선순위 
        edu_type = getattr(model, 'edu_type', None)
        if edu_type == 1:
            return settings.priority_high
        elif edu_type == 4:
            return settings.priority_low
        else:
            return settings.priority_medium
    
    def send_message_with_model(
        self,
        model: SokindBaseModel,
        client_ip: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """특화 모델을 사용한 메시지 전송"""
        logger.info(
            f"Sending message with model: {type(model).__name__}",
            extra={
                "request_id": request_id,
                "edu_type": getattr(model, "edu_type", None),
                "business_priority": model.get_business_priority(),
                "processing_type": model.get_processing_type(),
            }
        )
        
        # 큐와 우선순위 결정
        queue = self.get_queue_for_model(model)
        priority = self.get_priority_for_model(model)
        
        # 메시지 바디 생성
        body = model.dict()
        if request_id:
            body["request_id"] = request_id
        if client_ip:
            body["client_ip"] = client_ip
        
        # 실제 전송
        return self._send_to_queue(queue, body, priority, request_id)

    def send_message(
        self,
        request_body: SokindRequest,
        client_ip: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """기존 API 호환성을 위한 메시지 전송"""
        specialized_model = request_body.to_specialized_model()
        return self.send_message_with_model(specialized_model, client_ip, request_id)
    
    def _send_to_queue(
        self, 
        queue: str, 
        body: Dict[str, Any], 
        priority: int, 
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """실제 RabbitMQ 큐로 메시지 전송"""
        try:
            sender = MessageSender()
            
            # 큐가 존재하지 않으면 생성 (Quorum Queue로 생성)
            if not sender.queue_exists(queue):
                # 특정 큐에 대한 커스텀 설정이 필요한 경우 여기에 추가
                queue_args = {}
                
                # 우선순위가 높은 큐는 더 큰 메모리 제한 설정
                if priority >= settings.priority_high:
                    queue_args = {
                        'arguments': {
                            'x-max-in-memory-length': 200000,  # 고우선순위 큐는 더 많은 메시지 보관
                            'x-max-in-memory-bytes': 209715200  # 200MB
                        }
                    }
                
                sender.declare_queue(queue, **queue_args)
                
            # 메시지 전송
            sender.send_message(
                exchange="",
                routing_key=queue,
                body=body,
                priority=priority
            )
            sender.close()
            
            logger.info(
                f"Message sent successfully", 
                extra={
                    "queue": queue,
                    "priority": priority,
                    "request_id": request_id,
                    "edu_type": body.get("edu_type"),
                }
            )
            
            return {
                "message": "success",
                "status": 200,
                "request_id": request_id,
                "queue": queue,
                "priority": priority
            }
            
        except Exception as e:
            logger.error(
                f"Failed to send message: {e}",
                extra={
                    "queue": queue,
                    "request_id": request_id,
                    "edu_type": body.get("edu_type"),
                },
                exc_info=True,
            )
            raise