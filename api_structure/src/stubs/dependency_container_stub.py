"""Stub implementation of DependencyContainer for testing.

This module provides a stub version of the DependencyContainer class
that simulates the behavior of external dependencies without requiring
actual connections to Cosmos DB, Redis, or other services.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


class CosmosConfigStub:
    """Stub for Cosmos DB configuration and operations."""

    async def create_GPT_messages(
        self, session_id: str, user_input: str
    ) -> tuple:
        """Simulate retrieving chat history.
        
        Args:
            session_id: Session identifier
            user_input: Current user input
            
        Returns:
            Tuple of (messages, chat_count, user_info, last_bot_scope,
            last_extract_output)
        """
        messages = [user_input]
        chat_count = 1
        user_info = None
        last_bot_scope = None
        last_extract_output = {}
        return (messages, chat_count, user_info, last_bot_scope,
                last_extract_output)

    async def get_latest_hint(self, session_id: str) -> Optional[Dict]:
        """Simulate retrieving latest hint data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            None for first-time users
        """
        return None

    async def get_language_by_websitecode_dev(
        self, websitecode: str
    ) -> str:
        """Simulate language lookup by website code.
        
        Args:
            websitecode: Website code
            
        Returns:
            Language code
        """
        lang_map = {"tw": "zh-tw", "cn": "zh-cn", "us": "en"}
        return lang_map.get(websitecode, "en")

    async def insert_hint_data(
        self,
        chatflow_data: Any,
        intent_hints: List[Dict],
        search_info: str,
        hint_type: str,
    ) -> None:
        """Simulate inserting hint data.
        
        Args:
            chatflow_data: Chat flow data
            intent_hints: List of hint suggestions
            search_info: Search information
            hint_type: Type of hint
        """
        pass

    async def insert_data(self, cosmos_data: Dict[str, Any]) -> None:
        """Simulate inserting data to Cosmos DB.
        
        Args:
            cosmos_data: Data to insert
        """
        pass


class RedisConfigStub:
    """Stub for Redis configuration and operations."""

    async def get_productline(
        self, product_category: str, site: str
    ) -> Optional[str]:
        """Simulate product line lookup.
        
        Args:
            product_category: Product category
            site: Site code
            
        Returns:
            Product line or None
        """
        return product_category

    async def get_hint_simiarity(
        self, search_info: str
    ) -> Dict[str, Any]:
        """Simulate hint similarity search.
        
        Args:
            search_info: Search query
            
        Returns:
            Dictionary with faq and hints_id
        """
        return {"faq": "1234567", "hints_id": "hint_1"}


class SentenceGroupClassificationStub:
    """Stub for sentence group classification service."""

    async def sentence_group_classification(
        self, his_inputs: List[str]
    ) -> Dict[str, Any]:
        """Simulate sentence grouping.
        
        Args:
            his_inputs: List of historical inputs
            
        Returns:
            Dictionary with groups
        """
        return {
            "groups": [
                {"statements": his_inputs[-1:] if his_inputs else []}
            ]
        }


class ServiceDiscriminatorStub:
    """Stub for service discriminator."""

    async def service_discreminator_with_productline(
        self,
        user_question_english: str,
        site: str,
        specific_kb_mappings: Dict,
        productLine: Optional[str],
    ) -> tuple:
        """Simulate FAQ search with product line.
        
        Args:
            user_question_english: User question
            site: Site code
            specific_kb_mappings: KB mappings
            productLine: Product line filter
            
        Returns:
            Tuple of (faq_result, faq_result_wo_pl)
        """
        faq_result = {
            "faq": ["1043123"],
            "cosineSimilarity": [0.95],
            "productLine": [productLine or "notebook"],
        }
        faq_result_wo_pl = {
            "faq": ["1043123", "1043124", "1043125"],
            "cosineSimilarity": [0.95, 0.88, 0.82],
            "productLine": ["notebook", "desktop", "notebook"],
        }
        return (faq_result, faq_result_wo_pl)


class BaseServiceStub:
    """Stub for base service with GPT functionality."""

    async def GPT41_mini_response(
        self, prompt: List[Dict[str, str]]
    ) -> str:
        """Simulate GPT response.
        
        Args:
            prompt: List of message dictionaries
            
        Returns:
            Response string
        """
        return "true"


class ContentPolicyCheckStub:
    """Stub for content policy checking."""

    async def check(self, text: str) -> bool:
        """Simulate content policy check.
        
        Args:
            text: Text to check
            
        Returns:
            True if content passes policy
        """
        return True


class UserinfoDiscriminatorStub:
    """Stub for user info discrimination."""

    async def discriminate(self, user_input: str) -> Dict[str, Any]:
        """Simulate user info extraction.
        
        Args:
            user_input: User input text
            
        Returns:
            Dictionary with extracted user info
        """
        return {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": None,
            "sub_product_category": None,
        }


class FollowUpClassifierStub:
    """Stub for follow-up question classification."""

    async def classify(
        self, prev_q: str, prev_a: str, new_q: str
    ) -> Dict[str, Any]:
        """Simulate follow-up classification.
        
        Args:
            prev_q: Previous question
            prev_a: Previous answer
            new_q: New question
            
        Returns:
            Dictionary with is_follow_up flag
        """
        return {"is_follow_up": False}


class DependencyContainerStub:
    """Stub implementation of DependencyContainer.
    
    This class simulates all external dependencies used by the
    TechAgentProcessor without requiring actual connections.
    """

    def __init__(self):
        """Initialize stub container with mock data."""
        # Services
        self.cosmos_settings = CosmosConfigStub()
        self.redis_config = RedisConfigStub()
        self.sentence_group_classification = (
            SentenceGroupClassificationStub()
        )
        self.sd = ServiceDiscriminatorStub()
        self.base_service = BaseServiceStub()
        self.content_policy_check = ContentPolicyCheckStub()
        self.userinfo_discrimiator = UserinfoDiscriminatorStub()
        self.followup_discrimiator = FollowUpClassifierStub()

        # Mock data mappings
        self.KB_mappings = {
            "1043123_zh-tw": {
                "title": "筆電無法開機疑難排解",
                "content": "請確認電源連接，檢查電池狀態...",
                "summary": "筆電開機問題的解決方法",
            },
            "1043123_en": {
                "title": "Laptop won't turn on troubleshooting",
                "content": "Please check power connection...",
                "summary": "How to fix laptop power issues",
            },
        }

        self.rag_mappings = {
            "1043123_tw_1": {
                "question": "如何重置BIOS設定？",
                "title": "BIOS重置",
                "title_name": "BIOS重置",
                "icon": "settings",
                "ASUS_link": "https://www.asus.com/tw/support/FAQ/1043123",
                "ROG_link": "https://rog.asus.com/tw/support/FAQ/1043123",
            }
        }

        self.rag_hint_id_index_mapping = {
            "hint_1_tw": {"index": 1}
        }

        self.PL_mappings = {
            "tw": ["notebook", "desktop", "phone", "accessories"],
            "us": ["notebook", "desktop", "phone", "accessories"],
        }

        self.productline_name_map = {
            "notebook": "Notebook",
            "desktop": "Desktop",
            "phone": "Phone",
        }

        self.specific_kb_mappings = {}

        # Config object
        self.cfg = type("Config", (), {})()

    async def init_async(self, aiohttp_session):
        """Simulate async initialization.
        
        Args:
            aiohttp_session: aiohttp session (not used in stub)
        """
        pass

    async def close(self):
        """Simulate cleanup."""
        pass
