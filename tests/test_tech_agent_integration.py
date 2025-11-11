"""
技術支援 API 整合測試
測試 /v1/tech_agent 端點是否能正常處理請求
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(test_app):
    """建立測試用的 FastAPI client"""
    with TestClient(test_app) as test_client:
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
    
    # 驗證回應結構完整性（與原始 API 格式一致）
    assert "status" in response_data, "回應必須包含 status 欄位"
    assert "message" in response_data, "回應必須包含 message 欄位"
    assert "result" in response_data, "回應必須包含 result 欄位"
    
    # 驗證 status 和 message 的值
    assert response_data["status"] == 200, "status 應為 200"
    assert response_data["message"] == "OK", "message 應為 'OK'"
    
    # 驗證 result 是列表
    assert isinstance(response_data["result"], list), "result 應該是列表"
    assert len(response_data["result"]) > 0, "result 不應為空"
    
    # 驗證第一個 render item 的結構
    first_item = response_data["result"][0]
    assert "renderId" in first_item, "render item 必須包含 renderId"
    assert "stream" in first_item, "render item 必須包含 stream"
    assert "type" in first_item, "render item 必須包含 type"
    assert "message" in first_item, "render item 必須包含 message"
    assert "remark" in first_item, "render item 必須包含 remark"
    assert "option" in first_item, "render item 必須包含 option"
    
    # 驗證 type 符合預期（無產品線時應詢問產品線）
    assert first_item["type"] == "avatarAskProductLine", \
        "無產品線時 type 應為 'avatarAskProductLine'"
    
    # 驗證 option 包含產品線選項
    assert isinstance(first_item["option"], list), "option 應該是列表"
    assert len(first_item["option"]) > 0, "option 不應為空"
    
    # 驗證 option 結構
    for opt in first_item["option"]:
        assert "name" in opt, "option 項目必須包含 name"
        assert "value" in opt, "option 項目必須包含 value"
        assert "icon" in opt, "option 項目必須包含 icon"
    
    print(f"\n✅ 測試通過！回應資料: {response_data}")


def test_tech_agent_with_product_line(client):
    """測試有產品線的技術支援流程"""
    
    # 準備測試資料 - 包含產品線
    test_payload = {
        "cus_id": "GINA_TEST",
        "session_id": "test-session-with-pl",
        "chat_id": "test-chat-with-pl",
        "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
        "websitecode": "tw",
        "product_line": "notebook",  # 提供產品線
        "system_code": "rog"
    }
    
    # 發送 POST 請求
    response = client.post("/v1/tech_agent", json=test_payload)
    
    # 驗證回應
    assert response.status_code == 200, f"期望狀態碼 200，實際得到 {response.status_code}"
    
    response_data = response.json()
    assert isinstance(response_data, dict), "回應應該是字典格式"
    
    # 驗證基本結構
    assert "status" in response_data, "回應必須包含 status 欄位"
    assert "message" in response_data, "回應必須包含 message 欄位"
    assert "result" in response_data, "回應必須包含 result 欄位"
    
    # 有產品線時應該回傳技術支援內容
    first_item = response_data["result"][0]
    # 根據相似度，type 可能是 avatarTechnicalSupport 或 avatarText
    assert first_item["type"] in ["avatarTechnicalSupport", "avatarText"], \
        "有產品線時 type 應為技術支援或文字回應"
    
    print(f"\n✅ 有產品線測試通過！type: {first_item['type']}")



if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

