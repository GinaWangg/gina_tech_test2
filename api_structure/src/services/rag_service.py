"""RAG service for technical support responses."""

from typing import Any, Dict, List


class RAGService:
    """Service for RAG-based response generation.

    Handles technical support responses, avatar generation,
    and hint creation.
    """

    def __init__(self):
        """Initialize RAG service."""
        pass

    async def reply_with_avatar(
        self, user_input: str, lang: str, content_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate avatar response for user input.

        Args:
            user_input: User's input text.
            lang: Language code.
            content_data: Optional KB content data.

        Returns:
            Avatar response dictionary.
        """
        # TODO: Enable when environment ready
        # Original: Gemini-based avatar generation
        # For now, return mock data
        mock_response = {
            "response": type(
                "obj",
                (object,),
                {
                    "answer": "您好！我是華碩智能客服小布，很高興為您服務。"
                    "根據您的描述，筆電卡在登入畫面可能有幾種原因。"
                    "讓我為您提供一些排除步驟。"
                },
            )()
        }
        return mock_response

    async def create_hint_response(
        self,
        kb_list: List[str],
        top1_kb: str,
        top1_kb_sim: float,
        lang: str,
        search_info: str,
        his_inputs: List[str],
        system_code: str,
        websitecode: str,
    ) -> Dict[str, Any]:
        """Create hint response for high similarity KB match.

        Args:
            kb_list: List of KB numbers.
            top1_kb: Top matched KB number.
            top1_kb_sim: Top KB similarity score.
            lang: Language code.
            search_info: Search information.
            his_inputs: Historical inputs.
            system_code: System code (rog/asus).
            websitecode: Website code.

        Returns:
            RAG response with hints and KB content.
        """
        # TODO: Enable when environment ready
        # Original: Redis hint lookup + RAG content formatting
        # For now, return mock data
        rag_response = {
            "response_info": {
                "top1_kb": top1_kb,
                "top1_similarity": top1_kb_sim,
                "response_source": "RAG",
                "exec_time": 1.5,
            },
            "rag_content": {
                "ask_content": "根據知識庫，建議您先嘗試強制關機後重新開機。",
                "title": "筆記型電腦開機卡在登入畫面",
                "content": "請嘗試以下步驟：1. 強制關機 2. 移除外接設備 3. 重新開機",
                "link": f"https://www.asus.com/{websitecode}/support/FAQ/{top1_kb}",
            },
            "relative_questions": [
                {
                    "title": "notebook",
                    "title_name": "筆記型電腦",
                    "icon": "icon-notebook",
                    "question": "筆記型電腦問題",
                }
            ],
        }
        return rag_response

    async def create_product_line_reask(
        self,
        user_input: str,
        faqs_wo_pl: List[Dict[str, Any]],
        websitecode: str,
        lang: str,
        system_code: str,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Create product line re-ask response.

        Args:
            user_input: User input text.
            faqs_wo_pl: FAQs without product line filter.
            websitecode: Website code.
            lang: Language code.
            system_code: System code.

        Returns:
            Tuple of (ask_response, rag_response).
        """
        # TODO: Enable when environment ready
        # Original: TSProductLine service with hint generation
        # For now, return mock data
        ask_response = {
            "ask_content": "我可以幫您查詢技術支援相關問題，請問是關於哪個產品類別呢？",
            "ask_flag": True,
        }

        rag_response = {
            "relative_questions": [
                {
                    "title": "notebook",
                    "title_name": "筆記型電腦",
                    "icon": "icon-notebook",
                    "question": "筆記型電腦問題",
                },
                {
                    "title": "desktop",
                    "title_name": "桌上型電腦",
                    "icon": "icon-desktop",
                    "question": "桌上型電腦問題",
                },
                {
                    "title": "phone",
                    "title_name": "手機",
                    "icon": "icon-phone",
                    "question": "手機問題",
                },
            ]
        }

        return ask_response, rag_response
