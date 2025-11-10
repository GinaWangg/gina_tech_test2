"""Pipeline for tech agent request processing."""

from typing import Dict, Any
from api_structure.core.timer import timed
from api_structure.src.models.tech_agent_models import TechAgentRequest
from api_structure.src.handlers.tech_agent_handler import TechAgentHandler


class TechAgentPipeline:
    """Pipeline for orchestrating tech agent request processing."""

    def __init__(self):
        """Initialize the tech agent pipeline."""
        self.handler = TechAgentHandler()

    @timed(task_name="tech_agent_pipeline_execute")
    async def execute(self, request: TechAgentRequest) -> Dict[str, Any]:
        """
        Execute the tech agent processing pipeline.

        This method orchestrates the complete tech agent workflow:
        1. Validate input
        2. Process through handler
        3. Format response

        Args:
            request: Tech agent request data

        Returns:
            Formatted response dictionary
        """
        # 執行處理邏輯
        result = await self.handler.process(request)

        # 格式化回應
        response = {
            "status": 200,
            "message": "OK",
            "result": [item.model_dump() for item in result["render_items"]],
        }

        return response
