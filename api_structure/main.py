# 統一載入設定檔
import os
import asyncio
import pickle
import core.config

#---------------------- Lifespan Configuration --------------------------------
from fastapi.concurrency import asynccontextmanager
from fastapi import FastAPI
from src.clients.gpt import GptClient
from src.clients.aiohttp_client import AiohttpClient
# from src.db.cosmos_client import CosmosDbClient
import aiohttp
from src.integrations.containers import DependencyContainer
from src.services.update_service import UpdateService


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
        print(f"[Memory Load Error] {e}, updating from database...")
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
        print(f"[Load KB Mapping Error] {e}, updating from database...")
        await update_service.update_KB()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up...")
    
    # Initialize aiohttp session with connection pooling
    connector = aiohttp.TCPConnector(
        limit=100,
        limit_per_host=30,
        ttl_dns_cache=300,
        enable_cleanup_closed=True,
        force_close=False,
        keepalive_timeout=30
    )
    
    timeout = aiohttp.ClientTimeout(
        total=60,
        connect=10,
        sock_read=30
    )
    
    aiohttp_session = aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        trust_env=True
    )
    
    # Initialize DependencyContainer
    containers = DependencyContainer()
    await containers.init_async(aiohttp_session=aiohttp_session)
    app.state.container = containers
    
    # Initialize update service
    update_service = UpdateService(containers)
    
    try:
        # Load mappings in parallel
        results = await asyncio.gather(
            load_rag_mappings(containers, update_service),
            load_kb_mappings(containers, update_service),
            asyncio.to_thread(update_service.update_website_botname),
            asyncio.to_thread(update_service.update_specific_KB),
            return_exceptions=True
        )
        
        # Check for errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"初始化任務 {i} 失敗: {result}")
    
        # connection pooling (for api_structure examples)
        gpt_client = GptClient()
        await gpt_client.initialize()
        app.state.gpt_client = gpt_client

        # aiohttp client (for api_structure examples)
        aiohttp_client = AiohttpClient(
            timeout=30,
            connector_limit=100,
            connector_limit_per_host=30
        )
        await aiohttp_client.initialize()
        app.state.aiohttp_client = aiohttp_client

        # cosmos_client = CosmosDbClient()
        # await cosmos_client.initialize()
        # app.state.cosmos_client = cosmos_client

        yield
    
    finally:
        print("Application shutting down...")
        await aiohttp_session.close()
        await app.state.gpt_client.close()
        await app.state.aiohttp_client.close()
        # await app.state.cosmos_client.close()
        await asyncio.sleep(0.25)


#---------------------- FastAPI App & middleware ------------------------------
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=['Content-Type'],
    max_age=3600
)

from core.middleware import RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)


# --------------------- application insights ----------------------------------
if not os.getenv("SCM_DO_BUILD_DURING_DEPLOYMENT"):
    ''' 地端上使用 可以用這段 '''
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
    ''' azure上使用 可以用這段 '''
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    # Application Insights 的 Connection String
    CONNECTION_STRING = os.getenv('MYAPP_CONNECTION_STRING')
    if not CONNECTION_STRING:
        raise ValueError(
            "Environment variable 'MYAPP_CONNECTION_STRING' is not set.")

    # 配置 Azure Monitor OpenTelemetry
    configure_azure_monitor(
        connection_string=CONNECTION_STRING, 
        enable_live_metrics=True
    )

''' 不管地端還是 azure 都要這段 '''
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)


# --------------------- Background Scheduler for Data Update ------------------
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone

scheduler = BackgroundScheduler(timezone=timezone('Asia/Taipei'))

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
    HTTPException, exc_handler.custom_http_exception_handler)
app.add_exception_handler(
    Exception, exc_handler.global_exception_handler)


# --------------------- endpoints ---------------------------------------------

# from fastapi import Response
# from pydantic import BaseModel

# routers
from src.routers.tech_agent_router import router as tech_agent_router
app.include_router(tech_agent_router)


# root endpoint
@app.get("/")
async def root():
    return {"message": "api is running"}
    
# --------------------- local test --------------------------------------------

if __name__ == "__main__":
    import uvicorn  
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


