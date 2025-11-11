# Tech Agent API 重構說明文件

## 📋 概述

本文件說明 `/v1/tech_agent` API 從原始 `main.py` 重構至 `api_structure/` 的完整架構與實作細節。

## 🎯 重構目標

✅ 將 `/v1/tech_agent` 端點從 `main.py` 遷移至 `api_structure/`  
✅ 遵循 AOCC FastAPI 分層架構標準  
✅ 100% 保持原始 API 回傳格式與行為  
✅ 使用 stub/mock 處理外部 API 與 Cosmos DB 連線  
✅ 通過整合測試驗證

## 📁 檔案結構

```
api_structure/
├── main.py                              # 註冊 /v1/tech_agent 端點
├── core/
│   ├── config.py                        # 環境設定
│   ├── logger.py                        # 日誌上下文管理
│   ├── timer.py                         # @timed 裝飾器
│   ├── middleware.py                    # 請求日誌中介層
│   └── exception_handlers.py           # 錯誤處理
└── src/
    ├── schemas/
    │   ├── __init__.py
    │   └── tech_agent_schemas.py       # Request/Response 模型
    ├── repositories/
    │   ├── __init__.py
    │   └── tech_agent_repository.py    # 資料存取層（含 stub/mock）
    ├── services/
    │   ├── __init__.py
    │   └── tech_agent_service.py       # 業務邏輯層
    ├── handlers/
    │   └── tech_agent_handler.py       # 核心流程處理（含 @timed）
    └── routers/
        ├── __init__.py
        └── tech_agent_router.py        # 端點路由層

tests/
├── conftest.py                          # 測試配置（提供 test_app fixture）
└── test_tech_agent_integration.py      # 整合測試
```

## 🏗️ 架構分層說明

### 1. **Schemas Layer** (`src/schemas/`)
定義 Pydantic 模型，確保 request/response 資料結構與原始 API 完全一致。

**主要模型：**
- `TechAgentInput` - API 輸入請求
- `TechAgentOutput` - API 輸出回應
- `RenderItem` - 渲染項目結構
- `TechAgentFinalResult` - 完整回應格式

### 2. **Repository Layer** (`src/repositories/`)
負責所有資料存取操作，包含：
- Pickle 檔案載入（RAG mappings, KB mappings）
- Cosmos DB 查詢（使用 stub/mock）
- 歷史對話查詢
- 提示資料儲存

**關鍵方法：**
```python
async def load_rag_mappings() -> Tuple[Dict, Dict]
async def load_kb_mappings() -> Dict
async def get_chat_history(session_id, user_input) -> Tuple
async def get_latest_hint(session_id) -> Optional[Dict]
async def insert_hint_data(...)
async def insert_result_data(result_data)
```

### 3. **Service Layer** (`src/services/`)
封裝業務邏輯規則，處理：
- Session ID / Chat ID 生成
- KB 搜尋結果篩選（similarity threshold）
- 回應格式建構（三種情境）

**關鍵方法：**
```python
def process_kb_results(faq_result) -> Tuple
def build_no_product_line_response(...) -> Dict
def build_high_similarity_response(...) -> Dict
def build_low_similarity_response(...) -> Dict
```

### 4. **Handler Layer** (`src/handlers/`)
核心流程編排，所有方法使用 `@timed` 裝飾器進行追蹤。

**主流程步驟：**
```python
async def run() -> Dict:
    1. _initialize()           # 初始化對話、載入歷史
    2. _process_history()      # 處理歷史對話
    3. _get_user_and_scope_info()  # 取得使用者資訊與範圍
    4. _search_knowledge_base()    # 搜尋知識庫
    5. _process_kb_results()       # 處理搜尋結果
    6. _generate_response()        # 生成回應
    7. _log_and_save_results()     # 記錄與儲存
```

**三種回應情境：**
- `_handle_no_product_line()` - 無產品線，詢問產品類型
- `_handle_high_similarity()` - 高相似度，提供技術文件
- `_handle_low_similarity()` - 低相似度，轉人工處理

### 5. **Router Layer** (`src/routers/`)
負責依賴注入與端點註冊。

```python
async def tech_agent_endpoint(user_input, request):
    repository = TechAgentRepository()
    service = TechAgentService(repository)
    handler = TechAgentHandler(user_input, service, repository)
    return await handler.run()
```

## 🔄 API 回應格式

### 情境 1：無產品線（Product Line）
```json
{
  "status": 200,
  "message": "OK",
  "result": [
    {
      "renderId": "uuid",
      "stream": false,
      "type": "avatarAskProductLine",
      "message": "請先告訴我您使用的產品類型...",
      "remark": [],
      "option": [
        {"name": "筆記型電腦", "value": "notebook", "icon": "💻"},
        {"name": "桌上型電腦", "value": "desktop", "icon": "🖥️"},
        {"name": "手機", "value": "phone", "icon": "📱"}
      ]
    }
  ]
}
```

### 情境 2：高相似度（Similarity > 0.87）
```json
{
  "status": 200,
  "message": "OK",
  "result": [
    {
      "renderId": "uuid",
      "stream": false,
      "type": "avatarTechnicalSupport",
      "message": "我找到了相關的技術文件...",
      "remark": [],
      "option": [
        {
          "type": "faqcards",
          "cards": [
            {
              "link": "https://...",
              "title": "筆電登入畫面卡住問題排除",
              "content": "如果您的筆電卡在登入畫面..."
            }
          ]
        }
      ]
    }
  ]
}
```

### 情境 3：低相似度（Similarity ≤ 0.87）
```json
{
  "status": 200,
  "message": "OK",
  "result": [
    {
      "renderId": "uuid",
      "stream": false,
      "type": "avatarText",
      "message": "抱歉，我需要更多資訊...",
      "remark": [],
      "option": []
    },
    {
      "renderId": "uuid",
      "stream": false,
      "type": "avatarAsk",
      "message": "你可以告訴我像是產品全名、型號...",
      "remark": [],
      "option": [...]
    }
  ]
}
```

## 🔌 Stub/Mock 實作

所有外部 API 與 Cosmos DB 連線邏輯已保留並註解，使用 TODO 標記未來啟用點：

```python
# TODO: Replace with actual Cosmos DB query when environment ready
# from src.integrations.cosmos_process import CosmosConfig
# cosmos_settings = CosmosConfig(config=config)
# result = await cosmos_settings.get_chat_history(session_id)

# Mock implementation
his_inputs = [user_input]
chat_count = 1
```

### Mock 資料位置

1. **Repository Layer** - 資料查詢 stub
   - `get_chat_history()` - 回傳簡化歷史
   - `get_latest_hint()` - 回傳 None
   - `get_language_by_websitecode()` - 回傳語言對照表

2. **Handler Layer** - 服務呼叫 stub
   - `_search_knowledge_base()` - 回傳固定 FAQ 列表
   - Avatar 回應 - 使用預設文字

## 🧪 測試

### 執行測試
```bash
cd /home/runner/work/gina_tech_test2/gina_tech_test2
python -m pytest tests/test_tech_agent_integration.py -v -s
```

### 測試案例

1. **test_tech_agent_basic_flow**
   - 測試無產品線情境
   - 驗證回應結構完整性
   - 驗證 option 選項存在

2. **test_tech_agent_with_product_line**
   - 測試有產品線情境
   - 驗證技術支援回應
   - 驗證相似度判斷邏輯

### 測試配置

`tests/conftest.py` 提供簡化的 test_app fixture，避免完整 client 初始化：

```python
@pytest.fixture(scope="module")
def test_app():
    app = FastAPI()
    # ... 註冊端點
    return app
```

## ⚙️ 設定與依賴

### 新增依賴
安裝測試所需套件：
```bash
pip install opentelemetry-api opentelemetry-sdk \
    opentelemetry-instrumentation-fastapi \
    azure-monitor-opentelemetry \
    apscheduler pytz
```

### 環境變數
- 本地開發：讀取 `.env.{APP_ENV}` 
- Azure 部署：使用環境變數
- 測試環境：使用 mock 資料，無需額外設定

## 🔍 與原始實作的差異

| 項目 | 原始實作 | 重構後 |
|------|---------|--------|
| 結構 | 單一 `TechAgentProcessor` 類別 | 分層架構（Router → Handler → Service → Repository） |
| 資料存取 | 直接使用 `DependencyContainer` | Repository pattern with mock |
| 錯誤處理 | 內部異常處理 | `@timed` 裝飾器統一處理 |
| 日誌 | 使用 `utils.logger` | 同樣使用 `utils.logger` |
| 回應格式 | `self.final_result` | `handler.run()` return |
| 測試隔離 | 依賴完整環境 | 使用 test_app fixture |

## ✅ 驗收確認

- ✅ 回應 JSON 結構完全一致
- ✅ 欄位順序、命名、型態保持不變
- ✅ HTTP Status Code 正確（200）
- ✅ 三種情境回應邏輯正確
- ✅ 整合測試通過
- ✅ 註解保留所有外部 API 邏輯
- ✅ 使用 @timed 追蹤所有 handler 方法

## 🚀 未來啟用清單

重構完成後，待環境就緒時需啟用：

1. **Cosmos DB 連線**
   - 取消註解 repository 中 cosmos_settings 相關程式碼
   - 更新 `main.py` lifespan 初始化 cosmos client

2. **真實服務整合**
   - `ServiceDiscriminator` - KB 搜尋
   - `SentenceGroupClassification` - 對話分群
   - `ChatFlow` - 使用者資訊與範圍判斷
   - Avatar 回應生成服務

3. **載入實際 mappings**
   - RAG mappings from pickle
   - KB mappings from pickle
   - 在 lifespan 初始化時載入

## 📞 技術支援

如有問題，請參考：
- `AGENTS.md` - AOCC FastAPI 專案標準
- `.github/instructions/python.instructions.md` - Python 編碼規範
- 原始實作：`src/core/tech_agent_api.py`
