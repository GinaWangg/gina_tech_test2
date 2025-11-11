"""Tech agent router for handling tech support API endpoints."""

from fastapi import APIRouter, Request
from api_structure.src.models.tech_agent_models import TechAgentInput
from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.core.logger import logger

router = APIRouter(prefix="/v1", tags=["tech_agent"])


@router.post("/tech_agent")
async def tech_agent_endpoint(
    user_input: TechAgentInput, 
    request: Request
) -> dict:
    """技術支援 API 端點.
    
    處理技術支援問題，提供知識庫搜尋、產品線判斷等功能。
    
    Args:
        user_input: 使用者輸入資料
        request: FastAPI request 物件 (用於取得 app.state)
        
    Returns:
        包含技術支援回應的字典
        
    Raises:
        HTTPException: 當處理過程發生錯誤時
    """
    logger.info(
        f"[API Request] /v1/tech_agent - Session: {user_input.session_id}"
    )
    
    # Get container from app state
    container = request.app.state.tech_agent_container
    
    # Create handler and process
    handler = TechAgentHandler(container=container, user_input=user_input)
    result = await handler.run(log_record=True)
    
    logger.info(
        f"[API Response] /v1/tech_agent - Status: {result.get('status', 'unknown')}"
    )
    
    return result
