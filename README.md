# CDL Gateway

크디랩 통합 AI 분석 게이트웨이 - Sokind 서비스용 API

## 특징

- **통합 아키텍처**: `ai-gateway`와 `sokind_gateway_v2`의 장점을 통합
- **유연한 RabbitMQ 지원**: AWS MQ와 일반 RabbitMQ 모두 지원 (자동 fallback)
- **구조화된 미들웨어**: Request ID 추적, 상세 요청 로깅
- **강화된 예외 처리**: 명확한 에러 메시지와 상태 코드
- **확장 가능한 설계**: App Factory 패턴으로 테스트와 확장 용이

## 개선된 기능

### 1. 미들웨어 시스템
- **RequestIdMiddleware**: 모든 요청에 고유 ID 부여
- **RequestLoggingMiddleware**: 상세한 요청/응답 로깅

### 2. 통합 RabbitMQ 클라이언트
- AWS MQ 우선 연결, 실패시 일반 RabbitMQ로 자동 fallback
- 연결 상태 모니터링 및 에러 핸들링

### 3. 구조화된 설정 관리
- Pydantic 기반 타입 안전 설정
- 환경변수 기반 설정 관리

### 4. 향상된 로깅
- 구조화된 로그 포맷
- Request ID 기반 요청 추적
- 성능 메트릭 포함

## 프로젝트 구조

```
cdl-gateway/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 애플리케이션 팩토리
│   ├── core/
│   │   ├── config.py          # 설정 관리
│   │   └── logging_config.py   # 로깅 설정
│   ├── middleware/
│   │   ├── request_id.py       # Request ID 미들웨어
│   │   └── request_logging.py  # 로깅 미들웨어
│   ├── models/
│   │   └── requests.py         # 요청 데이터 모델
│   ├── services/
│   │   ├── rabbitmq.py         # RabbitMQ 클라이언트
│   │   └── message_service.py  # 메시지 서비스
│   └── api/
│       └── routes.py           # API 라우터
├── nginx/
│   └── nginx.conf              # Nginx 설정
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## 설치 및 실행

### 개발 환경 설정

1. uv 설치 (아직 없다면):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. 프로젝트 클론 및 종속성 설치:
```bash
git clone <repository-url>
cd cdl-gateway
uv sync  # 개발 종속성 포함 설치
```

3. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일 편집
```

4. 개발 서버 실행:
```bash
make run  # 또는 uv run uvicorn app.main:app --reload
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

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `APP_NAME` | 애플리케이션 이름 | "CDL Gateway" |
| `ENVIRONMENT` | 실행 환경 | "production" |
| `LOG_LEVEL` | 로그 레벨 | "INFO" |
| **기본 RabbitMQ (크레덴셜 방식)** |
| `RABBITMQ_HOSTNAME` | RabbitMQ 호스트 | "localhost" |
| `RABBITMQ_PORT` | RabbitMQ 포트 | "5672" |
| `RABBITMQ_USER` | RabbitMQ 사용자명 | "guest" |
| `RABBITMQ_PASSWORD` | RabbitMQ 비밀번호 | "guest" |
| **AWS MQ (Fallback 용도)** |
| `RABBITMQ_BROKER_ID` | AWS MQ 브로커 ID | None (선택) |
| `RABBITMQ_REGION` | AWS 리전 | "ap-northeast-2" |

## 🎯 주요 개선사항

### 1. **sokind_gateway_v2 장점 완전 통합** ✅
   - **App Factory 패턴**: 깔끔한 애플리케이션 초기화
   - **Request ID 미들웨어**: 모든 요청 고유 ID로 추적 가능
   - **Request Logging 미들웨어**: 상세한 요청/응답 로그 (IP, User-Agent, 응답시간)
   - **구조화된 예외 처리**: 명확한 에러 메시지와 상태 코드
   - **블루/그린 무중단 배포**: API 인스턴스 2개 + 헬스체크 + 자동 failover

### 2. **ai-gateway 기능 완전 호환** ✅
   - **교육 타입별 특화 모델**: 확장 가능하고 가독성 높은 모델 구조
   - **동적 모델 선택**: edu_type에 따른 자동 모델 매핑
   - **모든 edu_type (1-10) 지원**: 기존 API 완전 호환
   - **기존 큐 라우팅 로직**: 동일한 메시지 처리 방식
   - **Gunicorn 메모리 누수 방지**: MAX_REQUESTS, JITTER 설정으로 안정성 보장

### 3. **현대적 uv 프로젝트 구성** ✅
   - **pyproject.toml**: Python 표준 프로젝트 설정
   - **uv 기반 가상환경**: 빠른 패키지 관리
   - **개발 도구 통합**: black, ruff, mypy, pytest 완전 설정
   - **Makefile**: 편리한 개발 명령어 (30개+ 명령어)
   - **Docker 최적화**: uv 기반 빠른 빌드

### 4. **새로운 통합 기능** ✅
   - **통합 RabbitMQ 클라이언트**: 일반 크레덴셜 방식 우선, 실패시 AWS MQ로 자동 fallback
   - **향상된 로깅**: Request ID 기반 분산 추적
   - **Prometheus 메트릭**: 모니터링 엔드포인트 지원
   - **정적 파일 서빙**: Swagger UI/ReDoc 리소스 최적화
   - **포괄적 테스트**: pytest 기반 통합 테스트

## 헬스체크

서비스 상태 확인: `GET /status/`

## 모니터링

- Nginx 로그: `/var/log/nginx/`
- 애플리케이션 로그: stdout (Docker logs)
- 메트릭: 각 요청의 Request ID로 추적 가능