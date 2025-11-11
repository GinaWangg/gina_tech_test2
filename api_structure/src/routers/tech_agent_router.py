"""
Tech Agent Router - HTTP endpoint layer.
Handles HTTP requests for tech agent endpoint.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api_structure.core.logger import logger
from api_structure.src.schemas.tech_agent_schemas import TechAgentInput
from api_structure.src.pipelines.tech_agent_pipeline import TechAgentPipeline


router = APIRouter()


@router.post("/v1/tech_agent")
async def tech_agent_endpoint(
    user_input: TechAgentInput, request: Request
) -> JSONResponse:
    """
    技術支援 API endpoint.
    
    Args:
        user_input: Tech agent input data
        request: FastAPI request object
        
    Returns:
        JSON response with tech agent result
    """
    try:
        # Get repositories from app state
        cosmos_repo = request.app.state.cosmos_repo
        redis_repo = request.app.state.redis_repo
        kb_repo = request.app.state.kb_repo

        # Create pipeline
        pipeline = TechAgentPipeline(
            cosmos_repo=cosmos_repo,
            redis_repo=redis_repo,
            kb_repo=kb_repo
        )

        # Execute pipeline
        result = await pipeline.run(user_input, log_record=True)

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        logger.error(f"[TechAgentRouter] Error: {e}", exc_info=True)
        return JSONResponse(
            content={
                "status": 500,
                "message": f"Internal server error: {str(e)}",
                "result": {}
            },
            status_code=500
        )
