# Tech Agent API 重構說明文件

## 概述

本文件說明將 `main.py` 中的 `/v1/tech_agent` 端點重構至 `api_structure/` 的完整過程。重構後的程式碼完全遵循 AOCC FastAPI 專案標準，並保持與原系統相同的功能行為。

## 重構目標

- ✅ 將 `/v1/tech_agent` 從 `main.py` 重構至 `api_structure/`
- ✅ 遵循 AOCC FastAPI 分層架構標準
- ✅ 保持功能行為與回傳結果一致
- ✅ 使用 mock 資料替代無法連線的外部服務
- ✅ 通過所有整合測試

## 架構設計

### 分層架構

重構後的程式碼遵循以下分層架構：

```
Clients → Routers → Handlers → Models
```

### 目錄結構

```
api_structure/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── tech_agent_models.py          # Pydantic 模型定義
│   │
│   ├── clients/
│   │   ├── aiohttp_client.py
│   │   ├── gpt.py
│   │   ├── gemini.py
│   │   └── mock_container.py              # Mock 依賴容器
│   │
│   ├── handlers/
│   │   ├── tech_agent_handler.py          # 核心業務邏輯
│   │   └── ...
│   │
│   └── routers/
│       ├── __init__.py
│       └── tech_agent_router.py           # API 路由定義
│
├── core/
│   ├── config.py                          # 配置管理
│   ├── logger.py                          # 日誌工具
│   ├── timer.py                           # @timed 裝飾器
│   ├── middleware.py                      # 中間件
│   └── exception_handlers.py              # 錯誤處理
│
└── main.py                                # FastAPI 應用程式入口
```

## 核心模組說明

### 1. Models (`tech_agent_models.py`)

定義 API 的請求與回應模型：

- `TechAgentInput`: API 輸入模型
  - `cus_id`: 客戶 ID
  - `session_id`: 會話 ID
  - `chat_id`: 聊天 ID
  - `user_input`: 使用者輸入
  - `websitecode`: 網站代碼
  - `product_line`: 產品線
  - `system_code`: 系統代碼

- `TechAgentResponse`: API 回應模型
  - `status`: 狀態碼
  - `type`: 回應類型 (answer/reask/handoff)
  - `message`: 訊息
  - `output`: 輸出資料

- `KBInfo`: 知識庫資訊模型
- `HintCandidate`: 提示候選模型

### 2. Clients (`mock_container.py`)

模擬依賴容器，提供所有外部服務的 mock 實作：

- `MockCosmosSettings`: 模擬 Cosmos DB 操作
- `MockRedisConfig`: 模擬 Redis 操作
- `MockServiceDiscriminator`: 模擬服務分類器
- `MockSentenceGroupClassification`: 模擬句子分組
- `MockBaseService`: 模擬基礎服務（GPT 呼叫）
- `MockDependencyContainer`: 主容器，整合所有 mock 服務

**重要**: 所有外部 API 呼叫都已註解並標註 `# TODO: Enable when environment ready`

### 3. Handlers (`tech_agent_handler.py`)

核心業務邏輯處理器：

```python
class TechAgentHandler:
    """Tech agent 處理器
    
    處理流程:
    1. 初始化聊天會話
    2. 處理歷史記錄
    3. 取得使用者資訊與範圍
    4. 搜尋知識庫
    5. 處理搜尋結果
    6. 生成回應
    7. 記錄結果
    """
    
    @timed(task_name="tech_agent_process")
    async def run(self, log_record: bool = True) -> Dict:
        """主要處理流程"""
        ...
```

**特性**:
- 使用 `@timed` 裝飾器進行 OpenTelemetry 追蹤
- 完整的錯誤處理與日誌記錄
- 支援三種回應情境：
  - 無產品線：詢問產品線
  - 高相似度：提供知識庫答案
  - 低相似度：建議轉人工

### 4. Routers (`tech_agent_router.py`)

API 路由定義：

```python
@router.post("/tech_agent")
async def tech_agent_endpoint(
    user_input: TechAgentInput, 
    request: Request
) -> dict:
    """技術支援 API 端點"""
    container = request.app.state.tech_agent_container
    handler = TechAgentHandler(container=container, user_input=user_input)
    return await handler.run(log_record=True)
```

### 5. Main (`api_structure/main.py`)

FastAPI 應用程式入口：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 初始化 aiohttp client
    aiohttp_client = AiohttpClient(...)
    await aiohttp_client.initialize()
    app.state.aiohttp_client = aiohttp_client
    
    # 初始化 tech agent container
    tech_agent_container = MockDependencyContainer()
    await tech_agent_container.init_async()
    app.state.tech_agent_container = tech_agent_container
    
    yield
    
    # 清理資源
    await aiohttp_client.close()
    await tech_agent_container.close()

app = FastAPI(lifespan=lifespan)
app.include_router(tech_agent_router)
```

## 外部依賴 Stubbing 策略

### 已 Stubbed 的服務

1. **Cosmos DB**
   - 所有 query/insert 操作已註解
   - 使用 mock 資料回傳
   - 標註: `# TODO: Enable when environment ready`

2. **Redis API**
   - 所有 HTTP 呼叫已註解
   - 使用固定 mock 回傳值
   - 標註: `# TODO: Enable when environment ready`

3. **GPT API**
   - GPT 呼叫已註解
   - 使用簡單的文字回傳
   - 標註: `# TODO: Enable when environment ready`

4. **Translation API**
   - 翻譯服務已註解
   - 使用語言代碼映射
   - 標註: `# TODO: Enable when environment ready`

### Mock 資料範例

```python
# KB Mappings Mock
self.KB_mappings = {
    "1041668_zh-tw": {
        "kb_no": "1041668",
        "title": "筆電無法開機或卡在登入畫面",
        "content": "如果您的筆電卡在登入畫面，請嘗試以下步驟...",
        "summary": "筆電登入問題排除",
    },
}

# Product Line Mappings Mock
self.PL_mappings = {
    "tw": ["notebook", "desktop", "phone", "monitor"],
    "us": ["notebook", "desktop", "phone", "monitor"],
}
```

## 測試

### 整合測試

測試檔案: `tests/test_tech_agent_integration.py`

```bash
# 執行測試
python -m pytest tests/test_tech_agent_integration.py -v -s

# 預期結果
✅ 測試通過！回應資料: {
  'status': 200, 
  'message': 'OK', 
  'result': [...]
}
```

### 測試案例

```python
test_payload = {
    "cus_id": "GINA_TEST",
    "session_id": "f6b3ddd8-6c55-4edc-9cf0-8408664cb89d",
    "chat_id": "c516e816-0ad1-44f1-9046-7878bd78b3bc",
    "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
    "websitecode": "tw",
    "product_line": "",
    "system_code": "rog"
}
```

### 預期回應

```json
{
  "status": 200,
  "message": "OK",
  "result": [
    {
      "renderId": "...",
      "stream": false,
      "type": "avatarTechnicalSupport",
      "message": "根據您的問題，我找到了相關的解決方案。",
      "remark": [],
      "option": [
        {
          "type": "faqcards",
          "cards": [
            {
              "link": "https://rog.asus.com/tw/support/FAQ/1041668",
              "title": "筆電無法開機或卡在登入畫面",
              "content": "如果您的筆電卡在登入畫面，請嘗試以下步驟..."
            }
          ]
        }
      ]
    }
  ]
}
```

## 程式碼品質

### 格式化工具

所有程式碼已通過以下工具檢查：

- ✅ **black**: Python 程式碼格式化
- ✅ **isort**: Import 排序
- ✅ **flake8**: 程式碼檢查 (max-line-length=88)

### 執行格式化

```bash
# Black 格式化
python -m black api_structure/src/

# isort 排序
python -m isort api_structure/src/

# flake8 檢查
python -m flake8 api_structure/src/ --max-line-length=88 --extend-ignore=E203,W503
```

## 執行方式

### 啟動 API 服務

```bash
# 使用 api_structure 版本
python -m api_structure.main

# 或使用 uvicorn
uvicorn api_structure.main:app --host 127.0.0.1 --port 8000 --reload
```

### 測試 API

```bash
curl -X POST http://127.0.0.1:8000/v1/tech_agent \
  -H "Content-Type: application/json" \
  -d '{
    "cus_id": "GINA_TEST",
    "session_id": "test-session-001",
    "chat_id": "test-chat-001",
    "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
    "websitecode": "tw",
    "product_line": "",
    "system_code": "rog"
  }'
```

## 待完成事項

### 環境準備後需要恢復的功能

1. **Cosmos DB 連線**
   - 取消註解 `mock_container.py` 中的 Cosmos 相關程式碼
   - 設定環境變數: `TECH_COSMOS_URL`, `TECH_COSMOS_KEY`
   - 更新 `CosmosConfig` 類別以使用真實連線

2. **Redis API 連線**
   - 取消註解 `mock_container.py` 中的 Redis 相關程式碼
   - 設定環境變數: `TECH_REDIS_E50_URL`
   - 更新 API 呼叫以使用真實 endpoint

3. **GPT API 連線**
   - 取消註解 GPT 呼叫程式碼
   - 設定 Azure OpenAI 環境變數
   - 測試 GPT 回應品質

4. **Translation API**
   - 恢復翻譯服務連線
   - 設定 Google Translation credentials

### 搜尋並恢復所有註解

```bash
# 搜尋所有 TODO 標記
grep -r "TODO: Enable when environment ready" api_structure/
```

## 遷移建議

### 從 main.py 遷移到 api_structure

1. **保持雙版本運行**
   - 暫時保留 `main.py` 的原始實作
   - 同時運行 `api_structure/main.py` 進行測試
   - 確認功能完全一致後再移除 `main.py`

2. **逐步恢復真實連線**
   - 先恢復一個外部服務（如 Cosmos DB）
   - 測試該服務的所有功能
   - 確認無誤後再恢復下一個服務

3. **監控與日誌**
   - 使用 OpenTelemetry 追蹤所有請求
   - 比較新舊版本的效能差異
   - 記錄所有錯誤與異常

## 檔案清單

### 新增檔案

- `api_structure/src/models/__init__.py`
- `api_structure/src/models/tech_agent_models.py`
- `api_structure/src/clients/mock_container.py`
- `api_structure/src/handlers/tech_agent_handler.py`
- `api_structure/src/routers/__init__.py`
- `api_structure/src/routers/tech_agent_router.py`

### 修改檔案

- `api_structure/main.py` - 註冊 tech_agent router 與初始化 container
- `api_structure/core/logger.py` - 添加 logger 實例
- `tests/test_tech_agent_integration.py` - 更新為使用 api_structure.main

## 參考資料

- [AOCC FastAPI 標準](.github/copilot-instructions.md)
- [Python 編碼規範](.github/instructions/python.instructions.md)
- [原始 tech_agent_api.py](src/core/tech_agent_api.py)
- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
- [Pydantic 官方文檔](https://docs.pydantic.dev/)

## 聯絡資訊

如有任何問題或建議，請聯絡：
- GitHub Issue: [GinaWangg/gina_tech_test2](https://github.com/GinaWangg/gina_tech_test2/issues)

---

最後更新: 2025-11-11
版本: 1.0.0
