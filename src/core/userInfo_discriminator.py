# -*- coding: utf-8 -*-
"""
Created on Wed Sep  6 15:29:24 2023

@author: Billy_Hsu
"""
from pathlib import Path
import sys
REPO_ROOT = Path(__file__).resolve().parents[2]  # 指到 ts_agent 專案根目錄
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
# flake8: noqa E501, W605
import json
from src.services.base_service import BaseService
from utils.warper import async_timer
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, StrictStr, validator, Extra
 
class UserInfo(BaseModel):
    main_product_category: Optional[StrictStr]
    sub_product_category: Optional[StrictStr]
 
    def null_to_empty_list(cls, v):
        """
        如果輸入值是 None，則轉換成空的 list。
        """
        return [] if v is None else v
   
    class Config:
        extra = Extra.ignore  # 或 Extra.allow / Extra.forbid 根據需求選擇

class UserinfoDiscriminator(BaseService):

    def __init__(self, config):
        super().__init__(config)

        self.empty_userInfo = {
            "main_product_category": None,
            "sub_product_category": None
        }
        self.complaint_system_messages = [
            {
                "role": "system",
                "content": """
As an AI assistant, your task is to determine the severity of a customer's complaint based on their latest statement. Refer to the "Complaint Levels Descriptions" provided below to categorize the complaint. You must fill in the appropriate fields in the JSON format, ensuring all results are in English.

Complaint Levels Descriptions:

1. Casual Conversations:
   - Interactions where the customer is seeking information, service locations, repair locations, solutions, clarifications, or guidance related to products or services.
   - Customers may raise issues or ask questions without necessarily conveying disappointment or frustration.
   - Topics can include inquiries about product features, understanding repair procedures, warranty information, product recommendations, or simple repair requests.

2. Mild Complaints:
   - Interactions where customers express minor to medium dissatisfaction or concerns that do not indicate a severe safety hazard or total product failure.
   - Examples include feedback on specific features, aesthetic aspects, non-starting devices, minor software glitches, and battery drain.
   - These complaints address potential malfunctions or inconveniences without involving critical product malfunctions, safety concerns, major service failures, or signs of prior product use/tampering.

3. Severe Complaints:
   - Clear indications of product malfunction, safety hazards (including terms like "burn", "smoke", "explosion", "fire"), warranty and repair issues, questions of product authenticity, signs of prior use or tampering, major software or hardware issues post-update, and suspected unauthorized activities or anomalies with the product.
   - This category includes scenarios where agents have not responded within two days and interactions involving aggressive or passive-aggressive language, criticism, suggestions of legal actions, direct mentions of significant product defects, and service failures leading to escalated dissatisfaction.
   - Explicit requests for product replacements or indications of severe hardware damages also fall under this category.

Important Notes:
- If the complaint contains words like "burn", "smoke", "explosion", "fire", categorize it as a Severe Complaint.
- Words like "客訴" or "complaint", "I need to talk to your manager(owner)", or discrepancies between product advertisement and actual usage should be categorized as Severe Complaints.
- If the inquiry mentions 'seeking repair', 'ask repair', 'seeking repair location', 'inquire about repair', or 'can it be repaired', categorize it as Mild Complaints or Casual Conversations.
- Human-caused damages are not included in severe complaints.
- If the inquiry mentions 'Repair service center', categorize it as Casual Conversations or Mild Complaints.
- 'Royal Repair', '皇家', '皇家維修中心', and '皇家俱樂部' all refer to ASUS's repair service center.

""",
            }
        ]
        self.system_messages = [
            {
                "role": "system",
                "content": """
As an AI assistant, your role is to extract relevant information from a conversation on user's latest statements.
Your task is to fill in the appropriate fields in the JSON format and ensure all results are in English.

Context and Definitions:
- Software names include 'Armoury Crate', 'MyASUS', 'AURA Creator'.
- '手機' translates to 'Phone'.
- BTF means HIDDEN-CONNECTOR DESIGN, is an important feature of products. you should collect it in product name.
- EVA series, Gundum series are co-branded products.
- 西風之神是 ROG Zephyrus.
- NUC (Next Unit of Computing) is a series of small-sized barebone computers designed by ASUS.
- NUCs is Product of ASUS, not Intel!

Step-by-Step Instructions for Updating Information:

1.Categorization: If the product is independent, classify it under the 'main_product_category'.
2.Secondary Categorization: If there's an associated second product category linked with the 'main_product_category', ensure it's filled in.

Main product Categories Tips:

-Motherboard could cause BSOD(Blus screen of Death), wifi disconnected,hard dirve issue,driver issue,Internet issue.
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
"main_product_category": "If the user specifically mentions a product category (e.g., 'gaming_handhelds','desktop','pad','phone','wearable','motherboard','graphic cards','accessories','wireless','lcd','zenbo','nuc'), then input that category. If no product is mentioned or you are not very sure about the product (e.g. "I can't power on","Can not connect Internet","WiFi broken","Armoury Crate","GPU"), return null.",
"sub_product_category": "Specify part or subcategory of the main product (e.g., 'Display' for Laptop). If not mentioned, return 'null'.",
}

Example Output:
User: 我想查詢訂單編號 RMA-CS-13000696534-1
{'main_product_category': None, 'sub_product_category': None}
User: 我想查詢訂單編號 RMA-CS-13000696534-11111
{'main_product_category': None, 'sub_product_category': None}
User: 我想查詢訂單編號 RMA-CS-300。0181，-1
{'main_product_category': None, 'sub_product_category': None}
```""",
            }
        ]

    # @async_timer.timeit
    async def userInfo_GPT_part1(self, user_inputs):
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
                        }
                    },
                    "required": [
                        "main_product_category",
                        "sub_product_category"
                    ],
                },
            }
        ]
        messages = self.system_messages.copy()
        messages.extend([{"role": "user", "content": """{}""".format(user_inputs)}])

        try:
            response = await self.GPT41_mini_response_functions(
                messages, extraction_functions, {"name": "information_extraction"}
            )
            # response = await self.GPT4o_mini_response_functions(messages,extraction_functions,{"name": "information_extraction"})
            response = json.loads(response.function_call.arguments)
            response = UserInfo(**response).dict()
        except Exception as e:
            print(e)
            response = self.handle_gpt_error_response()
            response.pop("Complaint Level", None)
            response = UserInfo(**response).dict()
        return response

    # @async_timer.timeit
    async def complaint_GPT(self, user_input):
        messages = self.complaint_system_messages.copy()
        complaint_functions = [
            {
                "name": "complain_detect",
                "description": "This function is to detect user complaint level.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Complaint Level": {
                            "type": "string",
                            "description": "The level of the user's complaint.",
                            "enum": [
                                "Casual Conversations",
                                "Mild Complaints",
                                "Severe Complaints",
                            ],
                        }
                    },
                    "required": ["Complaint Level"],
                },
            }
        ]
        messages.extend(
            [
                {
                    "role": "user",
                    "content": """{}.(Please only determine complaint level in json format and follow the answer example.)""".format(
                        user_input
                    ),
                }
            ]
        )

        try:
            response = await self.GPT41_mini_response_functions(
                messages, complaint_functions, {"name": "complain_detect"}
            )
            # response = await self.GPT4o_mini_response_functions(messages,complaint_functions,{"name": "complain_detect"})
            response = json.loads(response.function_call.arguments)
        except Exception as e:
            print(e)
            response = self.handle_gpt_error_response()
            response = {"Complaint Level": None}
        return response

    # @async_timer.timeit
    async def userInfo_GPT(self, user_inputs):
        task_user_info = asyncio.create_task(self.userInfo_GPT_part1(user_inputs))
        task_complaint = asyncio.create_task(self.complaint_GPT(user_inputs))

        result = await asyncio.gather(task_user_info, task_complaint)
        userInfo = self.empty_userInfo.copy()
        userInfo.update(result[0])
        # userInfo.update(result[1])

        return userInfo

    def get_content(self, response):
        try:
            content = response
        except Exception as e:
            print({"userInfo_dicrimiator.py get content to default": e})
            content = self.handle_gpt_error_response()
        return content

    def handle_gpt_error_response(self):
        response = self.empty_userInfo
        return response


class FollowUpClassifierFunctionOnly(BaseService):
    """固定使用 function calling 的追問判斷服務。"""

    FOLLOW_UP_BOOL_V1 = {
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

    [4]
    Prev: 我們已將訂單 12345678901 出貨。
    User: 可以改收件地址嗎？
    → {"is_follow_up": true, "confidence": 0.75, "anchor": "shipping details of the order", "needs_disambiguation": false, "reason_short": "Follows up on shipping of the mentioned order."}

    [5]
    Prev: 以上是處理方式。
    User: 謝謝
    → {"is_follow_up": false, "confidence": 0.9, "anchor": null, "needs_disambiguation": false, "reason_short": "Closing utterance, not a follow-up question."}
    """.strip()

    USER_TEMPLATE = """
    Previous assistant reply:
    {prev_reply}

    Latest user message:
    {new_query}
    """.strip()

    def __init__(self, config):
        super().__init__(config)

    def _build_messages(self, prev_reply: str, new_query: str) -> List[Dict[str, str]]:
        sys_content = self.SYSTEM_PROMPT + ("\n\n" + self.FEW_SHOT)
        return [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": self.USER_TEMPLATE.format(prev_reply=prev_reply, new_query=new_query)},
        ]

    async def is_follow_up(
        self,
        prev_question: str,
        prev_answer: str,
        prev_answer_refs: str,
        new_question: str,
    ) -> Dict[str, Any]:
        """
        直接呼叫 function-calling，回傳模型 arguments（不做額外檢查/門檻）。
        回傳格式：
          {
            "is_follow_up": bool,
            "confidence": float,
            "anchor": str | None,
            "needs_disambiguation": bool,
            "reason_short": str
          }
        """
        # 組合前次上下文（保持原樣）
        parts = [
            "[Previous Question]\n" + prev_question,
            "[Previous Answer]\n" + prev_answer,
        ]
        if prev_answer_refs:
            parts.append("[Answer References]\n" + prev_answer_refs)
        prev_reply = "\n\n".join(parts)

        # 空新問題 → 直接判定非追問
        if new_question == "":
            return {
                "is_follow_up": False,
                "confidence": 0.0,
                "anchor": None,
                "needs_disambiguation": False,
                "reason_short": "Empty latest user message.",
            }

        messages = self._build_messages(prev_reply, new_question)

        msg = await self.GPT41_mini_response_functions(
            messages=messages,
            functions=[self.FOLLOW_UP_BOOL_V1],
            function_call={"name": "follow_up_bool"},
        )

        try:
            return json.loads(msg.function_call.arguments)  # type: ignore[attr-defined]
        except Exception as e:
            # 模型偶發格式錯誤時給保守輸出
            return {
                "is_follow_up": False,
                "confidence": 0.0,
                "anchor": None,
                "needs_disambiguation": False,
                "reason_short": f"Failed to parse function args: {e}",
            }


