import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """
    로깅 설정을 구성합니다.
    
    Args:
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        stream=sys.stdout,
        format=(
            "%(asctime)s %(levelname)s %(name)s "
            "[%(funcName)s:%(lineno)d] %(message)s"
        ),
    )

    # 시끄러운 로거들 레벨 조정
    for noisy in ("uvicorn.error", "uvicorn.access", "gunicorn.error"):
        logging.getLogger(noisy).setLevel(log_level)