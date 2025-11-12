"""Chat flow service for handling user info and bot scope logic."""

import json
from typing import Any, Dict, List, Optional

from api_structure.src.clients.gpt import GptClient


class ChatFlowService:
    """Service for managing chat flow logic.

    Handles user information extraction, bot scope determination,
    and follow-up question detection.
    """

    def __init__(self, gpt_client: Optional[GptClient]):
        """Initialize chat flow service.

        Args:
            gpt_client: Initialized GptClient instance for GPT operations.
                Can be None for testing/fallback mode.
        """
        self.gpt_client = gpt_client
        self.default_user_info = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": None,
            "sub_product_category": None,
            "first_time": True,
        }

        # GPT system messages for user info extraction
        self.system_messages = [
            {
                "role": "system",
                "content": """
As an AI assistant, your role is to extract relevant information from a conversation on user's latest statements.
Your task is to fill in the appropriate fields in the JSON format and ensure all results are in English.

Context and Definitions:
- Software names include 'Armoury Crate', 'MyASUS', 'AURA Creator'.
- '手機' translates to 'Phone'.
- BTF means HIDDEN-CONNECTOR DESIGN, is an important feature of products.
- EVA series, Gundum series are co-branded products.
- 西風之神是 ROG Zephyrus.
- NUC (Next Unit of Computing) is a series of small-sized barebone computers designed by ASUS.
- NUCs is Product of ASUS, not Intel!

Main product Categories Tips:
-Motherboard could cause BSOD(Blus screen of Death), wifi disconnected,hard dirve issue,driver issue,Internet issue.
-User's main_product_category is Notebook, but latest inquiry is GPU broken, you should stick to Notebook.
-If the latest inquiry mentions "Wifi" or "internet-related" issues, do not automatically classify it as "wireless".
-If the latest inquiry contains "pc" or "computer", the 'Main Product Category' is not always to be "Desktop".
-If the latest inquiry contains "screen", "display", "monitor", the 'Main Product Category' is not always to be "lcd".
-The 'main_product_category' for '電競掌機', 'ROG Ally', and 'Ally' correspond to 'gaming_handhelds'.
-The 'main_product_category' for 'screenpad' and 'screen pad' correspond to 'notebook'.
-The 'main_product_category' for "Kunai" corresponds to 'phone'.
-The 'main_product_category' for 'headphone', 'headset' correspond to 'accessories'.
-The 'main_product_category' for 'vivowatch', 'health hub' correspond to 'wearable'.
-The 'main_product_category' for '工作站',"work station" correspond to "desktops".
-The 'main_product_category' for "機殼","Computer Case","Liquid Cooling System" correspond to 'motherboards'.
-The 'main_product_category' for '顯卡','顯示卡' correspond to 'graphics-cards'.
-The 'main_product_category' for '外接螢幕','external monitor' correspond to 'lcd'.

Output Format:
{
"main_product_category": "If the user specifically mentions a product category (e.g., 'gaming_handhelds','desktop','pad','phone','wearable','motherboard','graphic cards','accessories','wireless','lcd','zenbo','nuc'), then input that category. If no product is mentioned or you are not very sure, return null.",
"sub_product_category": "Specify part or subcategory of the main product (e.g., 'Display' for Laptop). If not mentioned, return 'null'.",
}
""",
            }
        ]

    async def get_user_info(self, his_inputs: List[str]) -> tuple[Dict[str, Any], str]:
        """Extract user information from chat history using GPT.

        Args:
            his_inputs: List of historical user inputs.

        Returns:
            Tuple of (user_info_dict, search_info)
        """
        # Prepare default fallback
        user_info_dict = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": None,
            "sub_product_category": None,
            "first_time": False,
        }

        search_info = his_inputs[-1] if his_inputs else ""

        # Try real GPT extraction if client is available
        if self.gpt_client:
            try:
                extraction_functions = [
                    {
                        "name": "information_extraction",
                        "description": "This function is to extract user inforamtions.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "main_product_category": {
                                    "type": ["string", "null"],
                                    "description": "If the user specifically mentions a product category (e.g., 'gaming_handhelds','desktop','pad','phone','wearable','motherboard','graphic cards','accessories','wireless','lcd','zenbo'), then input that category. If no product is mentioned or you are not very sure about the product (e.g. 'I can't power on', 'Can not connect Internet', 'WiFi broken', 'Armoury Crate', 'GPU'), return null.",
                                },
                                "sub_product_category": {
                                    "type": ["string", "null"],
                                    "description": "Specify part or subcategory of the main product (e.g., 'Display' for Laptop). If not mentioned, return 'null'.",
                                },
                            },
                            "required": [
                                "main_product_category",
                                "sub_product_category",
                            ],
                        },
                    }
                ]

                messages = self.system_messages.copy()
                messages.extend([{"role": "user", "content": str(his_inputs)}])

                response = await self.gpt_client.call_with_functions(
                    messages, extraction_functions, {"name": "information_extraction"}
                )

                # Parse the function call response
                extracted_info = json.loads(response.function_call.arguments)

                # Update user_info_dict with extracted information
                if extracted_info.get("main_product_category"):
                    user_info_dict["main_product_category"] = extracted_info[
                        "main_product_category"
                    ]
                if extracted_info.get("sub_product_category"):
                    user_info_dict["sub_product_category"] = extracted_info[
                        "sub_product_category"
                    ]

                print(f"GPT user info extraction successful: {user_info_dict}")

            except Exception as e:
                print(f"GPT user info extraction failed: {e}, using fallback")
                # Fallback to default values already set above

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

        # Note: Redis product line mapping would go here in production
        # For now, use simple logic based on extracted product category
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
        """Determine if current question is a follow-up using GPT.

        Args:
            prev_question: Previous question.
            prev_answer: Previous answer.
            prev_answer_refs: Previous answer references.
            new_question: New question to evaluate.

        Returns:
            Dictionary with is_follow_up boolean.
        """
        # Default fallback
        default_result = {"is_follow_up": False}

        # Try real GPT follow-up detection if client is available
        if self.gpt_client:
            try:
                # Empty new question → not a follow-up
                if not new_question or new_question.strip() == "":
                    return default_result

                # Build context from previous interaction
                parts = [
                    "[Previous Question]\n" + prev_question,
                    "[Previous Answer]\n" + prev_answer,
                ]
                if prev_answer_refs:
                    parts.append("[Answer References]\n" + prev_answer_refs)
                prev_reply = "\n\n".join(parts)

                # Define follow-up detection function
                follow_up_function = {
                    "name": "follow_up_bool",
                    "description": "Decide if latest user message follows up on the previous assistant reply.",
                    "parameters": {
                        "type": "object",
                        "required": ["is_follow_up", "confidence"],
                        "properties": {
                            "is_follow_up": {"type": "boolean"},
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                        },
                    },
                }

                # Build system prompt
                system_prompt = """
You are a classifier that decides whether the latest user message is a FOLLOW-UP to the previous assistant reply.

DEFINITION (Follow-up):
- The message asks for steps/how-to/where-to-check/confirmation/clarification of an action or term mentioned in the previous assistant reply.
- It may use anaphora like: 你說的/剛剛/上述/這個/那個/this/that/above.
- Narrowing scope or asking details of a previously suggested action also counts.

NOT a follow-up:
- Topic shift / new product / unrelated chit-chat / emotions without referencing prior content.

OUTPUT: Return a function call with is_follow_up (bool) and confidence (0-1).
"""

                messages = [
                    {"role": "system", "content": system_prompt.strip()},
                    {
                        "role": "user",
                        "content": f"{prev_reply}\n\n[Latest User Message]\n{new_question}",
                    },
                ]

                response = await self.gpt_client.call_with_functions(
                    messages, [follow_up_function], {"name": "follow_up_bool"}
                )

                # Parse the function call response
                result = json.loads(response.function_call.arguments)

                print(f"GPT follow-up detection: {result}")

                return {"is_follow_up": bool(result.get("is_follow_up", False))}

            except Exception as e:
                print(f"GPT follow-up detection failed: {e}, using fallback")

        return default_result

    async def get_search_info(self, his_inputs: List[str]) -> str:
        """Extract search information from chat history.

        Args:
            his_inputs: List of historical user inputs.

        Returns:
            Search information string.
        """
        # For search info, just return the latest input
        # No GPT needed for this simple extraction
        return his_inputs[-1] if his_inputs else ""
