"""Router for tech agent endpoints.

This module provides the router that connects the FastAPI endpoint
to the tech agent handler.
"""

from typing import Any, Dict

from fastapi import Request
from src.handlers.tech_agent_handler import TechAgentHandler
from src.stubs.dependency_container_stub import DependencyContainerStub

from core.models import TechAgentInput
from core.timer import timed


class TechAgentRouter:
    """Router class for tech agent endpoint.

    This class handles routing for the /v1/tech_agent endpoint,
    managing the request lifecycle and calling the appropriate handler.
    """

    def __init__(self, container: DependencyContainerStub):
        """Initialize router with dependency container.

        Args:
            container: Dependency container with services
        """
        self.container = container

    @timed(task_name="tech_agent_router_run")
    async def run(self, user_input: TechAgentInput) -> Dict[str, Any]:
        """Process tech agent request.

        Args:
            user_input: User input data

        Returns:
            Response dictionary
        """
        handler = TechAgentHandler(container=self.container, user_input=user_input)
        result = await handler.run(log_record=True)
        return result


async def tech_agent_endpoint(request: Request) -> Dict[str, Any]:
    """Tech agent endpoint handler function.

    This is the main entry point for the /v1/tech_agent endpoint.
    It retrieves the container from app state and delegates to the router.

    Args:
        request: FastAPI request object

    Returns:
        Tech agent response dictionary
    """
    # Get container from app state
    container = getattr(request.app.state, "tech_agent_container", None)

    if container is None:
        # Fallback: create stub container if not in app state
        container = DependencyContainerStub()

    # Get input data from request
    # Note: This will be provided by FastAPI's dependency injection
    # when called from the endpoint
    router = TechAgentRouter(container=container)

    # The actual user_input will be passed from the endpoint
    # This is just a placeholder for the function signature
    # Return the router instance for the endpoint to use
    return router
