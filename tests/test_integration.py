"""통합 테스트"""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """테스트 클라이언트 픽스처"""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """헬스체크 엔드포인트 테스트"""
    response = client.get("/status/")
    assert response.status_code == 200
    assert "Health Check OK" in response.text


def test_root_endpoint_validation_error(client):
    """루트 엔드포인트 유효성 검사 에러 테스트"""
    response = client.post("/", json={})
    assert response.status_code == 422
    
    data = response.json()
    assert data["status"] == 422
    assert ("missing" in data["message"].lower() or "required" in data["message"].lower())


def test_root_endpoint_valid_request(client):
    """루트 엔드포인트 유효한 요청 테스트 (RabbitMQ 연결 실패 예상)"""
    valid_request = {
        "edu_key": 123,
        "edu_type": 1,
        "member_key": 456,
        "company_key": 789
    }
    
    response = client.post("/", json=valid_request)
    # RabbitMQ 연결 실패로 500 에러 예상
    assert response.status_code == 500
    
    data = response.json()
    assert data["status"] == 500
    assert "error" in data["detail"].lower()


def test_openapi_schema(client):
    """OpenAPI 스키마 테스트"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert schema["info"]["title"] == "CDL Gateway"
    assert "paths" in schema
    assert "/" in schema["paths"]
    assert "/status/" in schema["paths"]


def test_docs_endpoints(client):
    """문서 엔드포인트 테스트"""
    # Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200
    
    # ReDoc
    response = client.get("/redoc")
    assert response.status_code == 200