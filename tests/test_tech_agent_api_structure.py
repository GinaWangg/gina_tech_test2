"""
技術支援 API 整合測試 - api_structure 版本
測試 api_structure/main.py 的 /v1/tech_agent 端點
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """建立測試用的 FastAPI client for api_structure."""
    from api_structure.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_tech_agent_basic_flow_api_structure(client):
    """測試基本技術支援流程 - 筆電登入畫面卡住問題 (api_structure)."""
    # 準備測試資料
    test_payload = {
        "cus_id": "GINA_TEST",
        "session_id": "f6b3ddd8-6c55-4edc-9cf0-8408664cb89d",
        "chat_id": "c516e816-0ad1-44f1-9046-7878bd78b3bc",
        "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
        "websitecode": "tw",
        "product_line": "",
        "system_code": "rog",
    }

    # 發送 POST 請求
    response = client.post("/v1/tech_agent", json=test_payload)

    # 驗證回應
    assert response.status_code == 200, (
        f"期望狀態碼 200，實際得到 {response.status_code}"
    )

    # 驗證回應內容為 JSON 格式
    response_data = response.json()
    assert isinstance(response_data, dict), "回應應該是字典格式"

    # 基本欄位檢查
    assert "status" in response_data or "result" in response_data or (
        "message" in response_data
    ), "回應應包含 status、result 或 message 欄位"

    # 檢查回應結構
    if "status" in response_data:
        assert response_data["status"] == 200, "Status should be 200"

    if "result" in response_data:
        result = response_data["result"]
        assert isinstance(result, list), "Result should be a list"
        if result:
            first_item = result[0]
            assert "renderId" in first_item, (
                "Result item should have renderId"
            )
            assert "type" in first_item, "Result item should have type"
            assert "message" in first_item, (
                "Result item should have message"
            )

    print(f"\n✅ 測試通過！回應資料: {response_data}")


def test_tech_agent_with_product_line(client):
    """測試帶有產品線的技術支援請求."""
    test_payload = {
        "cus_id": "GINA_TEST",
        "session_id": "test-session-with-pl",
        "chat_id": "test-chat-with-pl",
        "user_input": "筆電電池無法充電",
        "websitecode": "tw",
        "product_line": "Laptops",
        "system_code": "rog",
    }

    response = client.post("/v1/tech_agent", json=test_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)

    print(f"\n✅ 帶產品線測試通過！回應資料: {response_data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
