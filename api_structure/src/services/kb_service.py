"""Knowledge base service for tech agent.

This module handles KB search, processing, and RAG response generation.
"""

from typing import Any, Dict, List, Optional, Tuple
from api_structure.core.timer import timed


class KnowledgeBaseService:
    """Service for KB search and processing."""

    def __init__(self, container: Any):
        """Initialize KB service.

        Args:
            container: Dependency container with KB mappings
        """
        self.container = container
        self.KB_mappings = getattr(container, "KB_mappings", {})
        self.rag_mappings = getattr(container, "rag_mappings", {})

    def get_kb_content(self, kb_no: str, lang: str) -> Dict[str, Any]:
        """Get KB content by number and language.

        Args:
            kb_no: KB number
            lang: Language code

        Returns:
            KB content dictionary
        """
        kb_key = f"{kb_no}_{lang}"
        kb_data = self.KB_mappings.get(kb_key, {})

        return {
            "kb_no": kb_no,
            "title": kb_data.get("title", ""),
            "content": kb_data.get("content", ""),
            "link": kb_data.get("link", ""),
        }

    def process_kb_results(
        self, faq_result: Dict[str, Any], threshold: float = 0.92
    ) -> tuple:
        """Process KB search results.

        Args:
            faq_result: FAQ search result
            threshold: Similarity threshold for filtering

        Returns:
            Tuple of (top4_kb_list, top1_kb, top1_kb_sim)
        """
        faq_list = faq_result.get("faq", [])
        sim_list = faq_result.get("cosineSimilarity", [])

        # Filter KBs above threshold, limit to top 3
        top4_kb_list = [
            faq
            for faq, sim in zip(faq_list, sim_list)
            if sim >= threshold
        ][:3]

        # Get top 1
        top1_kb = faq_list[0] if faq_list else None
        top1_kb_sim = sim_list[0] if sim_list else 0.0

        return top4_kb_list, top1_kb, top1_kb_sim

    def process_faqs_without_pl(
        self, faq_result_wo_pl: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process FAQs without product line.

        Args:
            faq_result_wo_pl: FAQ result without product line filter

        Returns:
            List of FAQ dictionaries with metadata
        """
        faqs_wo_pl = [
            {"kb_no": faq, "cosineSimilarity": sim, "productLine": pl}
            for faq, sim, pl in zip(
                faq_result_wo_pl.get("faq", []),
                faq_result_wo_pl.get("cosineSimilarity", []),
                faq_result_wo_pl.get("productLine", []),
            )
        ]
        return faqs_wo_pl

    @timed(task_name="generate_rag_response")
    async def generate_rag_response(
        self,
        top_kb_list: List[str],
        top1_kb: str,
        top1_kb_sim: float,
        lang: str,
        search_info: str,
        his_inputs: List[str],
        system_code: str,
        site: str,
    ) -> Dict[str, Any]:
        """Generate RAG response with hints.

        Args:
            top_kb_list: List of top KB numbers
            top1_kb: Top 1 KB number
            top1_kb_sim: Top 1 similarity score
            lang: Language code
            search_info: Search query
            his_inputs: History inputs
            system_code: System code
            site: Website code

        Returns:
            RAG response with content and hints
        """
        # Original would generate comprehensive response with:
        # 1. Get KB content
        # 2. Generate related questions
        # 3. Format response with links and cards

        # Mock response structure
        kb_content = self.get_kb_content(top1_kb, lang)

        mock_response = {
            "response_info": {
                "top1_kb": top1_kb,
                "top1_similarity": top1_kb_sim,
                "response_source": "mock_rag",
                "exec_time": 1.23,
            },
            "rag_content": {
                "title": kb_content.get("title", ""),
                "content": kb_content.get("content", ""),
                "link": kb_content.get(
                    "link", "https://www.asus.com/support/"
                ),
                "ask_content": (
                    "根據您的問題，我找到了相關的解決方案。"
                    "請參考以下資訊..."
                ),
            },
            "relative_questions": [
                {
                    "question": "如何重置筆電？",
                    "title": "reset",
                    "title_name": "重置筆電",
                    "icon": "reset_icon",
                },
                {
                    "question": "如何更新驅動程式？",
                    "title": "driver_update",
                    "title_name": "更新驅動",
                    "icon": "update_icon",
                },
            ],
        }

        return mock_response  # TODO: Enable when environment ready

    @timed(task_name="generate_productline_reask")
    async def generate_productline_reask(
        self,
        user_input: str,
        faqs_wo_pl: List[Dict[str, Any]],
        site: str,
        lang: str,
        system_code: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Generate product line reask response.

        Args:
            user_input: User input
            faqs_wo_pl: FAQs without product line
            site: Website code
            lang: Language code
            system_code: System code

        Returns:
            Tuple of (ask_response, rag_response)
        """
        # Original would:
        # 1. Analyze user input
        # 2. Generate product line options
        # 3. Create reask prompt

        ask_response = {
            "ask_content": (
                "為了更準確地協助您，請問您使用的是哪個產品線？"
            ),
            "ask_flag": True,
        }

        rag_response = {
            "relative_questions": [
                {
                    "question": "筆記型電腦",
                    "title": "notebook",
                    "title_name": "筆記型電腦",
                    "icon": "laptop",
                },
                {
                    "question": "桌上型電腦",
                    "title": "desktop",
                    "title_name": "桌上型電腦",
                    "icon": "desktop",
                },
                {
                    "question": "顯示器",
                    "title": "display",
                    "title_name": "顯示器",
                    "icon": "monitor",
                },
            ]
        }

        return (
            ask_response,
            rag_response,
        )  # TODO: Enable when environment ready

    @timed(task_name="generate_avatar_response")
    async def generate_avatar_response(
        self,
        user_input: str,
        lang: str,
        content_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate avatar response (friendly chat).

        Args:
            user_input: User input
            lang: Language code
            content_data: Optional content data for context

        Returns:
            Avatar response dictionary
        """
        # Original would use Gemini/GPT to generate friendly response

        # Mock response
        class MockResponse:
            def __init__(self, answer: str):
                self.answer = answer

        mock_answer = (
            "您好！我是華碩技術支援小幫手。"
            "我會盡力協助您解決問題。請告訴我更多細節吧！"
        )

        return {
            "response": MockResponse(mock_answer)
        }  # TODO: Enable when environment ready
