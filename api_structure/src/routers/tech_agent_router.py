"""Router for tech agent endpoints."""

from fastapi import APIRouter, Request

from api_structure.core.models import TechAgentInput, TechAgentResponse
from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.src.clients.tech_agent_container import (
    TechAgentContainer
)


router = APIRouter(prefix="/v1", tags=["tech_agent"])


@router.post("/tech_agent", response_model=TechAgentResponse)
async def tech_agent_endpoint(
    user_input: TechAgentInput,
    request: Request
) -> TechAgentResponse:
    """Tech agent API endpoint.
    
    Processes user input through the tech agent pipeline to provide
    technical support responses with KB search and product line detection.
    
    Args:
        user_input: Tech agent input model with user request data.
        request: FastAPI request object for accessing app state.
    
    Returns:
        TechAgentResponse with processing results.
    
    Raises:
        AbortException: If a critical error occurs during processing.
    """
    # Get container from app state
    container: TechAgentContainer = request.app.state.tech_agent_container
    
    # Create handler and process
    handler = TechAgentHandler(container, user_input)
    response = await handler.run()
    
    return response
