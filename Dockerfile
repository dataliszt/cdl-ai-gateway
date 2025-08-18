FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (BuildKit 불필요)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh -s -- \
    && cp /root/.local/bin/uv /usr/local/bin/uv \
    && chmod 755 /usr/local/bin/uv

# Python 종속성 복사 및 설치
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# 애플리케이션 코드 및 필요한 스크립트만 복사
COPY app/ ./app/
COPY scripts/start.sh ./scripts/start.sh
COPY scripts/export-secrets.py ./scripts/export-secrets.py

# 스크립트 실행 권한 부여
RUN chmod +x ./scripts/start.sh

# 로그 디렉토리 생성
RUN mkdir -p /var/log/cdl-gateway

# 환경변수 설정 (메모리 누수 방지)
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    GUNICORN_WORKERS=5 \
    GUNICORN_MAX_REQUESTS=10000 \
    GUNICORN_MAX_REQUESTS_JITTER=1000 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    AWS_REGION=ap-northeast-2

# 비루트 사용자 생성
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chown -R app:app /var/log/cdl-gateway
USER app

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
CMD curl -f http://localhost:8000/status/ || exit 1

# 애플리케이션 실행 (start.sh 스크립트 사용)
CMD ["./scripts/start.sh"]