"""Stub implementations for service layer classes.

This module provides stub versions of ServiceProcess, ChatFlow,
and related service classes.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime


class ChatFlowStub:
    """Stub implementation of ChatFlow class."""

    def __init__(self, data: Any, last_hint: Optional[Dict], container: Any):
        """Initialize ChatFlow stub.
        
        Args:
            data: Request data
            last_hint: Last hint data
            container: Dependency container
        """
        self.data = data
        self.last_hint = last_hint
        self.container = container
        self.default_user_info = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": getattr(data, "product_line", ""),
            "sub_product_category": None,
            "first_time": True,
        }

    async def get_bot_scope_chat(
        self,
        prev_user_info: Optional[Dict],
        curr_user_info: Dict,
        last_bot_scope: Optional[str],
    ) -> Optional[str]:
        """Simulate bot scope determination.
        
        Args:
            prev_user_info: Previous user info
            curr_user_info: Current user info
            last_bot_scope: Last bot scope
            
        Returns:
            Bot scope string or None
        """
        if self.last_hint and self.last_hint.get("hintType") == (
            "productline-reask"
        ):
            for hint in self.last_hint.get("intentHints", []):
                if self.data.user_input == hint.get("question"):
                    return hint.get("title")

        if curr_user_info.get("main_product_category"):
            return curr_user_info["main_product_category"]

        return getattr(self.data, "product_line", None) or None

    async def get_userInfo(
        self, his_inputs: List[str]
    ) -> tuple:
        """Simulate user info extraction.
        
        Args:
            his_inputs: Historical inputs
            
        Returns:
            Tuple of (user_info_dict, other_data)
        """
        user_info_dict = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": None,
            "sub_product_category": None,
        }
        return (user_info_dict, {})

    async def get_searchInfo(self, his_inputs: List[str]) -> str:
        """Simulate search info generation.
        
        Args:
            his_inputs: Historical inputs
            
        Returns:
            Search query string
        """
        return his_inputs[-1] if his_inputs else ""

    async def is_follow_up(
        self,
        prev_question: str,
        prev_answer: str,
        prev_answer_refs: str,
        new_question: str,
    ) -> Dict[str, bool]:
        """Simulate follow-up detection.
        
        Args:
            prev_question: Previous question
            prev_answer: Previous answer
            prev_answer_refs: Previous answer references
            new_question: New question
            
        Returns:
            Dictionary with is_follow_up flag
        """
        return {"is_follow_up": False}


class TSRAGStub:
    """Stub for Technical Support RAG service."""

    async def technical_rag(
        self,
        top1_kb: str,
        top1_kb_sim: float,
        title: str,
        content: str,
        summary: str,
        user_question: str,
        lang: str,
        site: str,
    ) -> tuple:
        """Simulate RAG response generation.
        
        Args:
            top1_kb: Top KB number
            top1_kb_sim: Similarity score
            title: KB title
            content: KB content
            summary: KB summary
            user_question: User's question
            lang: Language code
            site: Site code
            
        Returns:
            Tuple of (response_text, response_info)
        """
        response_text = f"根據您的問題，建議您檢查以下步驟：\n{summary}"
        response_info = {
            "top1_kb": top1_kb,
            "top1_similarity": top1_kb_sim,
            "response_source": "RAG",
            "exec_time": 0.5,
        }
        return (response_text, response_info)

    async def reply_with_faq_gemini_sys_avatar(
        self,
        user_input: str,
        lang: str,
        content_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Simulate avatar response generation.
        
        Args:
            user_input: User input
            lang: Language code
            content_data: Optional content data
            
        Returns:
            Dictionary with response
        """
        if content_data:
            answer = f"我瞭解您遇到了問題。{content_data.get('ask_content', '')}"
        else:
            answer = "您好！我是技術支援助手，很高興為您服務。"

        class Response:
            def __init__(self, answer_text):
                self.answer = answer_text

        return {"response": Response(answer)}


class TSProductLineStub:
    """Stub for product line service."""

    def __init__(self, config: Any, productline_name_map: Dict):
        """Initialize product line stub.
        
        Args:
            config: Configuration object
            productline_name_map: Product line name mappings
        """
        self.productline_name_map = productline_name_map


class ServiceProcessStub:
    """Stub implementation of ServiceProcess class."""

    def __init__(self, system_code: str, container: Any):
        """Initialize ServiceProcess stub.
        
        Args:
            system_code: System code
            container: Dependency container
        """
        self.system_code = system_code
        self.container = container
        self.ts_rag = TSRAGStub()
        self.ts_pl = TSProductLineStub(
            container.cfg, container.productline_name_map
        )
        self.redis_config = container.redis_config

    async def technical_support_hint_create(
        self,
        kb_list: List[str],
        top1_kb: str,
        top1_kb_sim: float,
        lang: str,
        search_info: str,
        his_inputs: List[str],
        system_code: str,
        site: str,
        config: Any,
    ) -> Dict[str, Any]:
        """Simulate hint creation for technical support.
        
        Args:
            kb_list: List of KB numbers
            top1_kb: Top KB number
            top1_kb_sim: Top similarity score
            lang: Language code
            search_info: Search information
            his_inputs: Historical inputs
            system_code: System code
            site: Site code
            config: Configuration
            
        Returns:
            Dictionary with RAG response and hints
        """
        # Simulate RAG processing
        kb_key = f"{top1_kb}_{lang}"
        kb_data = self.container.KB_mappings.get(
            kb_key, {"title": "", "content": "", "summary": ""}
        )

        tecnical_response, response_info = await self.ts_rag.technical_rag(
            top1_kb,
            top1_kb_sim,
            kb_data.get("title", ""),
            kb_data.get("content", ""),
            kb_data.get("summary", ""),
            his_inputs[-1] if his_inputs else "",
            lang=lang,
            site=site,
        )

        # Simulate hint generation
        relative_questions = []
        for kb in kb_list[:3]:
            rag_key = f"{kb}_{site}_1"
            if rag_key in self.container.rag_mappings:
                hint = self.container.rag_mappings[rag_key].copy()
                if system_code.lower() == "rog":
                    hint["link"] = hint.get("ROG_link", "")
                else:
                    hint["link"] = hint.get("ASUS_link", "")
                if "ASUS_link" in hint:
                    del hint["ASUS_link"]
                if "ROG_link" in hint:
                    del hint["ROG_link"]
                relative_questions.append(hint)

        # Build link
        if system_code.lower() == "rog":
            link = f"https://rog.asus.com/{site}/support/FAQ/{top1_kb}"
        else:
            link = f"https://www.asus.com/{site}/support/FAQ/{top1_kb}"

        return {
            "rag_response": tecnical_response,
            "rag_content": {
                "ask_content": tecnical_response,
                "title": kb_data.get("title", ""),
                "content": kb_data.get("content", ""),
                "link": link,
            },
            "response_info": response_info,
            "relative_questions": relative_questions,
        }

    async def technical_support_productline_reask(
        self,
        user_input: str,
        faqs_wo_pl: List[Dict],
        site: str,
        lang: str,
        system_code: str,
    ) -> tuple:
        """Simulate product line re-ask.
        
        Args:
            user_input: User input
            faqs_wo_pl: FAQs without product line
            site: Site code
            lang: Language code
            system_code: System code
            
        Returns:
            Tuple of (ask_response, rag_response)
        """
        ask_response = {
            "ask_content": "請問您想詢問哪個產品線的問題呢？",
            "ask_flag": True,
        }

        relative_questions = [
            {
                "title": "notebook",
                "title_name": "筆記型電腦",
                "question": "筆記型電腦",
                "icon": "laptop",
            },
            {
                "title": "desktop",
                "title_name": "桌上型電腦",
                "question": "桌上型電腦",
                "icon": "desktop",
            },
            {
                "title": "phone",
                "title_name": "手機",
                "question": "手機",
                "icon": "phone",
            },
        ]

        rag_response = {"relative_questions": relative_questions}

        return (ask_response, rag_response)
