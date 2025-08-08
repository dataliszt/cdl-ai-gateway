"""
기본 모델 정의
모든 요청 모델의 기본이 되는 클래스 제공
"""
from pydantic import BaseModel


class SokindBaseModel(BaseModel):
    """모든 Sokind 모델의 기본 클래스"""

    class Config:
        """Pydantic 설정"""
        # 추가 필드 허용 (호환성을 위해)
        extra = "allow"
        # 필드명 별칭 사용 허용
        populate_by_name = True