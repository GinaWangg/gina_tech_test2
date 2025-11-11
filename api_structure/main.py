# 統一載入設定檔
import os
import api_structure.core.config

# ---------------------- Lifespan Configuration -------------------------------
from contextlib import asynccontextmanager

from fastapi import FastAPI


# 由於權限問題，目前不需要初始化完整的 DependencyContainer
# 僅創建一個簡單的 mock container 用於結構展示
class MockContainer:
    """Mock container for structure demonstration."""

    def __init__(self):
        """Initialize mock container with minimal attributes."""
        self.cfg = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式生命週期管理。

    由於 API 和 Cosmos DB 的權限問題，目前使用簡化版本。
    實際部署時應使用完整的 DependencyContainer 初始化。

    完整初始化應包括：
    - DependencyContainer 初始化
    - aiohttp session 配置
    - RAG mappings 載入
    - KB mappings 載入
    - 其他服務初始化
    """
    print("Application starting up...")

    # 創建 mock container（實際應使用 DependencyContainer）
    containers = MockContainer()
    app.state.container = containers

    yield

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
