"""Router for tech_agent endpoint."""

from fastapi import APIRouter, Request

from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.src.models.tech_agent_models import TechAgentInput

router = APIRouter()


@router.post("/v1/tech_agent")
async def tech_agent_api(user_input: TechAgentInput, request: Request):
    """技術支援 API 端點.

    Args:
        user_input: 使用者輸入資料
        request: FastAPI request object (用於取得 app.state 中的容器)

    Returns:
        技術支援回應資料
    """
    # Get container from app state
    container = request.app.state.mock_container

    # Create handler and process
    handler = TechAgentHandler(container=container, user_input=user_input)
    result = await handler.process()

    return result
