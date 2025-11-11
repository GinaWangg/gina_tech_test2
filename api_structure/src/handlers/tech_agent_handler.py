"""Tech agent handler for processing technical support requests.

This module contains the main business logic for handling tech support queries.
Following AOCC FastAPI standards with proper layering and error handling.
"""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional

from api_structure.core.logger import logger
from api_structure.core.timer import timed
from api_structure.src.models.tech_agent_models import TechAgentInput

# Constants
TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentHandler:
    """Handler for tech agent processing logic.

    This handler processes technical support requests following a
    multi-step pipeline:
    1. Initialize chat and retrieve history
    2. Process user information and determine scope
    3. Search knowledge base
    4. Generate appropriate response
    5. Log results

    Attributes:
        container: Dependency container with all required clients
        user_input: Input data from the API request
    """

    def __init__(self, container: Any, user_input: TechAgentInput):
        """Initialize the tech agent handler.

        Args:
            container: Dependency container with clients and config
            user_input: Validated input from API request
        """
        self.container = container
        self.user_input = user_input
        self.start_time = time.perf_counter()

        # Initialize processing state
        self._init_state()

    def _init_state(self) -> None:
        """Initialize processing state variables."""
        self.his_inputs: List[str] = []
        self.chat_count: int = 0
        self.user_info: Optional[Dict] = None
        self.last_bot_scope: str = ""
        self.last_extract_output: Dict = {}
        self.last_hint: Optional[Dict] = None
        self.lang: str = "zh-tw"

        self.user_info_dict: Dict = {}
        self.bot_scope_chat: str = ""
        self.search_info: str = ""

        self.faq_result: Dict = {}
        self.faq_result_wo_pl: Dict = {}
        self.top1_kb: Optional[str] = None
        self.top1_kb_sim: float = 0.0
        self.top4_kb_list: List[str] = []

        self.is_follow_up: bool = False
        self.response_data: Dict = {}
        self.final_result: Dict = {}
        self.renderId: str = str(uuid.uuid4())

    @timed(task_name="tech_agent_process")
    async def run(self, log_record: bool = True) -> Dict:
        """Main processing pipeline for tech agent requests.

        Args:
            log_record: Whether to log the results to database

        Returns:
            Dict containing the response data
        """
        logger.info(
            f"[Agent 啟動] Session: {self.user_input.session_id}, "
            f"Input: {self.user_input.user_input}"
        )

        # Pipeline steps
        await self._initialize_chat()
        await self._process_history()
        await self._get_user_and_scope_info()
        await self._search_knowledge_base()
        self._process_kb_results()
        await self._generate_response()

        if log_record:
            await self._log_and_save_results()

        return self.final_result

    async def _initialize_chat(self) -> None:
        """Initialize chat session and retrieve history.

        This method:
        - Retrieves chat history
        - Gets language settings
        - Sets up default values if needed
        """
        settings = self.container.cosmos_settings

        # Parallel execution of I/O operations
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

        logger.info(f"[歷史對話] 取得 {self.chat_count} 筆對話記錄")

        # Set defaults if needed
        if not self.user_input.session_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.session_id = f"agent-{tail}"
        if not self.user_input.cus_id:
            self.user_input.cus_id = "test"
        if not self.user_input.chat_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.chat_id = f"agent-{tail}"

        # Set default user info if not exists
        if not self.user_info:
            self.user_info = {
                "our_brand": "ASUS",
                "location": None,
                "main_product_category": self.user_input.product_line,
                "sub_product_category": None,
                "first_time": True,
            }

    async def _process_history(self) -> None:
        """Process chat history for context.

        This method handles sentence grouping and follow-up detection
        for multi-turn conversations.
        """
        if len(self.his_inputs) <= 1:
            logger.info("首次對話，無需處理歷史")
            return

        # Process sentence grouping
        # TODO: Enable when environment ready
        # results_related = (
        #     await self.container.sentence_group_classification
        #     .sentence_group_classification(self.his_inputs)
        # )
        sgc = self.container.sentence_group_classification
        results_related = await sgc.sentence_group_classification(
            self.his_inputs
        )

        groups = (results_related or {}).get("groups", [])
        if groups:
            statements = groups[-1].get("statements") or []
            latest_group_statements = [s for s in statements if isinstance(s, str)]
            if latest_group_statements:
                self.his_inputs = latest_group_statements.copy()

        logger.info(f"處理後歷史: {self.his_inputs}")

    async def _get_user_and_scope_info(self) -> None:
        """Extract user information and determine bot scope.

        This method:
        - Extracts user info from input
        - Determines search information
        - Identifies product line scope
        """
        # Mock user info extraction - TODO: Enable when environment ready
        self.user_info_dict = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": self.user_input.product_line or "notebook",
            "sub_product_category": None,
        }

        # Set search info to user input
        self.search_info = (
            self.his_inputs[-1] if self.his_inputs else self.user_input.user_input
        )

        # Determine bot scope
        self.bot_scope_chat = self.user_input.product_line
        if not self.bot_scope_chat and self.user_info_dict.get("main_product_category"):
            self.bot_scope_chat = self.user_info_dict["main_product_category"]

        logger.info(f"[Bot Scope] {self.bot_scope_chat}")
        logger.info(f"[Search Info] {self.search_info}")

    async def _search_knowledge_base(self) -> None:
        """Search knowledge base with product line context."""
        response = await self.container.sd.service_discreminator_with_productline(
            user_question_english=self.search_info,
            site=self.user_input.websitecode,
            specific_kb_mappings=self.container.specific_kb_mappings,
            productLine=self.bot_scope_chat,
        )

        self.faq_result = response[0]
        self.faq_result_wo_pl = response[1]

        logger.info(f"[KB搜尋結果] Top1 KB: {self.faq_result.get('faq', [None])[0]}")

    def _process_kb_results(self) -> None:
        """Process and filter KB search results."""
        faq_list = self.faq_result.get("faq", [])
        sim_list = self.faq_result.get("cosineSimilarity", [])

        self.top4_kb_list = [
            faq for faq, sim in zip(faq_list, sim_list) if sim >= KB_THRESHOLD
        ][:3]

        self.top1_kb = faq_list[0] if faq_list else None
        self.top1_kb_sim = sim_list[0] if sim_list else 0.0

        logger.info(
            f"[KB處理] Top1 相似度: {self.top1_kb_sim}, "
            f"符合門檻KB數: {len(self.top4_kb_list)}"
        )

    async def _generate_response(self) -> None:
        """Generate appropriate response based on processing results.

        Routes to different handlers based on:
        - Product line availability
        - KB similarity score
        - Follow-up context
        """
        if not self.bot_scope_chat:
            await self._handle_no_product_line()
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            await self._handle_high_similarity()
        else:
            await self._handle_low_similarity()

    async def _handle_no_product_line(self) -> None:
        """Handle case when product line is not determined.

        Generates product line clarification request.
        """
        logger.info("[無產品線] 需要詢問產品線")

        # Mock avatar response - TODO: Enable when environment ready
        avatar_message = "請問您的問題是關於哪個產品線呢？"

        # Mock product line options - TODO: restore from real data
        relative_questions = [
            {
                "title": "notebook",
                "title_name": "筆記型電腦",
                "icon": "https://example.com/notebook.png",
                "question": "筆記型電腦",
            },
            {
                "title": "desktop",
                "title_name": "桌上型電腦",
                "icon": "https://example.com/desktop.png",
                "question": "桌上型電腦",
            },
        ]

        # TODO: Enable when environment ready
        # await self.container.cosmos_settings.insert_hint_data(...)

        self.response_data = {
            "status": 200,
            "type": "reask",
            "message": "ReAsk: Need product line clarification",
            "output": {
                "answer": "請問您的問題是關於哪個產品線呢？",
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

    async def _handle_high_similarity(self) -> None:
        """Handle case when KB similarity is high.

        Generates response with KB content and related hints.
        """
        logger.info(f"[高相似度] 相似度={self.top1_kb_sim}, KB={self.top1_kb}")

        # Get KB content
        kb_key = f"{self.top1_kb}_{self.lang}"
        kb_data = self.container.KB_mappings.get(
            kb_key, {"title": "", "content": "", "summary": ""}
        )

        # Mock avatar response - TODO: Enable when environment ready
        avatar_message = "根據您的問題，我找到了相關的解決方案。"

        # Generate response
        self.response_data = {
            "status": 200,
            "type": "answer",
            "message": "RAG Response",
            "output": {
                "answer": kb_data.get("content", ""),
                "ask_flag": False,
                "hint_candidates": [],
                "kb": {
                    "kb_no": str(self.top1_kb or ""),
                    "title": kb_data.get("title", ""),
                    "similarity": float(self.top1_kb_sim),
                    "source": "knowledge_base",
                    "exec_time": 0.0,
                },
            },
        }

        # Build link based on system code
        if self.user_input.system_code.lower() == "rog":
            link = (
                f"https://rog.asus.com/{self.user_input.websitecode}/"
                f"support/FAQ/{self.top1_kb}"
            )
        else:
            link = (
                f"https://www.asus.com/{self.user_input.websitecode}/"
                f"support/FAQ/{self.top1_kb}"
            )

        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarTechnicalSupport",
                    "message": avatar_message,
                    "remark": [],
                    "option": [
                        {
                            "type": "faqcards",
                            "cards": [
                                {
                                    "link": link,
                                    "title": kb_data.get("title", ""),
                                    "content": kb_data.get("content", ""),
                                }
                            ],
                        }
                    ],
                }
            ],
        }

    async def _handle_low_similarity(self) -> None:
        """Handle case when KB similarity is low.

        Suggests handoff to human agent with clarifying questions.
        """
        logger.info(f"[低相似度] 相似度={self.top1_kb_sim}，建議轉人工")

        # Mock avatar response - TODO: Enable when environment ready
        avatar_message = "我需要更多資訊來幫助您。"

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
                    "similarity": float(self.top1_kb_sim),
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
                    "message": avatar_message,
                    "remark": [],
                    "option": [],
                },
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarAsk",
                    "message": "你可以告訴我像是產品全名、型號，或你想問的活動名稱",
                    "remark": [],
                    "option": [],
                },
            ],
        }

    async def _log_and_save_results(self) -> None:
        """Log execution results and save to database.

        TODO: Enable when environment ready
        """
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)

        logger.info(f"[執行時間] tech_agent 處理耗時 {exec_time} 秒")

        # Prepare cosmos data for future logging
        # cosmos_data = {
        #     "id": (
        #         f"{self.user_input.cus_id}-{self.user_input.session_id}-"
        #         f"{self.user_input.chat_id}"
        #     ),
        #     "cus_id": self.user_input.cus_id,
        #     "session_id": self.user_input.session_id,
        #     "chat_id": self.user_input.chat_id,
        #     "createDate": datetime.utcnow().isoformat() + "Z",
        #     "user_input": self.user_input.user_input,
        #     "websitecode": self.user_input.websitecode,
        #     "product_line": self.user_input.product_line,
        #     "system_code": self.user_input.system_code,
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

        # TODO: Enable when environment ready
        # await self.container.cosmos_settings.insert_data(cosmos_data)

        logger.info("[Cosmos DB] 記錄已準備 (未實際寫入)")
