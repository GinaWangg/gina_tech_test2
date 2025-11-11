"""
技術支援 API 整合測試
測試 /v1/tech_agent 端點是否能正常處理請求
"""

import os

import pytest
from fastapi.testclient import TestClient

# Mock environment variables before importing
os.environ["MYAPP_GPT4O_RESOURCE_ENDPOINT"] = "https://mock.openai.azure.com"
os.environ["MYAPP_GPT4O_API_KEY"] = "mock_key"
os.environ["MYAPP_GPT4O_INTENTDETECT"] = "gpt-4"

# Import api_structure app instead of main
from api_structure.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    """建立測試用的 FastAPI client"""
    with TestClient(app) as test_client:
        yield test_client


def test_tech_agent_basic_flow(client):
    """測試基本技術支援流程 - 筆電登入畫面卡住問題"""

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
    assert (
        response.status_code == 200
    ), f"期望狀態碼 200，實際得到 {response.status_code}"

    # 驗證回應內容為 JSON 格式
    response_data = response.json()
    assert isinstance(response_data, dict), "回應應該是字典格式"

    # Middleware format: {"status": 200, "message": "Success", "data": <actual_data>}
    assert "status" in response_data, "回應應包含 status 欄位"
    assert "message" in response_data, "回應應包含 message 欄位"
    assert "data" in response_data, "回應應包含 data 欄位"

    # 驗證外層狀態碼
    assert (
        response_data["status"] == 200
    ), f"期望 status 為 200，實際得到 {response_data['status']}"

    # 驗證內層數據結構
    data = response_data["data"]
    assert data is not None, "data 欄位不應為 None"
    assert isinstance(data, dict), "data 應該是字典格式"

    # 驗證內層必要欄位
    assert "status" in data, "內層數據應包含 status"
    assert "message" in data, "內層數據應包含 message"
    assert "result" in data, "內層數據應包含 result"

    # 驗證內層狀態碼
    assert data["status"] == 200, f"內層 status 應為 200，實際得到 {data['status']}"

    # 驗證 result 結構
    assert isinstance(data["result"], list), "result 應該是列表格式"
    assert len(data["result"]) > 0, "result 不應該為空"

    # 驗證第一個 render item 的基本結構
    first_render = data["result"][0]
    assert "renderId" in first_render, "render item 應包含 renderId"
    assert "type" in first_render, "render item 應包含 type"
    assert "message" in first_render, "render item 應包含 message"
    assert "option" in first_render, "render item 應包含 option"

    print("\n✅ 測試通過！")
    print(
        f"外層回應: status={response_data['status']}, "
        f"message={response_data['message']}"
    )
    print(
        f"內層數據: status={data['status']}, "
        f"message={data['message']}, "
        f"render_type={first_render['type']}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
