"""
Tech Agent Service - Core business logic.
This service handles the main flow for technical support agent.
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from core.timer import timed
from src.repositories.data_repository import DataRepository
from src.schemas.tech_agent import TechAgentRequest


# Constants from original implementation
TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentService:
    """
    Main service for technical agent processing.
    Handles the complete flow from user input to response generation.
    """
    
    def __init__(self, repository: DataRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: Data repository for external dependencies
        """
        self.repository = repository
        
        # State variables for processing
        self.start_time = 0.0
        self.render_id = ""
        
        # Chat context
        self.his_inputs: List[str] = []
        self.chat_count = 0
        self.user_info: Optional[Dict] = None
        self.last_bot_scope: Optional[str] = None
        self.last_extract_output: Dict = {}
        self.last_hint: Optional[Dict] = None
        self.lang = "zh-tw"
        
        # Processing results
        self.user_info_dict: Dict = {}
        self.bot_scope_chat: Optional[str] = None
        self.search_info: Optional[str] = None
        self.is_follow_up = False
        
        # KB search results
        self.faq_result: Dict = {}
        self.faq_result_wo_pl: Dict = {}
        self.top1_kb: Optional[int] = None
        self.top1_kb_sim = 0.0
        self.top4_kb_list: List[int] = []
        self.faqs_wo_pl: List[Dict] = []
        
        # Response data
        self.response_type = ""
        self.avatar_response = ""
        self.response_data: Dict = {}
        self.final_result: Dict = {}
        
        # Previous interaction data
        self.prev_q = ""
        self.prev_a = ""
        self.kb_no = ""
    
    @timed(task_name="tech_agent_process")
    async def process(
        self,
        request: TechAgentRequest
    ) -> Dict[str, Any]:
        """
        Main processing method for tech agent.
        
        Args:
            request: Tech agent request data
            
        Returns:
            Complete response with final_result and cosmos_data
        """
        self.start_time = time.perf_counter()
        self.render_id = str(uuid.uuid4())
        
        # Step 1: Initialize chat context
        await self._initialize_chat(request)
        
        # Step 2: Process history for follow-up detection
        await self._process_history()
        
        # Step 3: Start avatar response generation (async)
        avatar_task = asyncio.create_task(
            self._generate_avatar_response(self.his_inputs[-1])
        )
        
        # Step 4: Get user info and bot scope
        await self._get_user_and_scope_info(request)
        
        # Step 5: Search knowledge base
        await self._search_knowledge_base(request)
        
        # Step 6: Process KB results
        self._process_kb_results()
        
        # Step 7: Generate final response
        await self._generate_response(request, avatar_task)
        
        # Step 8: Prepare cosmos data for logging
        cosmos_data = await self._prepare_cosmos_data(request)
        
        # Step 9: Save to Cosmos (async, don't wait)
        asyncio.create_task(self.repository.insert_data(cosmos_data))
        
        return {
            "final_result": self.final_result,
            "cosmos_data": cosmos_data
        }
    
    async def _initialize_chat(self, request: TechAgentRequest) -> None:
        """Initialize chat context and retrieve history."""
        # Parallel fetch of context data
        messages_task = self.repository.create_gpt_messages(
            request.session_id,
            request.user_input
        )
        hint_task = self.repository.get_latest_hint(request.session_id)
        lang_task = self.repository.get_language_by_websitecode(
            request.websitecode
        )
        
        # Wait for all context data
        results = await asyncio.gather(
            messages_task,
            hint_task,
            lang_task
        )
        
        (
            self.his_inputs,
            self.chat_count,
            self.user_info,
            self.last_bot_scope,
            self.last_extract_output
        ) = results[0]
        
        self.last_hint = results[1]
        self.lang = results[2]
        
        # Set default user info if not exists
        if not self.user_info:
            self.user_info = {
                "main_product_category": request.product_line or None,
                "sub_product_category": None
            }
        
        # Update user info if product_line provided and changed
        if (request.product_line and 
            self.last_bot_scope != request.product_line):
            self.user_info["main_product_category"] = request.product_line
    
    async def _process_history(self) -> None:
        """Process chat history for context."""
        if len(self.his_inputs) <= 1:
            self.is_follow_up = False
            return
        
        # Get previous interaction data
        self.prev_q = str(self.his_inputs[-2])
        self.prev_a = str(self.last_extract_output.get("answer", ""))
        self.kb_no = str(
            self.last_extract_output.get("kb", {}).get("kb_no", "")
        )
        
        # Sentence group classification
        results = await self.repository.sentence_group_classification(
            self.his_inputs
        )
        
        groups = results.get("groups", [])
        if groups:
            statements = groups[-1].get("statements", [])
            latest_statements = [s for s in statements if isinstance(s, str)]
            if latest_statements:
                self.his_inputs = latest_statements.copy()
        
        # Check if this is a follow-up question
        # TODO: Enable when environment ready
        # For now, assume not a follow-up
        self.is_follow_up = False
    
    async def _generate_avatar_response(
        self,
        user_input: str
    ) -> str:
        """
        Generate avatar response text.
        
        # TODO: Enable when environment ready
        # Would call Gemini/GPT for avatar personality response
        
        Returns:
            Avatar response text
        """
        # Stubbed avatar responses based on scenario
        responses = {
            "zh-tw": "喔，筆電卡在登入畫面喔，這真的有點麻煩耶。嗯...",
            "en": "Oh, your laptop is stuck on the login screen...",
        }
        return responses.get(self.lang, responses["zh-tw"])
    
    async def _get_user_and_scope_info(
        self,
        request: TechAgentRequest
    ) -> None:
        """Get user information and determine bot scope."""
        # Extract user info from input
        # TODO: Enable when environment ready
        # Would call GPT to extract user info
        self.user_info_dict = {
            "main_product_category": "notebook",
            "sub_product_category": None
        }
        
        # Translate user input to English for search
        self.search_info = await self.repository.translate_text(
            self.his_inputs[-1],
            "en"
        )
        
        # Determine bot scope
        if request.product_line:
            self.bot_scope_chat = request.product_line
        elif self.user_info_dict.get("main_product_category"):
            self.bot_scope_chat = await self.repository.get_productline(
                self.user_info_dict["main_product_category"],
                request.websitecode
            )
        else:
            self.bot_scope_chat = self.last_bot_scope
    
    async def _search_knowledge_base(
        self,
        request: TechAgentRequest
    ) -> None:
        """Search knowledge base for relevant FAQs."""
        response = await self.repository.service_discriminator_with_productline(
            user_question_english=self.search_info or self.his_inputs[-1],
            site=request.websitecode,
            specific_kb_mappings=self.repository.specific_kb_mappings,
            productLine=self.bot_scope_chat
        )
        
        self.faq_result = response[0]
        self.faq_result_wo_pl = response[1]
    
    def _process_kb_results(self) -> None:
        """Process and filter KB search results."""
        faq_list = self.faq_result.get("faq", [])
        sim_list = self.faq_result.get("cosineSimilarity", [])
        
        # Get top 4 KB with similarity >= threshold
        self.top4_kb_list = [
            faq for faq, sim in zip(faq_list, sim_list)
            if sim >= KB_THRESHOLD
        ][:3]
        
        # Get top 1 KB and its similarity
        self.top1_kb = faq_list[0] if faq_list else None
        self.top1_kb_sim = sim_list[0] if sim_list else 0.0
        
        # Process FAQs without product line filter
        self.faqs_wo_pl = [
            {
                "kb_no": faq,
                "cosineSimilarity": sim,
                "productLine": pl
            }
            for faq, sim, pl in zip(
                self.faq_result_wo_pl.get("faq", []),
                self.faq_result_wo_pl.get("cosineSimilarity", []),
                self.faq_result_wo_pl.get("productLine", [])
            )
        ]
    
    async def _generate_response(
        self,
        request: TechAgentRequest,
        avatar_task: asyncio.Task
    ) -> None:
        """Generate the final response based on processing results."""
        if not self.bot_scope_chat:
            # No product line - ask for clarification
            await self._handle_no_product_line(request, avatar_task)
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            # High similarity - provide technical support
            await self._handle_high_similarity(request, avatar_task)
        else:
            # Low similarity - suggest handoff to human
            await self._handle_low_similarity(request, avatar_task)
    
    async def _handle_no_product_line(
        self,
        request: TechAgentRequest,
        avatar_task: asyncio.Task
    ) -> None:
        """Handle case where product line is not determined."""
        self.response_type = "avatarAskProductLine"
        
        # Wait for avatar response
        self.avatar_response = await avatar_task
        
        # Generate product line options
        # TODO: Enable when environment ready
        # Would call RAG service for product line recommendations
        relative_questions = [
            {
                "title_name": "筆記型電腦",
                "title": "notebook",
                "icon": "laptop"
            },
            {
                "title_name": "桌上型電腦",
                "title": "desktop",
                "icon": "desktop"
            },
            {
                "title_name": "手機",
                "title": "phone",
                "icon": "phone"
            }
        ]
        
        # Save hint for next interaction
        await self.repository.insert_hint_data(
            chatflow_data=request,
            intent_hints=relative_questions,
            search_info=self.search_info or "",
            hint_type="productline-reask"
        )
        
        # Build response
        self.response_data = {
            "status": 200,
            "type": "reask",
            "message": "ReAsk: Need product line clarification",
            "output": {
                "answer": "我注意到你提到的問題，為了給你最準確的協助，能告訴我是哪個產品類別嗎？",
                "ask_flag": True,
                "hint_candidates": relative_questions,
                "kb": {
                    "kb_no": "",
                    "title": "",
                    "similarity": 0.0,
                    "source": "",
                    "exec_time": 0.0
                }
            }
        }
        
        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarAskProductLine",
                    "message": self.avatar_response,
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
        request: TechAgentRequest,
        avatar_task: asyncio.Task
    ) -> None:
        """Handle case where KB similarity is high."""
        self.response_type = "avatarTechnicalSupport"
        
        # Get KB content
        kb_key = f"{self.top1_kb}_{self.lang}"
        kb_data = self.repository.KB_mappings.get(kb_key, {})
        title = kb_data.get("title", "")
        content = kb_data.get("content", "")
        
        # Build link based on system code
        if request.system_code.lower() == "rog":
            link = f"https://rog.asus.com/{request.websitecode}/support/FAQ/{self.top1_kb}"
        else:
            link = f"https://www.asus.com/{request.websitecode}/support/FAQ/{self.top1_kb}"
        
        # Generate technical response with RAG
        # TODO: Enable when environment ready
        # Would call RAG service for technical content generation
        rag_content = {
            "ask_content": content[:500] if content else "請參考以下KB文章...",
            "title": title,
            "content": content,
            "link": link
        }
        
        # Wait for avatar response
        self.avatar_response = await avatar_task
        
        # Build response
        self.response_data = {
            "status": 200,
            "type": "answer",
            "message": "RAG Response",
            "output": {
                "answer": rag_content["ask_content"],
                "ask_flag": False,
                "hint_candidates": [],
                "kb": {
                    "kb_no": str(self.top1_kb),
                    "title": title,
                    "similarity": float(self.top1_kb_sim),
                    "source": "KB",
                    "exec_time": 0.0
                }
            }
        }
        
        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarTechnicalSupport",
                    "message": self.avatar_response,
                    "remark": [],
                    "option": [
                        {
                            "type": "faqcards",
                            "cards": [
                                {
                                    "link": link,
                                    "title": title,
                                    "content": content
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    async def _handle_low_similarity(
        self,
        request: TechAgentRequest,
        avatar_task: asyncio.Task
    ) -> None:
        """Handle case where KB similarity is low - suggest handoff."""
        self.response_type = "handoff"
        
        # Wait for avatar response
        self.avatar_response = await avatar_task
        
        # Get KB info for reference
        kb_key = f"{self.top1_kb}_{self.lang}"
        kb_data = self.repository.KB_mappings.get(kb_key, {})
        title = kb_data.get("title", "")
        
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
                    "title": title,
                    "similarity": float(self.top1_kb_sim),
                    "source": "",
                    "exec_time": 0.0
                }
            }
        }
        
        # Fixed suggestion options (from original code)
        suggestion_options = [
            {
                "name": "我想知道 ROG FLOW X16 的規格",
                "value": "我想知道 ROG FLOW X16 的規格",
                "answer": [
                    {"type": "inquireMode", "value": "intent"},
                    {"type": "inquireKey", "value": "specification-consultation"},
                    {"type": "mainProduct", "value": 25323}
                ]
            },
            {
                "name": "請幫我推薦16吋筆電",
                "value": "請幫我推薦16吋筆電",
                "answer": [
                    {"type": "inquireMode", "value": "intent"},
                    {"type": "inquireKey", "value": "purchasing-recommendation-of-asus-products"}
                ]
            },
            {
                "name": "請幫我介紹 ROG Phone 8 的特色",
                "value": "請幫我介紹 ROG Phone 8 的特色",
                "answer": [
                    {"type": "inquireMode", "value": "intent"},
                    {"type": "inquireKey", "value": "specification-consultation"},
                    {"type": "mainProduct", "value": 25323}
                ]
            }
        ]
        
        self.final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarText",
                    "message": self.avatar_response,
                    "remark": [],
                    "option": []
                },
                {
                    "renderId": self.render_id,
                    "stream": False,
                    "type": "avatarAsk",
                    "message": "你可以告訴我像是產品全名、型號，或你想問的活動名稱～比如「ROG Flow X16」或「我想查產品保固到期日」。給我多一點線索，我就能更快幫你找到對的資料，也不會漏掉重點！",
                    "remark": [],
                    "option": suggestion_options
                }
            ]
        }
    
    async def _prepare_cosmos_data(
        self,
        request: TechAgentRequest
    ) -> Dict[str, Any]:
        """Prepare data for Cosmos DB logging."""
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)
        
        cosmos_data = {
            "id": f"{request.cus_id}-{request.session_id}-{request.chat_id}",
            "cus_id": request.cus_id,
            "session_id": request.session_id,
            "chat_id": request.chat_id,
            "createDate": datetime.utcnow().isoformat() + "Z",
            "user_input": request.user_input,
            "websitecode": request.websitecode,
            "product_line": request.product_line,
            "system_code": request.system_code,
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
                    "kb_no": self.kb_no
                }
            },
            "final_result": self.final_result,
            "extract": self.response_data,
            "total_time": exec_time
        }
        
        return cosmos_data
