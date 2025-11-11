"""Handler for tech agent processing logic."""

from typing import Any, Dict

from api_structure.core.logger import set_extract_log
from api_structure.core.timer import timed
from api_structure.src.models.tech_agent_models import TechAgentRequest
from src.core.tech_agent_api import TechAgentInput, TechAgentProcessor


class TechAgentHandler:
    """Handler class for tech agent processing."""

    def __init__(self, containers):
        """
        Initialize the tech agent handler.

        Args:
            containers: DependencyContainer with all required services
        """
        self.containers = containers

    @timed(task_name="tech_agent_handler_process")
    async def process(self, request: TechAgentRequest) -> Dict[str, Any]:
        """
        Process tech agent request using original TechAgentProcessor.

        This method delegates to the original tech_agent_api logic
        to maintain the same processing flow and output format.

        Args:
            request: Tech agent request data

        Returns:
            Dictionary containing the full response with final_result
            and cosmos_data
        """
        # 記錄處理日誌
        set_extract_log(
            {
                "user_input": request.user_input,
                "session_id": request.session_id,
                "product_line": request.product_line,
                "system_code": request.system_code,
            }
        )

        # 將 TechAgentRequest 轉換為 TechAgentInput
        tech_input = TechAgentInput(
            cus_id=request.cus_id,
            session_id=request.session_id,
            chat_id=request.chat_id,
            user_input=request.user_input,
            websitecode=request.websitecode,
            product_line=request.product_line,
            system_code=request.system_code,
        )

        # 使用原始的 TechAgentProcessor 處理請求
        processor = TechAgentProcessor(
            containers=self.containers, user_input=tech_input
        )

        # 執行完整的處理流程
        response_data = await processor.process(log_record=False)

        # 返回包含 final_result 和完整資訊的回應
        return {
            "response_data": response_data,
            "final_result": processor.final_result,
            "cosmos_data": await processor._log_and_save_results(),
        }
