"""
技術支援 API 整合測試
測試 /v1/tech_agent 端點是否能正常處理請求
"""

import pytest
from fastapi.testclient import TestClient
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

    # 驗證 cosmos_data 結構（與原始 main.py 相同）
    assert "id" in response_data, "回應應包含 id 欄位"
    assert "cus_id" in response_data, "回應應包含 cus_id 欄位"
    assert "session_id" in response_data, "回應應包含 session_id 欄位"
    assert "chat_id" in response_data, "回應應包含 chat_id 欄位"
    assert "user_input" in response_data, "回應應包含 user_input 欄位"
    assert "final_result" in response_data, "回應應包含 final_result 欄位"
    assert "extract" in response_data, "回應應包含 extract 欄位"
    assert "user_info" in response_data, "回應應包含 user_info 欄位"
    assert "process_info" in response_data, "回應應包含 process_info 欄位"
    assert "total_time" in response_data, "回應應包含 total_time 欄位"

    # 驗證 final_result 結構
    final_result = response_data["final_result"]
    assert "status" in final_result, "final_result 應包含 status"
    assert "message" in final_result, "final_result 應包含 message"
    assert "result" in final_result, "final_result 應包含 result"
    assert final_result["status"] == 200, "final_result status 應為 200"

    # 驗證 result 陣列
    assert isinstance(
        final_result["result"], list
    ), "final_result result 應為陣列"
    assert len(final_result["result"]) > 0, "final_result result 不應為空"

    # 驗證第一個 render item
    first_item = final_result["result"][0]
    assert "type" in first_item, "render item 應包含 type"
    assert "message" in first_item, "render item 應包含 message"

    # 驗證 user_info 結構
    user_info = response_data["user_info"]
    assert (
        "main_product_category" in user_info
    ), "user_info 應包含 main_product_category"
    assert (
        "sub_product_category" in user_info
    ), "user_info 應包含 sub_product_category"

    # 驗證 process_info 結構
    process_info = response_data["process_info"]
    assert "bot_scope" in process_info, "process_info 應包含 bot_scope"
    assert "search_info" in process_info, "process_info 應包含 search_info"
    assert (
        "is_follow_up" in process_info
    ), "process_info 應包含 is_follow_up"
    assert "faq_pl" in process_info, "process_info 應包含 faq_pl"
    assert "faq_wo_pl" in process_info, "process_info 應包含 faq_wo_pl"
    assert "language" in process_info, "process_info 應包含 language"
    assert "last_info" in process_info, "process_info 應包含 last_info"

    # 驗證 extract 結構
    extract = response_data["extract"]
    assert "status" in extract, "extract 應包含 status"
    assert "type" in extract, "extract 應包含 type"
    assert "message" in extract, "extract 應包含 message"
    assert "output" in extract, "extract 應包含 output"

    print(
        f"\n✅ 測試通過！回應符合 cosmos_data 結構"
        f"\n  - ID: {response_data['id']}"
        f"\n  - User: {response_data['cus_id']}"
        f"\n  - Final result type: {first_item['type']}"
        f"\n  - Extract type: {extract['type']}"
        f"\n  - Total time: {response_data['total_time']}s"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

