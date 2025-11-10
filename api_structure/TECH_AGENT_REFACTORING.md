# Tech Agent API Refactoring

## 概述
本文件說明 `/v1/tech_agent` 端點的重構架構，遵循 AOCC FastAPI 開發規範。

## 架構說明

### 分層結構
```
api_structure/
├── main.py                          # FastAPI 應用主程式
├── core/                            # 核心組件
│   ├── config.py                    # 配置管理
│   ├── logger.py                    # 日誌管理
│   ├── timer.py                     # 計時裝飾器
│   ├── middleware.py                # 中介層
│   └── exception_handlers.py        # 異常處理
└── src/
    ├── models/                      # 資料模型層
    │   └── tech_agent_models.py     # Tech Agent 模型定義
    ├── handlers/                    # 處理器層（業務邏輯）
    │   └── tech_agent_handler.py    # Tech Agent 核心處理邏輯
    ├── pipelines/                   # 協調層
    │   └── tech_agent_pipeline.py   # Tech Agent 流程協調
    ├── routers/                     # 路由層
    │   └── tech_agent_router.py     # Tech Agent API 端點
    └── clients/                     # 客戶端層（外部服務）
        ├── gpt.py
        └── aiohttp_client.py
```

### 資料流向
```
HTTP Request 
    ↓
Router (tech_agent_router.py) - 接收 HTTP 請求
    ↓
Pipeline (tech_agent_pipeline.py) - 協調處理流程
    ↓
Handler (tech_agent_handler.py) - 執行業務邏輯
    ├── @timed 裝飾器 - 記錄執行時間
    ├── 使用 DependencyContainer - 存取服務
    └── set_extract_log - 設定日誌
    ↓
Middleware - 統一記錄請求/回應
    ↓
HTTP Response
```

## 主要組件

### 1. Models (tech_agent_models.py)
定義 API 的輸入輸出資料結構：
- `TechAgentInput`: 請求輸入模型
- `TechAgentResponse`: 回應輸出模型
- `KBInfo`: 知識庫資訊模型

### 2. Handler (tech_agent_handler.py)
核心業務邏輯處理器，包含：
- `TechAgentHandler`: 主要處理類別
- 所有方法都使用 `@timed` 裝飾器追蹤執行時間
- 分步驟處理：
  - `_initialize_chat()`: 初始化對話
  - `_process_history()`: 處理歷史記錄
  - `_get_user_and_scope_info()`: 取得使用者資訊
  - `_search_knowledge_base()`: 搜尋知識庫
  - `_process_kb_results()`: 處理搜尋結果
  - `_generate_response()`: 產生回應
  - `_log_and_save_results()`: 記錄並儲存結果

### 3. Pipeline (tech_agent_pipeline.py)
協調 handler 的執行流程：
- `TechAgentPipeline`: 管理請求處理流程
- 使用 `@timed` 裝飾器追蹤整體執行時間

### 4. Router (tech_agent_router.py)
定義 API 端點：
- `POST /v1/tech_agent`: 技術支援主要端點
- 從 `request.app.state.container` 取得依賴
- 呼叫 pipeline 處理請求

### 5. Main (main.py)
應用程式入口：
- 初始化 `DependencyContainer`
- 載入必要的映射資料（RAG mappings, KB mappings）
- 註冊路由器
- 配置中介層和異常處理器

## 關鍵設計原則

### 1. 依賴注入
所有服務透過 `DependencyContainer` 管理，在 `app.state.container` 中存取：
```python
containers = request.app.state.container
```

### 2. 追蹤與監控
使用 `@timed` 裝飾器追蹤所有重要方法的執行時間：
```python
@timed(task_name="tech_agent_handler_run")
async def run(self) -> Dict[str, Any]:
    # 業務邏輯
    pass
```

### 3. 日誌管理
- 使用 `set_extract_log()` 設定額外的日誌資訊
- 中介層自動記錄所有請求和回應
- 支援 OpenTelemetry 追蹤

### 4. 錯誤處理
- `AbortException`: 無法恢復的錯誤，中止請求
- `WarningException`: 可恢復的錯誤，記錄但繼續執行

## 測試

### 整合測試
位於 `tests/test_tech_agent_integration.py`：
```bash
# 執行測試
pytest tests/test_tech_agent_integration.py -v
```

注意：由於測試環境缺少必要的配置檔和資料庫連線，測試可能會跳過。這是預期行為。

## 使用範例

### API 請求
```bash
curl -X POST "http://localhost:8000/v1/tech_agent" \
  -H "Content-Type: application/json" \
  -d '{
    "cus_id": "test_user",
    "session_id": "session-123",
    "chat_id": "chat-456",
    "user_input": "我的筆電無法開機",
    "websitecode": "tw",
    "product_line": "notebook",
    "system_code": "rog"
  }'
```

### 回應格式
```json
{
  "status": 200,
  "message": "OK",
  "result": [
    {
      "renderId": "uuid",
      "stream": false,
      "type": "avatarTechnicalSupport",
      "message": "回應訊息",
      "remark": [],
      "option": []
    }
  ]
}
```

## 執行應用程式

### 本地開發
```bash
cd api_structure
python main.py
```

### 生產環境
```bash
cd api_structure
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 注意事項

1. **環境變數**: 需要設定以下環境變數：
   - `TECH_OPENAI_GPT41MINI_PAYGO_EU_AZURE_ENDPOINT`
   - `TECH_OPENAI_GPT41MINI_PAYGO_EU_API_KEY`
   - `TECH_OPENAI_GPT41MINI_PAYGO_EU_API_VERSION`
   - `TECH_TRANSLATE_CREDENTIALS`

2. **配置檔案**: 需要以下 pickle 檔案：
   - `config/rag_hint_id_index_mapping.pkl`
   - `config/rag_mappings.pkl`
   - `config/kb_mappings.pkl`

3. **資料庫連線**: 需要 Cosmos DB 和 Redis 的連線設定

## 遷移指南

### 從舊版 main.py 遷移
原本的程式碼位於 `/home/runner/work/gina_tech_test2/gina_tech_test2/main.py`。

主要變更：
1. 將 `TechAgentProcessor` 重構為 `TechAgentHandler`
2. 新增 Pipeline 層協調處理流程
3. 新增 Router 層定義 API 端點
4. 使用 `@timed` 裝飾器替代手動計時
5. 使用 `set_extract_log` 替代直接的日誌輸出
6. 透過 `app.state.container` 存取依賴，而非直接傳遞

### 相容性
新版 API 保持與舊版相同的請求/回應格式，確保向後相容。
