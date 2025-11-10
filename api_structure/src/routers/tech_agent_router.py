"""Tech agent router for /v1/tech_agent endpoint."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.models.tech_agent_models import (
    TechAgentInput,
    TechAgentResponse,
)
from src.pipelines.tech_agent_pipeline import TechAgentPipeline

router = APIRouter(prefix="/v1", tags=["tech_agent"])


@router.post("/tech_agent", response_model=TechAgentResponse)
async def tech_agent_endpoint(
    request: Request,
    user_input: TechAgentInput
) -> JSONResponse:
    """技術支援主流程 API 端點.
    
    處理技術支援請求，包括：
    - 解析使用者輸入
    - 搜尋知識庫
    - 生成回應
    - 記錄處理結果
    
    Args:
        request: FastAPI request object (用於存取 app.state)
        user_input: 使用者輸入資料
        
    Returns:
        JSONResponse containing the processed result
        
    Example:
        POST /v1/tech_agent
        {
            "cus_id": "test_user",
            "session_id": "session-123",
            "chat_id": "chat-456",
            "user_input": "我的筆電無法開機",
            "websitecode": "tw",
            "product_line": "notebook",
            "system_code": "rog"
        }
    """
    # Get containers from app state
    containers = request.app.state.container
    
    # Create pipeline and process request
    pipeline = TechAgentPipeline(containers=containers)
    result = await pipeline.process(user_input=user_input)
    
    # Return result as JSONResponse
    return JSONResponse(
        status_code=result.get("status", 200),
        content=result
    )
