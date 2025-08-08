import ssl
import json
import pika
import logging
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """통합 RabbitMQ 클라이언트 - AWS MQ와 일반 RabbitMQ 모두 지원"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        """RabbitMQ 연결 - 일반 크레덴셜 방식 우선, 실패시 AWS MQ로 fallback"""
        try:
            # 일반 RabbitMQ를 우선적으로 시도
            self._connect_traditional()
        except Exception as e:
            logger.warning(f"Traditional RabbitMQ connection failed: {e}")
            # AWS MQ가 설정되어 있으면 fallback으로 시도
            if settings.rabbitmq_broker_id:
                logger.info("Falling back to AWS MQ")
                try:
                    self._connect_aws_mq()
                except Exception as aws_e:
                    logger.error(f"AWS MQ connection also failed: {aws_e}")
                    raise aws_e
            else:
                logger.error("No AWS MQ configuration available for fallback")
                raise e
    
    def _connect_aws_mq(self):
        """AWS MQ 연결"""
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.set_ciphers("ECDHE+AESGCM:!ECDSA")

        url = (
            f"amqps://{settings.rabbitmq_user}:{settings.rabbitmq_password}"
            f"@{settings.rabbitmq_broker_id}.mq.{settings.rabbitmq_region}.amazonaws.com:5671"
        )
        parameters = pika.URLParameters(url)
        parameters.ssl_options = pika.SSLOptions(context=ssl_context)

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        logger.info("Connected to AWS MQ")
    
    def _connect_traditional(self):
        """일반 RabbitMQ 연결"""
        credentials = pika.PlainCredentials(
            settings.rabbitmq_user,
            settings.rabbitmq_password
        )
        parameters = pika.ConnectionParameters(
            host=settings.rabbitmq_hostname,
            port=int(settings.rabbitmq_port),
            credentials=credentials
        )
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        logger.info(f"Connected to traditional RabbitMQ at {settings.rabbitmq_hostname}:{settings.rabbitmq_port}")

    def close(self) -> None:
        """연결 종료"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
        except Exception as e:
            logger.warning(f"Error closing channel: {e}")
        
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")


class MessageSender(RabbitMQClient):
    """메시지 발송 클래스"""
    
    def queue_exists(self, queue_name: str, quorum: bool = True) -> bool:
        """큐 존재 여부 확인 코드 생성"""
        try:
            if quorum:
                self.channel.queue_declare(queue=queue_name, durable=True, arguments={'x-queue-type': 'quorum'})
            else:
                self.channel.queue_declare(queue=queue_name, durable=True)
            return True
        except pika.exceptions.ChannelClosed as e:
            if e.reply_code == 404:
                return False
            raise
        
    
    def declare_queue(self, queue_name: str, durable: bool = True, quorum: bool = True) -> None:
        """큐 선언"""
        if quorum:
            self.channel.queue_declare(queue=queue_name, durable=durable, arguments={'x-queue-type': 'quorum'})
        else:
            self.channel.queue_declare(queue=queue_name, durable=durable)
        logger.debug(f"Queue declared: {queue_name}")

    def send_message(
        self,
        exchange: str,
        routing_key: str,
        body: Dict[str, Any],
        priority: Optional[int] = None,
    ) -> None:
        """메시지 발송"""
        properties = pika.BasicProperties(
            priority=priority,
            delivery_mode=2  # 메시지 영속성
        )
        
        message_body = json.dumps(body, ensure_ascii=False, indent=None)
        
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=message_body,
            properties=properties,
        )
        
        logger.info(f"Message sent to queue: {routing_key}, priority: {priority}")


# Backward compatibility
BasicPikaClient = RabbitMQClient
BasicMessageSender = MessageSender