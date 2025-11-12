"""Tech agent handler for processing user requests.

This module contains the main business logic for the tech agent,
following AOCC FastAPI standards with @timed decorators.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from api_structure.core.logger import get_log_context, set_extract_log
from api_structure.core.timer import timed
from api_structure.src.models.tech_agent_models import TechAgentInput
from api_structure.src.services.chat_flow_service import ChatFlowService
from api_structure.src.services.kb_service import KnowledgeBaseService

# Constants
TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentHandler:
    """Handler for tech agent request processing."""

    def __init__(
        self,
        user_input: TechAgentInput,
        cosmos_service: Any,
        service_discriminator: Any,
        kb_mappings: Dict[str, Any],
        rag_mappings: Dict[str, Any],
        user_info_extractor: Optional[Any] = None,
        follow_up_detector: Optional[Any] = None,
        avatar_generator: Optional[Any] = None,
    ):
        """Initialize tech agent handler.

        Args:
            user_input: User input data
            cosmos_service: Cosmos DB service
            service_discriminator: Service discriminator for KB search
            kb_mappings: KB mappings dictionary
            rag_mappings: RAG mappings dictionary
            user_info_extractor: GPT-based user info extractor (optional)
            follow_up_detector: GPT-based follow-up detector (optional)
            avatar_generator: GPT-based avatar response generator (optional)
        """
        self.user_input = user_input
        self.cosmos_service = cosmos_service
        self.service_discriminator = service_discriminator
        self.start_time = time.perf_counter()
        self.user_info_extractor = user_info_extractor
        self.follow_up_detector = follow_up_detector
        self.avatar_generator = avatar_generator

        # Create mock container for services
        class MockContainer:
            def __init__(self, kb_map, rag_map):
                self.KB_mappings = kb_map
                self.rag_mappings = rag_map

        self.container = MockContainer(kb_mappings, rag_mappings)

        # Initialize services with GPT components
        self.kb_service = KnowledgeBaseService(
            self.container,
            avatar_generator=avatar_generator
        )

        # Initialize attributes
        self.chat_flow = None
        self.his_inputs = []
        self.user_info = None
        self.last_bot_scope = ""
        self.last_extract_output = {}
        self.last_hint = None
        self.is_follow_up = False
        self.lang = "zh-TW"
        self.chat_count = 0
        self.user_info_dict = {}
        self.bot_scope_chat = ""
        self.search_info = ""
        self.faq_result = {}
        self.faq_result_wo_pl = {}
        self.top1_kb = None
        self.top1_kb_sim = 0.0
        self.top4_kb_list = []
        self.faqs_wo_pl = []
        self.response_data = {}

        self.type = ""
        self.avatar_response = {}
        self.renderId = ""
        self.final_result = {}

    @timed(task_name="initialize_chat")
    async def _initialize_chat(self) -> None:
        """Initialize chat and retrieve history."""
        # Get session data from Cosmos
        messages_task = self.cosmos_service.create_gpt_messages(
            self.user_input.session_id, self.user_input.user_input
        )
        hint_task = self.cosmos_service.get_latest_hint(
            self.user_input.session_id
        )
        lang_task = (
            self.cosmos_service.get_language_by_websitecode_dev(
                self.user_input.websitecode
            )
        )

        # Wait for all results
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

        # Handle defaults
        if not self.user_input.session_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.session_id = f"agent-{tail}"
        if not self.user_input.cus_id:
            self.user_input.cus_id = "test"
        if not self.user_input.chat_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.chat_id = f"agent-{tail}"

        self.renderId = str(uuid.uuid4())

        # Initialize chat flow service with GPT components
        self.chat_flow = ChatFlowService(
            data=self.user_input,
            last_hint=self.last_hint,
            container=self.container,
            user_info_extractor=self.user_info_extractor,
            follow_up_detector=self.follow_up_detector,
        )

        if not self.user_info:
            self.user_info = self.chat_flow.default_user_info

        if (
            self.user_input.product_line
            and self.last_bot_scope != self.user_input.product_line
        ):
            self.user_info["main_product_category"] = (
                self.user_input.product_line
            )
            self.user_info["first_time"] = True

    @timed(task_name="get_user_and_scope_info")
    async def _get_user_and_scope_info(self) -> None:
        """Get user info, search info, and determine bot scope."""
        # Parallel execution
        ui_task = self.chat_flow.get_userInfo(his_inputs=self.his_inputs)
        si_task = self.chat_flow.get_searchInfo(self.his_inputs)

        results = await asyncio.gather(ui_task, si_task)

        result_user_info = results[0]
        self.user_info_dict = result_user_info[0]

        search_info_result = results[1]
        self.search_info = search_info_result

        # Get bot scope
        self.bot_scope_chat = (
            self.user_input.product_line
            or await self.chat_flow.get_bot_scope_chat(
                prev_user_info=self.user_info,
                curr_user_info=self.user_info_dict,
                last_bot_scope=self.last_bot_scope,
            )
        )

    @timed(task_name="search_knowledge_base")
    async def _search_knowledge_base(self) -> None:
        """Search knowledge base with product line."""
        response = (
            await self.service_discriminator.service_discreminator_with_productline(  # noqa: E501
                user_question_english=self.search_info,
                site=self.user_input.websitecode,
                specific_kb_mappings={},
                productLine=self.bot_scope_chat,
            )
        )

        self.faq_result = response[0]
        self.faq_result_wo_pl = response[1]

    @timed(task_name="process_kb_results")
    async def _process_kb_results(self) -> None:
        """Process and filter results from KB search."""
        (
            self.top4_kb_list,
            self.top1_kb,
            self.top1_kb_sim,
        ) = self.kb_service.process_kb_results(
            self.faq_result, threshold=KB_THRESHOLD
        )

        self.faqs_wo_pl = self.kb_service.process_faqs_without_pl(
            self.faq_result_wo_pl
        )

    @timed(task_name="generate_response")
    async def _generate_response(self) -> None:
        """Generate the final response based on processed data."""
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
        """Handle case where no product line is determined."""
        # Generate avatar response
        avatar_task = self.kb_service.generate_avatar_response(
            self.his_inputs[-1], self.lang
        )

        # Generate product line reask
        reask_task = self.kb_service.generate_productline_reask(
            user_input=self.user_input.user_input,
            faqs_wo_pl=self.faqs_wo_pl,
            site=self.user_input.websitecode,
            lang=self.lang,
            system_code=self.user_input.system_code,
        )

        self.avatar_response, (
            ask_response,
            rag_response,
        ) = await asyncio.gather(avatar_task, reask_task)

        relative_questions = rag_response.get("relative_questions", [])

        # Insert hint data
        await self.cosmos_service.insert_hint_data(
            chatflow_data=self.chat_flow.data,
            intent_hints=relative_questions,
            search_info=self.search_info,
            hint_type="productline-reask",
        )

        self.response_data = {
            "status": 200,
            "type": "reask",
            "message": "ReAsk: Need product line clarification",
            "output": {
                "answer": ask_response["ask_content"],
                "ask_flag": ask_response["ask_flag"],
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
        """Handle case where KB similarity is high."""
        # Generate RAG response
        rag_response = await self.kb_service.generate_rag_response(
            self.top4_kb_list,
            self.top1_kb,
            self.top1_kb_sim,
            self.lang,
            self.search_info,
            self.his_inputs,
            system_code=self.user_input.system_code,
            site=self.user_input.websitecode,
        )

        info = rag_response.get("response_info", {})
        content = rag_response.get("rag_content", {})

        # Generate avatar response with content
        self.avatar_response = (
            await self.kb_service.generate_avatar_response(
                self.his_inputs[-1], self.lang, content
            )
        )

        self.response_data = {
            "status": 200,
            "type": "answer",
            "message": "RAG Response",
            "output": {
                "answer": content.get("ask_content", ""),
                "ask_flag": False,
                "hint_candidates": rag_response.get(
                    "relative_questions", []
                ),
                "kb": {
                    "kb_no": str(info.get("top1_kb", "")),
                    "title": content.get("title", ""),
                    "similarity": float(
                        info.get("top1_similarity", 0.0) or 0.0
                    ),
                    "source": info.get("response_source", ""),
                    "exec_time": float(info.get("exec_time", 0.0) or 0.0),
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
        """Handle case where KB similarity is low."""
        # Generate avatar response
        self.avatar_response = (
            await self.kb_service.generate_avatar_response(
                self.his_inputs[-1], self.lang
            )
        )

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
                    "title": str(
                        self.kb_service.KB_mappings.get(
                            f"{self.top1_kb}_{self.lang}", {}
                        ).get("title", "")
                    ),
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
                        "給我多一點線索，我就能更快幫你找到對的資料，也不會漏掉重點！"
                    ),
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
                                    "value": "purchasing-recommendation-of-asus-products",  # noqa: E501
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

    @timed(task_name="log_and_save_results")
    async def _log_and_save_results(self) -> None:
        """Log and save final results to Cosmos DB."""
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)

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
            },
            "final_result": self.final_result,
            "extract": self.response_data,
            "total_time": exec_time,
        }

        # Save to Cosmos (mock)
        await self.cosmos_service.insert_data(cosmos_data)

        # Set extract log for middleware
        set_extract_log(
            {"exec_time": exec_time, "type": self.type, "kb": self.top1_kb}
        )

    @timed(task_name="tech_agent_process")
    async def run(self) -> Dict[str, Any]:
        """Main processing flow for tech agent.

        Returns:
            Final response dictionary
        """
        log_json = json.dumps(
            self.user_input.model_dump(), ensure_ascii=False, indent=2
        )
        print(f"\n[Agent 啟動] 輸入內容: {log_json}")

        # Execute processing pipeline
        await self._initialize_chat()
        await self._get_user_and_scope_info()
        await self._search_knowledge_base()
        await self._process_kb_results()
        await self._generate_response()
        await self._log_and_save_results()

        return self.final_result
