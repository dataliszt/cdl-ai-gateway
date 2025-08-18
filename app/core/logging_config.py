import logging
import sys
from datetime import datetime
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # Fallback: system localtime


class _KSTFormatter(logging.Formatter):
    """KST(Asia/Seoul) 타임존으로 시간 포맷팅하는 Formatter."""

    def formatTime(self, record, datefmt=None):  # type: ignore[override]
        if ZoneInfo is None:
            return super().formatTime(record, datefmt)
        dt = datetime.fromtimestamp(record.created, tz=ZoneInfo("Asia/Seoul"))
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(timespec="seconds")


def configure_logging(level: str = "INFO") -> None:
    """
    로깅 설정을 구성합니다.
    
    Args:
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, stream=sys.stdout)

    # 루트 핸들러에 KST 포맷터 적용
    root_logger = logging.getLogger()
    datefmt = "%Y-%m-%d %H:%M:%S %z"
    formatter = _KSTFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s [%(funcName)s:%(lineno)d] %(message)s",
        datefmt=datefmt,
    )
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

    # Uvicorn/Gunicorn 로거에도 동일 포맷터 적용
    for logger_name in ("uvicorn.error", "uvicorn.access", "gunicorn.error", "gunicorn.access"):
        lg = logging.getLogger(logger_name)
        lg.setLevel(log_level)
        for h in lg.handlers:
            h.setFormatter(formatter)

    # 시끄러운 로거들 레벨 조정
    for noisy in ("uvicorn.error", "uvicorn.access", "gunicorn.error"):
        logging.getLogger(noisy).setLevel(log_level)