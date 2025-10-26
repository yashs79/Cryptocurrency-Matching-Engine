"""
Test health check endpoint
"""
import pytest
from fastapi.testclient import TestClient
from src.matching_engine.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct response"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Cryptocurrency Matching Engine"
    assert data["status"] == "operational"
    assert "version" in data


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "matching-engine"


def test_docs_available():
    """Test API documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200
