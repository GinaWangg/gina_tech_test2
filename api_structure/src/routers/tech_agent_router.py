"""Tech agent router - API endpoint layer."""

from typing import Dict, Any

from fastapi import APIRouter, Request

from api_structure.core.logger import get_logger
from api_structure.src.models.tech_agent_models import TechAgentInput
from api_structure.src.pipelines.tech_agent_pipeline import TechAgentPipeline

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["tech_agent"])


@router.post("/tech_agent")
async def tech_agent_endpoint(
    user_input: TechAgentInput,
    request: Request,
) -> Dict[str, Any]:
    """Tech agent API endpoint.
    
    Args:
        user_input: User input data model.
        request: FastAPI request object.
        
    Returns:
        Response data dictionary.
    """
    logger.info("[Router] Received tech_agent request")

    # Create pipeline and execute
    pipeline = TechAgentPipeline()
    result = await pipeline.run(user_input)

    logger.info("[Router] Returning tech_agent response")
    return result
