# 統一載入設定檔
import os
import pickle
import asyncio
import api_structure.core.config

# ---------------------- Lifespan Configuration --------------------------------
from fastapi.concurrency import asynccontextmanager
from fastapi import FastAPI
from api_structure.src.clients.gpt import GptClient
from api_structure.src.clients.aiohttp_client import AiohttpClient
from src.integrations.containers import DependencyContainer
from src.services.update_service import UpdateService
from utils.logger import logger
import aiohttp

# from src.db.cosmos_client import CosmosDbClient


# ========================
# ✅ 輔助函式
# ========================
async def load_rag_mappings(containers, update_service):
    """非阻塞載入 RAG mappings"""
    try:
        loop = asyncio.get_event_loop()

        def load_files():
            with open(
                "config/rag_hint_id_index_mapping.pkl", "rb"
            ) as f1, open("config/rag_mappings.pkl", "rb") as f2:
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
        logger.warning(
            f"[Load KB Mapping Error] {e}, updating from database..."
        )
        await update_service.update_KB()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理 - 與原始 main.py 相同"""
    print("Application starting up...")

    # 創建 aiohttp session（與原始 main.py 相同的配置）
    connector = aiohttp.TCPConnector(
        limit=100,  # 總連線數上限
        limit_per_host=30,  # 每個 host 的連線數上限
        ttl_dns_cache=300,  # DNS 快取 5 分鐘
        enable_cleanup_closed=True,  # 啟用關閉連線清理
        force_close=False,  # 保持連線重用
        keepalive_timeout=30,  # Keep-alive 超時 30 秒
    )

    timeout = aiohttp.ClientTimeout(
        total=60,  # 總超時 60 秒
        connect=10,  # 連線超時 10 秒
        sock_read=30,  # 讀取超時 30 秒
    )

    aiohttp_session = aiohttp.ClientSession(
        connector=connector, timeout=timeout, trust_env=True  # 支援代理設定
    )

    # 初始化 DependencyContainer（與原始 main.py 相同）
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
            return_exceptions=True,  # 即使某個任務失敗，其他任務也繼續
        )

        # 檢查是否有錯誤
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"初始化任務 {i} 失敗: {result}")

        yield

    finally:
        await aiohttp_session.close()
        await asyncio.sleep(0.25)
        print("Application shutting down...")


# ---------------------- FastAPI App & middleware ------------------------------
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["Content-Type"],
    max_age=3600,
)

from api_structure.core.middleware import RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)


# --------------------- application insights ----------------------------------
if not os.getenv("SCM_DO_BUILD_DURING_DEPLOYMENT"):
    """地端上使用 可以用這段"""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter

    # 設定 OpenTelemetry 追蹤 將追蹤資料輸出到終端控制台
    def setup_tracing():
        if not isinstance(trace.get_tracer_provider(), TracerProvider):
            provider = TracerProvider()
            trace.set_tracer_provider(provider)
            # terminal輸出
            span_processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(span_processor)
            return provider
        else:
            return trace.get_tracer_provider()

    # # 初始化 Tracer => 這個註解掉 可以在地端測試 但不會有任何顯示
    # tracer_provider = setup_tracing()

else:
    """azure上使用 可以用這段"""
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    # Application Insights 的 Connection String
    CONNECTION_STRING = os.getenv("MYAPP_CONNECTION_STRING")
    if not CONNECTION_STRING:
        raise ValueError(
            "Environment variable 'MYAPP_CONNECTION_STRING' is not set."
        )

    # 配置 Azure Monitor OpenTelemetry
    configure_azure_monitor(
        connection_string=CONNECTION_STRING, enable_live_metrics=True
    )

""" 不管地端還是 azure 都要這段 """
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

FastAPIInstrumentor.instrument_app(app)


# --------------------- Background Scheduler for Data Update ------------------
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone

scheduler = BackgroundScheduler(timezone=timezone("Asia/Taipei"))

# # 設置不同的任務和執行間隔，定期重讀定義表
# scheduler.add_job(
#     scheduler_function_name,
#     trigger=IntervalTrigger(hours=1, timezone=timezone('Asia/Taipei'))
# )
# # 可以多個唷
# scheduler.add_job(
#     scheduler_function_name,
#     trigger=IntervalTrigger(hours=1, timezone=timezone('Asia/Taipei'))
# )
scheduler.start()


# --------------------- exception handlers ------------------------------------
from api_structure.core import exception_handlers as exc_handler
from fastapi import HTTPException

app.add_exception_handler(
    HTTPException, exc_handler.custom_http_exception_handler
)
app.add_exception_handler(Exception, exc_handler.global_exception_handler)


# --------------------- endpoints ---------------------------------------------

# from fastapi import Response
# from pydantic import BaseModel

# routers
from api_structure.src.routers.tech_agent_router import (
    router as tech_agent_router,
)

app.include_router(tech_agent_router)


# root endpoint
@app.get("/")
async def root():
    return {"message": "api is running"}


# --------------------- local test --------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
