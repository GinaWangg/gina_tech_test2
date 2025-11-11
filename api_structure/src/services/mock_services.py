"""Mock services for external dependencies (Cosmos DB, Redis, etc.)

This module provides stubbed implementations of external services that cannot
be connected due to permission issues. The original logic is preserved as
comments, with mock data returned for testing purposes.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class MockCosmosService:
    """Mock Cosmos DB service for testing without actual connection.

    TODO: Enable when environment ready
    Original implementation would connect to Azure Cosmos DB.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize mock Cosmos service.

        Args:
            config: Configuration dictionary
        """
        self.url = config.get("TECH_COSMOS_URL", "mock_url")
        # self.key = config.get("TECH_COSMOS_KEY")
        # self.client = CosmosClient(
        #     self.url, credential=self.key, consistency_level="Session"
        # )
        # self.database_name = config.get("TECH_COSMOS_DB")
        # self.lookup_db_name = config.get("TECH_COSMOS_LOOKUP_DB")

    async def create_gpt_messages(
        self, session_id: str, user_input: str
    ) -> Tuple[List[str], int, Dict, str, Dict]:
        """Create GPT messages from session history.

        Args:
            session_id: Session identifier
            user_input: Current user input

        Returns:
            Tuple of (history_inputs, chat_count, user_info,
            last_bot_scope, last_extract_output)
        """
        # Original code would query Cosmos DB:
        # container = self.database.get_container_client("chat_history")
        # query = "SELECT * FROM c WHERE c.session_id = @session_id"
        # items = list(container.query_items(
        #     query=query,
        #     parameters=[{"name": "@session_id", "value": session_id}]
        # ))

        # Mock return for testing
        his_inputs = [user_input]  # First time user
        chat_count = 1
        user_info = None  # Will use default
        last_bot_scope = ""
        last_extract_output = {}

        return (
            his_inputs,
            chat_count,
            user_info,
            last_bot_scope,
            last_extract_output,
        )

    async def get_latest_hint(
        self, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest hint from Cosmos DB.

        Args:
            session_id: Session identifier

        Returns:
            Latest hint data or None
        """
        # Original code would query:
        # container = self.database.get_container_client("hints")
        # query = "SELECT TOP 1 * FROM c WHERE c.session_id = @session_id"
        # result = list(container.query_items(...))

        # Mock return - no previous hints
        return None  # TODO: Enable when environment ready

    async def get_language_by_websitecode_dev(
        self, websitecode: str
    ) -> str:
        """Get language code from website code.

        Args:
            websitecode: Website code (e.g., 'tw', 'us')

        Returns:
            Language code (e.g., 'zh-TW', 'en-US')
        """
        # Original code would lookup in Cosmos DB
        # container = self.lookup_db.get_container_client("website_mapping")
        # query = "SELECT c.language FROM c WHERE c.code = @code"

        # Mock mapping
        lang_map = {
            "tw": "zh-TW",
            "us": "en-US",
            "cn": "zh-CN",
            "jp": "ja-JP",
        }
        return lang_map.get(websitecode, "zh-TW")

    async def insert_hint_data(
        self,
        chatflow_data: Any,
        intent_hints: List[Dict[str, Any]],
        search_info: str,
        hint_type: str,
    ) -> None:
        """Insert hint data to Cosmos DB.

        Args:
            chatflow_data: Chat flow data
            intent_hints: List of intent hints
            search_info: Search information
            hint_type: Type of hint
        """
        # Original code would insert:
        # container = self.database.get_container_client("hints")
        # hint_doc = {
        #     "id": str(uuid.uuid4()),
        #     "session_id": chatflow_data.session_id,
        #     "hints": intent_hints,
        #     "search_info": search_info,
        #     "type": hint_type,
        #     "timestamp": datetime.utcnow().isoformat()
        # }
        # container.create_item(body=hint_doc)

        # Mock - just log
        print(
            f"[Mock] Would insert hint: type={hint_type}, "
            f"hints={len(intent_hints)}"
        )  # TODO: Enable when environment ready

    async def insert_data(self, cosmos_data: Dict[str, Any]) -> None:
        """Insert data to Cosmos DB.

        Args:
            cosmos_data: Data to insert
        """
        # Original code would insert:
        # container = self.database.get_container_client("chat_logs")
        # container.create_item(body=cosmos_data)

        # Mock - just log
        print(
            f"[Mock] Would insert cosmos data: id={cosmos_data.get('id')}"
        )  # TODO: Enable when environment ready


class MockRedisService:
    """Mock Redis service for testing without actual connection.

    TODO: Enable when environment ready
    """

    def __init__(self, config: Dict[str, Any], session: Any):
        """Initialize mock Redis service.

        Args:
            config: Configuration dictionary
            session: Aiohttp session
        """
        self.config = config
        self.session = session
        # self.redis_url = config.get("REDIS_URL")
        # self.client = await aioredis.create_redis_pool(self.redis_url)

    async def get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data from Redis.

        Args:
            key: Cache key

        Returns:
            Cached data or None
        """
        # Original code would query Redis:
        # data = await self.client.get(key)
        # return json.loads(data) if data else None

        # Mock - no cache
        return None  # TODO: Enable when environment ready

    async def set_cached_data(
        self, key: str, value: Dict[str, Any], ttl: int = 3600
    ) -> None:
        """Set cached data in Redis.

        Args:
            key: Cache key
            value: Data to cache
            ttl: Time to live in seconds
        """
        # Original code would set:
        # await self.client.setex(key, ttl, json.dumps(value))

        # Mock - just log
        print(
            f"[Mock] Would cache: key={key}, ttl={ttl}"
        )  # TODO: Enable when environment ready


class MockServiceDiscriminator:
    """Mock service discriminator for KB search.

    TODO: Enable when environment ready
    """

    def __init__(self, redis_service: Any, base_service: Any):
        """Initialize mock service discriminator.

        Args:
            redis_service: Redis service instance
            base_service: Base service instance
        """
        self.redis = redis_service
        self.base_service = base_service

    async def service_discreminator_with_productline(
        self,
        user_question_english: str,
        site: str,
        specific_kb_mappings: Dict[str, Any],
        productLine: str = "",
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Discriminate service and search KB with product line.

        Args:
            user_question_english: User question in English
            site: Website code
            specific_kb_mappings: Specific KB mappings
            productLine: Product line filter

        Returns:
            Tuple of (faq_result, faq_result_wo_pl)
        """
        # Original would call actual KB search API
        # response = await self.base_service.call_kb_search_api(
        #     question=user_question_english,
        #     site=site,
        #     product_line=productLine
        # )

        # Mock KB search results
        mock_faq_result = {
            "faq": ["KB001", "KB002", "KB003"],
            "cosineSimilarity": [0.92, 0.85, 0.78],
            "productLine": [productLine, productLine, productLine],
        }

        mock_faq_result_wo_pl = {
            "faq": ["KB001", "KB004", "KB005"],
            "cosineSimilarity": [0.92, 0.82, 0.75],
            "productLine": ["notebook", "desktop", "notebook"],
        }

        return (
            mock_faq_result,
            mock_faq_result_wo_pl,
        )  # TODO: Enable when environment ready
