"""
기본 모델 정의
모든 요청 모델의 기본이 되는 클래스 제공
"""
from typing import Optional, List
from pydantic import BaseModel


class SokindBaseModel(BaseModel):
    """모든 Sokind 모델의 기본 클래스 - 순수 비즈니스 로직만 포함"""

    class Config:
        """Pydantic 설정"""
        # 추가 필드 허용 (호환성을 위해)
        extra = "allow"
        # 필드명 별칭 사용 허용
        populate_by_name = True
    
    def get_business_priority(self) -> str:
        """
        비즈니스 우선순위 반환
        - urgent: 즉시 처리 필요
        - high: 높은 우선순위
        - normal: 일반 우선순위  
        - low: 낮은 우선순위
        """
        return "normal"  # 기본값
    
    def get_required_fields(self) -> List[str]:
        """비즈니스 로직상 필수 필드 목록"""
        return []
    
    def get_processing_type(self) -> str:
        """
        처리 방식 반환
        - real_time: 실시간 처리
        - batch: 배치 처리
        - scheduled: 스케줄링 처리
        """
        return "real_time"  # 기본값