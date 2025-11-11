"""
Router for tech agent endpoints.
"""

from fastapi import APIRouter, Request

from src.schemas.tech_agent import TechAgentRequest
from src.handlers.tech_agent_handler import TechAgentHandler
from src.repositories.data_repository import DataRepository


router = APIRouter(prefix="/v1", tags=["Tech Agent"])


# Initialize repository (singleton pattern)
_repository = DataRepository()


@router.post("/tech_agent")
async def tech_agent_endpoint(
    request_data: TechAgentRequest,
    request: Request
) -> dict:
    """
    Technical support agent endpoint.
    
    Processes user questions and returns appropriate technical support
    responses based on knowledge base similarity.
    
    Args:
        request_data: Tech agent request with user input
        request: FastAPI request object
        
    Returns:
        JSON response with status, message, and result array
    """
    handler = TechAgentHandler(_repository)
    result = await handler.run(request_data)
    return result
