# CDL Gateway

크디랩 통합 AI 분석 게이트웨이 - Sokind 서비스용 API

## ✨ 주요 특징

- **🔐 AWS Secrets Manager 통합**: 프로덕션 환경의 안전한 설정 관리
- **🚀 IAM Role 기반 인증**: EC2/ECS에서 자동 자격증명 처리 (AWS 키 하드코딩 불필요)
- **🔄 RabbitMQ 클러스터 지원**: 고가용성 다중 노드 자동 fallback
- **📊 통합 메시지 서비스**: 교육 타입별 최적화된 큐 라우팅
- **🛡️ 구조화된 미들웨어**: Request ID 추적, 상세 요청 로깅
- **🎯 블루/그린 배포**: 무중단 서비스 배포 지원
- **📦 uv 기반 빌드**: 현대적이고 빠른 Python 패키지 관리

## 개선된 기능

### 1. 미들웨어 시스템
- **RequestIdMiddleware**: 모든 요청에 고유 ID 부여
- **RequestLoggingMiddleware**: 상세한 요청/응답 로깅

### 2. RabbitMQ 클러스터 클라이언트
- **다중 노드 지원**: 클러스터의 모든 노드에 대한 자동 fallback
- **회로 차단기 패턴**: 실패한 노드를 일시적으로 제외하여 성능 최적화
- **자동 재연결**: 연결 실패 시 다른 노드로 자동 전환
- **지수 백오프**: 재시도 간격을 점진적으로 증가시켜 시스템 부하 최소화
- **상태 모니터링**: 실시간 클러스터 노드 상태 추적

### 3. 구조화된 설정 관리
- Pydantic 기반 타입 안전 설정
- 환경변수 기반 설정 관리

### 4. 향상된 로깅
- 구조화된 로그 포맷
- Request ID 기반 요청 추적
- 성능 메트릭 포함

## 📁 프로젝트 구조

```
cdl-ai-gateway/
├── app/
│   ├── main.py                     # FastAPI 애플리케이션 진입점
│   ├── core/
│   │   ├── config.py              # 환경설정 관리 (API 키, RabbitMQ)
│   │   ├── secrets.py             # AWS Secrets Manager 통합
│   │   └── logging_config.py      # 구조화된 로깅 설정
│   ├── middleware/
│   │   ├── request_id.py          # 고유 요청 ID 생성
│   │   └── request_logging.py     # 요청/응답 로깅
│   ├── models/
│   │   ├── base.py                # 기본 Pydantic 모델
│   │   ├── requests.py            # API 요청 모델
│   │   └── education_models.py    # 교육 타입별 특화 모델
│   ├── services/
│   │   ├── rabbitmq.py            # RabbitMQ 클러스터 클라이언트
│   │   └── message_service.py     # 통합 메시지 디스패치 서비스
│   └── api/
│       └── routes.py              # REST API 엔드포인트
├── scripts/
│   └── start.sh                   # 컨테이너 시작 스크립트
├── nginx/
│   └── nginx.conf                 # 리버스 프록시 설정
├── docker-compose.yml             # 블루/그린 배포 설정
├── Dockerfile                     # 컨테이너 이미지 정의
├── pyproject.toml                 # Python 프로젝트 설정
└── .env.example                   # 환경변수 템플릿
```

## 🚀 설치 및 실행

### 📋 사전 준비사항

1. **Python 3.11+** 및 **uv** 설치
2. **AWS 계정** 및 Secrets Manager 설정
3. **Docker** 및 **Docker Compose** (프로덕션 배포 시)

### 🛠️ 개발 환경 설정

**1. 프로젝트 설정**
```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 클론 및 종속성 설치
git clone <repository-url>
cd cdl-ai-gateway
uv sync
```

**2. 환경변수 설정**
```bash
cp .env.example .env
# .env 파일 편집 (로컬 개발용 AWS 자격증명)
```

**3. 로컬 개발 실행**
```bash
# AWS 자격증명 설정 (개발 환경)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# 시크릿 로드 테스트
uv run python -m app.core.secrets

# 개발 서버 실행
make run  # 또는 uv run uvicorn app.main:app --reload
```

### 🏗️ 프로덕션 배포

**1. IAM Role 설정** ([상세 가이드](docs/AWS_CREDENTIALS_GUIDE.md))
```bash
# 새 EC2 인스턴스용
bash deployment/setup_ec2_instance.sh

# 기존 인스턴스에 권한 추가
bash deployment/add_policy_to_existing_role.sh

# ECS/Fargate용
bash deployment/setup_ecs_task.sh
```

**2. AWS Secrets Manager 설정**
```json
// Secret Name: cdl/ai/env
{
  "OPENAI_API_KEY": "your-openai-key",
  "ANTHROPIC_API_KEY": "your-anthropic-key",
  "GOOGLE_API_KEY": "your-google-key",
  "OPENAI_API_KEY_REALTIME": "your-openai-realtime-key",
  "ANTHROPIC_API_KEY_REALTIME": "your-anthropic-realtime-key",
  "GOOGLE_API_KEY_REALTIME": "your-google-realtime-key",
  "RABBITMQ_USER": "your-rabbitmq-user",
  "RABBITMQ_PASSWORD": "your-rabbitmq-password",
  "RABBITMQ_HOSTNAME": "your-rabbitmq-hostname",
  "RABBITMQ_PORT": "5672",
  "RABBITMQ_PORT2": "5673",
  "RABBITMQ_PORT3": "5674",
  "AWS_REGION": "ap-northeast-2"
}
```

**3. EC2 보안그룹 설정**
```bash
# 필수 포트 열기
Port 22  (SSH)        - Your IP
Port 80  (HTTP)       - 0.0.0.0/0
Port 443 (HTTPS)      - 0.0.0.0/0

# 선택적 포트 (디버깅용)
Port 8000  (Direct)   - 0.0.0.0/0
Port 18001 (Blue)     - 0.0.0.0/0
Port 18002 (Green)    - 0.0.0.0/0
```

**4. 배포 실행**
```bash
# EC2 인스턴스에서
git clone <repository-url>
cd cdl-ai-gateway

# Docker 배포 (IAM Role 자동 인증)
docker-compose -f deployment/docker-compose.prod.yml up -d

# 상태 확인
curl http://your-ec2-ip/status/
curl http://your-ec2-ip/status/rabbitmq

# 로그 확인 (시크릿 로드 확인)
docker logs cdl-gateway | grep "IAM 역할"
```

### 주요 명령어

```bash
make help           # 사용 가능한 명령어 목록
make dev            # 개발 종속성 설치
make format         # 코드 포맷팅
make lint           # 린팅 실행
make test           # 테스트 실행
make run            # 개발 서버 실행
make ci             # CI 파이프라인 (format-check + lint + test)
```

### Docker Compose 사용

```bash
make docker-compose-up    # 전체 스택 시작
make docker-compose-down  # 스택 종료
make docker-compose-logs  # 로그 확인
```

### 블루/그린 무중단 배포

```bash
# 배포 상태 확인
make deploy-status

# 블루 슬롯에 새 버전 배포
make blue-deploy

# 헬스체크 확인
make health-check-blue

# 트래픽을 블루로 전환 (그린 중단)
make switch-to-blue

# 또는 그린 슬롯 사용
make green-deploy
make health-check-green  
make switch-to-green
```

## API 문서

서비스 실행 후 다음 URL에서 API 문서 확인:
- Swagger UI: http://localhost/docs
- ReDoc: http://localhost/redoc

## 🔧 환경변수 및 설정

### 📝 환경변수 목록

| 분류 | 변수명 | 설명 | 소스 |
|------|--------|------|------|
| **앱 설정** | `APP_NAME` | 애플리케이션 이름 | .env |
| | `ENVIRONMENT` | 실행 환경 (development/production) | .env |
| | `LOG_LEVEL` | 로그 레벨 (DEBUG/INFO/WARNING) | .env |
| **AWS 인증** | `AWS_ACCESS_KEY_ID` | AWS 액세스 키 (개발용) | .env |
| | `AWS_SECRET_ACCESS_KEY` | AWS 시크릿 키 (개발용) | .env |
| | `AWS_REGION` | AWS 리전 | Secrets Manager |
| **API 키들** | `OPENAI_API_KEY` | OpenAI API 키 | Secrets Manager |
| | `ANTHROPIC_API_KEY` | Anthropic API 키 | Secrets Manager |
| | `GOOGLE_API_KEY` | Google API 키 | Secrets Manager |
| | `*_REALTIME` | 실시간 API 키들 | Secrets Manager |
| **RabbitMQ** | `RABBITMQ_USER` | RabbitMQ 사용자명 | Secrets Manager |
| | `RABBITMQ_PASSWORD` | RabbitMQ 비밀번호 | Secrets Manager |
| | `RABBITMQ_HOSTNAME` | RabbitMQ 호스트 | Secrets Manager |
| | `RABBITMQ_PORT*` | RabbitMQ 포트들 (3개) | Secrets Manager |
| **서버** | `GUNICORN_WORKERS` | 워커 프로세스 수 | .env |

### 🔐 보안 모델

**개발 환경**: `.env` 파일 → 환경변수 → AWS Secrets Manager
**프로덕션 환경**: EC2 IAM Role → AWS Secrets Manager → 환경변수

## 🔍 API 엔드포인트

### 📊 상태 확인
- `GET /status/` - 서비스 헬스체크
- `GET /status/rabbitmq` - RabbitMQ 클러스터 상태

### 📨 메시지 전송  
- `POST /` - Sokind 분석 요청 처리

### 📚 API 문서
- `/docs` - Swagger UI 
- `/redoc` - ReDoc

## 🏗️ 아키텍처 개선사항

### ✅ 완료된 주요 개선사항

**1. 보안 강화**
- ✅ AWS Secrets Manager 통합으로 민감정보 안전 관리
- ✅ IAM Role 기반 인증으로 하드코딩된 자격증명 제거
- ✅ 프로덕션 환경에서 자동 자격증명 로테이션 지원

**2. 코드 품질 향상**  
- ✅ 중복 서비스 레이어 통합 (MessageService + MessageDispatchService → MessageService)
- ✅ 구식 파일 정리 (rabbitmq_old.py, 테스트 스크립트 등 5개 파일 제거)
- ✅ 현대적 Python 프로젝트 구조 (uv + pyproject.toml)

**3. 설정 관리 개선**
- ✅ 환경별 설정 분리 (개발: .env, 프로덕션: AWS Secrets Manager)
- ✅ RabbitMQ 클러스터 설정 개별 포트 지원 (PORT, PORT2, PORT3)
- ✅ 13개 환경변수 자동 로드 및 매핑

**4. 배포 최적화**
- ✅ Docker 컨테이너 시작 시 자동 시크릿 로드
- ✅ Blue/Green 배포에서 AWS 자격증명 자동 처리
- ✅ EC2 Instance Profile을 통한 권한 관리

### 🎯 핵심 가치

**보안**: 민감정보 하드코딩 제거, IAM 기반 권한 관리
**안정성**: 고가용성 RabbitMQ 클러스터, 자동 failover
**유지보수성**: 단일 책임 서비스, 명확한 레이어 분리  
**확장성**: 환경별 설정, 컨테이너 기반 배포

## 📋 개발 명령어

### 🛠️ 주요 명령어
```bash
make help           # 사용 가능한 명령어 목록
make dev            # 개발 종속성 설치
make format         # 코드 포맷팅
make lint           # 린팅 실행
make test           # 테스트 실행
make run            # 개발 서버 실행
make ci             # CI 파이프라인 (format-check + lint + test)
```

### 🐳 Docker 명령어
```bash
make docker-compose-up    # 전체 스택 시작
make docker-compose-down  # 스택 종료
make docker-compose-logs  # 로그 확인

# 블루/그린 배포
make deploy-status        # 배포 상태 확인
make blue-deploy          # 블루 슬롯 배포
make health-check-blue    # 블루 헬스체크
make switch-to-blue       # 블루로 트래픽 전환
```

## 🔗 관련 링크

- **API 문서**: http://your-domain/docs
- **헬스체크**: http://your-domain/status/
- **RabbitMQ 상태**: http://your-domain/status/rabbitmq

---

**CDL Gateway v2.0** - 보안이 강화되고 현대적인 AI 분석 게이트웨이