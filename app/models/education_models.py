"""
교육 타입별 요청 모델 정의
각 교육 타입별로 특화된 요청 모델 클래스 제공
"""
from typing import Optional, List, Dict, Any
from pydantic import validator, Field
from .base import SokindBaseModel


class BasicEducationModel(SokindBaseModel):
    """기본 응대 교육 모델 (edu_type = 1)"""
    edu_type: int
    edu_key: int
    member_key: int
    return_url: Optional[str] = Field(None, alias="returnUrl")
    round: Optional[int] = 0
    user_video_url: Optional[str] = ""
    user_audio_url: Optional[str] = ""
    script: Optional[str] = ""
    transcribed_script: Optional[str] = ""
    face_cut_time: Optional[List[float]] = None
    training_type: Optional[int] = 1
    company_key: Optional[int] = 0 
    round_id: Optional[str] = None
    enterprise_key: Optional[int] = 0  
    disallowed_lst: Optional[List[str]] = []
    
    # Deprecated fields
    admin_url: Optional[str] = ""
    question: Optional[str] = ""
    
    @validator("face_cut_time")
    def validate_face_cut_time(cls, v):
        if v and any(x < 0 for x in v):
            raise ValueError("face_cut_time values must be greater than or equal to 0")
        return v
    
    def get_business_priority(self) -> str:
        """비즈니스 우선순위 결정"""
        if self.edu_type == 1:
            return "high"  # 기본 응대 교육은 높은 우선순위
        return "normal"
    
    def get_required_fields(self) -> List[str]:
        """필수 비즈니스 필드"""
        return ["edu_key", "member_key", "edu_type"]
    
    def get_processing_type(self) -> str:
        """실시간 처리 필요"""
        return "real_time"
    
    def is_video_analysis_required(self) -> bool:
        """비디오 분석이 필요한지 비즈니스 로직"""
        return bool(self.user_video_url and self.face_cut_time)
    
    def is_script_analysis_required(self) -> bool:
        """스크립트 분석이 필요한지 비즈니스 로직"""
        return bool(self.script or self.transcribed_script)


class FillOutBlankScriptModel(BasicEducationModel):
    """빈칸 채우기 교육 모델 (edu_type: 2)"""
    blank_script: Optional[str] = None
    answerArr: Optional[List[Dict[str, Any]]] = None
    
    def get_required_fields(self) -> List[str]:
        """빈칸 채우기 필수 필드"""
        base_fields = super().get_required_fields()
        return base_fields + ["blank_script", "answerArr"]
    
    def has_valid_answers(self) -> bool:
        """정답 배열이 유효한지 검증"""
        return bool(self.answerArr and len(self.answerArr) > 0)


class ListenAndRepeatModel(BasicEducationModel):
    """듣고 따라하기 교육 모델 (edu_type: 4)"""
    admin_type: Optional[int] = None       
    user_audio_url_sub: Optional[str] = ""
    main_gender: Optional[int] = None
    
    def get_business_priority(self) -> str:
        """듣고 따라하기는 낮은 우선순위"""
        return "low"
    
    def get_processing_type(self) -> str:
        """배치 처리 가능"""
        return "batch"
    
    def requires_gender_analysis(self) -> bool:
        """성별 분석이 필요한지"""
        return self.main_gender is not None


class KeywordMemorizationModel(BasicEducationModel):
    """키워드 말하기 교육 모델 (edu_type: 5)"""
    arrKeyword: Optional[List[str]] = Field(None, alias="arr_keyword")
    
    def get_required_fields(self) -> List[str]:
        """키워드 필수 필드"""
        base_fields = super().get_required_fields()
        return base_fields + ["arrKeyword"]
    
    def get_keyword_count(self) -> int:
        """키워드 개수 반환"""
        return len(self.arrKeyword) if self.arrKeyword else 0
    
    
class VirtualActorDialogueV1Model(BasicEducationModel):
    """가상 고객 대화 교육 모델 (edu_type: 6)"""
    chatList: Optional[List[Dict[str, Any]]] = Field(None, alias="chat_list")
    edu_contents: Optional[Dict[str, Any]] = None
    chat_round: Optional[int] = None        
    useFeedList: Optional[List[str]] = Field(None, alias="use_feed_list")
    
    def get_business_priority(self) -> str:
        """대화형 교육은 높은 우선순위"""
        return "high"
    
    def get_dialogue_length(self) -> int:
        """대화 라운드 반환"""
        return self.chat_round or 0
    
    def has_feedback_enabled(self) -> bool:
        """피드백 사용 여부"""
        return bool(self.useFeedList and len(self.useFeedList) > 0)


class VirtualActorDialogueV2Model(SokindBaseModel):
    """가상 고객 대화 교육 모델 (edu_type: 7)"""
    member_key: int
    edu_key: int
    edu_type: int
    enterprise_key: Optional[int] = 0
    request_type: Optional[int] = 0
    request_type_str: Optional[str] = ""
    return_url: Optional[str] = ""
    company_key: Optional[int] = 0 
    store_key: Optional[int] = 0 
    round_int: Optional[int] = 0 
    edu_title: Optional[str] = ""
    edu_subject: Optional[str] = ""
    intro: Optional[List[Dict[str, Any]]] = []
    mission: Optional[Dict[str, Any]] = {}
    interaction: Optional[Dict[str, Any]] = {}
    intent_history: Optional[List[Dict[str, Any]]] = []
    training_type: Optional[int] = 1
    generate_type: Optional[str] = ""
    reference_script: Optional[str] = ""
    question_history: Optional[List[Dict[str, Any]]] = []
    sp_summary: Optional[str] = ""
    sp_info: Optional[Dict[str, Any]] = None
    member_name: Optional[str] = ""
    
    def get_business_priority(self) -> str:
        """고급 대화형 교육은 높은 우선순위"""
        return "high"
    
    def get_processing_type(self) -> str:
        """실시간 대화 처리 필요"""
        return "real_time"
    
    def is_response_generation_type(self) -> bool:
        """응답 생성 타입인지 확인"""
        return self.request_type in [1, 2]
    
    def has_conversation_history(self) -> bool:
        """대화 이력이 있는지 확인"""
        return bool(self.intent_history and len(self.intent_history) > 0)


class VirtualActorDialogueV2ForeignDemoModel(SokindBaseModel):
    """가상 고객 대화 교육모델 해외 데모 버전 (edu_type: 8)"""
    request_type: Optional[int] = 0
    request_type_str: Optional[str] = ""
    return_url: Optional[str] = ""
    company_key: Optional[int] = 0 
    enterprise_key: Optional[int] = 0
    store_key: Optional[int] = 0 
    edu_key: int
    edu_type: int
    round_int: Optional[int] = 0 
    member_key: int
    training_type: Optional[int] = 1
    edu_title: Optional[str] = ""
    edu_subject: Optional[str] = ""
    intro: Optional[List[Dict[str, Any]]] = []
    mission: Optional[Dict[str, Any]] = {}
    interaction: Optional[Dict[str, Any]] = {}
    audio_analysis: Optional[Dict[str, Any]] = {}
    intent_history: Optional[List[Dict[str, Any]]] = []
    language: Optional[int] = 2
    
    def get_business_priority(self) -> str:
        """데모 버전은 일반 우선순위"""
        return "normal"
    
    def is_demo_generation_type(self) -> bool:
        """데모 생성 타입인지 확인"""
        return self.request_type in [1, 2]
    
    def is_demo_analysis_type(self) -> bool:
        """데모 분석 타입인지 확인"""
        return self.request_type in [3, 4]
    
    def get_target_language(self) -> str:
        """대상 언어 반환 (2=영어)"""
        return "english" if self.language == 2 else "korean"


class PeriodicReportModel(SokindBaseModel):
    """주간 리포트 (edu_type: 9)"""
    edu_type: int
    period_report_data_url: Optional[str] = ""
    return_url: Optional[str] = ""
    
    def get_business_priority(self) -> str:
        """리포트는 낮은 우선순위 (비실시간)"""
        return "low"
    
    def get_processing_type(self) -> str:
        """스케줄링 처리 가능"""
        return "scheduled"
    
    def has_data_url(self) -> bool:
        """리포트 데이터 URL이 있는지 확인"""
        return bool(self.period_report_data_url)


class VirtualActorDialogueV3BaseModel(SokindBaseModel):
    """가상 고객 대화 V3 기본 모델"""
    edu_type: int
    generation_type: Optional[str] = ""
    situation: Optional[str] = ""
    customer_data: Optional[Dict[str, Any]] = {}
    return_url: Optional[str] = ""
    
    def get_business_priority(self) -> str:
        """V3는 고급 AI 기능으로 높은 우선순위"""
        return "high"
    
    def get_processing_type(self) -> str:
        """실시간 AI 생성 처리"""
        return "real_time"
    
    def has_customer_context(self) -> bool:
        """고객 컨텍스트 데이터가 있는지 확인"""
        return bool(self.customer_data)
    
    def get_generation_category(self) -> str:
        """생성 카테고리 반환"""
        return self.generation_type.lower() if self.generation_type else "unknown"
    

class VirtualActorDialogueV3AugmentationModel(VirtualActorDialogueV3BaseModel):
    """가상 고객 대화 V3 증강 모델 (edu_type: 10, generation_type: AUGMENTATION)"""
    edu_key: int
    customer_key: Optional[str] = None
    
    def get_required_fields(self) -> List[str]:
        """페르소나 생성 필수 필드"""
        return ["edu_key", "customer_key", "situation"]
    
    def is_persona_augmentation(self) -> bool:
        """페르소나 증강 타입인지 확인"""
        return self.generation_type == "AUGMENTATION"


class VirtualActorDialogueV3QuestionModel(VirtualActorDialogueV3BaseModel):
    """가상 고객 대화 V3 질문 모델 (edu_type: 10, generation_type: QUESTION)"""
    chat_history_key: Optional[str] = None
    title: Optional[str] = ""
    user_role: Optional[str] = ""
    reference_data_list: Optional[List[Dict[str, Any]]] = []
    previous_chat_history_data_list: Optional[List[Dict[str, Any]]] = []
    user_answer_text: Optional[str] = ""
    augmentation: Optional[Dict[str, Any]] = None
    memory_data_list: Optional[List[Dict[str, Any]]] = []
    
    def get_business_priority(self) -> str:
        """질문 생성은 진적 우선순위"""
        return "urgent" if self.user_answer_text else "high"
    
    def has_conversation_context(self) -> bool:
        """대화 컨텍스트가 있는지 확인"""
        return bool(self.previous_chat_history_data_list)
    
    def has_user_input(self) -> bool:
        """사용자 입력이 있는지 확인"""
        return bool(self.user_answer_text)
    
    def get_memory_count(self) -> int:
        """메모리 데이터 개수"""
        return len(self.memory_data_list) if self.memory_data_list else 0


class VirtualActorDialogueV3ReportModel(VirtualActorDialogueV3BaseModel):
    """가상 고객 대화 V3 리포트 모델 (edu_type: 10, generation_type: REPORT)"""
    round_key: Optional[str] = None
    edu_play_type: Optional[str] = ""
    title: Optional[str] = ""
    augmentation: Optional[Dict[str, Any]] = None
    user_role: Optional[str] = ""
    reference_data_list: Optional[List[Dict[str, Any]]] = []
    mission_data_list: Optional[List[Dict[str, Any]]] = []
    previous_chat_history_data_list: Optional[List[Dict[str, Any]]] = []
    memory_data_list: Optional[List[Dict[str, Any]]] = []
    stop_word_list: Optional[List[str]] = []
    evaluation_item_data: Optional[Dict[str, Any]] = {}
    
    def get_business_priority(self) -> str:
        """리포트 생성은 일반 우선순위"""
        return "normal"
    
    def get_processing_type(self) -> str:
        """리포트는 배치 처리 가능"""
        return "batch"
    
    def has_evaluation_criteria(self) -> bool:
        """평가 항목이 있는지 확인"""
        return bool(self.evaluation_item_data)
    
    def get_mission_count(self) -> int:
        """미션 데이터 개수"""
        return len(self.mission_data_list) if self.mission_data_list else 0


# 교육 타입별 모델 매핑
EDUCATION_TYPE_MODELS = {
    1: BasicEducationModel,
    2: FillOutBlankScriptModel,
    3: BasicEducationModel,  # 일반 교육도 기본 모델 사용
    4: ListenAndRepeatModel,
    5: KeywordMemorizationModel,
    6: VirtualActorDialogueV1Model,
    7: VirtualActorDialogueV2Model,
    8: VirtualActorDialogueV2ForeignDemoModel,
    9: PeriodicReportModel,
}