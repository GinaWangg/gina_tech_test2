"""
Redis repository for tech_agent.
Handles all Redis operations with stubbed implementations.
"""

from typing import Any, Dict, Optional
from api_structure.core.logger import logger


class RedisRepository:
    """Repository for Redis operations."""

    def __init__(self):
        """Initialize Redis repository."""
        self.productline_name_map: Dict[str, str] = {}
        self._init_mock_data()

    def _init_mock_data(self) -> None:
        """Initialize mock data for stubbed operations."""
        self.productline_name_map = {
            "notebook": "筆記型電腦",
            "desktop": "桌上型電腦",
            "phone": "手機",
            "monitor": "螢幕"
        }

    async def get_productline(
        self, product_key: str, site: str
    ) -> Optional[str]:
        """
        Get product line from Redis.
        
        Args:
            product_key: Product key identifier
            site: Website code
            
        Returns:
            Product line name or None
        """
        # TODO: Enable when environment ready
        # result = await redis_client.get(f"pl:{product_key}:{site}")
        
        # Mock response
        pl = self.productline_name_map.get(product_key, product_key)
        logger.info(
            f"[Redis] get_productline (MOCK): "
            f"{product_key}@{site} -> {pl}"
        )
        return pl

    async def get_hint_similarity(
        self, search_info: str
    ) -> Dict[str, Any]:
        """
        Get hint similarity from Redis.
        
        Args:
            search_info: Search information
            
        Returns:
            Hint similarity data
        """
        # TODO: Enable when environment ready
        # result = await redis_client.search_hints(search_info)
        
        # Mock response
        logger.info(
            f"[Redis] get_hint_similarity (MOCK): query={search_info[:50]}"
        )
        return {
            "faq": "1234",
            "hints_id": "hint_001",
            "similarity": 0.85
        }
