"""Integration tests for tech agent functionality.

This module tests the complete refactored tech agent implementation
in the api_structure directory.
"""

import sys
from pathlib import Path

import pytest
import pytest_asyncio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "api_structure"))

# noqa: E402 - import after path modification
from core.models import TechAgentInput  # noqa: E402
from src.handlers.tech_agent_handler import TechAgentHandler  # noqa: E402
from src.stubs.dependency_container_stub import (  # noqa: E402
    DependencyContainerStub,
)


@pytest_asyncio.fixture
async def container():
    """Create a dependency container for testing.

    Returns:
        DependencyContainerStub instance
    """
    container = DependencyContainerStub()
    await container.init_async(None)
    yield container
    await container.close()


@pytest.fixture
def sample_input():
    """Create sample input data for testing.

    Returns:
        TechAgentInput instance
    """
    return TechAgentInput(
        cus_id="GINA_TEST",
        session_id="f6b3ddd8-6c55-4edc-9cf0-8408664cb89d",
        chat_id="c516e816-0ad1-44f1-9046-7878bd78b3bc",
        user_input="我的筆電卡在登入畫面，完全沒有反應。",
        websitecode="tw",
        product_line="",
        system_code="rog",
    )


@pytest.mark.asyncio
async def test_tech_agent_basic_flow(container, sample_input):
    """Test basic tech agent processing flow.

    Args:
        container: Dependency container fixture
        sample_input: Sample input fixture
    """
    handler = TechAgentHandler(container=container, user_input=sample_input)
    result = await handler.run(log_record=False)

    # Verify response structure
    assert result is not None
    assert "status" in result
    assert "message" in result
    assert "result" in result
    assert result["status"] == 200
    assert result["message"] == "OK"


@pytest.mark.asyncio
async def test_tech_agent_with_product_line(container):
    """Test tech agent with product line specified.

    Args:
        container: Dependency container fixture
    """
    input_data = TechAgentInput(
        cus_id="TEST_USER",
        session_id="test-session-123",
        chat_id="test-chat-456",
        user_input="筆電無法開機",
        websitecode="tw",
        product_line="notebook",
        system_code="asus",
    )

    handler = TechAgentHandler(container=container, user_input=input_data)
    result = await handler.run(log_record=False)

    # Verify high similarity case
    assert result["status"] == 200
    assert isinstance(result["result"], list)
    if len(result["result"]) > 0:
        render_item = result["result"][0]
        assert "type" in render_item


@pytest.mark.asyncio
async def test_tech_agent_no_product_line(container):
    """Test tech agent without product line (should trigger re-ask).

    Args:
        container: Dependency container fixture
    """
    input_data = TechAgentInput(
        cus_id="TEST_USER",
        session_id="test-session-789",
        chat_id="test-chat-012",
        user_input="我的電腦有問題",
        websitecode="tw",
        product_line="",
        system_code="asus",
    )

    handler = TechAgentHandler(container=container, user_input=input_data)
    result = await handler.run(log_record=False)

    # Verify response
    assert result["status"] == 200
    assert isinstance(result["result"], list)


@pytest.mark.asyncio
async def test_tech_agent_response_fields(container, sample_input):
    """Test that all required response fields are present.

    Args:
        container: Dependency container fixture
        sample_input: Sample input fixture
    """
    handler = TechAgentHandler(container=container, user_input=sample_input)
    result = await handler.run(log_record=False)

    # Check top-level fields
    assert "status" in result
    assert "message" in result
    assert "result" in result

    # Check result structure
    assert isinstance(result["result"], list)
    if len(result["result"]) > 0:
        render_item = result["result"][0]
        assert "renderId" in render_item
        assert "type" in render_item
        assert "message" in render_item


@pytest.mark.asyncio
async def test_tech_agent_input_validation():
    """Test input validation for TechAgentInput model."""
    # Valid input
    valid_input = TechAgentInput(
        cus_id="TEST",
        session_id="session-123",
        chat_id="chat-456",
        user_input="Test question",
        websitecode="tw",
        product_line="notebook",
        system_code="asus",
    )
    assert valid_input.cus_id == "TEST"

    # Test with missing optional field
    input_no_pl = TechAgentInput(
        cus_id="TEST",
        session_id="session-123",
        chat_id="chat-456",
        user_input="Test question",
        websitecode="tw",
        product_line="",
        system_code="asus",
    )
    assert input_no_pl.product_line == ""


@pytest.mark.asyncio
async def test_tech_agent_handler_initialization(container, sample_input):
    """Test handler initialization.

    Args:
        container: Dependency container fixture
        sample_input: Sample input fixture
    """
    handler = TechAgentHandler(container=container, user_input=sample_input)

    # Verify initialization
    assert handler.container is not None
    assert handler.user_input == sample_input
    assert handler.start_time > 0
    assert handler.his_inputs == []
    assert handler.top1_kb_sim == 0.0


@pytest.mark.asyncio
async def test_tech_agent_kb_search(container, sample_input):
    """Test knowledge base search functionality.

    Args:
        container: Dependency container fixture
        sample_input: Sample input fixture
    """
    handler = TechAgentHandler(container=container, user_input=sample_input)

    # Initialize and search
    await handler._initialize_chat()
    await handler._process_history()
    await handler._get_user_and_scope_info()
    await handler._search_knowledge_base()
    handler._process_kb_results()

    # Verify search results
    assert handler.faq_result is not None
    assert "faq" in handler.faq_result
    assert "cosineSimilarity" in handler.faq_result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
