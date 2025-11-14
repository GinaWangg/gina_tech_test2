"""Router for tech agent API endpoints."""

from fastapi import Request
from typing import Dict

from api_structure.core.logger import logger
from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.src.models.tech_agent_models import TechAgentInput


async def tech_agent_endpoint(
    user_input: TechAgentInput, request: Request
) -> Dict:
    """Tech agent endpoint - process technical support requests.

    Args:
        user_input: User input data.
        request: FastAPI request object.

    Returns:
        Response dictionary with status and result.
    """
    # Get container from app state
    container = request.app.state.tech_agent_container

    # Create handler and process
    handler = TechAgentHandler(container=container, user_input=user_input)
    result = await handler.run()

    logger.info(f"[TechAgentRouter] Processing complete")
    return result
