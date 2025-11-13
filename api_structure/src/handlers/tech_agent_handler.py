"""Tech agent handler - Business logic layer."""

import json
import time
import uuid
from typing import Any, Dict, List, Tuple

from api_structure.core.logger import get_logger
from api_structure.core.timer import timed
from api_structure.src.models.tech_agent_models import TechAgentInput

logger = get_logger(__name__)

# Constants from original implementation
TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentHandler:
    """Handler for tech agent business logic."""

    def __init__(self):
        """Initialize the handler."""
        self.start_time = time.perf_counter()
        self.render_id = str(uuid.uuid4())
        self.lang = "tw"
        self.bot_scope_chat = None
        self.search_info = None
        self.top1_kb = None
        self.top1_kb_sim = 0.0
        self.top4_kb_list: List[str] = []
        self.faqs_wo_pl: List[Dict[str, Any]] = []
        self.his_inputs: List[str] = []
        self.user_info_dict: Dict[str, Any] = {}
        self.user_info: Dict[str, Any] = {}
        self.last_hint: Dict[str, Any] = {}
        self.last_bot_scope: str = ""
        self.is_follow_up = False
        self.response_data: Dict[str, Any] = {}
        self.final_result: Dict[str, Any] = {}
        # Mock PL_mappings for bot_scope validation
        self.pl_mappings: Dict[str, List[str]] = {
            "tw": ["notebook", "desktop", "phone", "monitor"],
            "us": ["notebook", "desktop", "phone", "monitor"],
        }

    def _log_execution_time(self) -> float:
        """Calculate and log execution time."""
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)
        logger.info(f"[執行時間] tech_agent_handler 共耗時 {exec_time} 秒")
        return exec_time

    async def _initialize_chat(
        self, user_input: TechAgentInput
    ) -> Tuple[List[str], str]:
        """Initialize chat and retrieve history.

        Args:
            user_input: User input data.

        Returns:
            Tuple of (his_inputs, lang).
        """
        # TODO: Enable when environment ready
        # messages_task = cosmos_settings.create_GPT_messages(
        #     user_input.session_id, user_input.user_input
        # )
        # hint_task = cosmos_settings.get_latest_hint(user_input.session_id)
        # lang_task = cosmos_settings.get_language_by_websitecode_dev(
        #     user_input.websitecode
        # )
        # results, self.last_hint, lang = await asyncio.gather(
        #     messages_task, hint_task, lang_task
        # )
        # (
        #     his_inputs, chat_count, self.user_info,
        #     self.last_bot_scope, last_extract_output
        # ) = results

        # Mock data for testing
        his_inputs = [user_input.user_input]
        lang = "zh-TW" if user_input.websitecode == "tw" else "en"
        self.last_hint = {}  # Mock last hint
        self.user_info = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": user_input.product_line,
            "sub_product_category": None,
            "first_time": True,
        }
        self.last_bot_scope = ""

        log_json = json.dumps(
            {"his_inputs": his_inputs, "lang": lang},
            ensure_ascii=False,
            indent=2,
        )
        logger.info(f"[歷史對話]\n{log_json}")

        return his_inputs, lang

    async def _get_user_info(self, his_inputs: List[str]) -> Dict[str, Any]:
        """Get user information from chat history.

        Args:
            his_inputs: Historical user inputs.

        Returns:
            User info dictionary.
        """
        # TODO: Enable when environment ready
        # ui_task = chat_flow.get_userInfo(his_inputs=his_inputs)
        # result_user_info = await ui_task

        # Mock user info
        user_info = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": None,
            "sub_product_category": None,
        }

        logger.info(f"[使用者資訊] {json.dumps(user_info, ensure_ascii=False)}")
        return user_info

    async def _get_search_info(self, his_inputs: List[str]) -> str:
        """Get search info from user inputs.

        Args:
            his_inputs: Historical user inputs.

        Returns:
            Search info string.
        """
        # TODO: Enable when environment ready
        # si_task = chat_flow.get_searchInfo(his_inputs)
        # search_info_result = await si_task

        # Mock search info (use last input)
        search_info = his_inputs[-1] if his_inputs else ""
        logger.info(f"[搜尋資訊] {search_info}")
        return search_info

    def _update_user_info(
        self, previous: Dict[str, Any], current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user info by merging current info with previous.

        Args:
            previous: Previous user info.
            current: Current user info.

        Returns:
            Updated user info dictionary.
        """
        # Handle "null" strings
        for key, values in current.items():
            if values == "null":
                current[key] = None

        for key, values in previous.items():
            if values == "null":
                previous[key] = None

        # Keep first product category if first_time
        first_bot = None
        if previous.get("first_time"):
            first_bot = previous.get("main_product_category")
            del previous["first_time"]

        # Merge current into previous
        for key, values in current.items():
            if values:
                previous[key] = values

        # Restore first product category if it was set
        if first_bot:
            previous["main_product_category"] = first_bot

        return previous

    async def _get_bot_scope(
        self,
        user_input: TechAgentInput,
        user_info: Dict[str, Any],
    ) -> str:
        """Determine bot scope (product line).

        Implements the logic from ChatFlow.get_bot_scope_chat.

        Args:
            user_input: User input data.
            user_info: User information.

        Returns:
            Bot scope string.
        """
        # Check if user clicked product line hint
        if self.last_hint:
            if self.last_hint.get("hintType") == "productline-reask":
                for hint in self.last_hint.get("intentHints", []):
                    if user_input.user_input == hint.get("question"):
                        bot_scope_chat = hint.get("title", "")
                        logger.info(f"[Bot Scope] Matched hint: {bot_scope_chat}")
                        return bot_scope_chat

        # Merge user info
        updated_user_info = self._update_user_info(self.user_info.copy(), user_info)

        site = user_input.websitecode
        bot_scope_chat = ""

        # Determine bot scope from user info
        if updated_user_info.get("main_product_category"):
            # TODO: Enable when environment ready
            # bot_scope_chat = await redis_config.get_productline(
            #     updated_user_info.get("main_product_category"), site
            # )
            # Mock: Use the category directly
            bot_scope_chat = updated_user_info.get("main_product_category", "")
        elif updated_user_info.get("sub_product_category"):
            # TODO: Enable when environment ready
            # bot_scope_chat = await redis_config.get_productline(
            #     updated_user_info.get("sub_product_category"), site
            # )
            # Mock: Use the category directly
            bot_scope_chat = updated_user_info.get("sub_product_category", "")
        else:
            bot_scope_chat = user_input.product_line

        # Validate bot scope against PL_mappings
        if bot_scope_chat and bot_scope_chat not in self.pl_mappings.get(site, []):
            bot_scope_chat = self.last_bot_scope

        logger.info(f"[Bot Scope 判斷] {bot_scope_chat}")
        return bot_scope_chat

    async def _search_knowledge_base(
        self,
        search_info: str,
        websitecode: str,
        product_line: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Search knowledge base with product line.

        Args:
            search_info: Search query.
            websitecode: Website code.
            product_line: Product line.

        Returns:
            Tuple of (faq_result, faq_result_wo_pl).
        """
        # TODO: Enable when environment ready
        # response = await service_discriminator.
        #   service_discreminator_with_productline(
        #     user_question_english=search_info,
        #     site=websitecode,
        #     specific_kb_mappings=specific_kb_mappings,
        #     productLine=product_line,
        # )

        # Mock KB search results
        faq_result = {
            "faq": ["1049123"],
            "cosineSimilarity": [0.75],
            "productLine": [product_line] if product_line else [""],
        }

        faq_result_wo_pl = {
            "faq": ["1049123", "1049124"],
            "cosineSimilarity": [0.75, 0.72],
            "productLine": ["notebook", "notebook"],
        }

        logger.info(
            "[ServiceDiscriminator] %s", json.dumps(faq_result, ensure_ascii=False)
        )
        return faq_result, faq_result_wo_pl

    def _process_kb_results(
        self,
        faq_result: Dict[str, Any],
        faq_result_wo_pl: Dict[str, Any],
    ) -> None:
        """Process and filter results from KB search.

        Args:
            faq_result: FAQ results with product line.
            faq_result_wo_pl: FAQ results without product line.
        """
        faq_list = faq_result.get("faq", [])
        sim_list = faq_result.get("cosineSimilarity", [])

        self.top4_kb_list = [
            faq for faq, sim in zip(faq_list, sim_list) if sim >= KB_THRESHOLD
        ][:3]
        self.top1_kb = faq_list[0] if faq_list else None
        self.top1_kb_sim = sim_list[0] if sim_list else 0.0

        self.faqs_wo_pl = [
            {"kb_no": faq, "cosineSimilarity": sim, "productLine": pl}
            for faq, sim, pl in zip(
                faq_result_wo_pl.get("faq", []),
                faq_result_wo_pl.get("cosineSimilarity", []),
                faq_result_wo_pl.get("productLine", []),
            )
        ]

    async def _handle_no_product_line(
        self,
        user_input: TechAgentInput,
    ) -> Dict[str, Any]:
        """Handle no product line case.

        Args:
            user_input: User input data.

        Returns:
            Response data dictionary.
        """
        logger.info("[無產品線] 進行產品線追問")

        # TODO: Enable when environment ready
        # ask_response, rag_response = await
        #   technical_support_productline_reask(...)
        # relative_questions = rag_response.get("relative_questions", [])

        # Mock relative questions for product line reask
        relative_questions = [
            {
                "title": "notebook",
                "title_name": "筆記型電腦",
                "icon": "laptop",
                "question": "筆記型電腦相關問題",
            },
            {
                "title": "desktop",
                "title_name": "桌上型電腦",
                "icon": "desktop",
                "question": "桌上型電腦相關問題",
            },
        ]

        # Mock avatar response
        avatar_message = "我理解您遇到了技術問題。請問是哪個產品線的問題呢？"

        self.response_data = {
            "status": 200,
            "type": "reask",
            "message": "ReAsk: Need product line clarification",
            "output": {
                "answer": "請選擇產品線",
                "ask_flag": True,
                "hint_candidates": relative_questions,
                "kb": {},
            },
        }

        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarAskProductLine",
                    "message": avatar_message,
                    "remark": [],
                    "option": [
                        {
                            "name": item["title_name"],
                            "value": item["title"],
                            "icon": item["icon"],
                        }
                        for item in relative_questions
                    ],
                }
            ],
        }

        return self.final_result

    async def _handle_high_similarity(
        self,
        user_input: TechAgentInput,
    ) -> Dict[str, Any]:
        """Handle high similarity case.

        Args:
            user_input: User input data.

        Returns:
            Response data dictionary.
        """
        logger.info(f"[相似度高於門檻] 相似度={self.top1_kb_sim}，建立 Hint 回應")

        # TODO: Enable when environment ready
        # rag_response = await technical_support_hint_create(...)
        # content = rag_response.get("rag_content", {})

        # Mock content
        content = {
            "ask_content": "根據您的問題，我找到了相關的技術文件。",
            "title": "筆電登入問題排解",
            "content": "若筆電卡在登入畫面，請嘗試以下步驟...",
            "link": f"https://www.asus.com/{user_input.websitecode}/"
            f"support/FAQ/{self.top1_kb}",
        }

        avatar_message = "我找到了相關的解決方案，希望能幫到您！"

        self.response_data = {
            "status": 200,
            "type": "answer",
            "message": "RAG Response",
            "output": {
                "answer": content.get("ask_content", ""),
                "ask_flag": False,
                "hint_candidates": [],
                "kb": {
                    "kb_no": str(self.top1_kb or ""),
                    "title": content.get("title", ""),
                    "similarity": float(self.top1_kb_sim),
                    "source": "KB",
                    "exec_time": 0.0,
                },
            },
        }

        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarTechnicalSupport",
                    "message": avatar_message,
                    "remark": [],
                    "option": [
                        {
                            "type": "faqcards",
                            "cards": [
                                {
                                    "link": content.get("link", ""),
                                    "title": content.get("title", ""),
                                    "content": content.get("content", ""),
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        return self.final_result

    async def _handle_low_similarity(
        self,
        user_input: TechAgentInput,
    ) -> Dict[str, Any]:
        """Handle low similarity case.

        Args:
            user_input: User input data.

        Returns:
            Response data dictionary.
        """
        logger.info(f"[相似度低於門檻] 相似度={self.top1_kb_sim}，轉人工")

        avatar_message = "抱歉，我需要更多資訊才能協助您。"

        self.response_data = {
            "status": 200,
            "type": "handoff",
            "message": "相似度低，建議轉人工",
            "output": {
                "answer": "",
                "ask_flag": False,
                "hint_candidates": [],
                "kb": {
                    "kb_no": str(self.top1_kb or ""),
                    "title": "",
                    "similarity": float(self.top1_kb_sim or 0.0),
                    "source": "",
                    "exec_time": 0.0,
                },
            },
        }

        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarText",
                    "message": avatar_message,
                    "remark": [],
                    "option": [],
                },
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarAsk",
                    "message": "你可以告訴我像是產品全名、型號，或你想問的活動名稱～"
                    "比如「ROG Flow X16」或「我想查產品保固到期日」。"
                    "給我多一點線索，我就能更快幫你找到對的資料，也不會漏掉重點！",
                    "remark": [],
                    "option": [
                        {
                            "name": "我想知道 ROG FLOW X16 的規格",
                            "value": "我想知道 ROG FLOW X16 的規格",
                            "answer": [
                                {"type": "inquireMode", "value": "intent"},
                                {
                                    "type": "inquireKey",
                                    "value": "specification-consultation",
                                },
                                {"type": "mainProduct", "value": 25323},
                            ],
                        },
                        {
                            "name": "請幫我推薦16吋筆電",
                            "value": "請幫我推薦16吋筆電",
                            "answer": [
                                {"type": "inquireMode", "value": "intent"},
                                {
                                    "type": "inquireKey",
                                    "value": "purchasing-recommendation-of-asus"
                                    "-products",
                                },
                            ],
                        },
                        {
                            "name": "請幫我介紹 ROG Phone 8 的特色",
                            "value": "請幫我介紹 ROG Phone 8 的特色",
                            "answer": [
                                {"type": "inquireMode", "value": "intent"},
                                {
                                    "type": "inquireKey",
                                    "value": "specification-consultation",
                                },
                                {"type": "mainProduct", "value": 25323},
                            ],
                        },
                    ],
                },
            ],
        }

        return self.final_result

    async def _log_to_cosmos(
        self,
        user_input: TechAgentInput,
        exec_time: float,
    ) -> None:
        """Log results to Cosmos DB.

        Args:
            user_input: User input data.
            exec_time: Execution time.
        """
        # TODO: Enable when environment ready
        # cosmos_data = {
        #     "id": f"{user_input.cus_id}-{user_input.session_id}-"
        #           f"{user_input.chat_id}",
        #     "cus_id": user_input.cus_id,
        #     "session_id": user_input.session_id,
        #     "chat_id": user_input.chat_id,
        #     "createDate": datetime.utcnow().isoformat() + "Z",
        #     "user_input": user_input.user_input,
        #     "websitecode": user_input.websitecode,
        #     "product_line": user_input.product_line,
        #     "system_code": user_input.system_code,
        #     "user_info": self.user_info_dict,
        #     "process_info": {
        #         "bot_scope": self.bot_scope_chat,
        #         "search_info": self.search_info,
        #         "is_follow_up": self.is_follow_up,
        #         "language": self.lang,
        #     },
        #     "final_result": self.final_result,
        #     "extract": self.response_data,
        #     "total_time": exec_time,
        # }
        # await cosmos_settings.insert_data(cosmos_data)

        logger.info("[Cosmos DB] Mock log saved")

    @timed(task_name="tech_agent_handler_process")
    async def run(
        self,
        user_input: TechAgentInput,
    ) -> Dict[str, Any]:
        """Main processing flow for tech agent.

        Args:
            user_input: User input data.

        Returns:
            Response data dictionary.
        """
        log_json = json.dumps(user_input.model_dump(), ensure_ascii=False, indent=2)
        logger.info(f"[Agent 啟動] 輸入內容: {log_json}")

        # Initialize chat and get history
        self.his_inputs, self.lang = await self._initialize_chat(user_input)

        # Get user info and bot scope
        self.user_info_dict = await self._get_user_info(self.his_inputs)
        self.search_info = await self._get_search_info(self.his_inputs)
        self.bot_scope_chat = await self._get_bot_scope(user_input, self.user_info_dict)

        # Search knowledge base
        faq_result, faq_result_wo_pl = await self._search_knowledge_base(
            self.search_info,
            user_input.websitecode,
            self.bot_scope_chat,
        )
        self._process_kb_results(faq_result, faq_result_wo_pl)

        # Generate response based on conditions
        if not self.bot_scope_chat:
            result = await self._handle_no_product_line(user_input)
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            result = await self._handle_high_similarity(user_input)
        else:
            result = await self._handle_low_similarity(user_input)

        # Log execution time and save to Cosmos
        exec_time = self._log_execution_time()
        await self._log_to_cosmos(user_input, exec_time)

        return result
