"""
Tech Agent Router - API endpoint handler.
Orchestrates request/response flow following AOCC FastAPI pattern.
"""

from typing import Dict, Any
from fastapi import Request
from api_structure.core.logger import logger
from api_structure.src.schemas.tech_agent_schemas import TechAgentInput
from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.src.services.tech_agent_service import TechAgentService
from api_structure.src.repositories.tech_agent_repository import TechAgentRepository


async def tech_agent_endpoint(
    user_input: TechAgentInput,
    request: Request
) -> Dict[str, Any]:
    """
    Tech Agent API endpoint handler.
    
    Args:
        user_input: Tech agent input data
        request: FastAPI request object
    
    Returns:
        Response dictionary matching original format exactly
    """
    # Initialize repository (data access layer)
    repository = TechAgentRepository()
    
    # TODO: Load mappings from app.state when available
    # repository.rag_hint_id_index_mapping = request.app.state.rag_hint_id_index_mapping
    # repository.rag_mappings = request.app.state.rag_mappings
    # repository.KB_mappings = request.app.state.KB_mappings
    # repository.specific_kb_mappings = request.app.state.specific_kb_mappings
    
    # Initialize service (business logic layer)
    service = TechAgentService(repository)
    
    # Initialize handler (orchestration layer)
    handler = TechAgentHandler(
        user_input=user_input,
        service=service,
        repository=repository
    )
    
    # Run the handler
    result = await handler.run()
    
    return result
