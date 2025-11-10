"""Handler for tech agent business logic."""

import time
import uuid
from datetime import datetime
from api_structure.core.timer import timed


class TechAgentHandler:
    """Handler for processing tech agent requests."""

    def __init__(self):
        """Initialize the tech agent handler."""
        self.start_time = time.perf_counter()

    @timed(task_name="tech_agent_handler_process")
    async def process(self, user_input):
        """
        Process tech agent request and return response.

        This is a simplified version that returns mock responses since
        API and Cosmos connections are currently disabled.

        Args:
            user_input: TechAgentInput model with user request data

        Returns:
            Response dictionary with status, message, and result
        """
        # Generate unique IDs
        render_id = str(uuid.uuid4())

        # Determine response type based on product_line
        if not user_input.product_line:
            response_type = "avatarAskProductLine"
            result = await self._handle_no_product_line(render_id, user_input)
        else:
            # Default to technical support response
            response_type = "avatarTechnicalSupport"
            result = await self._handle_technical_support(
                render_id, user_input
            )

        # Calculate execution time
        exec_time = round(time.perf_counter() - self.start_time, 2)

        # Return final response
        return {
            "status": 200,
            "message": "OK",
            "result": result,
            "exec_time": exec_time
        }

    @timed(task_name="handle_no_product_line")
    async def _handle_no_product_line(self, render_id: str, user_input):
        """
        Handle case where no product line is specified.

        Args:
            render_id: Unique render ID
            user_input: User input data

        Returns:
            Result dictionary for no product line scenario
        """
        avatar_message = (
            "我可以幫您解決技術問題！"
            "為了更精確地協助您，請告訴我您使用的產品線是什麼呢？"
        )

        product_line_options = [
            {
                "name": "筆記型電腦",
                "value": "notebook",
                "icon": "laptop"
            },
            {
                "name": "桌上型電腦",
                "value": "desktop",
                "icon": "desktop"
            },
            {
                "name": "手機",
                "value": "mobile",
                "icon": "phone"
            }
        ]

        return [
            {
                "renderId": render_id,
                "stream": False,
                "type": "avatarAskProductLine",
                "message": avatar_message,
                "remark": [],
                "option": product_line_options
            }
        ]

    @timed(task_name="handle_technical_support")
    async def _handle_technical_support(self, render_id: str, user_input):
        """
        Handle technical support request with product line.

        Args:
            render_id: Unique render ID
            user_input: User input data

        Returns:
            Result dictionary for technical support scenario
        """
        avatar_message = (
            f"我了解您在{user_input.product_line}產品上遇到了問題。"
            "讓我為您查詢相關的解決方案。"
        )

        # Mock FAQ card
        faq_card = {
            "type": "faqcards",
            "cards": [
                {
                    "link": "https://www.asus.com/support/",
                    "title": "常見問題解決方案",
                    "content": "這裡是針對您問題的解決方案說明..."
                }
            ]
        }

        return [
            {
                "renderId": render_id,
                "stream": False,
                "type": "avatarTechnicalSupport",
                "message": avatar_message,
                "remark": [],
                "option": [faq_card]
            }
        ]
