"""Tech agent router for handling /v1/tech_agent endpoint."""

from fastapi import Request
from api_structure.src.models.tech_agent_models import (
    TechAgentInput,
    TechAgentResponse,
)
from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.core.timer import timed


@timed(task_name="tech_agent_router")
async def tech_agent_router(
    user_input: TechAgentInput, request: Request
) -> dict:
    """Route tech agent requests to handler.

    Args:
        user_input: Tech agent input model
        request: FastAPI request object

    Returns:
        Tech agent response dictionary
    """
    # Get services from app state
    cosmos_service = getattr(
        request.app.state, "cosmos_service", None
    )
    service_discriminator = getattr(
        request.app.state, "service_discriminator", None
    )
    kb_mappings = getattr(request.app.state, "kb_mappings", {})
    rag_mappings = getattr(request.app.state, "rag_mappings", {})
    
    # Get GPT-based services from app state
    user_info_extractor = getattr(
        request.app.state, "user_info_extractor", None
    )
    follow_up_detector = getattr(
        request.app.state, "follow_up_detector", None
    )
    avatar_generator = getattr(
        request.app.state, "avatar_generator", None
    )

    # Create handler and process
    handler = TechAgentHandler(
        user_input=user_input,
        cosmos_service=cosmos_service,
        service_discriminator=service_discriminator,
        kb_mappings=kb_mappings,
        rag_mappings=rag_mappings,
        user_info_extractor=user_info_extractor,
        follow_up_detector=follow_up_detector,
        avatar_generator=avatar_generator,
    )

    result = await handler.run()
    return result
