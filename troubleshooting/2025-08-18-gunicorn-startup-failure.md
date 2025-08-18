## Gunicorn 기동 실패 트러블슈팅 (2025-08-18)

### 증상
- 컨테이너가 재시작 루프에 빠짐. `Worker failed to boot`.
- 로그에 `pydantic_core.ValidationError: ... Field required`가 13개 항목으로 반복 발생.

### 원인
- `pydantic-settings`가 `Settings()` 인스턴스화 시점에 필수 환경변수를 검증하는데, 애플리케이션 import 시점에 초기화가 실행되어 AWS Secrets가 주입되기 전에 검증이 발생함.
- 동시에 Secrets를 코드(main.py)와 시작 스크립트(start.sh)에서 이중으로 로드하여 로그가 중복 출력되고, 초기 부팅 타이밍 경합을 유발.

### 조치 내역
1) 시작 스크립트 개선
   - `scripts/start.sh`를 POSIX sh 호환으로 변경.
   - `uv run python ./scripts/export-secrets.py` 결과를 `eval`로 적용하여 Secrets를 셸 환경에 선주입.
   - Gunicorn 로그를 stdout/stderr로 출력하도록 변경.

2) 설정 로더 안정화
   - `app/core/config.py`를 Pydantic v2 방식(`SettingsConfigDict`)으로 수정.
   - `Settings`를 즉시 생성하지 않고 `LazySettings`로 지연 로딩.
   - 환경변수 미로딩 시 초기 부팅이 깨지지 않도록 필드를 Optional로 전환하고, 실제 사용 지점에서 검증되도록 조정.
   - `main.py`의 Secrets 로드를 제거하여 시작 스크립트 단일 경로로 일원화.

3) Docker 빌드 개선
   - `Dockerfile`의 `uv` 설치를 스크립트 방식으로 교체(BuildKit 불필요).

4) Compose 경고 정리
   - `version: '3.8'` 제거하여 경고 해소.

5) 클린 재배포 절차 수행
   - down -v, 이미지/볼륨/빌더 캐시 prune, 이미지 재빌드, compose 재기동.

### 결과
- `/status/` 200 응답 확인, Gunicorn 워커 "Application startup complete" 로그 정상.

### 재발 방지 가이드
- Secrets 로딩은 단일 경로(start.sh)로 유지하고, 애플리케이션 import 단계에서 환경 의존 초기화를 피함.
- 필수 설정은 실제 사용 직전 검증하도록 설계.

### 유용한 명령어
```
docker-compose -f deployment/docker-compose.prod.yml down -v --remove-orphans
docker system prune -af --volumes && docker builder prune -af
docker build -t cdl-gateway:latest .
docker-compose -f deployment/docker-compose.prod.yml up -d
curl -fsS http://localhost:8000/status/
```

