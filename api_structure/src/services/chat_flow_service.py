"""Chat flow service for tech agent.

This module handles chat flow logic including user info extraction,
bot scope determination, and search info processing.
"""

from typing import Any, Dict, List, Optional, Tuple
from api_structure.src.models.tech_agent_models import TechAgentInput


class ChatFlowService:
    """Service for managing chat flow logic."""

    def __init__(
        self,
        data: TechAgentInput,
        last_hint: Optional[Dict[str, Any]],
        container: Any,
    ):
        """Initialize chat flow service.

        Args:
            data: Tech agent input data
            last_hint: Last hint from history
            container: Dependency container
        """
        self.data = data
        self.last_hint = last_hint
        self.container = container

        # Default user info structure
        self.default_user_info = {
            "main_product_category": "",
            "sub_product_category": "",
            "model_name": "",
            "serial_number": "",
            "purchase_location": "",
            "purchase_date": "",
            "first_time": True,
        }

    async def get_userInfo(
        self, his_inputs: List[str]
    ) -> Tuple[Dict[str, Any], bool]:
        """Extract user information from chat history.

        Args:
            his_inputs: History of user inputs

        Returns:
            Tuple of (user_info_dict, extraction_success)
        """
        # Original logic would use GPT to extract user info
        # prompt = f"Extract user info from: {his_inputs}"
        # response = await self.container.userinfo_discrimiator.extract(prompt)

        # Mock extraction - return empty for first-time users
        user_info_dict = {
            "main_product_category": "",
            "sub_product_category": "",
            "model_name": "",
            "serial_number": "",
            "purchase_location": "",
            "purchase_date": "",
        }

        return (
            user_info_dict,
            True,
        )  # TODO: Enable when environment ready

    async def get_searchInfo(self, his_inputs: List[str]) -> str:
        """Get search information from user inputs.

        Args:
            his_inputs: History of user inputs

        Returns:
            Search query string
        """
        # Original would process and clean user input
        # Merge multiple inputs, remove special chars, etc.

        # For now, use last input as search info
        return his_inputs[-1] if his_inputs else ""

    async def get_bot_scope_chat(
        self,
        prev_user_info: Optional[Dict[str, Any]],
        curr_user_info: Dict[str, Any],
        last_bot_scope: str,
    ) -> str:
        """Determine bot scope (product line) from user info.

        Args:
            prev_user_info: Previous user info
            curr_user_info: Current user info
            last_bot_scope: Last bot scope

        Returns:
            Bot scope (product line) string
        """
        # Check if user clicked a product line hint
        if self.last_hint:
            if self.last_hint.get("hintType") == "productline-reask":
                for hint in self.last_hint.get("intentHints", []):
                    if self.data.user_input == hint.get("question"):
                        bot_scope_chat = hint.get("title", "")
                        return bot_scope_chat

        # Extract from current user info
        main_category = curr_user_info.get("main_product_category", "")
        if main_category:
            return main_category

        # Use previous user info if available
        if prev_user_info:
            prev_category = prev_user_info.get("main_product_category", "")
            if prev_category:
                return prev_category

        # Use last bot scope
        if last_bot_scope:
            return last_bot_scope

        # No product line determined
        return ""

    async def is_follow_up(
        self,
        prev_question: str,
        prev_answer: str,
        prev_answer_refs: str,
        new_question: str,
    ) -> Dict[str, Any]:
        """Determine if current question is a follow-up.

        Args:
            prev_question: Previous question
            prev_answer: Previous answer
            prev_answer_refs: Previous answer references
            new_question: New question

        Returns:
            Dict with is_follow_up flag and metadata
        """
        # Original would use GPT function calling to determine
        # if new_question is related to previous Q&A

        # prompt = f'''
        # Previous Q: {prev_question}
        # Previous A: {prev_answer}
        # References: {prev_answer_refs}
        # New Q: {new_question}
        # Is this a follow-up? Respond with JSON: {{"is_follow_up": bool}}
        # '''
        # response = await self.container.followup_discrimiator.classify(prompt)

        # Mock - assume not follow-up for first interaction
        return {
            "is_follow_up": False,
            "confidence": 0.0,
        }  # TODO: Enable when environment ready
