"""
Knowledge Base (KB) and RAG repository.
Handles KB search and RAG operations with stubbed implementations.
"""

from typing import Any, Dict, List, Optional, Tuple
from api_structure.core.logger import logger


class KBRepository:
    """Repository for Knowledge Base and RAG operations."""

    def __init__(self):
        """Initialize KB repository."""
        self.rag_mappings: Dict[str, Any] = {}
        self.rag_hint_id_index_mapping: Dict[str, Any] = {}
        self._init_mock_data()

    def _init_mock_data(self) -> None:
        """Initialize mock data for stubbed operations."""
        # Mock RAG mappings
        self.rag_mappings = {
            "1234_tw_1": {
                "question": "如何重新啟動電腦？",
                "title": "重新啟動",
                "title_name": "重新啟動電腦",
                "icon": "restart",
                "ASUS_link": "https://www.asus.com/support/FAQ/1234",
                "ROG_link": "https://rog.asus.com/support/FAQ/1234"
            }
        }
        
        self.rag_hint_id_index_mapping = {
            "hint_001_tw": {"index": 1}
        }

    async def search_kb_with_productline(
        self,
        user_question: str,
        site: str,
        productline: Optional[str],
        specific_kb_mappings: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Search knowledge base with product line filter.
        
        Args:
            user_question: User's question
            site: Website code
            productline: Product line filter
            specific_kb_mappings: Specific KB mappings
            
        Returns:
            Tuple of (results_with_pl, results_without_pl)
        """
        # TODO: Enable when environment ready
        # result_pl = await kb_service.search(
        #     query=user_question,
        #     filters={"productLine": productline, "site": site}
        # )
        # result_all = await kb_service.search(
        #     query=user_question,
        #     filters={"site": site}
        # )
        
        # Mock response with product line
        results_with_pl = {
            "faq": ["1234", "5678"],
            "cosineSimilarity": [0.92, 0.85],
            "productLine": [productline, productline]
        }
        
        # Mock response without product line
        results_without_pl = {
            "faq": ["1234", "5678", "9012"],
            "cosineSimilarity": [0.92, 0.85, 0.78],
            "productLine": [productline, productline, "other"]
        }
        
        logger.info(
            f"[KB] search_kb_with_productline (MOCK): "
            f"query={user_question[:50]}, pl={productline}"
        )
        
        return (results_with_pl, results_without_pl)

    def get_rag_hint(
        self, kb: str, site: str, index_suffix: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get RAG hint by KB number, site, and index.
        
        Args:
            kb: KB number
            site: Website code
            index_suffix: Index suffix (e.g., "1", "2")
            
        Returns:
            RAG hint data or None
        """
        rag_key = f"{kb}_{site}_{index_suffix}"
        hint = self.rag_mappings.get(rag_key)
        
        if not hint:
            logger.warning(f"[KB] RAG hint not found (MOCK): {rag_key}")
            return None
        
        return hint.copy()

    def get_hint_index(
        self, hints_id: str, site: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get hint index mapping.
        
        Args:
            hints_id: Hint ID
            site: Website code
            
        Returns:
            Hint index data or None
        """
        key = f"{hints_id}_{site}"
        return self.rag_hint_id_index_mapping.get(key)
