"""Mock container for tech agent dependencies (stubbed for testing)."""

from typing import Any, Dict, List, Optional


class MockCosmosSettings:
    """Mock Cosmos DB settings - stubbed for testing.

    TODO: Enable when environment ready
    """

    async def create_GPT_messages(self, session_id: str, user_input: str) -> tuple:
        """Mock GPT messages creation.

        Returns:
            Tuple of (his_inputs, chat_count, user_info,
                     last_bot_scope, last_extract_output)
        """
        # Mock response - TODO: restore after env ready
        his_inputs = [user_input]
        chat_count = 1
        user_info = None
        last_bot_scope = ""
        last_extract_output = {}

        return (his_inputs, chat_count, user_info, last_bot_scope, last_extract_output)

    async def get_latest_hint(self, session_id: str) -> Optional[Dict]:
        """Mock get latest hint.

        Returns:
            Mock hint data or None
        """
        # Mock response - TODO: restore after env ready
        return None

    async def get_language_by_websitecode_dev(self, websitecode: str) -> str:
        """Mock language detection by website code.

        Args:
            websitecode: Website code like 'tw', 'us', etc.

        Returns:
            Language code
        """
        # Mock mapping - TODO: restore after env ready
        mapping = {
            "tw": "zh-tw",
            "cn": "zh-cn",
            "us": "en",
            "jp": "ja",
        }
        return mapping.get(websitecode, "zh-tw")

    async def insert_hint_data(
        self,
        chatflow_data: Any,
        intent_hints: List[Dict],
        search_info: str,
        hint_type: str,
    ) -> None:
        """Mock insert hint data.

        TODO: Enable when environment ready
        """
        # Mock implementation - no actual DB write
        pass

    async def insert_data(self, cosmos_data: Dict) -> None:
        """Mock insert cosmos data.

        TODO: Enable when environment ready
        """
        # Mock implementation - no actual DB write
        pass


class MockRedisConfig:
    """Mock Redis configuration - stubbed for testing.

    TODO: Enable when environment ready
    """

    async def get_hint_simiarity(self, search_info: str) -> Dict:
        """Mock hint similarity search."""
        # Mock response - TODO: restore after env ready
        return {"faq": "1234567", "cosineSimilarity": 0.85, "hints_id": "hint_001"}

    async def get_productline(self, main_product_category: str, site: str) -> str:
        """Mock product line retrieval."""
        # Mock response - TODO: restore after env ready
        return main_product_category if main_product_category else "notebook"


class MockServiceDiscriminator:
    """Mock service discriminator - stubbed for testing.

    TODO: Enable when environment ready
    """

    async def service_discreminator_with_productline(
        self,
        user_question_english: str,
        site: str,
        specific_kb_mappings: Dict,
        productLine: str,
    ) -> tuple:
        """Mock service discrimination with product line.

        Returns:
            Tuple of (faq_result, faq_result_wo_pl)
        """
        # Mock response - TODO: restore after env ready
        faq_result = {
            "faq": ["1041668"],
            "cosineSimilarity": [0.92],
            "productLine": ["notebook"],
        }
        faq_result_wo_pl = {
            "faq": ["1041668", "1041669"],
            "cosineSimilarity": [0.92, 0.88],
            "productLine": ["notebook", "desktop"],
        }
        return (faq_result, faq_result_wo_pl)


class MockSentenceGroupClassification:
    """Mock sentence group classification.

    TODO: Enable when environment ready
    """

    async def sentence_group_classification(
        self, his_inputs: List[str]
    ) -> Optional[Dict]:
        """Mock sentence grouping."""
        # Mock response - simple passthrough
        return {"groups": [{"statements": his_inputs}]}


class MockBaseService:
    """Mock base service for GPT calls.

    TODO: Enable when environment ready
    """

    async def GPT41_mini_response(self, prompt: List[Dict]) -> str:
        """Mock GPT response."""
        # Mock response - TODO: restore after env ready
        return "true"


class MockDependencyContainer:
    """Mock dependency container for tech agent.

    This replaces the real DependencyContainer with stubbed versions
    of all external dependencies for testing purposes.

    TODO: Enable real implementations when environment ready
    """

    def __init__(self):
        """Initialize mock container with default mock data."""
        # Mock configuration
        self.cfg = {"mock": "config"}

        # Mock clients
        self.cosmos_settings = MockCosmosSettings()
        self.redis_config = MockRedisConfig()
        self.sd = MockServiceDiscriminator()
        self.sentence_group_classification = MockSentenceGroupClassification()
        self.base_service = MockBaseService()

        # Mock KB mappings - TODO: restore after env ready
        self.KB_mappings = {
            "1041668_zh-tw": {
                "kb_no": "1041668",
                "title": "筆電無法開機或卡在登入畫面",
                "content": "如果您的筆電卡在登入畫面，請嘗試以下步驟...",
                "summary": "筆電登入問題排除",
            },
            "1041668_en": {
                "kb_no": "1041668",
                "title": "Laptop stuck at login screen",
                "content": "If your laptop is stuck at login screen...",
                "summary": "Login screen troubleshooting",
            },
        }

        # Mock RAG mappings - TODO: restore after env ready
        self.rag_mappings = {
            "1041668_tw_1": {
                "question": "如何重設密碼？",
                "title": "notebook",
                "title_name": "筆記型電腦",
                "icon": "https://example.com/notebook.png",
                "ASUS_link": "https://www.asus.com/tw/support/FAQ/1041668",
                "ROG_link": "https://rog.asus.com/tw/support/FAQ/1041668",
            }
        }

        self.rag_hint_id_index_mapping = {"hint_001_tw": {"index": 1}}

        # Mock product line mappings - TODO: restore after env ready
        self.PL_mappings = {
            "tw": ["notebook", "desktop", "phone", "monitor"],
            "us": ["notebook", "desktop", "phone", "monitor"],
        }

        self.productline_name_map = {
            "notebook": "筆記型電腦",
            "desktop": "桌上型電腦",
        }

        self.specific_kb_mappings = {}

        # Mock credentials - TODO: restore after env ready
        self.creds_trans = "mock_credentials"
        self._trans_client = None

    async def init_async(self, aiohttp_session=None):
        """Mock async initialization."""
        # Mock - no actual initialization needed
        pass

    async def close(self):
        """Mock cleanup."""
        # Mock - no actual cleanup needed
        pass
