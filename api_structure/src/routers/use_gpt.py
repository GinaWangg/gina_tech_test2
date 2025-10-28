"""Router for GPT-related endpoints."""

from src.handlers.gpt_prompt_examples import GptTaskHandler
from src.handlers.call_redis_api_examplse import CallRedisApiExamples
from core.timer import timed
from core.logger import set_extract_log
import asyncio
from fastapi import Request
from typing import Dict, Any

class TestGptEndpoint:
    """Class-based endpoint handler for testing GPT client."""
    
    def __init__(self, gpt_client, aiohttp_client):
        """Initialize with a GPT client instance.
        
        Args:
            gpt_client: Initialized GptClient instance.
        """
        self.gpt_client = gpt_client
        self.aiohttp_client = aiohttp_client
    
    @timed(task_name="test_gpt_endpoint_step1")
    async def _step1(self) -> str:
        """Step 1: Simple hello world example using GPT client.
        
        Returns:
            Response string from GPT model.
        """
        handler = GptTaskHandler(self.gpt_client)
        result = await handler.run()
        return result
    
    @timed(task_name="test_gpt_endpoint_step2")
    async def _step2(self) -> str:
        """Step 2: Another step that could involve more complex logic.
        
        Returns:
            Response string from GPT model.
        """
        await asyncio.sleep(0.5)
        return "Step 2 completed"
    
    @timed(task_name="fetch_faq_endpoint")
    async def fetch_faq_endpoint(self, keyword: str) -> Dict[str, Any]:
        """
        使用 aiohttp client 來呼叫 FAQ 搜尋 API 的範例。
        
        Args:
            request: FastAPI Request object containing app state
            data: FAQ search parameters
            
        Returns:
            FAQ search results
        """
        
        handler = CallRedisApiExamples(self.aiohttp_client)
        result = await handler.run(keyword=keyword)
        
        return result
    
    @timed(task_name="test_gpt_endpoint_run")
    async def run(self) -> dict:
        """Run the GPT task handler and return the result.
        
        Returns:
            Response string from GPT model.
        """
        result1 = await self._step1()
        result2 = await self._step2()
        redis_api = await self.fetch_faq_endpoint(keyword="example")
        final_result = {
            "step1_result": result1,
            "step2_result": result2,
            "redis_api_result": redis_api
        }
        
        set_extract_log(
            extract_log={
                "extra_info": "Test run completed",
                "log": "這個我都亂寫的 依照專案調整唷",
                "step1_length": len(result1) if result1 else 0,
                "step2_length": len(result2) if result2 else 0, 
                "redis_result": redis_api
            }
        )
        
        return final_result


async def use_gpt_endpoint(request: Request) -> dict:
    gpt_client = request.app.state.gpt_client
    aiohttp_client = request.app.state.aiohttp_client
    handler = TestGptEndpoint(
        gpt_client=gpt_client, 
        aiohttp_client=aiohttp_client)
    result = await handler.run()
    return result