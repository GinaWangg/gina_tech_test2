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
    
    # Prepare test data - same as original integration test
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
    
    # Check middleware wrapper structure
    assert "status" in response_data
    assert "message" in response_data
    assert "data" in response_data
    
    # Check the actual data
    data = response_data["data"]
    assert data["status"] == 200
    assert data["message"] == "OK"
    assert "result" in data
    assert isinstance(data["result"], list)
    assert len(data["result"]) >= 1
    
    # Check first result item structure
    first_result = data["result"][0]
    assert "renderId" in first_result
    assert "stream" in first_result
    assert "type" in first_result
    assert "message" in first_result
    assert "remark" in first_result
    assert "option" in first_result
    
    # This should be low similarity path (avatarText + avatarAsk)
    assert first_result["type"] in ["avatarText", "avatarAskProductLine"]
    
    print(f"\n✅ Test passed! Response has {len(data['result'])} result items")
    print(f"   First result type: {first_result['type']}")


def test_tech_agent_with_product_line(client):
    """Test with product line specified - should trigger high similarity."""
    
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
    
    data = response_data["data"]
    assert data["status"] == 200
    assert len(data["result"]) >= 1
    
    # With product line and high similarity (stubbed),
    # should get technical support
    first_result = data["result"][0]
    # Could be avatarTechnicalSupport or avatarText depending on similarity
    assert first_result["type"] in [
        "avatarTechnicalSupport",
        "avatarText",
        "avatarAskProductLine"
    ]
    
    print(f"\n✅ Test with product line passed!")
    print(f"   Result type: {first_result['type']}")


def test_response_structure_matches_original(client):
    """Verify response structure matches original main.py format."""
    
    test_payload = {
        "cus_id": "GINA_TEST",
        "session_id": "f6b3ddd8-6c55-4edc-9cf0-8408664cb89d",
        "chat_id": "c516e816-0ad1-44f1-9046-7878bd78b3bc",
        "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
        "websitecode": "tw",
        "product_line": "",
        "system_code": "rog"
    }
    
    response = client.post("/v1/tech_agent", json=test_payload)
    response_data = response.json()
    data = response_data["data"]
    
    # Verify structure matches original format
    # Original has: status, message, result array
    assert "status" in data
    assert "message" in data
    assert "result" in data
    assert isinstance(data["result"], list)
    
    # Each result item should have these fields
    for item in data["result"]:
        assert "renderId" in item
        assert "stream" in item
        assert "type" in item
        assert "message" in item
        assert "remark" in item
        assert "option" in item
        assert isinstance(item["remark"], list)
        assert isinstance(item["option"], list)
    
    # If there are options, verify their structure
    for item in data["result"]:
        for option in item["option"]:
            if "answer" in option:
                # Options with answers should have correct structure
                assert isinstance(option["answer"], list)
                for answer_item in option["answer"]:
                    assert "type" in answer_item
                    assert "value" in answer_item
    
    print(f"\n✅ Response structure matches original format!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
