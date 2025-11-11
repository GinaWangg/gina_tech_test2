"""Tech agent router for FastAPI endpoints."""

import logging
from fastapi import APIRouter, Request
from typing import Dict, Any

from api_structure.src.models.tech_agent_models import (
    TechAgentInput,
    TechAgentFinalResponse,
)
from api_structure.src.pipelines.tech_agent_pipeline import TechAgentPipeline

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/v1/tech_agent", response_model=None)
async def tech_agent_api(
    user_input: TechAgentInput,
    request: Request
) -> Dict[str, Any]:
    """Handle tech agent requests.

    This endpoint processes user questions and provides technical support
    using AI and knowledge base integration.

    Args:
        user_input: User request data including question and context
        request: FastAPI request object for accessing app state

    Returns:
        Technical support response with recommendations and KB references
    """
    # Access clients from app state
    gpt_client = request.app.state.gpt_client
    aiohttp_client = request.app.state.aiohttp_client
    # cosmos_client = request.app.state.cosmos_client  # TODO: Enable when ready

    # Create pipeline with injected dependencies
    pipeline = TechAgentPipeline(
        gpt_client=gpt_client,
        aiohttp_client=aiohttp_client,
        # cosmos_client=cosmos_client,  # TODO: Enable when ready
    )

    # Process the request
    result = await pipeline.process(user_input)

    return result
