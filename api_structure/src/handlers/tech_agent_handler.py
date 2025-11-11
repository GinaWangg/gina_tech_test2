"""Tech Agent Handler - Core business logic for technical support.

This module contains the TechAgentHandler class which orchestrates
the entire technical support flow including:
- Chat history processing
- User info extraction
- Knowledge base search
- Response generation
"""

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from api_structure.core.timer import timed
from api_structure.core.logger import get_log_context, set_extract_log
from api_structure.src.models.tech_agent_models import TechAgentInput
from api_structure.src.clients.mock_container_client import (
    MockDependencyContainer,
    MockChatFlow,
    MockServiceProcess,
)


# Constants
TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentHandler:
    """Handler for technical support agent processing."""

    def __init__(
        self, container: MockDependencyContainer, user_input: TechAgentInput
    ):
        """Initialize the tech agent handler.

        Args:
            container: Dependency container with all services
            user_input: User input data
        """
        self.containers = container
        self.user_input = user_input
        self.start_time = time.perf_counter()

        # Initialize attributes to be used across methods
        self.chat_flow: Optional[MockChatFlow] = None
        self.service_process: Optional[MockServiceProcess] = None
        self.his_inputs: Optional[List[str]] = None
        self.user_info: Optional[Dict] = None
        self.last_bot_scope: Optional[str] = None
        self.last_extract_output: Optional[Dict] = None
        self.last_hint: Optional[Dict] = None
        self.is_follow_up: bool = False
        self.lang: Optional[str] = None
        self.chat_count: int = 0
        self.user_info_dict: Dict = {}
        self.bot_scope_chat: Optional[str] = None
        self.search_info: Optional[str] = None
        self.faq_result: Dict = {}
        self.faq_result_wo_pl: Dict = {}
        self.top1_kb: Optional[str] = None
        self.top1_kb_sim: float = 0.0
        self.top4_kb_list: List[str] = []
        self.faqs_wo_pl: List[Dict] = []
        self.response_data: Dict = {}

        self.type: str = ""
        self.avatar_response: Any = None
        self.renderId: str = ""
        self.final_result: Dict = {}

    @timed(task_name="tech_agent_process")
    async def process(self) -> Dict[str, Any]:
        """Main processing flow for the tech agent.

        Returns:
            Response dictionary with status, message, and result
        """
        # Log input
        log_json = json.dumps(
            self.user_input.model_dump(), ensure_ascii=False, indent=2
        )
        print(f"\n[Agent 啟動] 輸入內容: {log_json}")

        # Initialize
        await self._initialize_chat()
        await self._process_history()

        # Get user and scope info
        await self._get_user_and_scope_info()

        # Search knowledge base
        await self._search_knowledge_base()
        self._process_kb_results()

        # Check if follow-up (mocked to always False for now)
        self.is_follow_up = False
        print(f"是否延續問題追問 : {self.is_follow_up}")

        # Generate response
        await self._generate_response()

        # Log results (mocked - no actual Cosmos write)
        await self._log_and_save_results()

        return self.final_result

    async def _initialize_chat(self) -> None:
        """Initialize chat, retrieve history and basic info.

        # TODO: Enable when environment ready
        # This would query Cosmos DB for real chat history
        """
        settings = self.containers.cosmos_settings

        # Get messages, hint, and language
        results = await settings.create_GPT_messages(
            self.user_input.session_id, self.user_input.user_input
        )
        self.last_hint = await settings.get_latest_hint(self.user_input.session_id)
        self.lang = await settings.get_language_by_websitecode_dev(
            self.user_input.websitecode
        )

        (
            self.his_inputs,
            self.chat_count,
            self.user_info,
            self.last_bot_scope,
            self.last_extract_output,
        ) = results

        log_json = json.dumps(
            {
                "his_inputs": self.his_inputs,
                "chat_count": self.chat_count,
                "user_info": self.user_info,
                "last_bot_scope": self.last_bot_scope,
            },
            ensure_ascii=False,
            indent=2,
        )
        print(f"\n[歷史對話]\n{log_json}")

        # Generate IDs if missing
        if not self.user_input.session_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.session_id = f"agent-{tail}"
        if not self.user_input.cus_id:
            self.user_input.cus_id = "test"
        if not self.user_input.chat_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.chat_id = f"agent-{tail}"

        self.renderId = str(uuid.uuid4())

        print(f"last_hint: {self.last_hint}")

        # Initialize services
        self.service_process = MockServiceProcess(
            system_code=self.user_input.system_code, container=self.containers
        )
        self.chat_flow = MockChatFlow(
            data=self.user_input,
            last_hint=self.last_hint,
            container=self.containers,
        )

        if not self.user_info:
            self.user_info = self.chat_flow.default_user_info
        if (
            self.user_input.product_line
            and self.last_bot_scope != self.user_input.product_line
        ):
            self.user_info["main_product_category"] = self.user_input.product_line
            self.user_info["first_time"] = True

    async def _process_history(self) -> None:
        """Process chat history.

        # TODO: Enable when environment ready
        # This would call real sentence grouping API
        """
        if len(self.his_inputs) <= 1:
            print(f"his_inputs : {self.his_inputs}")
            return

        # Mock: Simple grouping
        group_task = self.containers.sentence_group_classification
        results_related = await group_task.sentence_group_classification(
            self.his_inputs
        )

        # Process grouping results
        groups = (results_related or {}).get("groups", [])
        if groups:
            statements = (groups[-1].get("statements") or [])
            latest_group_statements = [s for s in statements if isinstance(s, str)]
            if latest_group_statements:
                self.his_inputs = latest_group_statements.copy()

        print(f"last group statements => {self.his_inputs[-1]}")
        print(f"his_inputs : {self.his_inputs}")

    async def _get_user_and_scope_info(self) -> None:
        """Get user info, search info, and determine bot scope.

        # TODO: Enable when environment ready
        # This would call real GPT APIs for extraction
        """
        # Get user info
        result_user_info = await self.chat_flow.get_userInfo(his_inputs=self.his_inputs)
        self.user_info_dict = result_user_info[0]

        # Get search info
        search_info_result = await self.chat_flow.get_searchInfo(self.his_inputs)

        # Check tech support related (mocked)
        tech_support_related = "true"
        if self.last_hint and self.last_hint.get("hintType") == "productline-reask":
            # TODO: Enable when environment ready
            # prompt = [{"role": "user", "content": prompt_content}]
            # tech_support_related = await self.chat_flow.container.base_service.GPT41_mini_response(prompt)
            pass

        log_json = json.dumps(self.user_info_dict, ensure_ascii=False, indent=2)
        print(f"\n[使用者資訊]\n{log_json}")

        # Determine search_info
        if tech_support_related == "false" and self.last_hint:
            self.search_info = self.last_hint.get("searchInfo")
        else:
            self.search_info = search_info_result

        # Get bot_scope
        self.bot_scope_chat = (
            self.user_input.product_line
            or await self.chat_flow.get_bot_scope_chat(
                prev_user_info=self.user_info,
                curr_user_info=self.user_info_dict,
                last_bot_scope=self.last_bot_scope,
            )
        )

        print(f"\n[Bot Scope 判斷] {self.bot_scope_chat}")

    async def _search_knowledge_base(self) -> None:
        """Search knowledge base with product line.

        # TODO: Enable when environment ready
        # This would call real Redis/Vector DB search
        """
        response = await self.containers.sd.service_discreminator_with_productline(
            user_question_english=self.search_info,
            site=self.user_input.websitecode,
            specific_kb_mappings=self.containers.specific_kb_mappings,
            productLine=self.bot_scope_chat,
        )
        log_json = json.dumps(response, ensure_ascii=False, indent=2)
        print(f"[ServiceDiscriminator] discrimination_productline_response: {log_json}")

        self.faq_result = response[0]
        self.faq_result_wo_pl = response[1]

    def _process_kb_results(self) -> None:
        """Process and filter results from KB search."""
        faq_list = self.faq_result.get("faq", [])
        sim_list = self.faq_result.get("cosineSimilarity", [])

        self.top4_kb_list = [
            faq for faq, sim in zip(faq_list, sim_list) if sim >= KB_THRESHOLD
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

    async def _generate_response(self) -> None:
        """Generate the final response based on the processed data."""
        if not self.bot_scope_chat:
            self.type = "avatarAskProductLine"
            await self._handle_no_product_line()
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            self.type = "avatarTechnicalSupport"
            await self._handle_high_similarity()
        else:
            self.type = "avatarText"
            await self._handle_low_similarity()

    async def _handle_no_product_line(self) -> None:
        """Handle case when no product line is identified.

        # TODO: Enable when environment ready
        # This would call real RAG service for product line reask
        """
        print("\n[無產品線] 進行產品線追問")

        # Get avatar response
        self.avatar_response = (
            await self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(
                self.his_inputs[-1], self.lang
            )
        )

        # Get reask response
        ask_response, rag_response = (
            await self.service_process.technical_support_productline_reask(
                user_input=self.user_input.user_input,
                faqs_wo_pl=self.faqs_wo_pl,
                site=self.user_input.websitecode,
                lang=self.lang,
                system_code=self.user_input.system_code,
            )
        )

        relative_questions = rag_response.get("relative_questions", [])

        # Insert hint data (mocked)
        await self.containers.cosmos_settings.insert_hint_data(
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

    async def _handle_high_similarity(self) -> None:
        """Handle case when similarity is high enough.

        # TODO: Enable when environment ready
        # This would call real RAG service for hint creation
        """
        print(f"\n[相似度高於門檻] 相似度={self.top1_kb_sim}，建立 Hint 回應")

        rag_response = await self.service_process.technical_support_hint_create(
            self.top4_kb_list,
            self.top1_kb,
            self.top1_kb_sim,
            self.lang,
            self.search_info,
            self.his_inputs,
            system_code=self.user_input.system_code,
            site=self.user_input.websitecode,
            config=self.containers.cfg,
        )

        info = rag_response.get("response_info", {})
        content = rag_response.get("rag_content", {})

        # Get avatar response
        self.avatar_response = (
            await self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(
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

    async def _handle_low_similarity(self) -> None:
        """Handle case when similarity is too low.

        # TODO: Enable when environment ready
        # This would get avatar response and return handoff
        """
        print(f"\n[相似度低於門檻] 相似度={self.top1_kb_sim}，轉人工")

        # Get avatar response
        self.avatar_response = (
            await self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(
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
                        self.containers.KB_mappings.get(
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
                    "message": "你可以告訴我像是產品全名、型號，或你想問的活動名稱～比如「ROG Flow X16」或「我想查產品保固到期日」。給我多一點線索，我就能更快幫你找到對的資料，也不會漏掉重點！",
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

    async def _log_and_save_results(self) -> None:
        """Log and save the final results to Cosmos DB.

        # TODO: Enable when environment ready
        # This would write to actual Cosmos DB
        """
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)
        print(f"\n[執行時間] tech_agent_api 共耗時 {exec_time} 秒\n")

        cosmos_data = {
            "id": f"{self.user_input.cus_id}-{self.user_input.session_id}-{self.user_input.chat_id}",
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

        # Mock: No actual insert
        await self.containers.cosmos_settings.insert_data(cosmos_data)

        log_json = json.dumps(cosmos_data, ensure_ascii=False, indent=2)
        print(f"\n[Cosmos DB] 寫入資料: {log_json}\n")

        # Set extract log for middleware
        set_extract_log(self.response_data)
