"""Router for tech agent endpoints."""

from fastapi import APIRouter, Request

from api_structure.src.models.tech_agent_models import (
    TechAgentRequest,
    TechAgentResponse,
)
from api_structure.src.pipelines.tech_agent_pipeline import TechAgentPipeline

router = APIRouter(prefix="/v1", tags=["tech_agent"])


@router.post("/tech_agent", response_model=TechAgentResponse)
async def tech_agent(request: Request, user_input: TechAgentRequest):
    """
    Technical support agent endpoint.

    Process user technical support requests and provide appropriate responses
    based on product line and user input.

    Args:
        request: FastAPI request object
        user_input: Tech agent request data

    Returns:
        Technical support response with render items
    """
    pipeline = TechAgentPipeline()
    response = await pipeline.execute(user_input)
    return response
