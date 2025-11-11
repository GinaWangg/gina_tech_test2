"""Tech agent API router."""

from fastapi import APIRouter, Request

from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.src.models.tech_agent_models import TechAgentInput
from api_structure.src.services.chat_flow_service import ChatFlowService
from api_structure.src.services.cosmos_service import CosmosService
from api_structure.src.services.kb_search_service import KBSearchService
from api_structure.src.services.rag_service import RAGService

router = APIRouter()


@router.post("/v1/tech_agent")
async def tech_agent_api(user_input: TechAgentInput, request: Request):
    """Tech agent API endpoint.

    Handles technical support queries with intelligent routing based on
    product line and knowledge base similarity.

    Args:
        user_input: Tech agent input data containing user query and context.
        request: FastAPI request object for accessing app state.

    Returns:
        Tech agent response with status, message, and result data.
    """
    # Initialize services
    chat_flow_service = ChatFlowService()
    kb_search_service = KBSearchService()
    rag_service = RAGService()
    cosmos_service = CosmosService()

    # Create handler
    handler = TechAgentHandler(
        chat_flow_service=chat_flow_service,
        kb_search_service=kb_search_service,
        rag_service=rag_service,
        cosmos_service=cosmos_service,
    )

    # Process request
    result = await handler.run(user_input)

    return result
