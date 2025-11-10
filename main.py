# main.py

import json
import pickle
import aiohttp
import uvicorn
import asyncio

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from src.core.tech_agent_api import TechAgentProcessor
from src.integrations.containers import DependencyContainer
from src.services.update_service import UpdateService
from src.routes.admin_routes import router as admin_router
from utils.logger import logger

# ========================
# ✅ 輔助函式
# ========================
async def load_rag_mappings(containers, update_service):
    """非阻塞載入 RAG mappings"""
    try:
        loop = asyncio.get_event_loop()
        
        def load_files():
            with open("config/rag_hint_id_index_mapping.pkl", "rb") as f1, \
                 open("config/rag_mappings.pkl", "rb") as f2:
                return pickle.load(f1), pickle.load(f2)
        
        # 在線程池中執行，不阻塞事件循環
        mapping1, mapping2 = await loop.run_in_executor(None, load_files)
        
        containers.rag_hint_id_index_mapping = mapping1
        containers.rag_mappings = mapping2
        
    except Exception as e:
        logger.warning(f"[Memory Load Error] {e}, updating from database...")
        await update_service.update_technical_rag()

async def load_kb_mappings(containers, update_service):
    """非阻塞載入 KB mappings"""
    try:
        loop = asyncio.get_event_loop()
        
        def load_file():
            with open("config/kb_mappings.pkl", "rb") as f:
                return pickle.load(f)
        
        containers.KB_mappings = await loop.run_in_executor(None, load_file)
        
    except Exception as e:
        logger.warning(f"[Load KB Mapping Error] {e}, updating from database...")
        await update_service.update_KB()

# ========================
# ✅ lifespan：啟動初始化 + 關閉清理
# ========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理 - 優化版"""
    
    connector = aiohttp.TCPConnector(
        limit=100,                      # 總連線數上限
        limit_per_host=30,              # 每個 host 的連線數上限
        ttl_dns_cache=300,              # DNS 快取 5 分鐘
        enable_cleanup_closed=True,     # 啟用關閉連線清理
        force_close=False,              # 保持連線重用
        keepalive_timeout=30            # Keep-alive 超時 30 秒
    )
    
    timeout = aiohttp.ClientTimeout(
        total=60,       # 總超時 60 秒
        connect=10,     # 連線超時 10 秒
        sock_read=30    # 讀取超時 30 秒
    )
    
    aiohttp_session = aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        trust_env=True  # 支援代理設定
    )
    
    containers = DependencyContainer()
    await containers.init_async(aiohttp_session=aiohttp_session)
    app.state.container = containers
    
    update_service = UpdateService(containers)

    try:
        results = await asyncio.gather(
            load_rag_mappings(containers, update_service),
            load_kb_mappings(containers, update_service),
            asyncio.to_thread(update_service.update_website_botname),
            asyncio.to_thread(update_service.update_specific_KB),
            return_exceptions=True  # 即使某個任務失敗，其他任務也繼續
        )
        
        # 檢查是否有錯誤
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"初始化任務 {i} 失敗: {result}")

        yield
        
    finally:
        await aiohttp_session.close()
        await asyncio.sleep(0.25)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers='Content-Type',
    max_age=3600
)

app.include_router(admin_router)


# ========================
# ✅ 技術支援主流程 API
# ========================
class TechAgentInput(BaseModel):
    """技術支援 API 輸入模型"""
    cus_id: str
    session_id: str
    chat_id: str
    user_input: str
    websitecode: str
    product_line: str
    system_code: str

@app.post("/v1/tech_agent")
async def tech_agent_api(user_input: TechAgentInput):
    containers: DependencyContainer = app.state.container
    tech_process = TechAgentProcessor(containers=containers, user_input=user_input)
    return await tech_process.process()


# @app.post("/tech_agent/stream")
# async def tech_agent_api_stream(user_input: TechAgentInput):
#     """技術支援 Streaming API"""
#     containers: DependencyContainer = app.state.container
#     processor = TechAgentProcessor(containers=containers, user_input=user_input)
    
#     async def event_generator():
#         try:
#             async for event in processor.process_stream():
#                 # 使用 SSE (Server-Sent Events) 格式
#                 json_data = json.dumps(event, ensure_ascii=False)
#                 yield f"data: {json_data}\n\n"
#         except Exception as e:
#             logger.error(f"Streaming error: {e}", exc_info=True)
#             error_event = {
#                 "status": 500,
#                 "message": f"error: {str(e)}",
#                 "result": {}
#             }
#             yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
    
#     return StreamingResponse(
#         event_generator(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "X-Accel-Buffering": "no",  # 關閉 Nginx 緩衝
#         }
#     )


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
