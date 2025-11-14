"""Tech agent handler - business logic for technical support processing.

This handler implements the core logic for processing technical support
requests, including history processing, user info extraction, KB search,
and response generation.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from api_structure.core.logger import logger
from api_structure.core.timer import timed
from api_structure.src.clients.tech_agent_container import (
    TechAgentContainer,
)
from api_structure.src.models.tech_agent_models import (
    KBInfo,
    TechAgentInput,
    TechAgentOutput,
    TechAgentResponse,
)

# Thresholds
TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentHandler:
    """Handler for tech agent processing logic."""

    def __init__(
        self, container: TechAgentContainer, user_input: TechAgentInput
    ):
        """Initialize tech agent handler.

        Args:
            container: Dependency container with services.
            user_input: User input data.
        """
        self.container = container
        self.user_input = user_input
        self.start_time = time.perf_counter()

        # Initialize processing state
        self.his_inputs: List[str] = []
        self.user_info: Optional[Dict] = None
        self.last_bot_scope: Optional[str] = None
        self.last_extract_output: Dict = {}
        self.last_hint: Optional[Dict] = None
        self.is_follow_up: bool = False
        self.lang: str = "zh-tw"
        self.chat_count: int = 0
        self.user_info_dict: Dict = {}
        self.bot_scope_chat: Optional[str] = None
        self.search_info: str = ""
        self.faq_result: Dict = {}
        self.faq_result_wo_pl: Dict = {}
        self.top1_kb: Optional[str] = None
        self.top1_kb_sim: float = 0.0
        self.top4_kb_list: List[str] = []
        self.faqs_wo_pl: List[Dict] = []
        self.response_data: Dict = {}

        # Response rendering state
        self.type: str = ""
        self.avatar_response: Any = None
        self.prev_q: str = ""
        self.prev_a: str = ""
        self.kb_no: str = ""
        self.content: str = ""
        self.result: Any = []
        self.final_result: Dict = {}
        self.renderId: str = ""
        self.fu_task: Optional[asyncio.Task] = None
        self.avatar_process: Optional[asyncio.Task] = None

        self.default_user_info = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": user_input.product_line,
            "sub_product_category": None,
            "first_time": True,
        }

    @timed(task_name="tech_agent_process")
    async def run(self) -> Dict:
        """Main processing flow for tech agent.

        Returns:
            Response dictionary with status and result.
        """
        log_json = json.dumps(
            self.user_input.model_dump(), ensure_ascii=False, indent=2
        )
        logger.info(f"\n[Agent 啟動] 輸入內容: {log_json}")

        await self._initialize_chat()
        await self._process_history()
        await self._get_user_and_scope_info()
        await self._search_knowledge_base()
        self._process_kb_results()

        follow_up = await self.fu_task if self.fu_task else {}
        self.is_follow_up = bool(follow_up.get("is_follow_up", False))
        logger.info(f"是否延續問題追問 : {self.is_follow_up}")

        await self._generate_response()
        asyncio.create_task(self._log_and_save_results())

        return self.final_result

    @timed(task_name="initialize_chat")
    async def _initialize_chat(self) -> None:
        """Initialize chat and retrieve history."""
        settings = self.container.cosmos_settings

        # Parallel I/O operations
        messages_task = settings.create_GPT_messages(
            self.user_input.session_id, self.user_input.user_input
        )
        hint_task = settings.get_latest_hint(self.user_input.session_id)
        lang_task = settings.get_language_by_websitecode_dev(
            self.user_input.websitecode
        )

        results, self.last_hint, self.lang = await asyncio.gather(
            messages_task, hint_task, lang_task
        )

        (
            self.his_inputs,
            self.chat_count,
            self.user_info,
            self.last_bot_scope,
            self.last_extract_output,
        ) = results

        log_json = json.dumps(results, ensure_ascii=False, indent=2)
        logger.info(f"\n[歷史對話]\n{log_json}")

        # Set defaults
        if not self.user_input.session_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.session_id = f"agent-{tail}"
        if not self.user_input.cus_id:
            self.user_input.cus_id = "test"
        if not self.user_input.chat_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.chat_id = f"agent-{tail}"

        self.renderId = str(uuid.uuid4())
        logger.info(f"last_hint: {self.last_hint}")

        if not self.user_info:
            self.user_info = self.default_user_info
        if (
            self.user_input.product_line
            and self.last_bot_scope != self.user_input.product_line
        ):
            self.user_info["main_product_category"] = (
                self.user_input.product_line
            )
            self.user_info["first_time"] = True

        # Create avatar task (stub returns mock response)
        async def mock_avatar_response() -> Dict:
            """Mock avatar response."""
            # TODO: Enable when environment ready
            await asyncio.sleep(0.1)
            return {
                "response": type(
                    "obj",
                    (object,),
                    {
                        "answer": (
                            "您好！我是華碩技術支援小幫手。"
                            "我會盡力協助您解決問題。"
                        )
                    },
                )()
            }

        self.avatar_process = asyncio.create_task(mock_avatar_response())

    @timed(task_name="process_history")
    async def _process_history(self) -> None:
        """Process chat history and check for follow-up."""
        if len(self.his_inputs) <= 1:
            logger.info(f"his_inputs : {self.his_inputs}")

            async def dummy_follow_up() -> Dict:
                """Dummy follow-up check."""
                return {"is_follow_up": False}

            self.fu_task = asyncio.create_task(dummy_follow_up())
            return

        # Prepare previous data
        self.prev_q = str(self.his_inputs[-2])
        self.prev_a = str(self.last_extract_output.get("answer", ""))
        self.kb_no = str(
            self.last_extract_output.get("kb", {}).get("kb_no", "")
        )
        self.content = str(
            self.container.KB_mappings.get(
                f"{self.kb_no}_{self.lang}", {}
            ).get("content")
        )

        # Sentence group classification
        group_task = self.container.sentence_group_classification
        results_related = (
            await group_task.sentence_group_classification(
                self.his_inputs
            )
        )

        # Process grouping results
        groups = (results_related or {}).get("groups", [])
        if groups:
            statements = groups[-1].get("statements") or []
            latest_group_statements = [
                s for s in statements if isinstance(s, str)
            ]
            if latest_group_statements:
                self.his_inputs = latest_group_statements.copy()

        logger.info(f"last group statements => {self.his_inputs[-1]}")
        logger.info(f"his_inputs : {self.his_inputs}")

        # Create follow-up task (don't wait)
        self.fu_task = asyncio.create_task(
            self.container.followup_discrimiator.reply_with_gpt(
                prev_question=self.prev_q,
                prev_answer=self.prev_a,
                prev_answer_refs=self.content,
                new_question=self.his_inputs[-1],
            )
        )

    @timed(task_name="get_user_and_scope_info")
    async def _get_user_and_scope_info(self) -> None:
        """Get user info, search info, and determine bot scope."""
        # Parallel operations
        ui_task = self.container.userinfo_discrimiator.reply_with_gpt(
            self.his_inputs
        )
        si_task = self._get_search_info_async()

        # Tech support related check
        tech_support_task = None
        if (
            self.last_hint
            and self.last_hint.get("hintType") == "productline-reask"
        ):
            prompt_content = f'''Please determine whether the sentence "{self.his_inputs[-1]}" 
            mentions any technical support-related issues, and reply with "true" or "false" only. 
            Here is an example you can refer to. 
            1. user's question:  it can only be turned on when plugged in. your response: "true" 
            2. user's question:  wearable. your response: "false" 
            3. user's question:  notebook. your response: "false"'''
            prompt = [{"role": "user", "content": prompt_content}]
            tech_support_task = (
                self.container.base_service.GPT41_mini_response(prompt)
            )

        # Wait for all results
        results = await asyncio.gather(
            ui_task,
            si_task,
            (
                tech_support_task
                if tech_support_task
                else asyncio.sleep(0)
            ),
            return_exceptions=True,
        )

        # Process user info
        result_user_info = results[0]
        self.user_info_dict = (
            result_user_info[0]
            if not isinstance(result_user_info, Exception)
            else {}
        )

        search_info_result = results[1]
        tech_support_related = (
            results[2] if tech_support_task else "true"
        )

        log_json = json.dumps(
            self.user_info_dict, ensure_ascii=False, indent=2
        )
        logger.info(f"\n[使用者資訊]\n{log_json}")

        # Determine search_info
        if tech_support_related == "false" and self.last_hint:
            self.search_info = self.last_hint.get("searchInfo", "")
        else:
            self.search_info = (
                search_info_result
                if not isinstance(search_info_result, Exception)
                else self.his_inputs[-1]
            )

        # Get bot_scope
        self.bot_scope_chat = (
            self.user_input.product_line
            or await self._get_bot_scope_chat()
        )

        logger.info(f"\n[Bot Scope 判斷] {self.bot_scope_chat}")

    async def _get_search_info_async(self) -> str:
        """Get search info asynchronously.

        Returns:
            Search info string.
        """
        # Mock implementation
        # TODO: Enable when environment ready
        return self.his_inputs[-1]

    async def _get_bot_scope_chat(self) -> Optional[str]:
        """Get bot scope from user info.

        Returns:
            Bot scope string or None.
        """
        # Check if user clicked hint
        if self.last_hint:
            if self.last_hint.get("hintType") == "productline-reask":
                for hint in self.last_hint["intentHints"]:
                    if self.user_input.user_input == hint["question"]:
                        return hint["title"]

        # Update user info
        user_info_updated = self._update_user_info(
            self.user_info, self.user_info_dict
        )
        site = self.user_input.websitecode

        bot_scope_chat = None
        if user_info_updated.get("main_product_category"):
            bot_scope_chat = await self.container.redis_config.get_productline(
                user_info_updated.get("main_product_category", ""), site
            )
        elif user_info_updated.get("sub_product_category"):
            bot_scope_chat = await self.container.redis_config.get_productline(
                user_info_updated.get("sub_product_category", ""), site
            )
        else:
            bot_scope_chat = self.user_input.product_line

        if bot_scope_chat not in self.container.PL_mappings.get(
            site, []
        ):
            bot_scope_chat = self.last_bot_scope

        return bot_scope_chat

    def _update_user_info(
        self, previous: Optional[Dict], current: Dict
    ) -> Dict:
        """Update user info with current info.

        Args:
            previous: Previous user info.
            current: Current user info.

        Returns:
            Updated user info.
        """
        if not previous:
            previous = {}

        # Clean null values
        for key, value in current.items():
            if value == "null":
                current[key] = None

        for key, value in previous.items():
            if value == "null":
                previous[key] = None

        # Save first bot scope
        first_bot = None
        if previous.get("first_time"):
            first_bot = previous.get("main_product_category")
            del previous["first_time"]

        # Update with current values
        for key, value in current.items():
            if value:
                previous[key] = value

        # Restore first bot scope if exists
        if first_bot:
            previous["main_product_category"] = first_bot

        return previous

    @timed(task_name="search_knowledge_base")
    async def _search_knowledge_base(self) -> None:
        """Search knowledge base with product line."""
        response = await self.container.sd.service_discreminator_with_productline(
            user_question_english=self.search_info,
            site=self.user_input.websitecode,
            specific_kb_mappings=self.container.specific_kb_mappings,
            productLine=self.bot_scope_chat,
        )
        log_json = json.dumps(response, ensure_ascii=False, indent=2)
        logger.info(
            "[ServiceDiscriminator] discrimination_productline_response: %s",
            log_json,
        )
        self.faq_result = response[0]
        self.faq_result_wo_pl = response[1]

    def _process_kb_results(self) -> None:
        """Process and filter results from KB search."""
        faq_list = self.faq_result.get("faq", [])
        sim_list = self.faq_result.get("cosineSimilarity", [])

        self.top4_kb_list = [
            faq
            for faq, sim in zip(faq_list, sim_list)
            if sim >= KB_THRESHOLD
        ][:3]
        self.top1_kb = faq_list[0] if faq_list else None
        self.top1_kb_sim = sim_list[0] if sim_list else 0.0

        self.faqs_wo_pl = [
            {
                "kb_no": faq,
                "cosineSimilarity": sim,
                "productLine": pl,
            }
            for faq, sim, pl in zip(
                self.faq_result_wo_pl.get("faq", []),
                self.faq_result_wo_pl.get("cosineSimilarity", []),
                self.faq_result_wo_pl.get("productLine", []),
            )
        ]

    @timed(task_name="generate_response")
    async def _generate_response(self) -> None:
        """Generate final response based on processed data."""
        if not self.bot_scope_chat:
            self.type = "avatarAskProductLine"
            await self._handle_no_product_line()
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            self.type = "avatarTechnicalSupport"
            await self._handle_high_similarity()
        else:
            self.type = "avatarText"
            await self._handle_low_similarity()

    @timed(task_name="handle_no_product_line")
    async def _handle_no_product_line(self) -> None:
        """Handle case when no product line is determined."""
        logger.info("\n[無產品線] 進行產品線追問")

        # Get avatar response
        self.avatar_response = await self.avatar_process

        # Mock product line reask
        # TODO: Enable when environment ready
        relative_questions = [
            {
                "title_name": "筆記型電腦",
                "title": "Laptops",
                "icon": "laptop",
                "question": "筆記型電腦相關問題",
            },
            {
                "title_name": "桌上型電腦",
                "title": "Desktop",
                "icon": "desktop",
                "question": "桌上型電腦相關問題",
            },
            {
                "title_name": "手機",
                "title": "Phone",
                "icon": "phone",
                "question": "手機相關問題",
            },
        ]

        await self.container.cosmos_settings.insert_hint_data(
            chatflow_data=self.user_input,
            intent_hints=relative_questions,
            search_info=self.search_info,
            hint_type="productline-reask",
        )

        self.response_data = {
            "status": 200,
            "type": "reask",
            "message": "ReAsk: Need product line clarification",
            "output": {
                "answer": "請問您需要哪個產品線的支援？",
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
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarAskProductLine",
                    "message": self.avatar_response["response"].answer,
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

    @timed(task_name="handle_high_similarity")
    async def _handle_high_similarity(self) -> None:
        """Handle case when KB similarity is high."""
        logger.info(
            f"\n[相似度高於門檻] 相似度={self.top1_kb_sim}，建立 Hint 回應"
        )

        # Mock RAG response with hints
        # TODO: Enable when environment ready
        relative_questions = self._get_relative_questions()
        kb_key = f"{self.top1_kb}_{self.lang}"
        kb_data = self.container.KB_mappings.get(kb_key, {})

        content = {
            "ask_content": kb_data.get(
                "summary", "這是技術支援的回答內容。"
            ),
            "title": kb_data.get("title", "技術支援"),
            "content": kb_data.get("content", "詳細內容"),
            "link": (
                f"https://rog.asus.com/{self.user_input.websitecode}/"
                f"support/FAQ/{self.top1_kb}"
                if self.user_input.system_code.lower() == "rog"
                else f"https://www.asus.com/{self.user_input.websitecode}/"
                f"support/FAQ/{self.top1_kb}"
            ),
        }

        # Get avatar response with content
        avatar_task = asyncio.create_task(
            self._get_avatar_response_with_content(content)
        )
        self.avatar_response = await avatar_task

        self.response_data = {
            "status": 200,
            "type": "answer",
            "message": "RAG Response",
            "output": {
                "answer": content.get("ask_content", ""),
                "ask_flag": False,
                "hint_candidates": relative_questions,
                "kb": {
                    "kb_no": str(self.top1_kb or ""),
                    "title": content.get("title", ""),
                    "similarity": float(self.top1_kb_sim or 0.0),
                    "source": "KB",
                    "exec_time": 0.5,
                },
            },
        }

        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarTechnicalSupport",
                    "message": self.avatar_response["response"].answer,
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

    @timed(task_name="handle_low_similarity")
    async def _handle_low_similarity(self) -> None:
        """Handle case when KB similarity is low."""
        logger.info(
            f"\n[相似度低於門檻] 相似度={self.top1_kb_sim}，轉人工"
        )

        self.avatar_response = await self.avatar_process

        kb_key = f"{self.top1_kb}_{self.lang}"
        kb_data = self.container.KB_mappings.get(kb_key, {})

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
                    "title": kb_data.get("title", ""),
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
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarText",
                    "message": self.avatar_response["response"].answer,
                    "remark": [],
                    "option": [],
                },
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarAsk",
                    "message": (
                        "你可以告訴我像是產品全名、型號，或你想問的活動名稱～"
                        "比如「ROG Flow X16」或「我想查產品保固到期日」。"
                        "給我多一點線索，我就能更快幫你找到對的資料，"
                        "也不會漏掉重點！"
                    ),
                    "remark": [],
                    "option": [
                        {
                            "name": "我想知道 ROG FLOW X16 的規格",
                            "value": "我想知道 ROG FLOW X16 的規格",
                            "answer": [
                                {
                                    "type": "inquireMode",
                                    "value": "intent",
                                },
                                {
                                    "type": "inquireKey",
                                    "value": "specification-consultation",
                                },
                                {
                                    "type": "mainProduct",
                                    "value": 25323,
                                },
                            ],
                        },
                        {
                            "name": "請幫我推薦16吋筆電",
                            "value": "請幫我推薦16吋筆電",
                            "answer": [
                                {
                                    "type": "inquireMode",
                                    "value": "intent",
                                },
                                {
                                    "type": "inquireKey",
                                    "value": (
                                        "purchasing-recommendation-of-"
                                        "asus-products"
                                    ),
                                },
                            ],
                        },
                        {
                            "name": "請幫我介紹 ROG Phone 8 的特色",
                            "value": "請幫我介紹 ROG Phone 8 的特色",
                            "answer": [
                                {
                                    "type": "inquireMode",
                                    "value": "intent",
                                },
                                {
                                    "type": "inquireKey",
                                    "value": "specification-consultation",
                                },
                                {
                                    "type": "mainProduct",
                                    "value": 25323,
                                },
                            ],
                        },
                    ],
                },
            ],
        }

    def _get_relative_questions(self) -> List[Dict]:
        """Get relative questions from RAG mappings.

        Returns:
            List of relative question dictionaries.
        """
        relative_questions = []

        if not self.top4_kb_list:
            return relative_questions

        for i, kb in enumerate(self.top4_kb_list):
            # Determine index suffix
            index_suffix = "1"

            # Get RAG key
            rag_key = f"{kb}_{self.user_input.websitecode}_{index_suffix}"
            if rag_key in self.container.rag_mappings:
                hint = self.container.rag_mappings.get(rag_key, {}).copy()

                # Set correct link based on system code
                if self.user_input.system_code.lower() == "rog":
                    hint["link"] = hint.get("ROG_link", "")
                else:
                    hint["link"] = hint.get("ASUS_link", "")

                if "ASUS_link" in hint:
                    del hint["ASUS_link"]
                if "ROG_link" in hint:
                    del hint["ROG_link"]

                relative_questions.append(hint)

        return relative_questions

    async def _get_avatar_response_with_content(
        self, content: Dict
    ) -> Dict:
        """Get avatar response with KB content.

        Args:
            content: KB content dictionary.

        Returns:
            Avatar response dictionary.
        """
        # TODO: Enable when environment ready
        # Mock avatar response with content
        await asyncio.sleep(0.1)
        opening_remarks = "您好！我是華碩技術支援小幫手。"
        answer_text = (
            f"{opening_remarks}\n\n{content.get('ask_content', '')}"
        )
        return {
            "response": type("obj", (object,), {"answer": answer_text})()
        }

    async def _log_and_save_results(self) -> None:
        """Log and save final results to Cosmos DB."""
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)
        logger.info(
            f"\n[執行時間] tech_agent_api 共耗時 {exec_time} 秒\n"
        )

        cosmos_data = {
            "id": (
                f"{self.user_input.cus_id}-{self.user_input.session_id}-"
                f"{self.user_input.chat_id}"
            ),
            "cus_id": self.user_input.cus_id,
            "session_id": self.user_input.session_id,
            "chat_id": self.user_input.chat_id,
            "createDate": datetime.utcnow().isoformat() + "Z",
            "user_input": self.user_input.user_input,
            "websitecode": self.user_input.websitecode,
            "product_line": self.user_input.product_line,
            "system_code": self.user_input.system_code,
            "user_info": self.user_info_dict,
            "process_info": {
                "bot_scope": self.bot_scope_chat,
                "search_info": self.search_info,
                "is_follow_up": self.is_follow_up,
                "faq_pl": self.faq_result,
                "faq_wo_pl": self.faq_result_wo_pl,
                "language": self.lang,
                "last_info": {
                    "prev_q": self.prev_q,
                    "prev_a": self.prev_a,
                    "kb_no": self.kb_no,
                },
            },
            "final_result": self.final_result,
            "extract": self.response_data,
            "total_time": exec_time,
        }

        await self.container.cosmos_settings.insert_data(cosmos_data)
        log_json = json.dumps(cosmos_data, ensure_ascii=False, indent=2)
        logger.info(f"\n[Cosmos DB] 寫入資料: {log_json}\n")
