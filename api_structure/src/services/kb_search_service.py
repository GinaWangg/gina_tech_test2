"""Knowledge base search service."""

from typing import Dict, List, Any


class KBSearchService:
    """Service for searching knowledge base.

    Handles KB similarity search and result filtering.
    """

    def __init__(self):
        """Initialize KB search service."""
        self.kb_threshold = 0.92
        self.top1_kb_similarity_threshold = 0.87

    async def search_kb_with_product_line(
        self,
        search_info: str,
        websitecode: str,
        product_line: str,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Search knowledge base with product line filter.

        Args:
            search_info: Search query information.
            websitecode: Website code (e.g., 'tw').
            product_line: Product line filter.

        Returns:
            Tuple of (faq_result_with_pl, faq_result_without_pl)
        """
        # TODO: Enable when environment ready
        # Original: ServiceDiscriminator with Redis/Vector DB
        # For now, return mock data
        faq_result_with_pl = {
            "faq": ["1049581"],
            "cosineSimilarity": [0.85],
            "productLine": ["notebook"],
        }

        faq_result_without_pl = {
            "faq": ["1049581", "1048932"],
            "cosineSimilarity": [0.85, 0.82],
            "productLine": ["notebook", "desktop"],
        }

        return faq_result_with_pl, faq_result_without_pl

    def filter_kb_results(
        self, faq_result: Dict[str, Any]
    ) -> tuple[List[str], str, float, List[Dict[str, Any]]]:
        """Filter and process KB search results.

        Args:
            faq_result: Raw FAQ search result.

        Returns:
            Tuple of (top4_kb_list, top1_kb, top1_kb_sim, faqs_wo_pl)
        """
        faq_list = faq_result.get("faq", [])
        sim_list = faq_result.get("cosineSimilarity", [])

        # Filter by threshold and take top 3
        top4_kb_list = [
            faq
            for faq, sim in zip(faq_list, sim_list)
            if sim >= self.kb_threshold
        ][:3]

        top1_kb = faq_list[0] if faq_list else ""
        top1_kb_sim = sim_list[0] if sim_list else 0.0

        faqs_wo_pl = [
            {"kb_no": faq, "cosineSimilarity": sim, "productLine": pl}
            for faq, sim, pl in zip(
                faq_result.get("faq", []),
                faq_result.get("cosineSimilarity", []),
                faq_result.get("productLine", []),
            )
        ]

        return top4_kb_list, top1_kb, top1_kb_sim, faqs_wo_pl
