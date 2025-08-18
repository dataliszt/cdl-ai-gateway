#!/bin/bash
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

# AWS Secrets Manager에서 환경변수 로드
echo "📡 Loading environment variables from AWS Secrets Manager..."
if uv run python -m app.core.secrets; then
    echo "✅ Environment variables loaded successfully"
    
    # 로드된 환경변수 확인 (민감 정보 제외)
    echo "📋 Loaded configuration summary:"
    echo "  ENVIRONMENT: ${ENVIRONMENT}"
    echo "  LOG_LEVEL: ${LOG_LEVEL}"
    echo "  RABBITMQ_HOSTNAME: ${RABBITMQ_HOSTNAME}"
    echo "  AWS_REGION: ${AWS_REGION}"
else
    echo "⚠️ Failed to load from AWS Secrets Manager"
    
    # .env 파일이 있으면 폴백으로 사용
    if [ -f ".env" ]; then
        echo "📂 Attempting to load from .env file..."
        export $(grep -v '^#' .env | xargs)
        echo "✅ Loaded environment from .env file"
    else
        echo "❌ No .env file found, cannot proceed without configuration"
        echo ""
        echo "💡 Solutions:"
        echo "1. Ensure EC2/ECS instance has proper IAM role with secretsmanager:GetSecretValue permission"
        echo "2. Set AWS credentials via environment variables:"
        echo "   export AWS_ACCESS_KEY_ID=your-key"
        echo "   export AWS_SECRET_ACCESS_KEY=your-secret"
        echo "3. Create a .env file with required variables"
        exit 1
    fi
fi

# 로그 디렉토리 생성
mkdir -p /var/log/cdl-gateway

# Gunicorn 서버 시작 (메모리 누수 방지 설정 포함)
exec uv run gunicorn app.main:app \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-5} \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --max-requests ${GUNICORN_MAX_REQUESTS:-10000} \
    --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-1000} \
    --preload \
    --access-logfile /var/log/cdl-gateway/access.log \
    --error-logfile /var/log/cdl-gateway/error.log \
    --log-level info