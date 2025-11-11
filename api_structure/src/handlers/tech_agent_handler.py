"""Tech agent handler with business logic.

This handler implements the core processing logic for the tech agent,
using stubbed external dependencies where services are unavailable.
"""

import json
import time
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from api_structure.core.timer import timed
from api_structure.src.models.tech_agent_models import (
    TechAgentInput,
    TechAgentResponse,
    TechAgentFinalResponse,
)

# Use standard Python logging
logger = logging.getLogger(__name__)


# Constants from original implementation
TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentHandler:
    """Handler for tech agent processing logic."""

    def __init__(
        self,
        gpt_client: Any,
        aiohttp_client: Any,
        # cosmos_client: Any = None,  # TODO: Enable when environment ready
    ):
        """Initialize the tech agent handler.

        Args:
            gpt_client: GPT client for AI interactions
            aiohttp_client: HTTP client for external API calls
        """
        self.gpt_client = gpt_client
        self.aiohttp_client = aiohttp_client
        # self.cosmos_client = cosmos_client  # TODO: Enable when ready
        self.start_time = time.perf_counter()

        # Initialize processing state
        self._init_processing_state()

    def _init_processing_state(self) -> None:
        """Initialize processing state variables."""
        self.his_inputs: List[str] = []
        self.user_info: Optional[Dict] = None
        self.last_bot_scope: Optional[str] = None
        self.last_extract_output: Dict = {}
        self.last_hint: Optional[Dict] = None
        self.is_follow_up: bool = False
        self.lang: str = "tw"
        self.chat_count: int = 0
        self.user_info_dict: Dict = {}
        self.bot_scope_chat: Optional[str] = None
        self.search_info: Optional[str] = None
        self.faq_result: Dict = {}
        self.faq_result_wo_pl: Dict = {}
        self.top1_kb: Optional[str] = None
        self.top1_kb_sim: float = 0.0
        self.top4_kb_list: List = []
        self.faqs_wo_pl: List = []
        self.response_data: Dict = {}
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

    @timed(task_name="tech_agent_process")
    async def run(self, user_input: TechAgentInput) -> Dict[str, Any]:
        """Main entry point for tech agent processing.

        Args:
            user_input: User input data

        Returns:
            Final response dictionary
        """
        log_json = json.dumps(user_input.dict(), ensure_ascii=False, indent=2)
        logger.info(f"\n[Agent 啟動] 輸入內容: {log_json}")

        await self._initialize_chat(user_input)
        await self._process_history()

        # Start avatar generation in background
        self.avatar_process = asyncio.create_task(
            self._generate_avatar_response()
        )

        await self._get_user_and_scope_info(user_input)
        await self._search_knowledge_base(user_input)
        self._process_kb_results()

        # Wait for follow-up task if it exists
        follow_up = await self.fu_task if self.fu_task else {}
        self.is_follow_up = bool(follow_up.get("is_follow_up", False))
        logger.info(f"是否延續問題追問: {self.is_follow_up}")

        await self._generate_response(user_input)

        # Log and save results asynchronously
        asyncio.create_task(self._log_and_save_results(user_input))

        return self.final_result

    async def _initialize_chat(self, user_input: TechAgentInput) -> None:
        """Initialize chat session and retrieve history."""
        # TODO: Enable when environment ready
        # messages, last_hint, lang = await asyncio.gather(
        #     cosmos_settings.create_GPT_messages(
        #         user_input.session_id, user_input.user_input
        #     ),
        #     cosmos_settings.get_latest_hint(user_input.session_id),
        #     cosmos_settings.get_language_by_websitecode_dev(
        #         user_input.websitecode
        #     )
        # )

        # Stubbed data
        messages_result = (
            [user_input.user_input],  # his_inputs
            1,  # chat_count
            None,  # user_info
            None,  # last_bot_scope
            {}  # last_extract_output
        )

        self.his_inputs = [user_input.user_input]
        self.chat_count = 1
        self.user_info = None
        self.last_bot_scope = None
        self.last_extract_output = {}
        self.last_hint = None
        self.lang = self._get_language_by_websitecode(user_input.websitecode)

        logger.info(f"[歷史對話] 初始化完成，輸入數量: {len(self.his_inputs)}")

        # Generate UUIDs for tracking
        self.renderId = str(uuid.uuid4())

        # Set default user info
        if not self.user_info:
            self.user_info = {
                "our_brand": "ASUS",
                "location": None,
                "main_product_category": user_input.product_line,
                "sub_product_category": None,
                "first_time": True,
            }

    def _get_language_by_websitecode(self, websitecode: str) -> str:
        """Map website code to language."""
        lang_map = {
            "tw": "tw",
            "cn": "cn",
            "en": "en",
            "jp": "jp",
            "us": "en",
        }
        return lang_map.get(websitecode, "tw")

    async def _process_history(self) -> None:
        """Process chat history for follow-up detection."""
        if len(self.his_inputs) <= 1:
            logger.info(f"his_inputs: {self.his_inputs}")

            async def dummy_follow_up():
                return {"is_follow_up": False}

            self.fu_task = asyncio.create_task(dummy_follow_up())
            return

        # TODO: Enable when environment ready
        # For follow-up detection with sentence grouping
        self.prev_q = str(self.his_inputs[-2] if len(self.his_inputs) > 1
                          else "")
        self.prev_a = str(self.last_extract_output.get("answer", ""))

        # Stubbed follow-up task
        async def dummy_follow_up():
            return {"is_follow_up": False}

        self.fu_task = asyncio.create_task(dummy_follow_up())

    async def _get_user_and_scope_info(
        self,
        user_input: TechAgentInput
    ) -> None:
        """Extract user information and determine bot scope."""
        # TODO: Enable when environment ready
        # ui_result = await chat_flow.get_userInfo(his_inputs=self.his_inputs)
        # si_result = await chat_flow.get_searchInfo(self.his_inputs)

        # Stubbed user info
        self.user_info_dict = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": user_input.product_line or "notebook",
            "sub_product_category": None,
        }

        logger.info(
            f"[使用者資訊] {json.dumps(self.user_info_dict, ensure_ascii=False)}"
        )

        self.search_info = self.his_inputs[-1]
        self.bot_scope_chat = user_input.product_line or None

        logger.info(f"[Bot Scope 判斷] {self.bot_scope_chat}")

    async def _search_knowledge_base(
        self,
        user_input: TechAgentInput
    ) -> None:
        """Search knowledge base for relevant FAQs."""
        # TODO: Enable when environment ready
        # response = await service_discriminator.discriminate_with_productline(
        #     user_question=self.search_info,
        #     site=user_input.websitecode,
        #     productLine=self.bot_scope_chat,
        # )

        # Stubbed KB search results
        self.faq_result = {
            "faq": ["1043959"],
            "cosineSimilarity": [0.75],
            "productLine": ["notebook"]
        }
        self.faq_result_wo_pl = {
            "faq": ["1043959", "1043960"],
            "cosineSimilarity": [0.75, 0.72],
            "productLine": ["notebook", "desktop"]
        }

        logger.info(
            f"[ServiceDiscriminator] "
            f"{json.dumps(self.faq_result, ensure_ascii=False)}"
        )

    def _process_kb_results(self) -> None:
        """Process and filter KB search results."""
        faq_list = self.faq_result.get("faq", [])
        sim_list = self.faq_result.get("cosineSimilarity", [])

        self.top4_kb_list = [
            faq for faq, sim in zip(faq_list, sim_list)
            if sim >= KB_THRESHOLD
        ][:3]

        self.top1_kb = faq_list[0] if faq_list else None
        self.top1_kb_sim = sim_list[0] if sim_list else 0.0

        self.faqs_wo_pl = [
            {"kb_no": faq, "cosineSimilarity": sim, "productLine": pl}
            for faq, sim, pl in zip(
                self.faq_result_wo_pl.get("faq", []),
                self.faq_result_wo_pl.get("cosineSimilarity", []),
                self.faq_result_wo_pl.get("productLine", []),
            )
        ]

    async def _generate_response(self, user_input: TechAgentInput) -> None:
        """Generate final response based on processed data."""
        if not self.bot_scope_chat:
            self.type = "avatarAskProductLine"
            await self._handle_no_product_line(user_input)
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            self.type = "avatarTechnicalSupport"
            await self._handle_high_similarity(user_input)
        else:
            self.type = "avatarText"
            await self._handle_low_similarity(user_input)

    async def _generate_avatar_response(self) -> Dict[str, Any]:
        """Generate avatar response using GPT."""
        # TODO: Use actual GPT client when ready
        # For now, return a stub response
        return {
            'response': '嗨！我是華碩智能助手，很高興為您服務！'
        }

    async def _handle_no_product_line(
        self,
        user_input: TechAgentInput
    ) -> None:
        """Handle case where product line is not specified."""
        logger.info("\n[無產品線] 進行產品線追問")

        self.avatar_response = await self.avatar_process

        # TODO: Enable when environment ready
        # ask_response, rag_response = await technical_support_reask(...)

        # Stubbed product line reask
        relative_questions = [
            {
                "title": "notebook",
                "title_name": "筆記型電腦",
                "icon": "💻",
                "question": "我的筆電有問題"
            },
            {
                "title": "desktop",
                "title_name": "桌上型電腦",
                "icon": "🖥️",
                "question": "我的桌機有問題"
            },
        ]

        self.response_data = {
            "status": 200,
            "type": "reask",
            "message": "ReAsk: Need product line clarification",
            "output": {
                "answer": "請問您需要哪種產品的協助？",
                "ask_flag": True,
                "hint_candidates": relative_questions,
                "kb": {}
            }
        }

        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarAskProductLine",
                    "message": self.avatar_response['response'],
                    "remark": [],
                    "option": [
                        {
                            "name": item["title_name"],
                            "value": item["title"],
                            "icon": item["icon"]
                        }
                        for item in relative_questions
                    ]
                }
            ]
        }

    async def _handle_high_similarity(
        self,
        user_input: TechAgentInput
    ) -> None:
        """Handle case with high KB similarity."""
        logger.info(
            f"\n[相似度高於門檻] 相似度={self.top1_kb_sim}，建立 Hint 回應"
        )

        # TODO: Enable when environment ready
        # rag_response = await technical_support_hint_create(...)

        # Stubbed RAG response
        content = {
            "ask_content": "根據您的問題，我建議您嘗試以下步驟...",
            "title": "筆記型電腦開機問題排解",
            "content": "詳細的故障排除步驟...",
            "link": "https://www.asus.com/tw/support/FAQ/1043959"
        }

        self.avatar_response = await self.avatar_process

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
                    "similarity": float(self.top1_kb_sim or 0.0),
                    "source": "KB",
                    "exec_time": 0.5
                }
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
                    "message": self.avatar_response['response'],
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
                            ]
                        }
                    ]
                }
            ]
        }

    async def _handle_low_similarity(
        self,
        user_input: TechAgentInput
    ) -> None:
        """Handle case with low KB similarity."""
        logger.info(f"\n[相似度低於門檻] 相似度={self.top1_kb_sim}，轉人工")

        self.avatar_response = await self.avatar_process

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
                    "exec_time": 0.0
                }
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
                    "message": self.avatar_response['response'],
                    "remark": [],
                    "option": []
                },
                {
                    "renderId": self.renderId,
                    "stream": False,
                    "type": "avatarAsk",
                    "message": "你可以告訴我像是產品全名、型號...",
                    "remark": [],
                    "option": [
                        {
                            "name": "我想知道 ROG FLOW X16 的規格",
                            "value": "我想知道 ROG FLOW X16 的規格",
                        },
                        {
                            "name": "請幫我推薦16吋筆電",
                            "value": "請幫我推薦16吋筆電",
                        },
                    ]
                }
            ]
        }

    async def _log_and_save_results(
        self,
        user_input: TechAgentInput
    ) -> None:
        """Log and save results to Cosmos DB."""
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)
        logger.info(f"\n[執行時間] tech_agent_api 共耗時 {exec_time} 秒\n")

        cosmos_data = {
            "id": (f"{user_input.cus_id}-{user_input.session_id}-"
                   f"{user_input.chat_id}"),
            "cus_id": user_input.cus_id,
            "session_id": user_input.session_id,
            "chat_id": user_input.chat_id,
            "createDate": datetime.utcnow().isoformat() + "Z",
            "user_input": user_input.user_input,
            "websitecode": user_input.websitecode,
            "product_line": user_input.product_line,
            "system_code": user_input.system_code,
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
            "total_time": exec_time
        }

        # TODO: Enable when environment ready
        # await cosmos_client.insert_data(cosmos_data)

        log_json = json.dumps(cosmos_data, ensure_ascii=False, indent=2)
        logger.info(f"\n[Cosmos DB] 寫入資料（已跳過）: {log_json}\n")
