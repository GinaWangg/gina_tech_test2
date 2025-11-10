"""Router for tech agent API endpoints."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from api_structure.src.pipelines.tech_agent_pipeline import TechAgentPipeline

router = APIRouter(prefix="/v1", tags=["tech_agent"])


class TechAgentInput(BaseModel):
    """Tech agent API input model."""

    cus_id: str
    session_id: str
    chat_id: str
    user_input: str
    websitecode: str
    product_line: str
    system_code: str


@router.post("/tech_agent")
async def tech_agent_api(user_input: TechAgentInput, request: Request):
    """
    Tech agent API endpoint.

    This endpoint processes technical support requests and returns
    appropriate responses based on the user input.

    Args:
        user_input: Tech agent input data
        request: FastAPI request object for accessing app state

    Returns:
        Response with status, message, and result data
    """
    pipeline = TechAgentPipeline(request=request)
    result = await pipeline.run(user_input)
    return result
