.PHONY: help install dev lint format test clean run docker-build docker-run init ssl-cert

help: ## 사용 가능한 명령어 목록 표시
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

init: ## 프로젝트 디렉토리 및 SSL 인증서 초기화
	@echo "🚀 CDL Gateway 초기화 중..."
	@mkdir -p logs/{blue,green,nginx}
	@mkdir -p nginx/{ssl,certbot}
	@chmod -R 755 logs nginx/certbot
	@echo "✅ 디렉토리 생성 완료"
	@echo "📋 SSL 인증서 생성을 위해 'make ssl-cert' 실행하세요"

ssl-cert: ## 개발용 자체 서명 SSL 인증서 생성
	@echo "🔐 자체 서명 SSL 인증서 생성 중..."
	@openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout nginx/ssl/key.pem \
		-out nginx/ssl/cert.pem \
		-subj "/C=KR/ST=Seoul/L=Seoul/O=CDL/OU=IT/CN=localhost"
	@chmod 600 nginx/ssl/key.pem
	@chmod 644 nginx/ssl/cert.pem
	@echo "✅ SSL 인증서 생성 완료"
	@echo "  - 개발용 자체 서명 인증서입니다"
	@echo "  - 프로덕션에서는 Let's Encrypt 사용을 권장합니다"

install: ## 프로덕션 종속성 설치
	uv sync --no-dev

dev: ## 개발 종속성 포함 설치
	uv sync

lint: ## 코드 린팅 실행
	uv run ruff check .
	uv run mypy app/

format: ## 코드 포맷팅 실행
	uv run black .
	uv run isort .
	uv run ruff check --fix .

format-check: ## 코드 포맷팅 체크만 실행
	uv run black --check .
	uv run isort --check-only .
	uv run ruff check .

test: ## 테스트 실행
	uv run pytest tests/ -v

clean: ## 임시 파일 정리
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete

run: ## 개발 서버 실행
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## 프로덕션 서버 실행
	uv run gunicorn app.main:app -w 5 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

docker-build: ## Docker 이미지 빌드
	docker build -t cdl-gateway .

docker-run: ## Docker 컨테이너 실행
	docker run -p 8000:8000 --env-file .env cdl-gateway

docker-compose-up: ## Docker Compose로 전체 스택 시작
	docker-compose up -d

docker-compose-down: ## Docker Compose 스택 종료
	docker-compose down

docker-compose-logs: ## Docker Compose 로그 확인
	docker-compose logs -f

# 블루/그린 배포 명령어
blue-deploy: ## 블루 슬롯에 배포
	docker-compose up -d --build cdl-gateway-blue
	@echo "✅ Blue deployment completed"

green-deploy: ## 그린 슬롯에 배포  
	docker-compose up -d --build cdl-gateway-green
	@echo "✅ Green deployment completed"

switch-to-blue: ## 트래픽을 블루 슬롯으로 전환
	docker-compose stop cdl-gateway-green
	@echo "🔵 Switched to BLUE deployment"

switch-to-green: ## 트래픽을 그린 슬롯으로 전환
	docker-compose stop cdl-gateway-blue
	@echo "🟢 Switched to GREEN deployment"

health-check-blue: ## 블루 슬롯 헬스체크
	curl -f http://localhost:18001/status/ && echo "\n✅ Blue is healthy" || echo "\n❌ Blue is not healthy"

health-check-green: ## 그린 슬롯 헬스체크
	curl -f http://localhost:18002/status/ && echo "\n✅ Green is healthy" || echo "\n❌ Green is not healthy"

health-check-all: health-check-blue health-check-green ## 모든 슬롯 헬스체크

deploy-status: ## 배포 상태 확인
	@echo "📊 Deployment Status:"
	@docker-compose ps

ci: format-check lint test ## CI 파이프라인 실행

deploy: init ssl-cert docker-compose-up ## 전체 배포 (init + ssl + docker-compose up)
	@echo "🎉 CDL Gateway 배포 완료!"
	@echo "📋 서비스 상태 확인:"
	@docker-compose ps