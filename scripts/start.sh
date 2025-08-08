#!/bin/bash
set -e

echo "🚀 Starting CDL Gateway..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Workers: ${GUNICORN_WORKERS:-3}"
echo "Max requests: ${GUNICORN_MAX_REQUESTS:-10000}"
echo "Max requests jitter: ${GUNICORN_MAX_REQUESTS_JITTER:-1000}"
echo "Deployment slot: ${DEPLOYMENT_SLOT:-default}"

# 로그 디렉토리 생성
mkdir -p /var/log/cdl-gateway

# Gunicorn 서버 시작 (메모리 누수 방지 설정 포함)
exec uv run gunicorn app.main:app \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-3} \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --max-requests ${GUNICORN_MAX_REQUESTS:-10000} \
    --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-1000} \
    --preload \
    --access-logfile /var/log/cdl-gateway/access.log \
    --error-logfile /var/log/cdl-gateway/error.log \
    --log-level info