"""
메시지 서비스 모듈
RabbitMQ 연결 및 메시지 전송 관련 기능 제공
"""
import logging
from typing import Dict, Any, Optional, Tuple

from app.core.config import settings
from app.models.requests import SokindRequest
from app.services.rabbitmq import MessageSender

logger = logging.getLogger(__name__)


class MessageService:
    """통합 메시지 서비스"""
    
    def __init__(self):
        self.default_queue = settings.default_queue
        
    def build_message_and_queue(self, request_body: SokindRequest, client_ip: str) -> Tuple[str, int, Dict[str, Any]]:
        """요청 내용에 따라 메시지와 큐를 구성"""
        priority = settings.priority_medium
        queue = self.default_queue
        body: Dict[str, Any] = {}

        if request_body.edu_type in [1, 2, 3, 4, 5, 6]:
            body.update({
                "round_int": request_body.round,
                "member_key": request_body.member_key,
                "edu_key": request_body.edu_key,
                "edu_type": request_body.edu_type,
                "user_video_url": request_body.user_video_url,
                "user_audio_url": request_body.user_audio_url,
                "admin_url": request_body.admin_url,
                "question": request_body.question,
                "script": request_body.script,
                "face_cut_time": request_body.face_cut_time,
                "training_type": request_body.training_type,
                "company_key": request_body.company_key,
                "return_url": request_body.return_url,
                "round_id": request_body.round_id,
                "enterprise_key": request_body.enterprise_key,
                "disallowed_lst": request_body.disallowed_lst,
                "transcribed_script": request_body.transcribed_script,
            })

            if request_body.edu_type == 1:
                priority = settings.priority_high
            elif request_body.edu_type == 4:
                priority = settings.priority_low

            if request_body.edu_type == 2:
                body["blank_script"] = request_body.blank_script
                body["answerArr"] = request_body.answerArr
            elif request_body.edu_type == 4:
                body["admin_type"] = request_body.admin_type
                body["user_audio_url_sub"] = request_body.user_audio_url_sub
                body["main_gender"] = request_body.main_gender
            elif request_body.edu_type == 5:
                body["arr_keyword"] = request_body.arrKeyword
            elif request_body.edu_type == 6:
                body["chat_list"] = request_body.chatList
                body["edu_contents"] = request_body.edu_contents
                body["chat_round"] = request_body.chat_round
                body["use_feed_list"] = request_body.useFeedList

        elif request_body.edu_type == 7:
            body = {
                "request_type": request_body.request_type,
                "request_type_str": request_body.request_type_str,
                "return_url": request_body.return_url,
                "company_key": request_body.company_key,
                "enterprise_key": request_body.enterprise_key,
                "store_key": request_body.store_key,
                "edu_key": request_body.edu_key,
                "edu_type": request_body.edu_type,
                "round_int": request_body.round_int,
                "member_key": request_body.member_key,
                "training_type": request_body.training_type,
                "edu_title": request_body.edu_title,
                "edu_subject": request_body.edu_subject,
                "intro": request_body.intro,
                "mission": request_body.mission,
                "interaction": request_body.interaction,
                "intent_history": request_body.intent_history,
                "generate_type": request_body.generate_type,
                "reference_script": request_body.reference_script,
                "question_history": request_body.question_history,
                "sp_summary": request_body.sp_summary,
                "sp_info": request_body.sp_info,
                "member_name": request_body.member_name,
            }
            queue = "sokind_conversation_generate_response" if request_body.request_type in [1, 2] else "sokind_conversation"

        elif request_body.edu_type == 8:
            body = {
                "request_type": request_body.request_type,
                "request_type_str": request_body.request_type_str,
                "return_url": request_body.return_url,
                "company_key": request_body.company_key,
                "enterprise_key": request_body.enterprise_key,
                "store_key": request_body.store_key,
                "edu_key": request_body.edu_key,
                "edu_type": request_body.edu_type,
                "round_int": request_body.round_int,
                "member_key": request_body.member_key,
                "training_type": request_body.training_type,
                "edu_title": request_body.edu_title,
                "edu_subject": request_body.edu_subject,
                "intro": request_body.intro,
                "mission": request_body.mission,
                "interaction": request_body.interaction,
                "audio_analysis": request_body.audio_analysis,
                "intent_history": request_body.intent_history,
                "language": request_body.language,
            }
            if request_body.request_type in [1, 2]:
                queue = "sokind_demo_generate_response"
            elif request_body.request_type in [3, 4]:
                queue = "sokind_demo_analyze_response"

        elif request_body.edu_type == 9:
            body = {
                "edu_type": request_body.edu_type,
                "period_report_data_url": request_body.period_report_data_url,
                "return_url": request_body.return_url,
            }
            queue = "periodic_report"

        elif request_body.edu_type == 10:
            if request_body.generation_type == "AUGMENTATION":
                body = {
                    "client_ip": client_ip,
                    "edu_type": request_body.edu_type,
                    "generation_type": request_body.generation_type,
                    "edu_key": request_body.edu_key,
                    "customer_key": request_body.customer_key,
                    "situation": request_body.situation,
                    "customer_data": request_body.customer_data,
                    "return_url": request_body.return_url,
                }
                queue = "V3_PERSONA_GENERATION"
            elif request_body.generation_type == "QUESTION":
                body = {
                    "client_ip": client_ip,
                    "edu_type": request_body.edu_type,
                    "generation_type": request_body.generation_type,
                    "chat_history_key": request_body.chat_history_key,
                    "title": request_body.title,
                    "situation": request_body.situation,
                    "user_role": request_body.user_role,
                    "reference_data_list": request_body.reference_data_list,
                    "customer_data": request_body.customer_data,
                    "previous_chat_history_data_list": request_body.previous_chat_history_data_list,
                    "user_answer_text": request_body.user_answer_text,
                    "augmentation": request_body.augmentation,
                    "memory_data_list": request_body.memory_data_list,
                    "return_url": request_body.return_url,
                }
                queue = "V3_RESPONSE_GENERATION"
            elif request_body.generation_type == "REPORT":
                body = {
                    "client_ip": client_ip,
                    "edu_type": request_body.edu_type,
                    "generation_type": request_body.generation_type,
                    "round_key": request_body.round_key,
                    "edu_play_type": request_body.edu_play_type,
                    "title": request_body.title,
                    "situation": request_body.situation,
                    "customer_data": request_body.customer_data,
                    "augmentation": request_body.augmentation,
                    "user_role": request_body.user_role,
                    "reference_data_list": request_body.reference_data_list,
                    "mission_data_list": request_body.mission_data_list,
                    "previous_chat_history_data_list": request_body.previous_chat_history_data_list,
                    "memory_data_list": request_body.memory_data_list,
                    "stop_word_list": request_body.stop_word_list,
                    "evaluation_item_data": request_body.evaluation_item_data,
                    "return_url": request_body.return_url,
                }
                queue = "V3_CONVERSATION_ANALYSIS_REPORT"

        return queue, priority, body

    def send_message(
        self,
        request_body: SokindRequest,
        client_ip: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """메시지 전송"""
        queue, priority, body = self.build_message_and_queue(request_body, client_ip)
        
        # 요청 ID 추가
        if request_id:
            body["request_id"] = request_id
        
        try:
            sender = MessageSender()
            
            exists = sender.queue_exists(queue)
            if not exists:
                sender.declare_queue(queue)
                
            sender.send_message(
                exchange="",
                routing_key=queue,
                body=body,
                priority=priority
            )
            sender.close()
            
            logger.info(f"Message sent successfully to queue: {queue}")
            return {
                "message": "success",
                "status": 200,
                "request_id": request_id,
                "queue": queue
            }
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise