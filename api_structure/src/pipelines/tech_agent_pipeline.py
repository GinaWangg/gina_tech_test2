"""Pipeline for tech agent request processing."""

from typing import Any, Dict

from api_structure.core.timer import timed
from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.src.models.tech_agent_models import TechAgentRequest


class TechAgentPipeline:
    """Pipeline for orchestrating tech agent request processing."""

    def __init__(self, containers):
        """
        Initialize the tech agent pipeline.

        Args:
            containers: DependencyContainer with all required services
        """
        self.handler = TechAgentHandler(containers)

    @timed(task_name="tech_agent_pipeline_execute")
    async def execute(self, request: TechAgentRequest) -> Dict[str, Any]:
        """
        Execute the tech agent processing pipeline.

        This method orchestrates the complete tech agent workflow
        with mocked responses (due to permission limitations).

        Args:
            request: Tech agent request data

        Returns:
            Complete cosmos_data structure matching original format
        """
        # 執行處理邏輯（使用模擬的回應）
        cosmos_data = await self.handler.process(request)

        # 返回完整的 cosmos_data
        return cosmos_data
