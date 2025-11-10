"""Tech agent pipeline for coordinating request processing."""

from typing import Any, Dict

from core.timer import timed
from src.handlers.tech_agent_handler import TechAgentHandler
from src.models.tech_agent_models import TechAgentInput


class TechAgentPipeline:
    """Pipeline for coordinating tech agent request processing.
    
    This pipeline orchestrates the flow of a technical support request
    through various processing stages using the TechAgentHandler.
    
    Attributes:
        containers: Dependency container with all required services
    """

    def __init__(self, containers: Any):
        """Initialize the tech agent pipeline.
        
        Args:
            containers: DependencyContainer with initialized services
        """
        self.containers = containers

    @timed(task_name="tech_agent_pipeline_process")
    async def process(self, user_input: TechAgentInput) -> Dict[str, Any]:
        """Process a tech agent request through the pipeline.
        
        Args:
            user_input: User input data model
            
        Returns:
            Response dictionary containing status, message, and result
            
        Raises:
            Exception: If processing fails at any stage
        """
        handler = TechAgentHandler(
            containers=self.containers,
            user_input=user_input
        )
        
        result = await handler.run()
        
        return result
