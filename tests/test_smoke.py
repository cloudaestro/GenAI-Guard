import os
import time
import pytest
import requests


@pytest.fixture
def app_url():
    """Get the app URL from environment variable."""
    url = os.getenv("APP_URL")
    if not url:
        pytest.skip("APP_URL environment variable not set")
    return url.rstrip("/")


def test_health_check(app_url):
    """Test that the health check endpoint returns 200."""
    response = requests.get(f"{app_url}/health", timeout=10)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "my-bedrock-proxy"


def test_generate_endpoint_performance(app_url):
    """Test the generate endpoint performance and functionality."""
    payload = {
        "prompt": "Hello, how are you today?",
        "user_id": "test_user_001",
        "max_tokens": 100
    }
    
    start_time = time.time()
    response = requests.post(
        f"{app_url}/generate",
        json=payload,
        timeout=30,
        headers={"Content-Type": "application/json"}
    )
    end_time = time.time()
    
    # Check response status
    assert response.status_code == 200
    
    # Check response structure
    data = response.json()
    assert "response" in data
    assert "tokens_used" in data
    assert "latency_ms" in data
    assert "cost_usd" in data
    
    # Check performance requirement
    latency_seconds = end_time - start_time
    assert latency_seconds < 30.0, f"Request took {latency_seconds:.2f}s, expected < 30s"
    
    # Check data types and ranges
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0
    assert isinstance(data["tokens_used"], int)
    assert data["tokens_used"] > 0
    assert isinstance(data["latency_ms"], float)
    assert data["latency_ms"] > 0
    assert isinstance(data["cost_usd"], float)
    assert data["cost_usd"] > 0


def test_generate_endpoint_with_different_users(app_url):
    """Test the generate endpoint with different user IDs."""
    user_ids = ["user_1", "user_2", "test_analytics_001"]
    
    for user_id in user_ids:
        payload = {
            "prompt": f"Test message for {user_id}",
            "user_id": user_id,
            "max_tokens": 50
        }
        
        response = requests.post(
            f"{app_url}/generate",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["response"]) > 0


def test_generate_endpoint_validation(app_url):
    """Test that the generate endpoint validates input properly."""
    # Test missing prompt
    payload = {
        "user_id": "test_user",
        "max_tokens": 100
    }
    
    response = requests.post(
        f"{app_url}/generate",
        json=payload,
        timeout=10,
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422  # Validation error
    
    # Test missing user_id
    payload = {
        "prompt": "Test prompt",
        "max_tokens": 100
    }
    
    response = requests.post(
        f"{app_url}/generate",
        json=payload,
        timeout=10,
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422  # Validation error


def test_api_documentation(app_url):
    """Test that the API documentation is accessible."""
    response = requests.get(f"{app_url}/docs", timeout=10)
    assert response.status_code == 200
    
    response = requests.get(f"{app_url}/openapi.json", timeout=10)
    assert response.status_code == 200
    
    openapi_data = response.json()
    assert "openapi" in openapi_data
    assert "info" in openapi_data
    assert openapi_data["info"]["title"] == "GenAI Guardian - Bedrock Proxy"


if __name__ == "__main__":
    # For local testing
    if not os.getenv("APP_URL"):
        os.environ["APP_URL"] = "http://localhost:8080"
    
    pytest.main([__file__, "-v"])