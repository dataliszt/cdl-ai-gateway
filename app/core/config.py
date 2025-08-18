from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
import os

# AWS Secrets Manager에서 환경변수 로드
# Secrets 로드는 시작 스크립트에서 수행합니다.


class Settings(BaseSettings):
    app_name: str = "CDL Gateway"
    environment: str = Field("production", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # API Keys
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY") 
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    openai_api_key_realtime: Optional[str] = Field(None, env="OPENAI_API_KEY_REALTIME")
    anthropic_api_key_realtime: Optional[str] = Field(None, env="ANTHROPIC_API_KEY_REALTIME")
    google_api_key_realtime: Optional[str] = Field(None, env="GOOGLE_API_KEY_REALTIME")
    
    # AWS Region
    aws_region: Optional[str] = Field(None, env="AWS_REGION")
    
    # RabbitMQ 설정
    rabbitmq_user: Optional[str] = Field(None, env="RABBITMQ_USER")
    rabbitmq_password: Optional[str] = Field(None, env="RABBITMQ_PASSWORD")
    rabbitmq_hostname: Optional[str] = Field(None, env="RABBITMQ_HOSTNAME")
    rabbitmq_port: Optional[str] = Field(None, env="RABBITMQ_PORT")
    rabbitmq_port2: Optional[str] = Field(None, env="RABBITMQ_PORT2")
    rabbitmq_port3: Optional[str] = Field(None, env="RABBITMQ_PORT3")
    
    # 클러스터 연결 설정
    rabbitmq_connection_timeout: int = Field(10, env="RABBITMQ_CONNECTION_TIMEOUT")
    rabbitmq_retry_attempts: int = Field(3, env="RABBITMQ_RETRY_ATTEMPTS")
    rabbitmq_retry_delay: float = Field(2.0, env="RABBITMQ_RETRY_DELAY")
    rabbitmq_heartbeat: int = Field(600, env="RABBITMQ_HEARTBEAT")
    
    # AWS MQ settings (fallback 용도)
    rabbitmq_broker_id: Optional[str] = Field(None, env="RABBITMQ_BROKER_ID")
    rabbitmq_region: str = Field("ap-northeast-2", env="RABBITMQ_REGION")
    
    def get_rabbitmq_nodes(self) -> List[Dict[str, Any]]:
        """RabbitMQ 클러스터 노드 정보 반환 (개별 포트별)"""
        # 필수 값이 없으면 빈 리스트 반환 (나중에 연결 시점에 검증)
        if not (self.rabbitmq_hostname and self.rabbitmq_user and self.rabbitmq_password and self.rabbitmq_port):
            return []

        nodes = [
            {
                "host": self.rabbitmq_hostname,
                "port": int(self.rabbitmq_port),
                "user": self.rabbitmq_user,
                "password": self.rabbitmq_password
            },
            {
                "host": self.rabbitmq_hostname,
                "port": int(self.rabbitmq_port2),
                "user": self.rabbitmq_user,
                "password": self.rabbitmq_password
            },
            {
                "host": self.rabbitmq_hostname,
                "port": int(self.rabbitmq_port3),
                "user": self.rabbitmq_user,
                "password": self.rabbitmq_password
            }
        ]
        return nodes

    # Queue settings
    default_queue: str = "sokind"
    
    # Priority settings
    priority_high: int = 1
    priority_medium: int = 2
    priority_low: int = 9
    
    # Quorum Queue settings
    quorum_initial_group_size: int = Field(3, env="QUORUM_INITIAL_GROUP_SIZE")  # 클러스터 노드 수에 맞춰 조정
    quorum_delivery_limit: int = Field(10, env="QUORUM_DELIVERY_LIMIT")  # 재배달 제한
    quorum_max_in_memory_length: int = Field(100000, env="QUORUM_MAX_IN_MEMORY_LENGTH")  # 메모리 메시지 수
    quorum_max_in_memory_bytes: int = Field(104857600, env="QUORUM_MAX_IN_MEMORY_BYTES")  # 100MB

    # Server settings  
    gunicorn_workers: int = Field(5, env="GUNICORN_WORKERS")
    uvicorn_log_level: str = "info"

    # Pydantic v2 설정 로딩 방식
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

class LazySettings:
    _settings_instance: Optional[Settings] = None

    def _ensure_loaded(self) -> None:
        if self._settings_instance is None:
            # 환경변수는 start.sh에서 선주입됨
            self._settings_instance = Settings()

    def __getattr__(self, name: str):
        self._ensure_loaded()
        return getattr(self._settings_instance, name)


settings = LazySettings()