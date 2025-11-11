"""Tech agent handler with business logic orchestration."""

import time
import uuid
from datetime import datetime
from typing import Dict, Any

from api_structure.core.timer import timed
from api_structure.core.logger import get_log_context
from api_structure.src.models.tech_agent_models import TechAgentInput
from api_structure.src.services.chat_flow_service import ChatFlowService
from api_structure.src.services.kb_search_service import KBSearchService
from api_structure.src.services.rag_service import RAGService
from api_structure.src.services.cosmos_service import CosmosService


class TechAgentHandler:
    """Handler for tech agent API requests.

    Orchestrates the complete tech support flow including:
    - Chat history processing
    - User information extraction
    - Knowledge base search
    - Response generation
    """

    def __init__(
        self,
        chat_flow_service: ChatFlowService,
        kb_search_service: KBSearchService,
        rag_service: RAGService,
        cosmos_service: CosmosService,
    ):
        """Initialize tech agent handler.

        Args:
            chat_flow_service: Chat flow service instance.
            kb_search_service: KB search service instance.
            rag_service: RAG service instance.
            cosmos_service: Cosmos service instance.
        """
        self.chat_flow_service = chat_flow_service
        self.kb_search_service = kb_search_service
        self.rag_service = rag_service
        self.cosmos_service = cosmos_service

        # Processing state
        self.start_time = 0.0
        self.render_id = ""
        self.his_inputs: list[str] = []
        self.chat_count = 0
        self.user_info: Dict[str, Any] = {}
        self.last_bot_scope = ""
        self.last_extract_output: Dict[str, Any] = {}
        self.last_hint: Dict[str, Any] | None = None
        self.lang = ""
        self.user_info_dict: Dict[str, Any] = {}
        self.bot_scope_chat = ""
        self.search_info = ""
        self.top1_kb = ""
        self.top1_kb_sim = 0.0
        self.top4_kb_list: list[str] = []
        self.faqs_wo_pl: list[Dict[str, Any]] = []
        self.is_follow_up = False
        self.avatar_response: Dict[str, Any] = {}
        self.response_data: Dict[str, Any] = {}
        self.final_result: Dict[str, Any] = {}

    @timed(task_name="tech_agent_handler_run")
    async def run(self, user_input: TechAgentInput) -> Dict[str, Any]:
        """Main execution entry point for tech agent processing.

        Args:
            user_input: Tech agent input data.

        Returns:
            Final response dictionary.
        """
        self.start_time = time.perf_counter()
        self.render_id = str(uuid.uuid4())

        # Phase 1: Initialize chat and get history
        await self._initialize_chat(user_input)

        # Phase 2: Process history and check follow-up
        await self._process_history()

        # Phase 3: Get user info and bot scope
        await self._get_user_and_scope_info(user_input)

        # Phase 4: Generate avatar response (async)
        avatar_task = self.rag_service.reply_with_avatar(
            self.his_inputs[-1], self.lang
        )

        # Phase 5: Search knowledge base
        await self._search_knowledge_base(user_input)

        # Phase 6: Process KB results
        self._process_kb_results()

        # Phase 7: Generate final response based on scenario
        await self._generate_response(user_input, avatar_task)

        # Phase 8: Log and save results
        await self._log_and_save_results(user_input)

        return self.final_result

    async def _initialize_chat(self, user_input: TechAgentInput) -> None:
        """Initialize chat and retrieve history.

        Args:
            user_input: Tech agent input data.
        """
        (
            self.his_inputs,
            self.chat_count,
            self.user_info,
            self.last_bot_scope,
            self.last_extract_output,
        ) = await self.cosmos_service.create_gpt_messages(
            user_input.session_id, user_input.user_input
        )

        self.last_hint = await self.cosmos_service.get_latest_hint(
            user_input.session_id
        )

        self.lang = await self.cosmos_service.get_language_by_websitecode(
            user_input.websitecode
        )

        # Use default user info if none exists
        if not self.user_info:
            self.user_info = self.chat_flow_service.default_user_info.copy()
            self.user_info["main_product_category"] = user_input.product_line

    async def _process_history(self) -> None:
        """Process chat history for follow-up detection."""
        if len(self.his_inputs) <= 1:
            self.is_follow_up = False
            return

        # TODO: Enable when environment ready
        # Original: Sentence group classification
        # results_related = await sentence_group_classification(his_inputs)
        # For now, skip grouping

        # Check if follow-up
        prev_q = str(self.his_inputs[-2]) if len(self.his_inputs) > 1 else ""
        prev_a = str(self.last_extract_output.get("answer", ""))
        prev_kb_content = ""  # Would come from KB_mappings

        follow_up_result = await self.chat_flow_service.is_follow_up(
            prev_q, prev_a, prev_kb_content, self.his_inputs[-1]
        )
        self.is_follow_up = follow_up_result.get("is_follow_up", False)

    async def _get_user_and_scope_info(
        self, user_input: TechAgentInput
    ) -> None:
        """Get user information and determine bot scope.

        Args:
            user_input: Tech agent input data.
        """
        # Get user info and search info
        self.user_info_dict, _ = await self.chat_flow_service.get_user_info(
            self.his_inputs
        )

        self.search_info = await self.chat_flow_service.get_search_info(
            self.his_inputs
        )

        # Determine bot scope
        self.bot_scope_chat = await self.chat_flow_service.get_bot_scope(
            prev_user_info=self.user_info,
            curr_user_info=self.user_info_dict,
            last_bot_scope=self.last_bot_scope,
            product_line=user_input.product_line,
            last_hint=self.last_hint,
            user_input=user_input.user_input,
        )

    async def _search_knowledge_base(self, user_input: TechAgentInput) -> None:
        """Search knowledge base with product line.

        Args:
            user_input: Tech agent input data.
        """
        faq_result, faq_result_wo_pl = (
            await self.kb_search_service.search_kb_with_product_line(
                search_info=self.search_info,
                websitecode=user_input.websitecode,
                product_line=self.bot_scope_chat,
            )
        )

        self.faq_result = faq_result
        self.faq_result_wo_pl = faq_result_wo_pl

    def _process_kb_results(self) -> None:
        """Process and filter KB search results."""
        (
            self.top4_kb_list,
            self.top1_kb,
            self.top1_kb_sim,
            _,
        ) = self.kb_search_service.filter_kb_results(self.faq_result)

        _, _, _, self.faqs_wo_pl = self.kb_search_service.filter_kb_results(
            self.faq_result_wo_pl
        )

    async def _generate_response(
        self, user_input: TechAgentInput, avatar_task: Any
    ) -> None:
        """Generate final response based on processing results.

        Args:
            user_input: Tech agent input data.
            avatar_task: Async task for avatar response.
        """
        if not self.bot_scope_chat:
            # Scenario 1: No product line - ask for clarification
            await self._handle_no_product_line(user_input, avatar_task)
        elif self.top1_kb_sim > self.kb_search_service.top1_kb_similarity_threshold:
            # Scenario 2: High similarity - provide KB answer
            await self._handle_high_similarity(user_input, avatar_task)
        else:
            # Scenario 3: Low similarity - suggest handoff
            await self._handle_low_similarity(user_input, avatar_task)

    async def _handle_no_product_line(
        self, user_input: TechAgentInput, avatar_task: Any
    ) -> None:
        """Handle case when product line is not determined.

        Args:
            user_input: Tech agent input data.
            avatar_task: Async task for avatar response.
        """
        # Get avatar response
        self.avatar_response = await avatar_task

        # Generate product line re-ask
        ask_response, rag_response = (
            await self.rag_service.create_product_line_reask(
                user_input=user_input.user_input,
                faqs_wo_pl=self.faqs_wo_pl,
                websitecode=user_input.websitecode,
                lang=self.lang,
                system_code=user_input.system_code,
            )
        )

        relative_questions = rag_response.get("relative_questions", [])

        # Save hint data
        await self.cosmos_service.insert_hint_data(
            chatflow_data=user_input,
            intent_hints=relative_questions,
            search_info=self.search_info,
            hint_type="productline-reask",
        )

        # Build response
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
                    "renderId": self.render_id,
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

    async def _handle_high_similarity(
        self, user_input: TechAgentInput, avatar_task: Any
    ) -> None:
        """Handle case when KB match has high similarity.

        Args:
            user_input: Tech agent input data.
            avatar_task: Async task for avatar response.
        """
        # Get RAG response with hints
        rag_response = await self.rag_service.create_hint_response(
            kb_list=self.top4_kb_list,
            top1_kb=self.top1_kb,
            top1_kb_sim=self.top1_kb_sim,
            lang=self.lang,
            search_info=self.search_info,
            his_inputs=self.his_inputs,
            system_code=user_input.system_code,
            websitecode=user_input.websitecode,
        )

        info = rag_response.get("response_info", {})
        content = rag_response.get("rag_content", {})

        # Get avatar response with KB content
        self.avatar_response = await self.rag_service.reply_with_avatar(
            self.his_inputs[-1], self.lang, content
        )

        # Build response
        self.response_data = {
            "status": 200,
            "type": "answer",
            "message": "RAG Response",
            "output": {
                "answer": content.get("ask_content", ""),
                "ask_flag": False,
                "hint_candidates": rag_response.get("relative_questions", []),
                "kb": {
                    "kb_no": str(info.get("top1_kb", "")),
                    "title": content.get("title", ""),
                    "similarity": float(info.get("top1_similarity", 0.0) or 0.0),
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
                    "renderId": self.render_id,
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

    async def _handle_low_similarity(
        self, user_input: TechAgentInput, avatar_task: Any
    ) -> None:
        """Handle case when KB match has low similarity.

        Args:
            user_input: Tech agent input data.
            avatar_task: Async task for avatar response.
        """
        # Get avatar response
        self.avatar_response = await avatar_task

        # Build response
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
                    "message": self.avatar_response["response"].answer,
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
                                    "value": "purchasing-recommendation-of-asus-products",
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

    async def _log_and_save_results(self, user_input: TechAgentInput) -> None:
        """Log execution time and save results to Cosmos.

        Args:
            user_input: Tech agent input data.
        """
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)

        # Prepare Cosmos data
        cosmos_data = {
            "id": f"{user_input.cus_id}-{user_input.session_id}-{user_input.chat_id}",
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
                "language": self.lang,
            },
            "final_result": self.final_result,
            "extract": self.response_data,
            "total_time": exec_time,
        }

        # Save to Cosmos (stubbed)
        await self.cosmos_service.insert_data(cosmos_data)
