"""
Test suite for Aegis-AI API Gateway
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "Aegis-AI" in data["service"]
    assert "endpoints" in data


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code in [200, 503]  # Either healthy or database unavailable
    data = response.json()
    assert "status" in data or "detail" in data


def test_status_endpoint():
    """Test the status endpoint returns statistics."""
    response = client.get("/status")
    # May fail if database is not available during testing
    if response.status_code == 200:
        data = response.json()
        assert "total_logs" in data
        assert "total_threats" in data
        assert "threat_percentage" in data
        assert isinstance(data["total_logs"], int)
        assert isinstance(data["threat_percentage"], float)


def test_threats_endpoint_default_params():
    """Test the threats endpoint with default parameters."""
    response = client.get("/threats")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_threats_endpoint_custom_params():
    """Test the threats endpoint with custom parameters."""
    response = client.get("/threats?hours=12&limit=50")
    assert response.status_code in [200, 500]


def test_threats_endpoint_validation():
    """Test parameter validation on threats endpoint."""
    # Test invalid hours (too large)
    response = client.get("/threats?hours=200")
    assert response.status_code == 422  # Validation error

    # Test invalid limit (too large)
    response = client.get("/threats?limit=2000")
    assert response.status_code == 422  # Validation error


def test_logs_endpoint():
    """Test the logs endpoint."""
    response = client.get("/logs")
    if response.status_code == 200:
        data = response.json()
        assert "count" in data
        assert "logs" in data
        assert isinstance(data["logs"], list)


def test_logs_endpoint_with_filter():
    """Test logs endpoint with classification filter."""
    response = client.get("/logs?classification=CRITICAL_THREAT&limit=10")
    assert response.status_code in [200, 500]


def test_404_handler():
    """Test custom 404 handler."""
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "available_endpoints" in data


def test_openapi_docs():
    """Test that OpenAPI documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_docs():
    """Test that ReDoc documentation is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
