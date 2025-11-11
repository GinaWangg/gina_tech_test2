"""
技術支援 API 整合測試 - api_structure 版本
測試 api_structure/main.py 中的 /v1/tech_agent 端點
"""

import pytest
import sys
from pathlib import Path

# Add api_structure to path
api_structure_path = Path(__file__).parent.parent / "api_structure"
sys.path.insert(0, str(api_structure_path))

from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """建立測試用的 FastAPI client"""
    import main as api_main
    with TestClient(api_main.app) as test_client:
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
    assert response.status_code == 200, \
        f"期望狀態碼 200，實際得到 {response.status_code}"
    
    # 驗證回應內容為 JSON 格式
    response_data = response.json()
    assert isinstance(response_data, dict), "回應應該是字典格式"
    
    # 基本欄位檢查（api_structure 有 middleware wrapper）
    assert "status" in response_data, "回應應包含 status 欄位"
    assert "message" in response_data, "回應應包含 message 欄位"
    assert "data" in response_data, "回應應包含 data 欄位"
    
    # 檢查 data 內容
    data = response_data["data"]
    assert "status" in data, "data 應包含 status 欄位"
    assert "message" in data, "data 應包含 message 欄位"
    assert "result" in data, "data 應包含 result 欄位"
    assert isinstance(data["result"], list), "result 應該是陣列"
    assert len(data["result"]) > 0, "result 不應為空"
    
    # 檢查 result 項目結構
    first_result = data["result"][0]
    assert "renderId" in first_result, "result 項目應包含 renderId"
    assert "type" in first_result, "result 項目應包含 type"
    assert "message" in first_result, "result 項目應包含 message"
    assert "option" in first_result, "result 項目應包含 option"
    
    print(f"\n✅ 測試通過！")
    print(f"狀態碼: {response.status_code}")
    print(f"回應類型: {first_result['type']}")
    print(f"結果數量: {len(data['result'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
