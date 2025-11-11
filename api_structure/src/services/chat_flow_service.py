"""Chat flow service for handling user info and bot scope logic."""

import json
from typing import Any, Dict, List, Optional


class ChatFlowService:
    """Service for managing chat flow logic.

    Handles user information extraction, bot scope determination,
    and follow-up question detection.
    """

    def __init__(self):
        """Initialize chat flow service."""
        self.default_user_info = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": None,
            "sub_product_category": None,
            "first_time": True,
        }

    async def get_user_info(self, his_inputs: List[str]) -> tuple[Dict[str, Any], str]:
        """Extract user information from chat history.

        Args:
            his_inputs: List of historical user inputs.

        Returns:
            Tuple of (user_info_dict, search_info)
        """
        # TODO: Enable when environment ready
        # Original: await GPT to extract user info
        # For now, return mock data
        user_info_dict = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": "notebook",
            "sub_product_category": None,
            "first_time": False,
        }

        search_info = his_inputs[-1] if his_inputs else ""

        return user_info_dict, search_info

    async def get_bot_scope(
        self,
        prev_user_info: Dict[str, Any],
        curr_user_info: Dict[str, Any],
        last_bot_scope: str,
        product_line: str,
        last_hint: Optional[Dict[str, Any]],
        user_input: str,
    ) -> str:
        """Determine bot scope from user information.

        Args:
            prev_user_info: Previous user information.
            curr_user_info: Current user information extracted from input.
            last_bot_scope: Last determined bot scope.
            product_line: Explicitly provided product line.
            last_hint: Last hint data for product line re-ask.
            user_input: Current user input.

        Returns:
            Bot scope (product line) string.
        """
        # Handle product line re-ask hint
        if last_hint and last_hint.get("hintType") == "productline-reask":
            for hint in last_hint.get("intentHints", []):
                if user_input == hint.get("question"):
                    return hint.get("title", "")

        # Update user info
        user_info_string = self._update_user_info(prev_user_info, curr_user_info)
        user_info_dict = json.loads(user_info_string)

        # TODO: Enable when environment ready
        # Original: Redis lookup for product line mapping
        # For now, use simple logic
        bot_scope = ""

        if user_info_dict.get("main_product_category"):
            bot_scope = user_info_dict.get("main_product_category")
        elif user_info_dict.get("sub_product_category"):
            bot_scope = user_info_dict.get("sub_product_category")
        else:
            bot_scope = product_line

        # If invalid, fallback to last bot scope
        if not bot_scope:
            bot_scope = last_bot_scope

        return bot_scope or ""

    def _update_user_info(
        self, previous: Dict[str, Any], current: Dict[str, Any]
    ) -> str:
        """Update user information merging previous and current.

        Args:
            previous: Previous user information.
            current: Current user information.

        Returns:
            JSON string of merged user information.
        """
        # Handle null values
        for key, values in current.items():
            if values == "null":
                current[key] = None

        for key, values in previous.items():
            if values == "null":
                previous[key] = None

        # First time flag handling
        first_bot = None
        if previous.get("first_time"):
            first_bot = previous.get("main_product_category")
            del previous["first_time"]

        # Merge current into previous
        for key, values in current.items():
            if values:
                previous[key] = values

        # Preserve first bot if exists
        if first_bot:
            previous["main_product_category"] = first_bot

        return json.dumps(previous, ensure_ascii=False)

    async def is_follow_up(
        self,
        prev_question: str,
        prev_answer: str,
        prev_answer_refs: str,
        new_question: str,
    ) -> Dict[str, bool]:
        """Determine if current question is a follow-up.

        Args:
            prev_question: Previous question.
            prev_answer: Previous answer.
            prev_answer_refs: Previous answer references.
            new_question: New question to evaluate.

        Returns:
            Dictionary with is_follow_up boolean.
        """
        # TODO: Enable when environment ready
        # Original: GPT-based follow-up detection
        # For now, return mock data
        return {"is_follow_up": False}

    async def get_search_info(self, his_inputs: List[str]) -> str:
        """Extract search information from chat history.

        Args:
            his_inputs: List of historical user inputs.

        Returns:
            Search information string.
        """
        # TODO: Enable when environment ready
        # Original: Translation and search info extraction
        # For now, return latest input
        return his_inputs[-1] if his_inputs else ""
