from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "CDL Gateway"
    environment: str = "production"
    log_level: str = "INFO"

    # RabbitMQ settings (Traditional 크레덴셜 방식 우선)
    rabbitmq_hostname: str = Field("localhost", env="RABBITMQ_HOSTNAME")
    rabbitmq_port: str = Field("5672", env="RABBITMQ_PORT")
    rabbitmq_user: str = Field("guest", env="RABBITMQ_USER")
    rabbitmq_password: str = Field("guest", env="RABBITMQ_PASSWORD")
    
    # AWS MQ settings (fallback 용도)
    rabbitmq_broker_id: Optional[str] = Field(None, env="RABBITMQ_BROKER_ID")
    rabbitmq_region: str = Field("ap-northeast-2", env="RABBITMQ_REGION")

    # Queue settings
    default_queue: str = "sokind"
    
    # Priority settings
    priority_high: int = 1
    priority_medium: int = 2
    priority_low: int = 9

    # Server settings
    gunicorn_workers: int = 3
    uvicorn_log_level: str = "info"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()