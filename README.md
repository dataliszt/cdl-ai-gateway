# CDL Gateway

크디랩 통합 AI 분석 게이트웨이 (FastAPI + Gunicorn + Docker + Nginx)

## 빠른 시작 (개발/로컬)

```bash
git clone <repository-url>
cd cdl-ai-gateway

# uv 설치 (없다면)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync

# 준비 (디렉터리/개발용 인증서)
make prepare

# 블루/그린 + Nginx 스택 실행
docker-compose up -d

# 상태 확인
curl -k https://localhost/status/
```

## 프로덕션 배포 (EC2/ECS, IAM Role 권장)

1) AWS Secrets Manager에 다음 시크릿 생성 (`cdl/ai/env`)
```json
{
  "OPENAI_API_KEY": "...",
  "ANTHROPIC_API_KEY": "...",
  "GOOGLE_API_KEY": "...",
  "OPENAI_API_KEY_REALTIME": "...",
  "ANTHROPIC_API_KEY_REALTIME": "...",
  "GOOGLE_API_KEY_REALTIME": "...",
  "RABBITMQ_USER": "cdl",
  "RABBITMQ_PASSWORD": "...",
  "RABBITMQ_HOSTNAME": "<rabbitmq-host>",
  "RABBITMQ_PORT": "5672",
  "RABBITMQ_PORT2": "5673",
  "RABBITMQ_PORT3": "5674",
  "AWS_REGION": "ap-northeast-2"
}
```

2) 배포 (EC2에서)
```bash
git clone <repository-url>
cd cdl-ai-gateway
docker-compose -f deployment/docker-compose.prod.yml up -d
```

3) 헬스 체크
```bash
curl http://<ec2-ip>/status/
```

## 주요 명령어

```bash
make help
make prepare            # 디렉터리/인증서 자동 준비
make blue-deploy        # 블루 슬롯 배포 (사전 준비 포함)
make green-deploy       # 그린 슬롯 배포 (사전 준비 포함)
make switch-to-blue     # 트래픽 블루로 전환
make switch-to-green    # 트래픽 그린으로 전환
make docker-compose-logs
```

## 폴더 구조

```
app/                # FastAPI 앱 코드
scripts/            # start.sh, export-secrets.py
nginx/              # nginx.conf (인증서/로그는 Git 무시)
deployment/         # 프로덕션 compose 파일
docker-compose.yml  # 로컬 블루/그린+Nginx
Dockerfile
pyproject.toml
.env.example        # 환경변수 템플릿
```

## 환경 변수 (.env / AWS Secrets)

- ENVIRONMENT, LOG_LEVEL, GUNICORN_WORKERS 등은 `.env` (로컬)로 관리
- 민감 정보와 RabbitMQ 연결 정보는 AWS Secrets Manager(`cdl/ai/env`)로 관리

## 참고

- 시크릿은 컨테이너 시작 시 `scripts/export-secrets.py`를 통해 환경에 선주입됩니다.
- 애플리케이션은 Nginx(HTTPS) → Gunicorn(UvicornWorker) → FastAPI 순으로 서비스됩니다.