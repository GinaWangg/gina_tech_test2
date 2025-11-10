"""
技術支援 API 整合測試
測試 /v1/tech_agent 端點是否能正常處理請求
"""

import os
import pytest
from fastapi.testclient import TestClient

# Set mock environment variables before importing app
os.environ['MYAPP_GPT4O_API_KEY'] = 'test-key'
os.environ['MYAPP_GPT4O_RESOURCE_ENDPOINT'] = 'https://test-endpoint.com'
os.environ['MYAPP_GPT4O_INTENTDETECT'] = 'test-model'

from api_structure.main import app


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
        "system_code": "rog"
    }
    
    # 發送 POST 請求
    response = client.post("/v1/tech_agent", json=test_payload)
    
    # 驗證回應
    assert response.status_code == 200, f"期望狀態碼 200，實際得到 {response.status_code}"
    
    # 驗證回應內容為 JSON 格式
    response_data = response.json()
    assert isinstance(response_data, dict), "回應應該是字典格式"
    
    # 基本欄位檢查（依實際 API 回應結構調整）
    assert "status" in response_data or "result" in response_data or "message" in response_data, \
        "回應應包含 status、result 或 message 欄位"
    
    print(f"\n✅ 測試通過！回應資料: {response_data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
