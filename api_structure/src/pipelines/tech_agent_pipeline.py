"""Tech agent pipeline for orchestrating the processing flow."""

from typing import Dict, Any
from api_structure.src.handlers.tech_agent_handler import TechAgentHandler
from api_structure.src.models.tech_agent_models import TechAgentInput


class TechAgentPipeline:
    """Pipeline for tech agent request processing."""

    def __init__(
        self,
        gpt_client: Any,
        aiohttp_client: Any,
        # cosmos_client: Any = None,  # TODO: Enable when environment ready
    ):
        """Initialize the tech agent pipeline.

        Args:
            gpt_client: GPT client for AI interactions
            aiohttp_client: HTTP client for external API calls
        """
        self.gpt_client = gpt_client
        self.aiohttp_client = aiohttp_client
        # self.cosmos_client = cosmos_client  # TODO: Enable when ready

    async def process(self, user_input: TechAgentInput) -> Dict[str, Any]:
        """Process tech agent request through the pipeline.

        Args:
            user_input: User input data

        Returns:
            Final response dictionary
        """
        # Create handler with injected dependencies
        handler = TechAgentHandler(
            gpt_client=self.gpt_client,
            aiohttp_client=self.aiohttp_client,
            # cosmos_client=self.cosmos_client,  # TODO: Enable when ready
        )

        # Execute the handler
        result = await handler.run(user_input)

        return result
