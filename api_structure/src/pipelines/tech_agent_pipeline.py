"""Tech agent pipeline - Orchestration layer."""

from typing import Any, Dict

from api_structure.core.logger import get_logger
from api_structure.core.timer import timed
from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.src.models.tech_agent_models import TechAgentInput

logger = get_logger(__name__)


class TechAgentPipeline:
    """Pipeline for tech agent processing."""

    def __init__(self):
        """Initialize the pipeline."""
        self.handler = TechAgentHandler()

    @timed(task_name="tech_agent_pipeline")
    async def run(
        self,
        user_input: TechAgentInput,
    ) -> Dict[str, Any]:
        """Execute the tech agent pipeline.

        Args:
            user_input: User input data.

        Returns:
            Response data dictionary.
        """
        logger.info("[Pipeline] Starting tech agent processing")

        # Execute handler
        result = await self.handler.run(user_input)

        logger.info("[Pipeline] Tech agent processing completed")
        return result
