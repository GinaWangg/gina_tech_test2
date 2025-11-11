"""Response generation components for tech agent.

This module contains focused classes for generating different types
of responses in the technical support flow.
"""

from typing import Any, Dict, List

from api_structure.src.clients.mock_container_client import (
    MockChatFlow,
    MockServiceProcess,
)


class ResponseGenerator:
    """Handles response generation based on different scenarios."""

    def __init__(
        self,
        service_process: MockServiceProcess,
        chat_flow: MockChatFlow,
        user_input: Any,
        render_id: str,
        lang: str,
    ):
        """Initialize response generator.

        Args:
            service_process: Service process instance
            chat_flow: Chat flow instance
            user_input: User input data
            render_id: Unique render ID
            lang: Language code
        """
        self.service_process = service_process
        self.chat_flow = chat_flow
        self.user_input = user_input
        self.render_id = render_id
        self.lang = lang
        self.avatar_response = None
        self.response_data = {}
        self.final_result = {}

    async def generate_no_product_line_response(
        self,
        his_inputs: List[str],
        faqs_wo_pl: List[Dict],
        search_info: str,
        containers: Any,
    ) -> Dict[str, Any]:
        """Generate response when no product line is identified.

        Args:
            his_inputs: Historical user inputs
            faqs_wo_pl: FAQs without product line
            search_info: Search information
            containers: Dependency container

        Returns:
            Response dictionary
        """
        print("\n[無產品線] 進行產品線追問")

        # Get avatar response
        self.avatar_response = (
            await self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(
                his_inputs[-1], self.lang
            )
        )

        # Get reask response
        ask_response, rag_response = (
            await self.service_process.technical_support_productline_reask(
                user_input=self.user_input.user_input,
                faqs_wo_pl=faqs_wo_pl,
                site=self.user_input.websitecode,
                lang=self.lang,
                system_code=self.user_input.system_code,
            )
        )

        relative_questions = rag_response.get("relative_questions", [])

        # Insert hint data (mocked)
        await containers.cosmos_settings.insert_hint_data(
            chatflow_data=self.chat_flow.data,
            intent_hints=relative_questions,
            search_info=search_info,
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

        return self.final_result

    async def generate_high_similarity_response(
        self,
        top4_kb_list: List[str],
        top1_kb: str,
        top1_kb_sim: float,
        search_info: str,
        his_inputs: List[str],
        containers: Any,
    ) -> Dict[str, Any]:
        """Generate response when similarity is high enough.

        Args:
            top4_kb_list: Top 4 KB results
            top1_kb: Top KB result
            top1_kb_sim: Top similarity score
            search_info: Search information
            his_inputs: Historical inputs
            containers: Dependency container

        Returns:
            Response dictionary
        """
        print(f"\n[相似度高於門檻] 相似度={top1_kb_sim}，建立 Hint 回應")

        rag_response = await self.service_process.technical_support_hint_create(
            top4_kb_list,
            top1_kb,
            top1_kb_sim,
            self.lang,
            search_info,
            his_inputs,
            system_code=self.user_input.system_code,
            site=self.user_input.websitecode,
            config=containers.cfg,
        )

        info = rag_response.get("response_info", {})
        content = rag_response.get("rag_content", {})

        # Get avatar response
        self.avatar_response = (
            await self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(
                his_inputs[-1], self.lang, content
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

        return self.final_result

    async def generate_low_similarity_response(
        self, top1_kb: str, top1_kb_sim: float, his_inputs: List[str], kb_mappings: Dict
    ) -> Dict[str, Any]:
        """Generate response when similarity is too low.

        Args:
            top1_kb: Top KB result
            top1_kb_sim: Top similarity score
            his_inputs: Historical inputs
            kb_mappings: KB mappings dictionary

        Returns:
            Response dictionary
        """
        print(f"\n[相似度低於門檻] 相似度={top1_kb_sim}，轉人工")

        # Get avatar response
        self.avatar_response = (
            await self.service_process.ts_rag.reply_with_faq_gemini_sys_avatar(
                his_inputs[-1], self.lang
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
                    "kb_no": str(top1_kb or ""),
                    "title": str(
                        kb_mappings.get(f"{top1_kb}_{self.lang}", {}).get("title", "")
                    ),
                    "similarity": float(top1_kb_sim or 0.0),
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
                                    "value": (
                                        "purchasing-recommendation-" "of-asus-products"
                                    ),
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

        return self.final_result
