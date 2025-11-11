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
        using the original processing logic.

        Args:
            request: Tech agent request data

        Returns:
            Complete response including final_result and cosmos_data
        """
        # 執行處理邏輯（使用原始的 TechAgentProcessor）
        result = await self.handler.process(request)

        # 返回包含 final_result 的完整回應
        return result["cosmos_data"]
