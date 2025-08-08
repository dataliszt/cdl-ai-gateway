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


class FillOutBlankScriptModel(BasicEducationModel):
    """빈칸 채우기 교육 모델 (edu_type: 2)"""
    blank_script: Optional[str] = None
    answerArr: Optional[List[Dict[str, Any]]] = None


class ListenAndRepeatModel(BasicEducationModel):
    """듣고 따라하기 교육 모델 (edu_type: 4)"""
    admin_type: Optional[int] = None       
    user_audio_url_sub: Optional[str] = ""
    main_gender: Optional[int] = None


class KeywordMemorizationModel(BasicEducationModel):
    """키워드 말하기 교육 모델 (edu_type: 5)"""
    arrKeyword: Optional[List[str]] = Field(None, alias="arr_keyword")
    
    
class VirtualActorDialogueV1Model(BasicEducationModel):
    """가상 고객 대화 교육 모델 (edu_type: 6)"""
    chatList: Optional[List[Dict[str, Any]]] = Field(None, alias="chat_list")
    edu_contents: Optional[Dict[str, Any]] = None
    chat_round: Optional[int] = None        
    useFeedList: Optional[List[str]] = Field(None, alias="use_feed_list")


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


class PeriodicReportModel(SokindBaseModel):
    """주간 리포트 (edu_type: 9)"""
    edu_type: int
    period_report_data_url: Optional[str] = ""
    return_url: Optional[str] = ""


class VirtualActorDialogueV3BaseModel(SokindBaseModel):
    """가상 고객 대화 V3 기본 모델"""
    edu_type: int
    generation_type: Optional[str] = ""
    situation: Optional[str] = ""
    customer_data: Optional[Dict[str, Any]] = {}
    return_url: Optional[str] = ""
    

class VirtualActorDialogueV3AugmentationModel(VirtualActorDialogueV3BaseModel):
    """가상 고객 대화 V3 증강 모델 (edu_type: 10, generation_type: AUGMENTATION)"""
    edu_key: int
    customer_key: Optional[str] = None


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