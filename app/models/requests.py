from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from .education_models import (
    BasicEducationModel,
    FillOutBlankScriptModel, 
    ListenAndRepeatModel,
    KeywordMemorizationModel,
    VirtualActorDialogueV1Model,
    VirtualActorDialogueV2Model,
    VirtualActorDialogueV2ForeignDemoModel,
    PeriodicReportModel,
    VirtualActorDialogueV3AugmentationModel,
    VirtualActorDialogueV3QuestionModel,
    VirtualActorDialogueV3ReportModel,
    EDUCATION_TYPE_MODELS
)


class SokindRequest(BaseModel):
    """
    통합 Sokind 분석 요청 모델
    
    호환성을 위해 모든 필드를 Optional로 유지하면서,
    edu_type에 따라 적절한 모델로 변환 가능
    """
    
    # 공통 필수 필드
    edu_key: int
    edu_type: int
    member_key: int
    
    # 공통 선택 필드
    company_key: Optional[int] = None
    enterprise_key: Optional[int] = None
    store_key: Optional[int] = None
    return_url: Optional[str] = Field(None, alias="returnUrl")
    
    # 기본 교육 타입 (1-6)
    round: Optional[int] = None
    round_id: Optional[str] = None
    user_video_url: Optional[str] = None
    user_audio_url: Optional[str] = None
    user_audio_url_sub: Optional[str] = None
    admin_url: Optional[str] = None
    question: Optional[str] = None
    script: Optional[str] = None
    transcribed_script: Optional[str] = None
    face_cut_time: Optional[List[float]] = None
    training_type: Optional[int] = None
    disallowed_lst: Optional[List[str]] = None
    
    # edu_type 2 전용
    blank_script: Optional[str] = None
    answerArr: Optional[List[Dict[str, Any]]] = None
    
    # edu_type 4 전용
    admin_type: Optional[int] = None
    main_gender: Optional[int] = None
    
    # edu_type 5 전용
    arrKeyword: Optional[List[str]] = Field(None, alias="arr_keyword")
    
    # edu_type 6 전용
    chatList: Optional[List[Dict[str, Any]]] = Field(None, alias="chat_list")
    edu_contents: Optional[Dict[str, Any]] = None
    chat_round: Optional[int] = None
    useFeedList: Optional[List[str]] = Field(None, alias="use_feed_list")
    
    # edu_type 7, 8 (대화형)
    request_type: Optional[int] = None
    request_type_str: Optional[str] = None
    round_int: Optional[int] = None
    edu_title: Optional[str] = None
    edu_subject: Optional[str] = None
    intro: Optional[List[Dict[str, Any]]] = None
    mission: Optional[Dict[str, Any]] = None
    interaction: Optional[Dict[str, Any]] = None
    intent_history: Optional[List[Dict[str, Any]]] = None
    generate_type: Optional[str] = None
    reference_script: Optional[str] = None
    question_history: Optional[List[Dict[str, Any]]] = None
    sp_summary: Optional[str] = None
    sp_info: Optional[Dict[str, Any]] = None
    member_name: Optional[str] = None
    audio_analysis: Optional[Dict[str, Any]] = None
    language: Optional[int] = None
    
    # edu_type 9 (정기 리포트)
    period_report_data_url: Optional[str] = None
    
    # edu_type 10 (v3)
    generation_type: Optional[str] = None
    customer_key: Optional[str] = None
    situation: Optional[str] = None
    customer_data: Optional[Dict[str, Any]] = None
    chat_history_key: Optional[str] = None
    title: Optional[str] = None
    user_role: Optional[str] = None
    reference_data_list: Optional[List[Dict[str, Any]]] = None
    previous_chat_history_data_list: Optional[List[Dict[str, Any]]] = None
    user_answer_text: Optional[str] = None
    augmentation: Optional[Dict[str, Any]] = None
    memory_data_list: Optional[List[Dict[str, Any]]] = None
    round_key: Optional[str] = None
    edu_play_type: Optional[str] = None
    mission_data_list: Optional[List[Dict[str, Any]]] = None
    stop_word_list: Optional[List[str]] = None
    evaluation_item_data: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True
    
    def to_specialized_model(self):
        """
        edu_type에 따라 적절한 특화 모델로 변환
        
        Returns:
            교육 타입에 맞는 특화된 모델 인스턴스
        """
        # edu_type 10 (V3)의 경우 generation_type에 따라 세분화
        if self.edu_type == 10:
            v3_models = {
                "AUGMENTATION": VirtualActorDialogueV3AugmentationModel,
                "QUESTION": VirtualActorDialogueV3QuestionModel,
                "REPORT": VirtualActorDialogueV3ReportModel,
            }
            model_class = v3_models.get(self.generation_type, VirtualActorDialogueV3AugmentationModel)
            return model_class(**self.dict())
        
        # 일반 교육 타입들
        model_class = EDUCATION_TYPE_MODELS.get(self.edu_type, BasicEducationModel)
        return model_class(**self.dict())
    
    @validator("edu_type")
    def validate_edu_type(cls, v):
        """edu_type 유효성 검사"""
        if v not in range(1, 11):
            raise ValueError("edu_type must be between 1 and 10")
        return v