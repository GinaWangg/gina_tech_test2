"""Tech agent handler for processing technical support requests."""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict

from core.logger import set_extract_log
from core.timer import timed
from src.models.tech_agent_models import TechAgentInput

# Constants
TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentHandler:
    """Handler for tech agent processing logic.
    
    This handler orchestrates the technical support workflow including:
    - Chat history processing
    - User information extraction
    - Knowledge base search
    - Response generation
    
    Attributes:
        containers: Dependency container with all required services
        user_input: User's input data
    """

    def __init__(self, containers: Any, user_input: TechAgentInput):
        """Initialize the tech agent handler.
        
        Args:
            containers: DependencyContainer with initialized services
            user_input: User input data model
        """
        self.containers = containers
        self.user_input = user_input
        self.start_time = time.perf_counter()

        # Initialize processing state
        self.chat_flow = None
        self.service_process = None
        self.his_inputs = None
        self.user_info = None
        self.last_bot_scope = None
        self.last_extract_output = None
        self.last_hint = None
        self.is_follow_up = False
        self.lang = None
        self.chat_count = 0
        self.user_info_dict = {}
        self.bot_scope_chat = None
        self.search_info = None
        self.faq_result = {}
        self.faq_result_wo_pl = {}
        self.top1_kb = None
        self.top1_kb_sim = 0.0
        self.top4_kb_list = []
        self.faqs_wo_pl = []
        self.response_data = {}

        # Response rendering
        self.type = ""
        self.avatar_response = ""
        self.avatar_process = None
        self.prev_q = ""
        self.prev_a = ""
        self.kb_no = ""
        self.content = ""
        self.result = []
        self.final_result = {}
        self.renderId = ""
        self.fu_task = None

    @timed(task_name="tech_agent_initialize_chat")
    async def _initialize_chat(self) -> None:
        """Initialize chat, retrieve history and basic info."""
        settings = self.containers.cosmos_settings

        # Parallel execution of all I/O operations
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

        # Handle default values
        if not self.user_input.session_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.session_id = f"agent-{tail}"
        if not self.user_input.cus_id:
            self.user_input.cus_id = "test"
        if not self.user_input.chat_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.chat_id = f"agent-{tail}"

        self.renderId = str(uuid.uuid4())

        # Import here to avoid circular dependencies
        from src.core.chat_flow import ChatFlow
        from src.services.service_process import ServiceProcess

        self.service_process = ServiceProcess(
            system_code=self.user_input.system_code,
            container=self.containers
        )
        self.chat_flow = ChatFlow(
            data=self.user_input,
            last_hint=self.last_hint,
            container=self.containers
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

    @timed(task_name="tech_agent_process_history")
    async def _process_history(self) -> None:
        """Process chat history and determine follow-up status."""
        if len(self.his_inputs) <= 1:

            async def dummy_follow_up():
                return {"is_follow_up": False}

            self.fu_task = asyncio.create_task(dummy_follow_up())
            return

        # Prepare data
        self.prev_q = str(self.his_inputs[-2])
        self.prev_a = str(self.last_extract_output.get("answer", ""))
        self.kb_no = str(
            self.last_extract_output.get("kb", {}).get("kb_no", "")
        )
        self.content = str(
            self.containers.KB_mappings.get(
                f"{self.kb_no}_{self.lang}", {}
            ).get("content")
        )

        # Execute sentence grouping
        group_task = self.containers.sentence_group_classification
        results_related = (
            await group_task.sentence_group_classification(
                self.his_inputs
            )
        )

        # Process grouping results
        groups = (results_related or {}).get("groups", [])
        if groups:
            statements = (groups[-1].get("statements") or [])
            latest_group_statements = [
                s for s in statements if isinstance(s, str)
            ]
            if latest_group_statements:
                self.his_inputs = latest_group_statements.copy()

        # Create follow-up task (don't wait)
        self.fu_task = asyncio.create_task(
            self.chat_flow.is_follow_up(
                prev_question=self.prev_q,
                prev_answer=self.prev_a,
                prev_answer_refs=self.content,
                new_question=self.his_inputs[-1]
            )
        )

    @timed(task_name="tech_agent_get_user_and_scope_info")
    async def _get_user_and_scope_info(self) -> None:
        """Get user info, search info, and determine bot scope."""
        # Parallel execution
        ui_task = self.chat_flow.get_userInfo(his_inputs=self.his_inputs)
        si_task = self.chat_flow.get_searchInfo(self.his_inputs)

        # Handle tech_support_related check
        tech_support_task = None
        if (
            self.last_hint
            and self.last_hint.get("hintType") == "productline-reask"
        ):
            prompt_content = f'''Please determine whether the sentence 
            "{self.his_inputs[-1]}" mentions any technical support-related 
            issues, and reply with "true" or "false" only. 
            Here is an example you can refer to. 
            1. user's question: it can only be turned on when plugged in. 
               your response: "true" 
            2. user's question: wearable. your response: "false" 
            3. user's question: notebook. your response: "false"'''
            prompt = [{"role": "user", "content": prompt_content}]
            tech_support_task = (
                self.chat_flow.container.base_service.GPT41_mini_response(
                    prompt
                )
            )

        # Parallel wait
        results = await asyncio.gather(
            ui_task,
            si_task,
            tech_support_task if tech_support_task else asyncio.sleep(0),
            return_exceptions=True
        )

        # Process results
        result_user_info = results[0]
        self.user_info_dict = (
            result_user_info[0]
            if not isinstance(result_user_info, Exception)
            else {}
        )

        search_info_result = results[1]
        tech_support_related = results[2] if tech_support_task else "true"

        # Determine search_info
        if tech_support_related == "false" and self.last_hint:
            self.search_info = self.last_hint.get("searchInfo")
        else:
            self.search_info = (
                search_info_result
                if not isinstance(search_info_result, Exception)
                else self.his_inputs[-1]
            )

        # Get bot_scope
        self.bot_scope_chat = (
            self.user_input.product_line
            or await self.chat_flow.get_bot_scope_chat(
                prev_user_info=self.user_info,
                curr_user_info=self.user_info_dict,
                last_bot_scope=self.last_bot_scope
            )
        )

    @timed(task_name="tech_agent_search_knowledge_base")
    async def _search_knowledge_base(self) -> None:
        """Search knowledge base with product line."""
        response = (
            await self.containers.sd
            .service_discreminator_with_productline(
                user_question_english=self.search_info,
                site=self.user_input.websitecode,
                specific_kb_mappings=self.containers.specific_kb_mappings,
                productLine=self.bot_scope_chat,
            )
        )
        self.faq_result = response[0]
        self.faq_result_wo_pl = response[1]

    @timed(task_name="tech_agent_process_kb_results")
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
            {"kb_no": faq, "cosineSimilarity": sim, "productLine": pl}
            for faq, sim, pl in zip(
                self.faq_result_wo_pl.get("faq", []),
                self.faq_result_wo_pl.get("cosineSimilarity", []),
                self.faq_result_wo_pl.get("productLine", []),
            )
        ]

    @timed(task_name="tech_agent_handle_no_product_line")
    async def _handle_no_product_line(self) -> Dict[str, Any]:
        """Handle case when no product line is specified."""
        reask_result_task = asyncio.create_task(
            self.service_process.technical_support_productline_reask(
                user_input=self.user_input.user_input,
                faqs_wo_pl=self.faqs_wo_pl,
                site=self.user_input.websitecode,
                lang=self.lang,
                system_code=self.user_input.system_code,
            )
        )
        self.avatar_response, (ask_response, rag_response) = (
            await asyncio.gather(self.avatar_process, reask_result_task)
        )
        relative_questions = rag_response.get("relative_questions", [])
        
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
        
        return self.final_result

    @timed(task_name="tech_agent_handle_high_similarity")
    async def _handle_high_similarity(self) -> Dict[str, Any]:
        """Handle case when KB similarity is high."""
        rag_response = (
            await self.service_process.technical_support_hint_create(
                self.top4_kb_list,
                self.top1_kb,
                self.top1_kb_sim,
                self.lang,
                self.search_info,
                self.his_inputs,
                system_code=self.user_input.system_code,
                site=self.user_input.websitecode,
                config=self.containers.cfg
            )
        )
        info = rag_response.get("response_info", {})
        content = rag_response.get("rag_content", {})
        
        self.avatar_response = (
            await self.service_process.ts_rag
            .reply_with_faq_gemini_sys_avatar(
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
                    "exec_time": float(info.get("exec_time", 0.0) or 0.0)
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
                    "message": self.avatar_response['response'].answer,
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
        
        return self.final_result

    @timed(task_name="tech_agent_handle_low_similarity")
    async def _handle_low_similarity(self) -> Dict[str, Any]:
        """Handle case when KB similarity is low."""
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
                    "title": str(
                        self.containers.KB_mappings.get(
                            f"{self.top1_kb}_{self.lang}", {}
                        ).get("title", "")
                    ),
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
                                {"type": "inquireMode", "value": "intent"},
                                {
                                    "type": "inquireKey",
                                    "value": "specification-consultation"
                                },
                                {"type": "mainProduct", "value": 25323}
                            ]
                        },
                        {
                            "name": "請幫我推薦16吋筆電",
                            "value": "請幫我推薦16吋筆電",
                            "answer": [
                                {"type": "inquireMode", "value": "intent"},
                                {
                                    "type": "inquireKey",
                                    "value": (
                                        "purchasing-recommendation-of-"
                                        "asus-products"
                                    )
                                }
                            ]
                        },
                        {
                            "name": "請幫我介紹 ROG Phone 8 的特色",
                            "value": "請幫我介紹 ROG Phone 8 的特色",
                            "answer": [
                                {"type": "inquireMode", "value": "intent"},
                                {
                                    "type": "inquireKey",
                                    "value": "specification-consultation"
                                },
                                {"type": "mainProduct", "value": 25323}
                            ]
                        }
                    ]
                }
            ]
        }
        
        return self.final_result

    @timed(task_name="tech_agent_generate_response")
    async def _generate_response(self) -> Dict[str, Any]:
        """Generate the final response based on processed data."""
        if not self.bot_scope_chat:
            self.type = "avatarAskProductLine"
            return await self._handle_no_product_line()
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            self.type = "avatarTechnicalSupport"
            return await self._handle_high_similarity()
        else:
            self.type = "avatarText"
            return await self._handle_low_similarity()

    @timed(task_name="tech_agent_log_and_save_results")
    async def _log_and_save_results(self) -> Dict[str, Any]:
        """Log and save the final results to Cosmos DB."""
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
        
        asyncio.create_task(
            self.containers.cosmos_settings.insert_data(cosmos_data)
        )
        
        # Set extract log for middleware logging
        set_extract_log(self.response_data)
        
        return cosmos_data

    @timed(task_name="tech_agent_handler_run")
    async def run(self) -> Dict[str, Any]:
        """Main entry point for tech agent processing.
        
        Returns:
            Final response data dictionary
            
        Raises:
            Exception: If processing fails
        """
        log_json = json.dumps(
            self.user_input.dict(), ensure_ascii=False, indent=2
        )
        print(f"\n[Agent 啟動] 輸入內容: {log_json}")

        await self._initialize_chat()
        await self._process_history()
        
        self.avatar_process = asyncio.create_task(
            self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(
                self.his_inputs[-1], self.lang
            )
        )
        
        await self._get_user_and_scope_info()
        await self._search_knowledge_base()
        self._process_kb_results()

        follow_up = await self.fu_task if self.fu_task else {}
        self.is_follow_up = bool(follow_up.get("is_follow_up", False))
        
        result = await self._generate_response()
        
        # Log and save asynchronously
        asyncio.create_task(self._log_and_save_results())

        return result
