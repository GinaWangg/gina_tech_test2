# Tech Agent Configuration Guide

## 切換模式說明

重構後的 `/v1/tech_agent` 端點支援兩種運行模式：

### 1. Mock 模式（預設）

使用固定的模擬回應，不需要外部 API 或資料庫權限。

**設定方式：**

在 `api_structure/src/handlers/tech_agent_handler.py` 中：
```python
USE_MOCK_RESPONSES = True  # 使用模擬回應
```

在 `api_structure/main.py` 中：
```python
USE_MOCK_CONTAINER = True  # 使用簡化的 MockContainer
```

**特點：**
- ✅ 不需要環境變數
- ✅ 不需要 API 權限
- ✅ 快速測試和開發
- ✅ 返回固定格式的回應
- ❌ 無法進行真實的知識庫搜尋

### 2. Real 模式

使用真實的 API 調用和資料庫連接。

**設定方式：**

在 `api_structure/src/handlers/tech_agent_handler.py` 中：
```python
USE_MOCK_RESPONSES = False  # 使用真實 API
```

在 `api_structure/main.py` 中：
```python
USE_MOCK_CONTAINER = False  # 使用真實 DependencyContainer
```

**前置需求：**
1. 設定所有必要的環境變數（參考原始 `main.py`）
2. 有 Cosmos DB 的讀寫權限
3. 有 Azure OpenAI API 的存取權限
4. 準備好所有必要的配置檔案（pkl 檔案等）

**特點：**
- ✅ 真實的 KB 搜尋
- ✅ 動態的 RAG 回應
- ✅ Cosmos DB 持久化
- ✅ 完整的服務整合
- ❌ 需要完整的權限設定

## 程式碼結構

### Mock 模式實作

```python
async def _process_with_mock(self, request: TechAgentRequest) -> Dict[str, Any]:
    """使用模擬回應進行處理"""
    # 步驟 1: 初始化 chat（模擬）
    lang = "zh-tw"
    
    # 步驟 2-6: 模擬所有處理步驟...
    
    return cosmos_data
```

### Real 模式實作

```python
async def _process_with_real_api(self, request: TechAgentRequest) -> Dict[str, Any]:
    """使用真實 API 進行處理"""
    # 步驟 1: 初始化 chat
    await self.containers.cosmos_settings.create_GPT_messages(
        session_id=request.session_id,
        chat_id=request.chat_id,
        cus_id=request.cus_id,
    )
    
    # 步驟 2-6: 調用真實的服務...
    
    return cosmos_data
```

## 切換步驟

1. **開啟檔案：**
   - `api_structure/src/handlers/tech_agent_handler.py`
   - `api_structure/main.py`

2. **修改標誌：**
   ```python
   # 在 tech_agent_handler.py 頂部
   USE_MOCK_RESPONSES = False  # 改為 False
   
   # 在 main.py 頂部
   USE_MOCK_CONTAINER = False  # 改為 False
   ```

3. **確認環境：**
   - 檢查所有環境變數是否設定
   - 確認 API 權限可用
   - 驗證配置檔案存在

4. **重新啟動應用：**
   ```bash
   # 開發環境
   uvicorn api_structure.main:app --reload
   
   # 生產環境
   uvicorn api_structure.main:app --host 0.0.0.0 --port 8000
   ```

## 測試

### Mock 模式測試

```bash
python -c "
from fastapi.testclient import TestClient
from api_structure.main import app

with TestClient(app) as client:
    response = client.post('/v1/tech_agent', json={
        'cus_id': 'TEST',
        'session_id': 'test-session',
        'chat_id': 'test-chat',
        'user_input': '測試問題',
        'websitecode': 'tw',
        'product_line': '',
        'system_code': 'rog'
    })
    print('Status:', response.status_code)
    print('Response:', response.json()['final_result']['result'][0]['type'])
"
```

### Real 模式測試

確保環境變數已設定後：

```bash
curl -X POST http://localhost:8000/v1/tech_agent \
  -H "Content-Type: application/json" \
  -d '{
    "cus_id": "REAL_TEST",
    "session_id": "real-session",
    "chat_id": "real-chat",
    "user_input": "我的筆電有問題",
    "websitecode": "tw",
    "product_line": "",
    "system_code": "rog"
  }'
```

## 注意事項

1. **開發環境**建議使用 Mock 模式，避免消耗 API 配額
2. **生產環境**必須使用 Real 模式以提供真實服務
3. 切換模式後需要重新啟動應用
4. Mock 模式的回應是靜態的，用於展示結構
5. Real 模式會實際調用所有外部服務，需要確保權限正確

## 故障排除

### Mock 模式問題

如果 Mock 模式無法運行：
- 檢查 `USE_MOCK_RESPONSES = True` 是否設定
- 檢查 `USE_MOCK_CONTAINER = True` 是否設定
- 確認沒有語法錯誤

### Real 模式問題

如果 Real 模式無法運行：
- 檢查所有環境變數是否設定正確
- 確認 Cosmos DB 連接字串有效
- 驗證 Azure OpenAI API 金鑰有效
- 檢查網路連接和防火牆設定
- 查看日誌檔案獲取詳細錯誤訊息

## 相關檔案

- `api_structure/src/handlers/tech_agent_handler.py` - Handler 實作（包含兩種模式）
- `api_structure/src/pipelines/tech_agent_pipeline.py` - Pipeline 編排
- `api_structure/src/routers/tech_agent_router.py` - FastAPI 路由定義
- `api_structure/src/models/tech_agent_models.py` - 資料模型
- `api_structure/main.py` - 應用程式入口（包含 lifespan 管理）
