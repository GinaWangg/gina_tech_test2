"""Pipeline for tech agent processing."""

from fastapi import Request
from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.core.timer import timed


class TechAgentPipeline:
    """Pipeline that orchestrates tech agent request processing."""

    def __init__(self, request: Request):
        """
        Initialize the pipeline with request context.

        Args:
            request: FastAPI request object for accessing app state
        """
        self.request = request

    @timed(task_name="tech_agent_pipeline_run")
    async def run(self, user_input):
        """
        Execute the tech agent pipeline.

        This method orchestrates the flow between handlers and returns
        the final response.

        Args:
            user_input: TechAgentInput model with user request data

        Returns:
            Response dictionary with status, message, and result
        """
        handler = TechAgentHandler()
        result = await handler.process(user_input)
        return result
