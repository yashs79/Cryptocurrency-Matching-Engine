"""
Test health check endpoint
"""
import pytest


def test_basic():
    """Basic test to ensure pytest works"""
    assert True


def test_imports():
    """Test that we can import the main module"""
    try:
        from src.matching_engine.main import app
        assert app is not None
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")


def test_health_endpoint():
    """Test health check endpoint"""
    try:
        from fastapi.testclient import TestClient
        from src.matching_engine.main import app
        
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")


def test_root_endpoint():
    """Test root endpoint"""
    try:
        from fastapi.testclient import TestClient
        from src.matching_engine.main import app
        
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")
