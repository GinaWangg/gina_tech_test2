# 技術支援 API 整合測試

## 📋 測試說明

此測試套件使用 pytest 框架測試技術支援 API 的基本功能。

## 🚀 執行測試

### 1. 安裝測試依賴

```powershell
pip install pytest httpx
```

### 2. 執行所有測試

```powershell
# 在專案根目錄執行
pytest tests/ -v

# 或執行特定測試檔案
pytest tests/test_tech_agent_integration.py -v

# 顯示 print 輸出
pytest tests/ -v -s
```

### 3. 執行特定測試案例

```powershell
pytest tests/test_tech_agent_integration.py::test_tech_agent_basic_flow -v
```

## 📝 測試案例

### test_tech_agent_basic_flow
測試使用真實資料（筆電登入畫面卡住問題）呼叫 `/v1/tech_agent` 端點：
- ✅ 驗證 HTTP 狀態碼為 200
- ✅ 驗證回應為 JSON 格式
- ✅ 驗證回應包含必要欄位

測試資料：
```json
{
  "cus_id": "GINA_TEST",
  "session_id": "f6b3ddd8-6c55-4edc-9cf0-8408664cb89d",
  "chat_id": "c516e816-0ad1-44f1-9046-7878bd78b3bc",
  "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
  "websitecode": "tw",
  "product_line": "",
  "system_code": "rog"
}
```

### test_tech_agent_missing_required_fields
測試缺少必要欄位時的錯誤處理：
- ✅ 驗證回傳 422 狀態碼
- ✅ 驗證 FastAPI 自動驗證機制運作正常

## 📊 測試報告

執行後會顯示：
- 測試通過/失敗數量
- 執行時間
- 詳細錯誤訊息（如有失敗）

## 🔧 故障排除

### 問題：ModuleNotFoundError
**解決方案**：確保在專案根目錄執行測試，或檢查 `conftest.py` 的路徑設定。

### 問題：測試超時
**解決方案**：確認 API 服務所需的外部依賴（資料庫、AI 模型等）都已正確設定。

## 📌 注意事項

1. 測試會實際呼叫 API 端點，需要確保所有依賴服務可用
2. 首次執行可能需要載入大量資料（RAG mappings、KB mappings 等）
3. 如需 mock 外部服務，可擴充 `conftest.py` 加入 fixtures
