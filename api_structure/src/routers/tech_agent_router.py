"""Router for tech agent endpoints."""

from fastapi import APIRouter, Request

from api_structure.src.models.tech_agent_models import TechAgentRequest
from api_structure.src.pipelines.tech_agent_pipeline import TechAgentPipeline

router = APIRouter(prefix="/v1", tags=["tech_agent"])


@router.post("/tech_agent")
async def tech_agent(request: Request, user_input: TechAgentRequest):
    """
    Technical support agent endpoint.

    Process user technical support requests using the original
    TechAgentProcessor logic to maintain the same behavior and output.

    Args:
        request: FastAPI request object
        user_input: Tech agent request data

    Returns:
        Complete cosmos_data with all processing information
    """
    # Get containers from app state
    containers = request.app.state.container

    # Execute pipeline with containers
    pipeline = TechAgentPipeline(containers)
    cosmos_data = await pipeline.execute(user_input)

    # Return the cosmos_data directly (matches original format)
    return cosmos_data
