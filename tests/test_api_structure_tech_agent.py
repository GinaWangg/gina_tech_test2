"""
Test for api_structure tech_agent endpoint.
This tests the refactored version in api_structure/.
"""

import pytest
import sys
from pathlib import Path

# Add api_structure to path BEFORE any other imports
api_structure_path = Path(__file__).parent.parent / "api_structure"
sys.path.insert(0, str(api_structure_path))

from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create test client for api_structure app."""
    # Import here to use the modified sys.path
    import main as api_main
    with TestClient(api_main.app) as test_client:
        yield test_client


def test_tech_agent_basic_flow(client):
    """Test basic technical support flow - laptop login screen issue."""
    
    # Prepare test data
    test_payload = {
        "cus_id": "GINA_TEST",
        "session_id": "f6b3ddd8-6c55-4edc-9cf0-8408664cb89d",
        "chat_id": "c516e816-0ad1-44f1-9046-7878bd78b3bc",
        "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
        "websitecode": "tw",
        "product_line": "",
        "system_code": "rog"
    }
    
    # Send POST request
    response = client.post("/v1/tech_agent", json=test_payload)
    
    # Verify response
    assert response.status_code == 200, \
        f"Expected status 200, got {response.status_code}"
    
    # Verify response is JSON
    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be dict"
    
    # Basic field checks
    assert "status" in response_data or "result" in response_data \
        or "message" in response_data, \
        "Response should contain status, result or message field"
    
    # If middleware is working, check the structure
    if "data" in response_data:
        data = response_data["data"]
        assert "status" in data
        assert "message" in data
        assert "result" in data
        assert isinstance(data["result"], list)
    else:
        # Direct response from handler
        assert "status" in response_data
        assert "message" in response_data
        assert "result" in response_data
        assert isinstance(response_data["result"], list)
    
    print(f"\n✅ Test passed! Response: {response_data}")


def test_tech_agent_with_product_line(client):
    """Test with product line specified."""
    
    test_payload = {
        "cus_id": "GINA_TEST",
        "session_id": "test-session-123",
        "chat_id": "test-chat-456",
        "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
        "websitecode": "tw",
        "product_line": "notebook",
        "system_code": "rog"
    }
    
    response = client.post("/v1/tech_agent", json=test_payload)
    
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    
    print(f"\n✅ Test with product line passed! Response: {response_data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
