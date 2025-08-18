from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    app_name: str = "CDL Gateway"
    environment: str = Field("production", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY") 
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    openai_api_key_realtime: str = Field(..., env="OPENAI_API_KEY_REALTIME")
    anthropic_api_key_realtime: str = Field(..., env="ANTHROPIC_API_KEY_REALTIME")
    google_api_key_realtime: str = Field(..., env="GOOGLE_API_KEY_REALTIME")
    
    # AWS Region
    aws_region: str = Field(..., env="AWS_REGION")
    
    # RabbitMQ 설정
    rabbitmq_user: str = Field(..., env="RABBITMQ_USER")
    rabbitmq_password: str = Field(..., env="RABBITMQ_PASSWORD")
    rabbitmq_hostname: str = Field(..., env="RABBITMQ_HOSTNAME")
    rabbitmq_port: str = Field(..., env="RABBITMQ_PORT")
    rabbitmq_port2: str = Field(..., env="RABBITMQ_PORT2")
    rabbitmq_port3: str = Field(..., env="RABBITMQ_PORT3")
    
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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()