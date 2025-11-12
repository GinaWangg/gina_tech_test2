"""
Integration tests for api_structure tech agent endpoint.
Tests /v1/tech_agent endpoint from api_structure module.
"""

import pytest
from fastapi.testclient import TestClient
from api_structure.main import app


@pytest.fixture(scope="module")
def client():
    """Create test client for api_structure FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


def test_tech_agent_api_structure_basic_flow(client):
    """Test basic tech agent flow in api_structure."""
    
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
    assert response.status_code == 200, (
        f"Expected status code 200, got {response.status_code}"
    )
    
    # Verify response is JSON
    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be dict"
    
    # Verify required fields exist
    assert "status" in response_data, "Response should contain 'status'"
    assert "type" in response_data, "Response should contain 'type'"
    assert "message" in response_data, "Response should contain 'message'"
    assert "output" in response_data, "Response should contain 'output'"
    
    # Verify output structure
    output = response_data["output"]
    assert "kb" in output, "Output should contain 'kb'"
    
    print(f"\n✅ Test passed! Response: {response_data}")


def test_tech_agent_api_structure_response_structure(client):
    """Test that api_structure response matches expected structure."""
    
    test_payload = {
        "cus_id": "GINA_TEST",
        "session_id": "test-session-123",
        "chat_id": "test-chat-456",
        "user_input": "My laptop is stuck at the login screen.",
        "websitecode": "tw",
        "product_line": "",
        "system_code": "rog"
    }
    
    response = client.post("/v1/tech_agent", json=test_payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify top-level structure
    assert data["status"] == 200
    assert data["type"] in ["answer", "reask", "handoff"]
    assert isinstance(data["message"], str)
    
    # Verify output structure
    output = data["output"]
    assert isinstance(output["answer"], str)
    assert isinstance(output["ask_flag"], bool)
    assert isinstance(output["hint_candidates"], list)
    assert isinstance(output["kb"], dict)
    
    # Verify KB structure
    kb = output["kb"]
    assert "kb_no" in kb
    assert "title" in kb
    assert "similarity" in kb
    assert isinstance(kb["similarity"], (int, float))
    
    print(f"\n✅ Structure validation passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
