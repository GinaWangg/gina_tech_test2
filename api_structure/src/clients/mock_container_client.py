"""Mock Dependency Container Client for tech_agent endpoint.

This client provides stubbed data for testing when external services
(Cosmos, Redis, GPT APIs) are unavailable.
"""

from typing import Any, Dict, List, Optional, Tuple


class MockCosmosSettings:
    """Mock Cosmos DB operations."""

    async def create_GPT_messages(
        self, session_id: str, user_input: str
    ) -> Tuple[List[str], int, Optional[Dict], Optional[str], Optional[Dict]]:
        """Mock: Get chat history and user info.

        # TODO: Enable when environment ready
        # Real implementation would query Cosmos DB for:
        # - his_inputs: Historical user inputs
        # - chat_count: Number of messages in session
        # - user_info: User profile data
        # - last_bot_scope: Previous product line context
        # - last_extract_output: Previous response extract
        """
        # Mock data
        his_inputs = [user_input]
        chat_count = 1
        user_info = None
        last_bot_scope = None
        last_extract_output = None

        return (his_inputs, chat_count, user_info, last_bot_scope, last_extract_output)

    async def get_latest_hint(self, session_id: str) -> Optional[Dict]:
        """Mock: Get latest hint data.

        # TODO: Enable when environment ready
        # result = await cosmos_client.query(...)
        """
        return None  # Mock: No previous hints

    async def get_language_by_websitecode_dev(self, websitecode: str) -> str:
        """Mock: Get language from websitecode.

        # TODO: Enable when environment ready
        # result = await cosmos_client.query_language(websitecode)
        """
        # Mock mapping
        lang_map = {
            "tw": "zh-TW",
            "cn": "zh-CN",
            "us": "en-US",
            "jp": "ja-JP",
        }
        return lang_map.get(websitecode, "zh-TW")

    async def insert_hint_data(
        self,
        chatflow_data: Any,
        intent_hints: List[Dict],
        search_info: str,
        hint_type: str,
    ) -> None:
        """Mock: Insert hint data to Cosmos.

        # TODO: Enable when environment ready
        # await cosmos_client.insert(...)
        """
        pass  # Mock: No-op

    async def insert_data(self, cosmos_data: Dict) -> None:
        """Mock: Insert log data to Cosmos.

        # TODO: Enable when environment ready
        # await cosmos_client.insert(...)
        """
        pass  # Mock: No-op


class MockSentenceGroupClassification:
    """Mock sentence grouping service."""

    async def sentence_group_classification(
        self, his_inputs: List[str]
    ) -> Dict[str, Any]:
        """Mock: Group related sentences.

        # TODO: Enable when environment ready
        # result = await api_call(his_inputs)
        """
        # Mock: Return single group with all inputs
        return {
            "groups": [
                {
                    "statements": his_inputs,
                }
            ]
        }


class MockBaseService:
    """Mock GPT service."""

    async def GPT41_mini_response(self, prompt: List[Dict]) -> str:
        """Mock: Get GPT response.

        # TODO: Enable when environment ready
        # result = await openai_client.chat.completions.create(...)
        """
        return "true"  # Mock: Default to tech support related


class MockServiceDiscriminator:
    """Mock service discriminator for KB search."""

    async def service_discreminator_with_productline(
        self,
        user_question_english: str,
        site: str,
        specific_kb_mappings: Dict,
        productLine: Optional[str],
    ) -> Tuple[Dict, Dict]:
        """Mock: Search knowledge base.

        # TODO: Enable when environment ready
        # result = await redis_api.search(...)
        """
        # Mock: Return empty results (low similarity case)
        faq_result = {
            "faq": [],
            "cosineSimilarity": [],
        }
        faq_result_wo_pl = {
            "faq": [],
            "cosineSimilarity": [],
            "productLine": [],
        }
        return (faq_result, faq_result_wo_pl)


class MockTechSupportRAG:
    """Mock technical support RAG service."""

    async def reply_with_faq_gemini_sys_avatar(
        self, user_input: str, lang: str, content_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Mock: Generate avatar response.

        # TODO: Enable when environment ready
        # result = await gemini_api.generate(...)
        """
        # Mock avatar response
        return {
            "response": type(
                "obj",
                (object,),
                {"answer": "我了解您的筆電卡在登入畫面的問題。讓我協助您解決這個情況。"},
            )()
        }


class MockServiceProcess:
    """Mock service process wrapper."""

    def __init__(self, system_code: str, container: "MockDependencyContainer"):
        self.system_code = system_code
        self.container = container
        self.ts_rag = MockTechSupportRAG()

    async def technical_support_productline_reask(
        self,
        user_input: str,
        faqs_wo_pl: List[Dict],
        site: str,
        lang: str,
        system_code: str,
    ) -> Tuple[Dict, Dict]:
        """Mock: Product line reask logic.

        # TODO: Enable when environment ready
        # ask_response = await api_call(...)
        # rag_response = await rag_search(...)
        """
        ask_response = {
            "ask_content": "請告訴我您的產品線",
            "ask_flag": True,
        }
        rag_response = {
            "relative_questions": [
                {
                    "title": "筆記型電腦",
                    "title_name": "筆記型電腦",
                    "icon": "laptop",
                },
                {
                    "title": "桌上型電腦",
                    "title_name": "桌上型電腦",
                    "icon": "desktop",
                },
            ]
        }
        return (ask_response, rag_response)

    async def technical_support_hint_create(
        self,
        top4_kb_list: List[str],
        top1_kb: Optional[str],
        top1_kb_sim: float,
        lang: str,
        search_info: str,
        his_inputs: List[str],
        system_code: str,
        site: str,
        config: Dict,
    ) -> Dict[str, Any]:
        """Mock: Create hint response.

        # TODO: Enable when environment ready
        # rag_response = await rag_service.create_hint(...)
        """
        return {
            "response_info": {
                "top1_kb": top1_kb or "",
                "top1_similarity": top1_kb_sim,
                "response_source": "mock",
                "exec_time": 0.0,
            },
            "rag_content": {
                "ask_content": "根據您的問題，這裡是相關的解決方案。",
                "title": "筆電登入問題",
                "link": "https://example.com/kb/123",
                "content": "請嘗試重新啟動您的裝置...",
            },
            "relative_questions": [],
        }


class MockChatFlow:
    """Mock chat flow utilities."""

    def __init__(self, data: Any, last_hint: Optional[Dict], container: Any):
        self.data = data
        self.last_hint = last_hint
        self.container = container
        self.default_user_info = {
            "main_product_category": "",
            "first_time": True,
        }

    async def is_follow_up(
        self,
        prev_question: str,
        prev_answer: str,
        prev_answer_refs: str,
        new_question: str,
    ) -> Dict[str, bool]:
        """Mock: Check if question is follow-up.

        # TODO: Enable when environment ready
        # result = await gpt_analysis(...)
        """
        return {"is_follow_up": False}

    async def get_userInfo(self, his_inputs: List[str]) -> Tuple[Dict, Any]:
        """Mock: Extract user info from conversation.

        # TODO: Enable when environment ready
        # result = await gpt_extraction(his_inputs)
        """
        user_info = {
            "product_model": "",
            "issue_type": "login_issue",
        }
        return (user_info, None)

    async def get_searchInfo(self, his_inputs: List[str]) -> str:
        """Mock: Get search query from inputs.

        # TODO: Enable when environment ready
        # result = await gpt_summarize(his_inputs)
        """
        return his_inputs[-1] if his_inputs else ""

    async def get_bot_scope_chat(
        self,
        prev_user_info: Optional[Dict],
        curr_user_info: Dict,
        last_bot_scope: Optional[str],
    ) -> Optional[str]:
        """Mock: Determine bot scope (product line).

        # TODO: Enable when environment ready
        # result = await gpt_classification(...)
        """
        return None  # Mock: No product line identified


class MockDependencyContainer:
    """Mock dependency container with stubbed services."""

    def __init__(self):
        """Initialize mock container."""
        self.cfg = {}  # Mock config
        self.cosmos_settings = MockCosmosSettings()
        self.sentence_group_classification = MockSentenceGroupClassification()
        self.base_service = MockBaseService()
        self.sd = MockServiceDiscriminator()
        
        # Mock mappings (empty for now)
        self.KB_mappings = {}
        self.specific_kb_mappings = {}

    async def initialize(self) -> None:
        """Initialize async components.

        # TODO: Enable when environment ready
        # await self.cosmos_client.connect()
        # await self.redis_client.connect()
        """
        pass  # Mock: No initialization needed

    async def close(self) -> None:
        """Close async components.

        # TODO: Enable when environment ready
        # await self.cosmos_client.close()
        # await self.redis_client.close()
        """
        pass  # Mock: No cleanup needed
