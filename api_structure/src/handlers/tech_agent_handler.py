"""
Tech Agent Handler - Orchestrates the service layer.
"""

from fastapi import Request

from core.timer import timed
from src.schemas.tech_agent import TechAgentRequest
from src.services.tech_agent_service import TechAgentService
from src.repositories.data_repository import DataRepository


class TechAgentHandler:
    """Handler for tech agent requests."""
    
    def __init__(self, repository: DataRepository):
        """
        Initialize handler with repository.
        
        Args:
            repository: Data repository instance
        """
        self.repository = repository
        self.service = TechAgentService(repository)
    
    @timed(task_name="tech_agent_handler")
    async def run(
        self,
        request: TechAgentRequest
    ) -> dict:
        """
        Process tech agent request.
        
        Args:
            request: Tech agent request data
            
        Returns:
            Final result dict with status, message, and result
        """
        # Process through service layer
        result = await self.service.process(request)
        
        # Return only the final_result part for API response
        return result["final_result"]
