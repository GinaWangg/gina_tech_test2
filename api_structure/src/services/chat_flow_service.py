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
        user_info_extractor: Optional[Any] = None,
        follow_up_detector: Optional[Any] = None,
    ):
        """Initialize chat flow service.

        Args:
            data: Tech agent input data
            last_hint: Last hint from history
            container: Dependency container
            user_info_extractor: GPT-based user info extractor (optional)
            follow_up_detector: GPT-based follow-up detector (optional)
        """
        self.data = data
        self.last_hint = last_hint
        self.container = container
        self.user_info_extractor = user_info_extractor
        self.follow_up_detector = follow_up_detector

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
        # Use GPT to extract user info if extractor is available
        if self.user_info_extractor:
            try:
                # Combine inputs for context
                combined_input = "\n".join(his_inputs)
                result = await self.user_info_extractor.extract(combined_input)
                
                user_info_dict = {
                    "main_product_category": result.get("main_product_category") or "",
                    "sub_product_category": result.get("sub_product_category") or "",
                    "model_name": "",
                    "serial_number": "",
                    "purchase_location": "",
                    "purchase_date": "",
                }
                return (user_info_dict, True)
            except Exception as e:
                print(f"[ChatFlowService] User info extraction failed: {e}")

        # Fallback - return empty for first-time users
        user_info_dict = {
            "main_product_category": "",
            "sub_product_category": "",
            "model_name": "",
            "serial_number": "",
            "purchase_location": "",
            "purchase_date": "",
        }

        return (user_info_dict, True)

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
        # Use GPT to detect follow-up if detector is available
        if self.follow_up_detector:
            try:
                result = await self.follow_up_detector.detect(
                    prev_question=prev_question,
                    prev_answer=prev_answer,
                    prev_answer_refs=prev_answer_refs,
                    new_question=new_question,
                )
                return result
            except Exception as e:
                print(f"[ChatFlowService] Follow-up detection failed: {e}")

        # Fallback - assume not follow-up
        return {
            "is_follow_up": False,
            "confidence": 0.0,
        }
