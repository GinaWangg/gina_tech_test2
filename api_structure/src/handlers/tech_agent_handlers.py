"""
Tech Agent Handlers - Business logic layer.
Contains focused handlers for different aspects of tech agent processing.
"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from api_structure.core.logger import logger
from api_structure.core.timer import timed
from api_structure.src.schemas.tech_agent_schemas import TechAgentInput


TOP1_KB_SIMILARITY_THRESHOLD = 0.87
KB_THRESHOLD = 0.92


class ChatInitHandler:
    """Handler for chat initialization."""

    def __init__(
        self,
        cosmos_repo: Any,
        redis_repo: Any,
        kb_repo: Any
    ):
        """Initialize chat handler."""
        self.cosmos_repo = cosmos_repo
        self.redis_repo = redis_repo
        self.kb_repo = kb_repo

    @timed(task_name="chat_init_handler")
    async def initialize_chat(
        self, user_input: TechAgentInput
    ) -> Dict[str, Any]:
        """
        Initialize chat session and retrieve history.
        
        Args:
            user_input: User input data
            
        Returns:
            Initialization data including history and settings
        """
        # Parallel execution of I/O operations
        messages_task = self.cosmos_repo.create_gpt_messages(
            user_input.session_id, user_input.user_input
        )
        hint_task = self.cosmos_repo.get_latest_hint(user_input.session_id)
        lang_task = self.cosmos_repo.get_language_by_websitecode(
            user_input.websitecode
        )

        # Wait for all results
        (
            (his_inputs, chat_count, user_info, 
             last_bot_scope, last_extract_output),
            last_hint,
            lang
        ) = await messages_task, await hint_task, await lang_task

        # Generate IDs if not provided
        session_id = user_input.session_id or f"agent-{uuid.uuid4()}"
        cus_id = user_input.cus_id or "test"
        chat_id = user_input.chat_id or f"agent-{uuid.uuid4()}"
        render_id = str(uuid.uuid4())

        # Default user info
        if not user_info:
            user_info = {
                "our_brand": "ASUS",
                "location": None,
                "main_product_category": user_input.product_line,
                "sub_product_category": None,
                "first_time": True,
            }

        # Update user info if product line changed
        if (user_input.product_line and
                last_bot_scope != user_input.product_line):
            user_info["main_product_category"] = user_input.product_line
            user_info["first_time"] = True

        logger.info(
            f"[ChatInit] Initialized: session={session_id}, "
            f"chat_count={chat_count}"
        )

        return {
            "his_inputs": his_inputs,
            "chat_count": chat_count,
            "user_info": user_info,
            "last_bot_scope": last_bot_scope,
            "last_extract_output": last_extract_output or {},
            "last_hint": last_hint,
            "lang": lang,
            "session_id": session_id,
            "cus_id": cus_id,
            "chat_id": chat_id,
            "render_id": render_id
        }


class HistoryProcessHandler:
    """Handler for processing chat history."""

    def __init__(self):
        """Initialize history handler."""
        pass

    @timed(task_name="history_process_handler")
    async def process_history(
        self,
        his_inputs: List[str],
        last_extract_output: Dict[str, Any],
        kb_mappings: Dict[str, Any],
        lang: str
    ) -> Dict[str, Any]:
        """
        Process chat history and determine follow-up status.
        
        Args:
            his_inputs: History inputs
            last_extract_output: Last extraction output
            kb_mappings: KB mappings
            lang: Language code
            
        Returns:
            Processed history data
        """
        if len(his_inputs) <= 1:
            logger.info("[History] Single input, no follow-up check needed")
            return {
                "is_follow_up": False,
                "prev_q": "",
                "prev_a": "",
                "kb_no": "",
                "content": "",
                "processed_inputs": his_inputs
            }

        # Prepare data for follow-up check
        prev_q = str(his_inputs[-2])
        prev_a = str(last_extract_output.get("answer", ""))
        kb_no = str(
            last_extract_output.get("kb", {}).get("kb_no", "")
        )
        content = str(
            kb_mappings.get(f"{kb_no}_{lang}", {}).get("content", "")
        )

        # TODO: Enable when environment ready
        # Sentence group classification would go here
        # group_result = await sentence_classifier.classify(his_inputs)
        # Process groups to extract latest statements

        logger.info(
            f"[History] Processed: prev_q exists={bool(prev_q)}, "
            f"kb={kb_no}"
        )

        # Mock follow-up determination
        # In real implementation, this would call GPT for analysis
        is_follow_up = False

        return {
            "is_follow_up": is_follow_up,
            "prev_q": prev_q,
            "prev_a": prev_a,
            "kb_no": kb_no,
            "content": content,
            "processed_inputs": his_inputs
        }


class UserInfoHandler:
    """Handler for user information extraction."""

    def __init__(self, redis_repo: Any, cosmos_repo: Any):
        """Initialize user info handler."""
        self.redis_repo = redis_repo
        self.cosmos_repo = cosmos_repo

    @timed(task_name="user_info_handler")
    async def get_user_and_scope_info(
        self,
        his_inputs: List[str],
        user_info: Dict[str, Any],
        last_bot_scope: Optional[str],
        last_hint: Optional[Dict[str, Any]],
        product_line: str,
        websitecode: str
    ) -> Dict[str, Any]:
        """
        Extract user info and determine bot scope.
        
        Args:
            his_inputs: History inputs
            user_info: Current user info
            last_bot_scope: Last bot scope
            last_hint: Last hint data
            product_line: Product line from input
            websitecode: Website code
            
        Returns:
            User info and scope data
        """
        # TODO: Enable when environment ready
        # user_info_dict = await userinfo_discriminator.extract(his_inputs)
        # search_info = await search_extractor.extract(his_inputs)

        # Mock user info extraction
        user_info_dict = {
            "main_product_category": None,
            "sub_product_category": None
        }

        # Mock search info
        search_info = his_inputs[-1] if his_inputs else ""

        # Check if tech support related for product line reask
        tech_support_related = "true"
        if last_hint and last_hint.get("hintType") == "productline-reask":
            # TODO: Enable when environment ready
            # tech_support_related = await gpt_check(his_inputs[-1])
            tech_support_related = "true"

        # Determine search info
        if tech_support_related == "false" and last_hint:
            search_info = last_hint.get("searchInfo", search_info)

        # Determine bot scope
        bot_scope_chat = product_line
        if not bot_scope_chat:
            # Check hint for product line
            if last_hint and \
               last_hint.get("hintType") == "productline-reask":
                for hint in last_hint.get("intentHints", []):
                    if his_inputs[-1] == hint.get("question", ""):
                        bot_scope_chat = hint.get("title")
                        break

            # Get from user info
            if not bot_scope_chat:
                if user_info_dict.get("main_product_category"):
                    bot_scope_chat = await self.redis_repo.get_productline(
                        user_info_dict["main_product_category"],
                        websitecode
                    )
                elif user_info_dict.get("sub_product_category"):
                    bot_scope_chat = await self.redis_repo.get_productline(
                        user_info_dict["sub_product_category"],
                        websitecode
                    )

            # Validate against PL mappings
            pl_list = self.cosmos_repo.get_pl_list(websitecode)
            if bot_scope_chat not in pl_list:
                bot_scope_chat = last_bot_scope

        logger.info(
            f"[UserInfo] bot_scope={bot_scope_chat}, "
            f"search_info={search_info[:50] if search_info else 'N/A'}"
        )

        return {
            "user_info_dict": user_info_dict,
            "search_info": search_info,
            "bot_scope_chat": bot_scope_chat
        }


class KBSearchHandler:
    """Handler for knowledge base search."""

    def __init__(self, kb_repo: Any):
        """Initialize KB search handler."""
        self.kb_repo = kb_repo

    @timed(task_name="kb_search_handler")
    async def search_knowledge_base(
        self,
        search_info: str,
        websitecode: str,
        bot_scope_chat: Optional[str],
        specific_kb_mappings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Search knowledge base for relevant FAQs.
        
        Args:
            search_info: Search query
            websitecode: Website code
            bot_scope_chat: Bot scope/product line
            specific_kb_mappings: Specific KB mappings
            
        Returns:
            Search results with and without product line filter
        """
        faq_result, faq_result_wo_pl = \
            await self.kb_repo.search_kb_with_productline(
                user_question=search_info,
                site=websitecode,
                productline=bot_scope_chat,
                specific_kb_mappings=specific_kb_mappings
            )

        # Process results
        faq_list = faq_result.get("faq", [])
        sim_list = faq_result.get("cosineSimilarity", [])

        # Filter by threshold
        top4_kb_list = [
            faq for faq, sim in zip(faq_list, sim_list)
            if sim >= KB_THRESHOLD
        ][:3]

        top1_kb = faq_list[0] if faq_list else None
        top1_kb_sim = sim_list[0] if sim_list else 0.0

        # Process results without product line
        faqs_wo_pl = [
            {
                "kb_no": faq,
                "cosineSimilarity": sim,
                "productLine": pl
            }
            for faq, sim, pl in zip(
                faq_result_wo_pl.get("faq", []),
                faq_result_wo_pl.get("cosineSimilarity", []),
                faq_result_wo_pl.get("productLine", []),
            )
        ]

        logger.info(
            f"[KBSearch] top1_kb={top1_kb}, "
            f"similarity={top1_kb_sim:.3f}, "
            f"top4_count={len(top4_kb_list)}"
        )

        return {
            "faq_result": faq_result,
            "faq_result_wo_pl": faq_result_wo_pl,
            "top1_kb": top1_kb,
            "top1_kb_sim": top1_kb_sim,
            "top4_kb_list": top4_kb_list,
            "faqs_wo_pl": faqs_wo_pl
        }


class ResponseGenerationHandler:
    """Handler for generating responses."""

    def __init__(
        self,
        cosmos_repo: Any,
        redis_repo: Any,
        kb_repo: Any
    ):
        """Initialize response handler."""
        self.cosmos_repo = cosmos_repo
        self.redis_repo = redis_repo
        self.kb_repo = kb_repo

    @timed(task_name="response_generation_handler")
    async def generate_response(
        self,
        bot_scope_chat: Optional[str],
        top1_kb: Optional[str],
        top1_kb_sim: float,
        top4_kb_list: List[str],
        faqs_wo_pl: List[Dict[str, Any]],
        his_inputs: List[str],
        search_info: str,
        lang: str,
        websitecode: str,
        system_code: str,
        user_input_text: str,
        render_id: str
    ) -> Dict[str, Any]:
        """
        Generate appropriate response based on KB results.
        
        Args:
            bot_scope_chat: Bot scope/product line
            top1_kb: Top KB number
            top1_kb_sim: Top KB similarity
            top4_kb_list: Top 4 KB list
            faqs_wo_pl: FAQs without product line filter
            his_inputs: History inputs
            search_info: Search information
            lang: Language code
            websitecode: Website code
            system_code: System code
            user_input_text: User input text
            render_id: Render ID
            
        Returns:
            Generated response data
        """
        # Determine response type
        if not bot_scope_chat:
            return await self._handle_no_product_line(
                faqs_wo_pl, user_input_text, websitecode,
                lang, system_code, his_inputs, search_info, render_id
            )
        elif top1_kb_sim > TOP1_KB_SIMILARITY_THRESHOLD:
            return await self._handle_high_similarity(
                top1_kb, top1_kb_sim, top4_kb_list, his_inputs,
                search_info, lang, websitecode, system_code, render_id
            )
        else:
            return await self._handle_low_similarity(
                top1_kb, top1_kb_sim, his_inputs, lang, render_id
            )

    async def _handle_no_product_line(
        self,
        faqs_wo_pl: List[Dict[str, Any]],
        user_input: str,
        websitecode: str,
        lang: str,
        system_code: str,
        his_inputs: List[str],
        search_info: str,
        render_id: str
    ) -> Dict[str, Any]:
        """Handle case when product line is not determined."""
        logger.info("[Response] No product line - asking for clarification")

        # TODO: Enable when environment ready
        # ask_response, rag_response = await ts_service.productline_reask(...)
        # avatar_response = await avatar_service.generate(...)

        # Mock avatar response
        avatar_response = "請問您使用的是筆記型電腦、桌上型電腦還是其他產品呢？"

        # Mock relative questions
        relative_questions = [
            {
                "question": "筆記型電腦",
                "title": "notebook",
                "title_name": "筆記型電腦",
                "icon": "laptop"
            },
            {
                "question": "桌上型電腦",
                "title": "desktop",
                "title_name": "桌上型電腦",
                "icon": "desktop"
            }
        ]

        # TODO: Enable when environment ready
        # await cosmos_repo.insert_hint_data(...)

        response_data = {
            "status": 200,
            "type": "reask",
            "message": "ReAsk: Need product line clarification",
            "output": {
                "answer": "請選擇您的產品類型",
                "ask_flag": True,
                "hint_candidates": relative_questions,
                "kb": {}
            }
        }

        final_result = {
            "status": 200,
            "message": "OK",
            "result": {
                "renderTime": int(time.time()),
                "render": [
                    {
                        "renderId": render_id,
                        "stream": False,
                        "type": "avatarAskProductLine",
                        "message": avatar_response,
                        "remark": [],
                        "option": [
                            {
                                "name": item["title_name"],
                                "value": item["title"],
                                "icon": item.get("icon", "")
                            }
                            for item in relative_questions
                        ]
                    }
                ]
            }
        }

        return {
            "response_data": response_data,
            "final_result": final_result,
            "type": "avatarAskProductLine"
        }

    async def _handle_high_similarity(
        self,
        top1_kb: str,
        top1_kb_sim: float,
        top4_kb_list: List[str],
        his_inputs: List[str],
        search_info: str,
        lang: str,
        websitecode: str,
        system_code: str,
        render_id: str
    ) -> Dict[str, Any]:
        """Handle case when KB similarity is high."""
        logger.info(
            f"[Response] High similarity ({top1_kb_sim:.3f}) - "
            f"providing KB answer"
        )

        # TODO: Enable when environment ready
        # rag_response = await ts_service.hint_create(...)
        # avatar_response = await avatar_service.generate(...)

        # Get KB content
        kb_content = self.cosmos_repo.get_kb_content(top1_kb, lang)

        # Mock avatar response
        avatar_response = "根據您的問題，我找到了相關的解決方案。"

        # Mock RAG response
        content = {
            "ask_content": kb_content.get(
                "content", "這是知識庫的內容。"
            ),
            "title": kb_content.get("title", "知識庫標題"),
            "content": kb_content.get("content", ""),
            "link": kb_content.get("link", "")
        }

        relative_questions = []
        # Process hints from top4 KBs
        # TODO: Enable when environment ready
        # for kb in top4_kb_list:
        #     hint = kb_repo.get_rag_hint(kb, websitecode, "1")
        #     if hint: relative_questions.append(hint)

        response_data = {
            "status": 200,
            "type": "answer",
            "message": "RAG Response",
            "output": {
                "answer": content.get("ask_content", ""),
                "ask_flag": False,
                "hint_candidates": relative_questions,
                "kb": {
                    "kb_no": str(top1_kb),
                    "title": content.get("title", ""),
                    "similarity": float(top1_kb_sim),
                    "source": "KB",
                    "exec_time": 0.0
                }
            }
        }

        final_result = {
            "status": 200,
            "message": "OK",
            "result": {
                "renderTime": int(time.time()),
                "render": [
                    {
                        "renderId": render_id,
                        "stream": False,
                        "type": "avatarTechnicalSupport",
                        "message": avatar_response,
                        "remark": [],
                        "option": [
                            {
                                "type": "faqcards",
                                "cards": [
                                    {
                                        "link": content.get("link", ""),
                                        "title": content.get("title", ""),
                                        "content": content.get(
                                            "content", ""
                                        ),
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }

        return {
            "response_data": response_data,
            "final_result": final_result,
            "type": "avatarTechnicalSupport"
        }

    async def _handle_low_similarity(
        self,
        top1_kb: Optional[str],
        top1_kb_sim: float,
        his_inputs: List[str],
        lang: str,
        render_id: str
    ) -> Dict[str, Any]:
        """Handle case when KB similarity is low."""
        logger.info(
            f"[Response] Low similarity ({top1_kb_sim:.3f}) - "
            f"suggesting handoff"
        )

        # TODO: Enable when environment ready
        # avatar_response = await avatar_service.generate(...)

        # Mock avatar response
        avatar_response = "抱歉，我需要更多資訊才能幫助您。"

        # Get KB info
        kb_title = ""
        if top1_kb:
            kb_content = self.cosmos_repo.get_kb_content(top1_kb, lang)
            kb_title = kb_content.get("title", "")

        response_data = {
            "status": 200,
            "type": "handoff",
            "message": "相似度低，建議轉人工",
            "output": {
                "answer": "",
                "ask_flag": False,
                "hint_candidates": [],
                "kb": {
                    "kb_no": str(top1_kb or ""),
                    "title": kb_title,
                    "similarity": float(top1_kb_sim),
                    "source": "",
                    "exec_time": 0.0
                }
            }
        }

        final_result = {
            "status": 200,
            "message": "OK",
            "result": [
                {
                    "renderTime": int(time.time()),
                    "render": [
                        {
                            "renderId": render_id,
                            "stream": False,
                            "type": "avatarText",
                            "message": avatar_response,
                            "remark": [],
                            "option": []
                        }
                    ]
                },
                {
                    "renderTime": int(time.time()),
                    "render": [
                        {
                            "renderId": render_id,
                            "stream": False,
                            "type": "avatarAsk",
                            "message": "你可以告訴我像是產品全名、型號，或你想問的活動名稱～",
                            "remark": [],
                            "option": [
                                {
                                    "name": "我想知道 ROG FLOW X16 的規格",
                                    "value": "我想知道 ROG FLOW X16 的規格",
                                    "answer": [
                                        {
                                            "type": "inquireMode",
                                            "value": "intent"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        return {
            "response_data": response_data,
            "final_result": final_result,
            "type": "avatarText"
        }
