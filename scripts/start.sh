#!/usr/bin/env sh
set -e

echo "🚀 Starting CDL Gateway..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Workers: ${GUNICORN_WORKERS:-5}"
echo "Max requests: ${GUNICORN_MAX_REQUESTS:-10000}"
echo "Max requests jitter: ${GUNICORN_MAX_REQUESTS_JITTER:-1000}"
echo "Deployment slot: ${DEPLOYMENT_SLOT:-default}"

# AWS 환경 정보 출력 (디버깅용)
echo "📋 AWS Configuration:"
echo "  Region: ${AWS_REGION:-ap-northeast-2}"
echo "  Default Region: ${AWS_DEFAULT_REGION:-not set}"
echo "  Access Key: ${AWS_ACCESS_KEY_ID:+[SET]}"
echo "  Secret Key: ${AWS_SECRET_ACCESS_KEY:+[SET]}"
echo "  Session Token: ${AWS_SESSION_TOKEN:+[SET]}"

# AWS Secrets Manager에서 환경변수 선로드 (셸 환경에 주입)
echo "📡 Loading environment variables from AWS Secrets Manager (preload)..."
if eval "$(uv run python ./scripts/export-secrets.py)"; then
    echo "✅ Secrets loaded into environment (preload)"
else
    echo "❌ Failed to preload secrets into environment"
    exit 1
fi

# 로드된 환경변수 확인 (민감 정보 제외)
echo "📋 Configuration summary:"
echo "  ENVIRONMENT: ${ENVIRONMENT}"
echo "  LOG_LEVEL: ${LOG_LEVEL}"
echo "  AWS_REGION: ${AWS_REGION}"

# 로그 디렉토리 생성
mkdir -p /var/log/cdl-gateway

# Gunicorn 서버 시작 (로그는 stdout/stderr로 출력)
echo "🚀 Starting Gunicorn server..."
exec uv run gunicorn app.main:app \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-5} \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --max-requests ${GUNICORN_MAX_REQUESTS:-10000} \
    --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-1000} \
    --log-level info