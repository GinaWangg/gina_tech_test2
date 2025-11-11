"""
Tech Agent Handler - Core business logic with @timed decorators.
Maintains exact behavior of original TechAgentProcessor implementation.
"""

import time
import json
from typing import Dict, Any, Optional
from api_structure.core.timer import timed
from api_structure.core.logger import logger
from api_structure.src.services.tech_agent_service import (
    TechAgentService,
    TOP1_KB_SIMILARITY_THRESHOLD,
)
from api_structure.src.repositories.tech_agent_repository import TechAgentRepository
from api_structure.src.schemas.tech_agent_schemas import TechAgentInput


class TechAgentHandler:
    """Handler for tech agent API endpoint with complete business logic."""
    
    def __init__(
        self,
        user_input: TechAgentInput,
        service: TechAgentService,
        repository: TechAgentRepository
    ):
        """
        Initialize handler with dependencies.
        
        Args:
            user_input: Tech agent input data
            service: TechAgentService instance
            repository: TechAgentRepository instance
        """
        self.user_input = user_input
        self.service = service
        self.repository = repository
        self.start_time = time.perf_counter()
        
        # State variables matching original implementation
        self.his_inputs = None
        self.chat_count = 0
        self.user_info = None
        self.last_bot_scope = None
        self.last_extract_output = None
        self.last_hint = None
        self.lang = None
        self.render_id = ""
        self.bot_scope_chat = None
        self.search_info = None
        self.faq_result = {}
        self.faq_result_wo_pl = {}
        self.top1_kb = None
        self.top1_kb_sim = 0.0
        self.top4_kb_list = []
        self.faqs_wo_pl = []
        self.avatar_message = ""
        self.response_data = {}
        self.final_result = {}
    
    @timed(task_name="tech_agent_handler_run")
    async def run(self) -> Dict[str, Any]:
        """
        Main processing flow for tech agent.
        
        Returns:
            Final response dictionary matching original format
        """
        log_json = json.dumps(
            self.user_input.model_dump(), ensure_ascii=False, indent=2
        )
        logger.info(f"\n[Agent 啟動] 輸入內容: {log_json}")
        
        await self._initialize()
        await self._process_history()
        await self._get_user_and_scope_info()
        await self._search_knowledge_base()
        self._process_kb_results()
        await self._generate_response()
        await self._log_and_save_results()
        
        return self.final_result
    
    @timed(task_name="initialize")
    async def _initialize(self) -> None:
        """Initialize chat session and load basic information."""
        # Get chat history and related info
        (
            self.his_inputs,
            self.chat_count,
            self.user_info,
            self.last_bot_scope,
            self.last_extract_output
        ) = await self.repository.get_chat_history(
            self.user_input.session_id,
            self.user_input.user_input
        )
        
        # Get latest hint
        self.last_hint = await self.repository.get_latest_hint(
            self.user_input.session_id
        )
        
        # Get language
        self.lang = await self.repository.get_language_by_websitecode(
            self.user_input.websitecode
        )
        
        log_json = json.dumps({
            "his_inputs": self.his_inputs,
            "chat_count": self.chat_count,
            "user_info": self.user_info,
            "last_bot_scope": self.last_bot_scope,
            "last_extract_output": self.last_extract_output
        }, ensure_ascii=False, indent=2)
        logger.info(f"\n[歷史對話]\n{log_json}")
        
        # Ensure valid IDs
        (
            self.user_input.session_id,
            self.user_input.chat_id,
            self.user_input.cus_id
        ) = self.service.ensure_session_and_chat_ids(
            self.user_input.session_id,
            self.user_input.chat_id,
            self.user_input.cus_id
        )
        
        self.render_id = self.service.generate_render_id()
        logger.info(f"last_hint: {self.last_hint}")
        
        # Set default user info if not exists
        if not self.user_info:
            self.user_info = {
                "main_product_category": "",
                "first_time": True
            }
        
        # Update user info if product line changed
        if (self.user_input.product_line and
                self.last_bot_scope != self.user_input.product_line):
            self.user_info["main_product_category"] = self.user_input.product_line
            self.user_info["first_time"] = True
    
    @timed(task_name="process_history")
    async def _process_history(self) -> None:
        """Process chat history."""
        if len(self.his_inputs) <= 1:
            logger.info(f"his_inputs : {self.his_inputs}")
            return
        
        # TODO: Implement sentence group classification when service available
        # from src.services.sentence_group_classification import SentenceGroupClassification
        # sentence_group = SentenceGroupClassification(config=config)
        # results_related = await sentence_group.sentence_group_classification(self.his_inputs)
        
        logger.info(f"his_inputs : {self.his_inputs}")
    
    @timed(task_name="get_user_and_scope_info")
    async def _get_user_and_scope_info(self) -> None:
        """Get user info, search info, and determine bot scope."""
        # TODO: Implement user info extraction when service available
        # from src.core.chat_flow import ChatFlow
        # chat_flow = ChatFlow(data=self.user_input, last_hint=self.last_hint, container=containers)
        # user_info_dict = await chat_flow.get_userInfo(his_inputs=self.his_inputs)
        # search_info = await chat_flow.get_searchInfo(self.his_inputs)
        
        # Mock implementation
        user_info_dict = {}
        self.search_info = self.his_inputs[-1] if self.his_inputs else self.user_input.user_input
        
        log_json = json.dumps(user_info_dict, ensure_ascii=False, indent=2)
        logger.info(f"\n[使用者資訊]\n{log_json}")
        
        # Determine bot scope
        self.bot_scope_chat = self.user_input.product_line or self.last_bot_scope
        logger.info(f"\n[Bot Scope 判斷] {self.bot_scope_chat}")
    
    @timed(task_name="search_knowledge_base")
    async def _search_knowledge_base(self) -> None:
        """Search knowledge base with product line."""
        # TODO: Implement service discriminator when available
        # from src.services.service_discriminator_merge_input import ServiceDiscriminator
        # sd = ServiceDiscriminator(redis_config, base_service)
        # response = await sd.service_discreminator_with_productline(...)
        
        # Mock implementation with realistic structure
        self.faq_result = {
            "faq": ["FAQ001", "FAQ002", "FAQ003"],
            "cosineSimilarity": [0.92, 0.88, 0.85],
            "productLine": ["notebook", "notebook", "notebook"]
        }
        
        self.faq_result_wo_pl = {
            "faq": ["FAQ001", "FAQ002", "FAQ003", "FAQ004"],
            "cosineSimilarity": [0.92, 0.88, 0.85, 0.82],
            "productLine": ["notebook", "notebook", "desktop", "phone"]
        }
        
        log_json = json.dumps({
            "faq_result": self.faq_result,
            "faq_result_wo_pl": self.faq_result_wo_pl
        }, ensure_ascii=False, indent=2)
        logger.info(f"[ServiceDiscriminator] discrimination_productline_response: {log_json}")
    
    @timed(task_name="process_kb_results")
    def _process_kb_results(self) -> None:
        """Process and filter results from KB search."""
        (
            self.top4_kb_list,
            self.top1_kb,
            self.top1_kb_sim
        ) = self.service.process_kb_results(self.faq_result)
        
        self.faqs_wo_pl = self.service.prepare_faqs_wo_pl(self.faq_result_wo_pl)
    
    @timed(task_name="generate_response")
    async def _generate_response(self) -> None:
        """Generate the final response based on processed data."""
        if not self.bot_scope_chat:
            await self._handle_no_product_line()
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            await self._handle_high_similarity()
        else:
            await self._handle_low_similarity()
    
    @timed(task_name="handle_no_product_line")
    async def _handle_no_product_line(self) -> None:
        """Handle no product line case - ask for product line clarification."""
        logger.info("\n[無產品線] 進行產品線追問")
        
        # TODO: Implement avatar response when service available
        # from src.services.service_process import ServiceProcess
        # service_process = ServiceProcess(system_code=self.user_input.system_code, container=containers)
        # avatar_response = await service_process.ts_rag.reply_with_faq_gemini_sys_avatar(...)
        
        # Mock avatar response
        self.avatar_message = "我會協助您解決技術問題。請先告訴我您使用的產品類型，這樣我才能提供更準確的協助。"
        
        # TODO: Implement product line reask when service available
        # ask_response, rag_response = await service_process.technical_support_productline_reask(...)
        
        # Mock implementation
        relative_questions = [
            {
                "title": "notebook",
                "title_name": "筆記型電腦",
                "icon": "💻"
            },
            {
                "title": "desktop",
                "title_name": "桌上型電腦",
                "icon": "🖥️"
            },
            {
                "title": "phone",
                "title_name": "手機",
                "icon": "📱"
            }
        ]
        
        await self.repository.insert_hint_data(
            session_id=self.user_input.session_id,
            intent_hints=relative_questions,
            search_info=self.search_info,
            hint_type="productline-reask"
        )
        
        self.response_data = self.service.build_response_data(
            status=200,
            response_type="reask",
            message="ReAsk: Need product line clarification",
            output={
                "answer": "請選擇您的產品類型",
                "ask_flag": True,
                "hint_candidates": relative_questions,
                "kb": {}
            }
        )
        
        self.final_result = self.service.build_no_product_line_response(
            self.render_id,
            self.avatar_message,
            relative_questions
        )
    
    @timed(task_name="handle_high_similarity")
    async def _handle_high_similarity(self) -> None:
        """Handle high similarity case - provide direct answer with KB content."""
        logger.info(
            f"\n[相似度高於門檻] 相似度={self.top1_kb_sim}，建立 Hint 回應"
        )
        
        # TODO: Implement RAG response when service available
        # from src.services.service_process import ServiceProcess
        # service_process = ServiceProcess(system_code=self.user_input.system_code, container=containers)
        # rag_response = await service_process.technical_support_hint_create(...)
        
        # Mock RAG content
        content = {
            "ask_content": "根據您的問題，這是相關的技術支援內容。",
            "title": "筆電登入畫面卡住問題排除",
            "content": "如果您的筆電卡在登入畫面，請嘗試以下步驟...",
            "link": "https://www.asus.com/support/faq/123456"
        }
        
        # Mock avatar response
        self.avatar_message = "我找到了相關的技術文件，應該可以幫助您解決這個問題。"
        
        relative_questions = []
        
        info = {
            "top1_kb": self.top1_kb,
            "top1_similarity": self.top1_kb_sim,
            "response_source": "knowledge_base",
            "exec_time": 0.5
        }
        
        self.response_data = self.service.build_response_data(
            status=200,
            response_type="answer",
            message="RAG Response",
            output={
                "answer": content.get("ask_content", ""),
                "ask_flag": False,
                "hint_candidates": relative_questions,
                "kb": {
                    "kb_no": str(info.get("top1_kb", "")),
                    "title": content.get("title", ""),
                    "similarity": float(info.get("top1_similarity", 0.0) or 0.0),
                    "source": info.get("response_source", ""),
                    "exec_time": float(info.get("exec_time", 0.0) or 0.0)
                }
            }
        )
        
        self.final_result = self.service.build_high_similarity_response(
            self.render_id,
            self.avatar_message,
            content
        )
    
    @timed(task_name="handle_low_similarity")
    async def _handle_low_similarity(self) -> None:
        """Handle low similarity case - handoff to human agent."""
        logger.info(f"\n[相似度低於門檻] 相似度={self.top1_kb_sim}，轉人工")
        
        # Mock avatar response
        self.avatar_message = "抱歉，我需要更多資訊才能準確協助您。"
        
        kb_title = ""
        if self.top1_kb and self.repository.KB_mappings:
            kb_data = self.repository.KB_mappings.get(
                f"{self.top1_kb}_{self.lang}", {}
            )
            kb_title = kb_data.get("title", "")
        
        self.response_data = self.service.build_response_data(
            status=200,
            response_type="handoff",
            message="相似度低，建議轉人工",
            output={
                "answer": "",
                "ask_flag": False,
                "hint_candidates": [],
                "kb": {
                    "kb_no": str(self.top1_kb or ""),
                    "title": kb_title,
                    "similarity": float(self.top1_kb_sim or 0.0),
                    "source": "",
                    "exec_time": 0.0
                }
            }
        )
        
        self.final_result = self.service.build_low_similarity_response(
            self.render_id,
            self.avatar_message
        )
    
    @timed(task_name="log_and_save_results")
    async def _log_and_save_results(self) -> None:
        """Log and save the final results."""
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)
        logger.info(f"\n[執行時間] tech_agent_api 共耗時 {exec_time} 秒\n")
        
        cosmos_data = {
            "id": f"{self.user_input.cus_id}-{self.user_input.session_id}-{self.user_input.chat_id}",
            "cus_id": self.user_input.cus_id,
            "session_id": self.user_input.session_id,
            "chat_id": self.user_input.chat_id,
            "createDate": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "user_input": self.user_input.user_input,
            "websitecode": self.user_input.websitecode,
            "product_line": self.user_input.product_line,
            "system_code": self.user_input.system_code,
            "user_info": {},
            "process_info": {
                "bot_scope": self.bot_scope_chat,
                "search_info": self.search_info,
                "is_follow_up": False,
                "faq_pl": self.faq_result,
                "faq_wo_pl": self.faq_result_wo_pl,
                "language": self.lang,
                "last_info": {
                    "prev_q": "",
                    "prev_a": "",
                    "kb_no": "",
                },
            },
            "final_result": self.final_result,
            "extract": self.response_data,
            "total_time": exec_time
        }
        
        await self.repository.insert_result_data(cosmos_data)
        
        log_json = json.dumps(cosmos_data, ensure_ascii=False, indent=2)
        logger.info(f"\n[Cosmos DB] 寫入資料: {log_json}\n")
