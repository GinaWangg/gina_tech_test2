"""GPT-based services for user info extraction and follow-up detection.

This module provides GPT-powered services that were previously mocked,
now enabled as the GPT environment is ready.
"""

import json
from typing import Any, Dict, List, Optional
from api_structure.src.clients.gpt import GptClient


class UserInfoExtractor:
    """Extract user information using GPT function calling."""

    SYSTEM_PROMPT = """You are tasked with extracting product-related information from user queries for technical support purposes. Analyze the user's message and reference information (if provided) to identify:

1. **Main Product Category**: The primary product type the user is referring to
2. **Sub Product Category**: Specific parts or subcategories if mentioned

Key Rules:
-User's main_product_category is Notebook, but latest inquiry is GPU broken, you should stick to Notebook.
-If the latest inquiry mentions "Wifi" or "internet-related" issues, do not automatically classify it as "wireless" in the 'Main Product Category'. Only categorize it as such if "Router" is explicitly mentioned in the inquiry. Instead, refer to and use the 'Main Product Category' specified in the 'Reference Information'.
-If the latest inquiry contains "pc" or "computer", the 'Main Product Category' is not always to be "Desktop",bacause user may talk about their component issue, you need to keep the 'main_product_category' from "Reference Information".
-If the latest inquiry contains "screen", "display", "monitor", the 'Main Product Category' is not always to be "lcd", because many products have screens, you need to keep the 'main_product_category' from "Reference Information".
-If the latest inquiry contains "fingerprint", "authentication", "scanner", the 'Main Product Category' is not always to be "notebook", because many products have fingerprint features, you need to keep the 'main_product_category' from "Reference Information".           
-The 'main_product_category' for '電競掌機', 'ROG Ally', and 'Ally' correspond to 'gaming_handhelds'.
-The 'main_product_category' for 'screenpad' and 'screen pad' correspond to 'notebook'.
-The 'main_product_category' for "Kunai" corresponds to 'phone'.
-The 'main_product_category' for 'headphone', 'headset', and 'cetra true wireless' correspond to 'accessories'.
-The 'main_product_category' for 'vivowatch', 'health hub' and 'handheld ultrasound' correspond to 'wearable'.
-The 'main_product_category' for '工作站',"work station" correspond to "desktops".
-The 'main_product_category' for "機殼","Computer Case","Liquid Cooling System","Sound cards","音效卡","光碟機" correspond to 'motherboards'.
-The 'main_product_category' for '顯卡','顯示卡' correspond to 'graphics-cards'.
-The 'main_product_category' for '外接螢幕','external monitor' correspond to 'lcd'.
- BIOS related issue 'main_product_category' should be "motherboard".
-'Zenbo' is an intellgenct robot,hence 'main_product_category' correspond to 'zenbo'.
-If the latest inquiry mentioned as "pad", it refers to tablets, and it's essential for the user to be explicit.

Output Format:
```json
{
"main_product_category": "If the user specifically mentions a product category (e.g., 'gaming_handhelds','desktop','pad','phone','wearable','motherboard','graphic cards','accessories','wireless','lcd','zenbo','nuc'), then input that category. If no product is mentioned or you are not very sure about the product (e.g. 'I can't power on','Can not connect Internet','WiFi broken','Armoury Crate','GPU'), return null.",
"sub_product_category": "Specify part or subcategory of the main product (e.g., 'Display' for Laptop). If not mentioned, return 'null'.",
}
"""

    EXTRACTION_FUNCTION = {
        "name": "information_extraction",
        "description": "This function is to extract user inforamtions.",
        "parameters": {
            "type": "object",
            "properties": {
                "main_product_category": {
                    "type": ["string", "null"],
                    "description": "If the user specifically mentions a product category, then input that category. If no product is mentioned or you are not very sure about the product, return null.",
                },
                "sub_product_category": {
                    "type": ["string", "null"],
                    "description": "Specify part or subcategory of the main product. If not mentioned, return 'null'.",
                }
            },
            "required": [
                "main_product_category",
                "sub_product_category"
            ],
        },
    }

    def __init__(self, gpt_client: GptClient):
        """Initialize user info extractor.

        Args:
            gpt_client: Initialized GPT client instance
        """
        self.gpt_client = gpt_client

    async def extract(self, user_inputs: str) -> Dict[str, Any]:
        """Extract user information from inputs.

        Args:
            user_inputs: User message or conversation history

        Returns:
            Dictionary with main_product_category and sub_product_category
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_inputs}
        ]

        try:
            response = await self.gpt_client.call_with_functions(
                messages=messages,
                functions=[self.EXTRACTION_FUNCTION],
                function_call={"name": "information_extraction"}
            )
            
            if response and hasattr(response, 'function_call'):
                result = json.loads(response.function_call.arguments)
                return {
                    "main_product_category": result.get("main_product_category"),
                    "sub_product_category": result.get("sub_product_category"),
                }
        except Exception as e:
            print(f"[UserInfoExtractor] Error: {e}")
        
        # Return empty on error
        return {
            "main_product_category": None,
            "sub_product_category": None,
        }


class FollowUpDetector:
    """Detect if user message is a follow-up using GPT function calling."""

    FOLLOW_UP_FUNCTION = {
        "name": "follow_up_bool",
        "description": "Decide if latest user message follows up on the previous assistant reply.",
        "parameters": {
            "type": "object",
            "required": [
                "is_follow_up",
                "confidence",
                "anchor",
                "needs_disambiguation",
                "reason_short",
            ],
            "properties": {
                "is_follow_up": {"type": "boolean"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "anchor": {"type": ["string", "null"]},
                "needs_disambiguation": {"type": "boolean"},
                "reason_short": {"type": "string"},
            },
            "additionalProperties": False,
        },
    }

    SYSTEM_PROMPT = """
    You are a classifier that decides whether the latest user message is a FOLLOW-UP to the previous assistant reply.

    DEFINITION (Follow-up):
    - The message asks for steps/how-to/where-to-check/confirmation/clarification of an action or term mentioned in the previous assistant reply.
    - It may use anaphora like: 你說的/剛剛/上述/這個/那個/this/that/above.
    - Narrowing scope or asking details of a previously suggested action also counts.

    NOT a follow-up:
    - Topic shift / new product / unrelated chit-chat / emotions without referencing prior content.

    Ambiguity:
    - If likely referring to the prior reply but unclear which part, set is_follow_up=true and needs_disambiguation=true, and anchor with a short hint.

    OUTPUT:
    Return ONLY a function call with arguments in this JSON shape:
    { "is_follow_up": bool, "confidence": 0~1, "anchor": string|null, "needs_disambiguation": bool, "reason_short": string }
    """.strip()

    FEW_SHOT = """
    EXAMPLES:

    [1]
    Prev: 建議先更新 BIOS，或先檢查目前 BIOS 版本是否為最新。
    User: 要怎麼檢查 BIOS 是否完成更新？
    → {"is_follow_up": true, "confidence": 0.9, "anchor": "check BIOS version", "needs_disambiguation": false, "reason_short": "Asks for steps to verify an action from the previous reply."}

    [2]
    Prev: 建議先更新 BIOS，或先檢查目前 BIOS 版本是否為最新。
    User: 那個步驟在哪裡看？
    → {"is_follow_up": true, "confidence": 0.8, "anchor": "steps for BIOS check/update", "needs_disambiguation": true, "reason_short": "Pronoun refers to steps; unclear which one."}

    [3]
    Prev: 建議先更新 BIOS，或先檢查目前 BIOS 版本是否為最新。
    User: 我還想問螢幕有沒有 4K？
    → {"is_follow_up": false, "confidence": 0.7, "anchor": null, "needs_disambiguation": false, "reason_short": "Topic shift to monitor resolution."}
    """.strip()

    USER_TEMPLATE = """
    Previous assistant reply:
    {prev_reply}

    Latest user message:
    {new_query}
    """.strip()

    def __init__(self, gpt_client: GptClient):
        """Initialize follow-up detector.

        Args:
            gpt_client: Initialized GPT client instance
        """
        self.gpt_client = gpt_client

    async def detect(
        self,
        prev_question: str,
        prev_answer: str,
        prev_answer_refs: str,
        new_question: str,
    ) -> Dict[str, Any]:
        """Detect if new question is a follow-up.

        Args:
            prev_question: Previous user question
            prev_answer: Previous assistant answer
            prev_answer_refs: Previous answer references
            new_question: New user question

        Returns:
            Dictionary with is_follow_up, confidence, anchor, etc.
        """
        # Handle empty question
        if not new_question:
            return {
                "is_follow_up": False,
                "confidence": 0.0,
                "anchor": None,
                "needs_disambiguation": False,
                "reason_short": "Empty latest user message.",
            }

        # Build context
        parts = [f"[Previous Question]\n{prev_question}"]
        parts.append(f"[Previous Answer]\n{prev_answer}")
        if prev_answer_refs:
            parts.append(f"[Answer References]\n{prev_answer_refs}")
        prev_reply = "\n\n".join(parts)

        # Build messages
        sys_content = self.SYSTEM_PROMPT + "\n\n" + self.FEW_SHOT
        user_content = self.USER_TEMPLATE.format(
            prev_reply=prev_reply,
            new_query=new_question
        )
        
        messages = [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_content},
        ]

        try:
            response = await self.gpt_client.call_with_functions(
                messages=messages,
                functions=[self.FOLLOW_UP_FUNCTION],
                function_call={"name": "follow_up_bool"}
            )
            
            if response and hasattr(response, 'function_call'):
                return json.loads(response.function_call.arguments)
        except Exception as e:
            print(f"[FollowUpDetector] Error: {e}")

        # Conservative fallback
        return {
            "is_follow_up": False,
            "confidence": 0.0,
            "anchor": None,
            "needs_disambiguation": False,
            "reason_short": "Failed to parse function args",
        }


class AvatarResponseGenerator:
    """Generate friendly avatar responses using GPT."""

    def __init__(self, gpt_client: GptClient):
        """Initialize avatar response generator.

        Args:
            gpt_client: Initialized GPT client instance
        """
        self.gpt_client = gpt_client

    async def generate(
        self,
        user_input: str,
        lang: str,
        context: Optional[str] = None
    ) -> str:
        """Generate avatar response.

        Args:
            user_input: User's message
            lang: Language code (e.g., 'zh-TW', 'en-US')
            context: Optional KB content or context for response

        Returns:
            Generated avatar response text
        """
        # Build system prompt based on language
        if lang.startswith('zh'):
            system_prompt = """你是華碩技術支援小幫手。請用友善、專業的語氣回應用戶的技術問題。
如果有提供知識庫內容，請根據內容給出建議。保持回應簡潔、有幫助。"""
        else:
            system_prompt = """You are ASUS technical support assistant. Please respond to user's technical questions in a friendly and professional manner.
If KB content is provided, base your suggestions on that content. Keep responses concise and helpful."""

        # Build user prompt
        if context:
            user_prompt = f"User question: {user_input}\n\nKB context: {context}\n\nPlease provide a helpful response based on this information."
        else:
            user_prompt = f"User question: {user_input}\n\nPlease provide a friendly greeting and let them know you're here to help."

        try:
            response = await self.gpt_client.call_with_prompts(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            if response and isinstance(response, dict):
                # Extract response from various possible formats
                return response.get('content', response.get('answer', str(response)))
            elif response:
                return str(response)
        except Exception as e:
            print(f"[AvatarResponseGenerator] Error: {e}")

        # Fallback response
        if lang.startswith('zh'):
            return "您好！我是華碩技術支援小幫手。我會盡力協助您解決問題。請告訴我更多細節吧！"
        else:
            return "Hello! I'm ASUS technical support assistant. I'll do my best to help you. Please tell me more details!"
