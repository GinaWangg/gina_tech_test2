"""
Dependency container for tech agent with stubbed external services.

This module provides mock implementations of external services
(Cosmos, Redis, etc.) that cannot connect due to permission issues.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime


class MockCosmosSettings:
    """Mock Cosmos DB settings with stubbed methods.
    
    Original implementation in src/integrations/cosmos_process.py
    is commented out due to connection issues.
    """
    
    async def create_GPT_messages(
        self, session_id: str, user_input: str
    ) -> tuple:
        """Create GPT messages from history.
        
        Returns:
            Tuple of (his_inputs, chat_count, user_info,
                     last_bot_scope, last_extract_output)
        """
        # TODO: Enable when environment ready
        # Original logic:
        # messages = await cosmos_client.query(...)
        # return parse_messages(messages)
        
        # Mock return for testing
        his_inputs = [user_input]
        chat_count = 1
        user_info = None
        last_bot_scope = None
        last_extract_output = {}
        
        return (his_inputs, chat_count, user_info,
                last_bot_scope, last_extract_output)
    
    async def get_latest_hint(self, session_id: str) -> Optional[Dict]:
        """Get latest hint from session.
        
        Returns:
            Latest hint dictionary or None.
        """
        # TODO: Enable when environment ready
        # Original: hint = await cosmos_client.get_latest_hint(session_id)
        return None
    
    async def get_language_by_websitecode_dev(
        self, websitecode: str
    ) -> str:
        """Get language code by website code.
        
        Args:
            websitecode: Website code (e.g., 'tw', 'cn', 'us').
        
        Returns:
            Language code.
        """
        # TODO: Enable when environment ready
        # Original: lang = await lookup_db.get_language(websitecode)
        
        # Mock language mapping
        lang_map = {
            "tw": "zh-tw",
            "cn": "zh-cn",
            "us": "en-us",
            "jp": "ja-jp"
        }
        return lang_map.get(websitecode, "zh-tw")
    
    async def insert_hint_data(
        self,
        chatflow_data: Any,
        intent_hints: List[Dict],
        search_info: str,
        hint_type: str
    ) -> None:
        """Insert hint data to Cosmos DB.
        
        Args:
            chatflow_data: Chat flow data.
            intent_hints: List of intent hints.
            search_info: Search information.
            hint_type: Type of hint.
        """
        # TODO: Enable when environment ready
        # Original: await cosmos_client.insert_hint(...)
        pass
    
    async def insert_data(self, data: Dict[str, Any]) -> None:
        """Insert data to Cosmos DB.
        
        Args:
            data: Data dictionary to insert.
        """
        # TODO: Enable when environment ready
        # Original: await cosmos_client.insert_item(data)
        pass


class MockRedisConfig:
    """Mock Redis configuration with stubbed methods."""
    
    async def get_hint_simiarity(self, search_info: str) -> Dict:
        """Get hint similarity from Redis.
        
        Args:
            search_info: Search query text.
        
        Returns:
            Dictionary with faq and hints_id.
        """
        # TODO: Enable when environment ready
        # Original: result = await redis_client.get_similarity(search_info)
        return {"faq": "", "hints_id": ""}
    
    async def get_productline(
        self, category: str, site: str
    ) -> str:
        """Get product line from category.
        
        Args:
            category: Product category.
            site: Website code.
        
        Returns:
            Product line string.
        """
        # TODO: Enable when environment ready
        # Original: return await redis_client.get_productline(...)
        return category


class MockSentenceGroupClassification:
    """Mock sentence group classification service."""
    
    async def sentence_group_classification(
        self, inputs: List[str]
    ) -> Optional[Dict]:
        """Classify sentences into groups.
        
        Args:
            inputs: List of input sentences.
        
        Returns:
            Classification result or None.
        """
        # TODO: Enable when environment ready
        # Original: return await classifier.classify(inputs)
        return None


class MockServiceDiscriminator:
    """Mock service discriminator for KB search."""
    
    async def service_discreminator_with_productline(
        self,
        user_question_english: str,
        site: str,
        specific_kb_mappings: Dict,
        productLine: Optional[str] = None
    ) -> tuple:
        """Discriminate service with product line.
        
        Args:
            user_question_english: User question in English.
            site: Website code.
            specific_kb_mappings: KB mappings dictionary.
            productLine: Product line filter.
        
        Returns:
            Tuple of (faq_result, faq_result_wo_pl).
        """
        # TODO: Enable when environment ready
        # Original: results = await discriminator.search(...)
        
        # Mock KB search results
        faq_result = {
            "faq": ["1051479"],
            "cosineSimilarity": [0.816743731499],
            "productLine": ["notebook"]
        }
        faq_result_wo_pl = {
            "faq": ["1051479", "1051480"],
            "cosineSimilarity": [0.816743731499, 0.75],
            "productLine": ["notebook", "desktop"]
        }
        
        return (faq_result, faq_result_wo_pl)


class MockBaseService:
    """Mock base service for GPT calls."""
    
    async def GPT41_mini_response(self, prompt: List[Dict]) -> str:
        """Get GPT-4.1 mini response.
        
        Args:
            prompt: List of message dictionaries.
        
        Returns:
            Response string.
        """
        # TODO: Enable when environment ready
        # Original: return await gpt_client.chat(prompt)
        return "true"


class TechAgentContainer:
    """Container for tech agent dependencies with mocked services.
    
    This container provides all necessary dependencies for the tech agent
    handler, with external services mocked to work without actual
    connections.
    """
    
    def __init__(self):
        """Initialize container with mock services."""
        # Mock configuration
        self.cfg = {}
        
        # Mock external service clients
        self.cosmos_settings = MockCosmosSettings()
        self.redis_config = MockRedisConfig()
        self.sentence_group_classification = (
            MockSentenceGroupClassification()
        )
        self.sd = MockServiceDiscriminator()
        self.base_service = MockBaseService()
        
        # Mock data mappings (loaded from pickle files in production)
        self.rag_mappings: Dict = {}
        self.rag_hint_id_index_mapping: Dict = {}
        self.KB_mappings: Dict = {}
        self.PL_mappings: Dict = {"tw": [], "cn": [], "us": []}
        self.productline_name_map: Dict = {}
        self.specific_kb_mappings: Dict = {}
        
        # Mock credentials
        self.creds_trans = ""
        self._trans_client = None
    
    async def initialize(self) -> None:
        """Initialize async resources.
        
        In production, this would initialize actual client connections.
        For mock implementation, this is a no-op.
        """
        # TODO: Enable when environment ready
        # await self.cosmos_settings.initialize()
        # await self.redis_config.initialize()
        pass
    
    async def close(self) -> None:
        """Close async resources.
        
        In production, this would close actual client connections.
        For mock implementation, this is a no-op.
        """
        # TODO: Enable when environment ready
        # await self.cosmos_settings.close()
        # await self.redis_config.close()
        pass
