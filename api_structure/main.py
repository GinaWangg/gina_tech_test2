# 統一載入設定檔
import os
import pickle
import asyncio
import api_structure.core.config

#---------------------- Lifespan Configuration --------------------------------
from fastapi.concurrency import asynccontextmanager
from fastapi import FastAPI
from api_structure.src.clients.gpt import GptClient
from api_structure.src.clients.aiohttp_client import AiohttpClient
# from src.db.cosmos_client import CosmosDbClient

# Import mock services for tech_agent
from api_structure.src.services.mock_services import (
    MockCosmosService,
    MockRedisService,
    MockServiceDiscriminator,
)


async def load_pickle_data(app: FastAPI):
    """Load pickle data files for KB and RAG mappings."""
    try:
        loop = asyncio.get_event_loop()

        def load_files():
            kb_mappings = {}
            rag_mappings = {}
            rag_hint_id_index = {}

            try:
                with open("config/kb_mappings.pkl", "rb") as f:
                    kb_mappings = pickle.load(f)
            except Exception as e:
                print(f"[Warning] Failed to load kb_mappings.pkl: {e}")

            try:
                with open("config/rag_mappings.pkl", "rb") as f:
                    rag_mappings = pickle.load(f)
            except Exception as e:
                print(f"[Warning] Failed to load rag_mappings.pkl: {e}")

            try:
                with open("config/rag_hint_id_index_mapping.pkl", "rb") as f:
                    rag_hint_id_index = pickle.load(f)
            except Exception as e:
                print(
                    f"[Warning] Failed to load "
                    f"rag_hint_id_index_mapping.pkl: {e}"
                )

            return kb_mappings, rag_mappings, rag_hint_id_index

        kb_map, rag_map, rag_idx = await loop.run_in_executor(
            None, load_files
        )

        app.state.kb_mappings = kb_map
        app.state.rag_mappings = rag_map
        app.state.rag_hint_id_index_mapping = rag_idx

        print(
            f"[Startup] Loaded KB mappings: {len(kb_map)} entries, "
            f"RAG mappings: {len(rag_map)} entries"
        )

    except Exception as e:
        print(f"[Error] Failed to load pickle data: {e}")
        app.state.kb_mappings = {}
        app.state.rag_mappings = {}
        app.state.rag_hint_id_index_mapping = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up...")
    
    # Try to initialize GPT client
    gpt_client = None
    try:
        gpt_client = GptClient()
        await gpt_client.initialize()
        app.state.gpt_client = gpt_client
        print("[Startup] GPT client initialized")
        
        # Initialize GPT-based services now that client is available
        from api_structure.src.services.gpt_services import (
            UserInfoExtractor,
            FollowUpDetector,
            AvatarResponseGenerator,
        )
        
        app.state.user_info_extractor = UserInfoExtractor(gpt_client)
        app.state.follow_up_detector = FollowUpDetector(gpt_client)
        app.state.avatar_generator = AvatarResponseGenerator(gpt_client)
        print("[Startup] GPT-based services initialized")
        
    except ValueError as e:
        print(f"[Startup] GPT client not initialized: {e}")
        app.state.gpt_client = None
        app.state.user_info_extractor = None
        app.state.follow_up_detector = None
        app.state.avatar_generator = None

    # aiohttp client with connection pooling
    aiohttp_client = AiohttpClient(
        timeout=30,
        connector_limit=100,
        connector_limit_per_host=30
    )
    await aiohttp_client.initialize()
    app.state.aiohttp_client = aiohttp_client
    print("[Startup] Aiohttp client initialized")

    # cosmos_client = CosmosDbClient()
    # await cosmos_client.initialize()
    # app.state.cosmos_client = cosmos_client

    # Initialize mock services for tech_agent
    mock_config = {}  # Empty config for mock services
    cosmos_service = MockCosmosService(mock_config)
    redis_service = MockRedisService(mock_config, aiohttp_client)
    service_discriminator = MockServiceDiscriminator(
        redis_service, None
    )

    app.state.cosmos_service = cosmos_service
    app.state.redis_service = redis_service
    app.state.service_discriminator = service_discriminator
    print("[Startup] Mock services initialized")

    # Load pickle data
    await load_pickle_data(app)

    yield

    print("Application shutting down...")
    if app.state.gpt_client:
        await app.state.gpt_client.close()
    await app.state.aiohttp_client.close()
    # await app.state.cosmos_client.close()


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

from api_structure.core.middleware import RequestLoggingMiddleware
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

from fastapi import Request, Response
from api_structure.src.models.tech_agent_models import TechAgentInput
from api_structure.src.routers.tech_agent_router import tech_agent_router

# root endpoint
@app.get("/")
async def root():
    return {"message": "api is running"}


# tech_agent endpoint
@app.post("/v1/tech_agent")
async def v1_tech_agent(
    user_input: TechAgentInput, request: Request, response: Response
):
    """Tech agent endpoint for technical support.

    Args:
        user_input: Tech agent input model
        request: FastAPI request
        response: FastAPI response

    Returns:
        Tech agent response
    """
    result = await tech_agent_router(user_input, request)
    return result

    
# --------------------- local test --------------------------------------------

if __name__ == "__main__":
    import uvicorn  
    uvicorn.run("api_structure.main:app", host="127.0.0.1", port=8000, reload=True)


