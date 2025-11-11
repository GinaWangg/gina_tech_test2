"""Simple test script to verify the API endpoint works."""

import asyncio
import json
import sys
from pathlib import Path

# Add api_structure to path
sys.path.insert(0, str(Path(__file__).parent / "api_structure"))

from core.models import TechAgentInput
from src.routers.tech_agent_router import TechAgentRouter
from src.stubs.dependency_container_stub import DependencyContainerStub


async def test_endpoint():
    """Test the tech agent endpoint with sample data."""
    # Create container
    container = DependencyContainerStub()
    await container.init_async(None)
    
    # Create sample input as specified in the issue
    user_input = TechAgentInput(
        cus_id="GINA_TEST",
        session_id="f6b3ddd8-6c55-4edc-9cf0-8408664cb89d",
        chat_id="c516e816-0ad1-44f1-9046-7878bd78b3bc",
        user_input="我的筆電卡在登入畫面，完全沒有反應。",
        websitecode="tw",
        product_line="",
        system_code="rog",
    )
    
    # Create router and call endpoint
    router = TechAgentRouter(container=container)
    result = await router.run(user_input)
    
    # Print result
    print("\n" + "="*60)
    print("Tech Agent API Test Result")
    print("="*60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("="*60 + "\n")
    
    # Verify basic structure
    assert "status" in result
    assert "message" in result
    assert "result" in result
    assert result["status"] == 200
    
    print("✓ All assertions passed!")
    print(f"✓ Response type: {result.get('message', 'N/A')}")
    print(f"✓ Result items: {len(result.get('result', []))}")
    
    await container.close()
    return result


if __name__ == "__main__":
    result = asyncio.run(test_endpoint())
