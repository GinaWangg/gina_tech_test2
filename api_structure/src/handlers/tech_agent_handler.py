"""Tech agent handler with core processing logic.

This module implements the main tech agent processing logic following
AOCC FastAPI layered architecture standards.
"""

import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from api_structure.core.models import (
    TechAgentInput,
    TechAgentResponse,
    TechAgentOutput,
    KBInfo
)
from api_structure.core.timer import timed
from api_structure.core.exception_handlers import (
    AbortException,
    WarningException
)
from api_structure.core.logger import get_log_context
from api_structure.src.clients.tech_agent_container import (
    TechAgentContainer
)


# Thresholds from original implementation
TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class TechAgentHandler:
    """Handler for tech agent processing logic.
    
    This class implements the complete tech agent flow including:
    - Chat history initialization
    - User info and scope determination
    - Knowledge base search
    - Response generation based on similarity scores
    """
    
    def __init__(
        self,
        container: TechAgentContainer,
        user_input: TechAgentInput
    ):
        """Initialize handler with container and input.
        
        Args:
            container: Dependency container with services.
            user_input: User input model.
        """
        self.container = container
        self.user_input = user_input
        self.start_time = time.perf_counter()
        
        # Initialize processing state
        self.his_inputs: List[str] = []
        self.chat_count: int = 0
        self.user_info: Optional[Dict] = None
        self.last_bot_scope: Optional[str] = None
        self.last_extract_output: Dict = {}
        self.last_hint: Optional[Dict] = None
        self.lang: str = "zh-tw"
        
        # Processing results
        self.bot_scope_chat: Optional[str] = None
        self.search_info: str = ""
        self.user_info_dict: Dict = {}
        self.faq_result: Dict = {}
        self.faq_result_wo_pl: Dict = {}
        
        # KB search results
        self.top1_kb: Optional[str] = None
        self.top1_kb_sim: float = 0.0
        self.top4_kb_list: List[str] = []
        self.faqs_wo_pl: List[Dict] = []
        
        # Response data
        self.response_data: Dict[str, Any] = {}
        self.render_id: str = str(uuid.uuid4())
    
    @timed(task_name="tech_agent_process")
    async def run(self) -> TechAgentResponse:
        """Execute the complete tech agent processing flow.
        
        Returns:
            TechAgentResponse with results.
        
        Raises:
            AbortException: If a critical error occurs.
            WarningException: If a recoverable error occurs.
        """
        # Log input
        try:
            ctx = get_log_context()
            if ctx.extract_log is None:
                ctx.extract_log = {}
            ctx.extract_log["user_input"] = self.user_input.model_dump()
        except Exception:
            # If logging fails, continue without logging
            pass
        
        # Main processing pipeline
        await self._initialize_chat()
        await self._process_history()
        await self._get_user_and_scope_info()
        await self._search_knowledge_base()
        self._process_kb_results()
        await self._generate_response()
        await self._log_and_save_results()
        
        # Build final response
        return self._build_response()
    
    async def _initialize_chat(self) -> None:
        """Initialize chat session and retrieve history.
        
        Retrieves chat history, hint data, and language settings.
        Sets default values if session is new.
        """
        settings = self.container.cosmos_settings
        
        # Get chat history and settings
        results, self.last_hint, self.lang = (
            await settings.create_GPT_messages(
                self.user_input.session_id,
                self.user_input.user_input
            ),
            await settings.get_latest_hint(
                self.user_input.session_id
            ),
            await settings.get_language_by_websitecode_dev(
                self.user_input.websitecode
            )
        )
        
        (
            self.his_inputs,
            self.chat_count,
            self.user_info,
            self.last_bot_scope,
            self.last_extract_output
        ) = results
        
        # Set defaults if not provided
        if not self.user_input.session_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.session_id = f"agent-{tail}"
        
        if not self.user_input.cus_id:
            self.user_input.cus_id = "test"
        
        if not self.user_input.chat_id:
            tail = str(uuid.uuid4()).split("-", 1)[1]
            self.user_input.chat_id = f"agent-{tail}"
        
        # Initialize default user info if needed
        if not self.user_info:
            self.user_info = {
                "our_brand": "ASUS",
                "location": None,
                "main_product_category": self.user_input.product_line,
                "sub_product_category": None,
                "first_time": True,
            }
        
        # Update user info if product line changed
        if (self.user_input.product_line and
                self.last_bot_scope != self.user_input.product_line):
            self.user_info["main_product_category"] = (
                self.user_input.product_line
            )
            self.user_info["first_time"] = True
    
    async def _process_history(self) -> None:
        """Process chat history for context.
        
        Groups related sentences together if multiple messages exist.
        """
        if len(self.his_inputs) <= 1:
            return
        
        # Get sentence grouping
        results_related = (
            await self.container.sentence_group_classification
            .sentence_group_classification(self.his_inputs)
        )
        
        # Process groups
        if results_related:
            groups = results_related.get("groups", [])
            if groups:
                statements = groups[-1].get("statements") or []
                latest_group_statements = [
                    s for s in statements if isinstance(s, str)
                ]
                if latest_group_statements:
                    self.his_inputs = latest_group_statements.copy()
    
    async def _get_user_and_scope_info(self) -> None:
        """Get user information and determine bot scope.
        
        Extracts user info from conversation and determines the
        appropriate product line scope for KB search.
        """
        # Mock user info extraction
        # TODO: Enable when environment ready
        # Original logic in src/core/chat_flow.py get_userInfo()
        # user_info = await chat_flow.get_userInfo(self.his_inputs)
        self.user_info_dict = {}
        
        # Mock search info extraction
        # TODO: Enable when environment ready
        # Original logic in src/core/chat_flow.py get_searchInfo()
        # search_info = await chat_flow.get_searchInfo(self.his_inputs)
        self.search_info = self.his_inputs[-1] if self.his_inputs else ""
        
        # Determine bot scope
        # Check if user clicked a product line hint
        if (self.last_hint and
                self.last_hint.get("hintType") == "productline-reask"):
            for hint in self.last_hint.get("intentHints", []):
                if self.user_input.user_input == hint.get("question"):
                    self.bot_scope_chat = hint.get("title")
                    return
        
        # Use provided product line or determine from user info
        if self.user_input.product_line:
            self.bot_scope_chat = self.user_input.product_line
        elif self.user_info_dict.get("main_product_category"):
            category = self.user_info_dict["main_product_category"]
            self.bot_scope_chat = (
                await self.container.redis_config.get_productline(
                    category, self.user_input.websitecode
                )
            )
        elif self.user_info_dict.get("sub_product_category"):
            category = self.user_info_dict["sub_product_category"]
            self.bot_scope_chat = (
                await self.container.redis_config.get_productline(
                    category, self.user_input.websitecode
                )
            )
        else:
            self.bot_scope_chat = self.last_bot_scope
    
    async def _search_knowledge_base(self) -> None:
        """Search knowledge base with current scope.
        
        Performs KB search using service discriminator with
        optional product line filtering.
        """
        response = (
            await self.container.sd
            .service_discreminator_with_productline(
                user_question_english=self.search_info,
                site=self.user_input.websitecode,
                specific_kb_mappings=self.container.specific_kb_mappings,
                productLine=self.bot_scope_chat,
            )
        )
        
        self.faq_result = response[0]
        self.faq_result_wo_pl = response[1]
    
    def _process_kb_results(self) -> None:
        """Process and filter KB search results.
        
        Filters results by similarity threshold and extracts top
        candidates for response generation.
        """
        faq_list = self.faq_result.get("faq", [])
        sim_list = self.faq_result.get("cosineSimilarity", [])
        
        # Get top KB results above threshold
        self.top4_kb_list = [
            faq for faq, sim in zip(faq_list, sim_list)
            if sim >= KB_THRESHOLD
        ][:3]
        
        # Get top 1 result
        self.top1_kb = faq_list[0] if faq_list else None
        self.top1_kb_sim = sim_list[0] if sim_list else 0.0
        
        # Process results without product line
        self.faqs_wo_pl = [
            {
                "kb_no": faq,
                "cosineSimilarity": sim,
                "productLine": pl
            }
            for faq, sim, pl in zip(
                self.faq_result_wo_pl.get("faq", []),
                self.faq_result_wo_pl.get("cosineSimilarity", []),
                self.faq_result_wo_pl.get("productLine", []),
            )
        ]
    
    async def _generate_response(self) -> None:
        """Generate final response based on processing results.
        
        Routes to appropriate response handler based on:
        - Product line availability
        - KB similarity score
        """
        if not self.bot_scope_chat:
            await self._handle_no_product_line()
        elif self.top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            await self._handle_high_similarity()
        else:
            await self._handle_low_similarity()
    
    async def _handle_no_product_line(self) -> None:
        """Handle case where product line is not determined.
        
        Generates product line clarification request with hints.
        """
        # TODO: Enable when environment ready
        # Original: await service_process.technical_support_productline_reask()
        
        # Mock product line reask
        relative_questions = []
        
        # Save hint data
        await self.container.cosmos_settings.insert_hint_data(
            chatflow_data=self.user_input,
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
                "answer": "",
                "ask_flag": True,
                "hint_candidates": relative_questions,
                "kb": {}
            }
        }
    
    async def _handle_high_similarity(self) -> None:
        """Handle case with high KB similarity.
        
        Generates answer with KB content and related questions.
        """
        # TODO: Enable when environment ready
        # Original: await service_process.technical_support_hint_create()
        
        # Mock KB content
        kb_info = self.container.KB_mappings.get(
            f"{self.top1_kb}_{self.lang}", {}
        )
        
        # Build response
        self.response_data = {
            "status": 200,
            "type": "answer",
            "message": "RAG Response",
            "output": {
                "answer": "",
                "ask_flag": False,
                "hint_candidates": [],
                "kb": {
                    "kb_no": str(self.top1_kb or ""),
                    "title": kb_info.get("title", ""),
                    "similarity": float(self.top1_kb_sim or 0.0),
                    "source": "",
                    "exec_time": 0.0
                }
            }
        }
    
    async def _handle_low_similarity(self) -> None:
        """Handle case with low KB similarity.
        
        Suggests handoff to human agent.
        """
        # Get KB info if available
        kb_info = self.container.KB_mappings.get(
            f"{self.top1_kb}_{self.lang}", {}
        )
        
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
                    "title": kb_info.get("title", ""),
                    "similarity": float(self.top1_kb_sim or 0.0),
                    "source": "",
                    "exec_time": 0.0
                }
            }
        }
    
    async def _log_and_save_results(self) -> None:
        """Log execution time and save results to Cosmos DB.
        
        Constructs complete data record and saves to database.
        """
        end_time = time.perf_counter()
        exec_time = round(end_time - self.start_time, 2)
        
        # Build Cosmos DB data
        cosmos_data = {
            "id": (
                f"{self.user_input.cus_id}-"
                f"{self.user_input.session_id}-"
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
                "faq_pl": self.faq_result,
                "faq_wo_pl": self.faq_result_wo_pl,
                "language": self.lang,
            },
            "extract": self.response_data,
            "total_time": exec_time
        }
        
        # Save to Cosmos DB
        await self.container.cosmos_settings.insert_data(cosmos_data)
        
        # Log to context
        try:
            ctx = get_log_context()
            if ctx.extract_log is None:
                ctx.extract_log = {}
            ctx.extract_log["exec_time"] = exec_time
            ctx.extract_log["cosmos_data"] = cosmos_data
        except Exception:
            # If logging fails, continue without logging
            pass
    
    def _build_response(self) -> TechAgentResponse:
        """Build final API response.
        
        Returns:
            TechAgentResponse with all results.
        """
        output = self.response_data.get("output", {})
        kb_data = output.get("kb", {})
        
        return TechAgentResponse(
            status=self.response_data.get("status", 200),
            type=self.response_data.get("type", "answer"),
            message=self.response_data.get("message", "OK"),
            output=TechAgentOutput(
                answer=output.get("answer", ""),
                ask_flag=output.get("ask_flag", False),
                hint_candidates=output.get("hint_candidates", []),
                kb=KBInfo(
                    kb_no=kb_data.get("kb_no", ""),
                    title=kb_data.get("title", ""),
                    similarity=kb_data.get("similarity", 0.0),
                    source=kb_data.get("source", ""),
                    exec_time=kb_data.get("exec_time", 0.0)
                )
            )
        )
