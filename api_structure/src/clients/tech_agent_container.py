"""Stub container for tech agent dependencies.

This module provides stub implementations of services that would normally
connect to external APIs and databases. These stubs return mock data
for testing purposes.
"""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

from api_structure.core.logger import logger


class StubCosmosConfig:
    """Stub Cosmos DB configuration - returns mock data."""

    def __init__(self):
        """Initialize stub cosmos config."""
        logger.info("Initializing StubCosmosConfig (mock mode)")

    async def create_GPT_messages(
        self, session_id: str, user_input: str
    ) -> tuple:
        """Create GPT messages from history.

        Returns mock history data.
        """
        # TODO: Enable when environment ready
        # Real implementation would query Cosmos DB
        his_inputs = [user_input]
        chat_count = 1
        user_info = None
        last_bot_scope = None
        last_extract_output = {}

        return (
            his_inputs,
            chat_count,
            user_info,
            last_bot_scope,
            last_extract_output,
        )

    async def get_latest_hint(self, session_id: str) -> Optional[Dict]:
        """Get latest hint from session.

        Returns None as mock data.
        """
        # TODO: Enable when environment ready
        return None

    async def get_language_by_websitecode_dev(self, websitecode: str) -> str:
        """Get language from website code.

        Returns mock language based on website code.
        """
        lang_map = {
            "tw": "zh-tw",
            "cn": "zh-cn",
            "us": "en",
            "uk": "en",
            "jp": "ja",
        }
        return lang_map.get(websitecode.lower(), "zh-tw")

    async def insert_hint_data(
        self,
        chatflow_data: Any,
        intent_hints: List,
        search_info: str,
        hint_type: str,
    ) -> None:
        """Insert hint data to Cosmos DB.

        Mock implementation - logs but doesn't actually insert.
        """
        # TODO: Enable when environment ready
        logger.info(
            f"[STUB] Would insert hint data: type={hint_type}, "
            f"hints count={len(intent_hints)}"
        )

    async def insert_data(self, cosmos_data: Dict) -> None:
        """Insert data to Cosmos DB.

        Mock implementation - logs but doesn't actually insert.
        """
        # TODO: Enable when environment ready
        logger.info(
            f"[STUB] Would insert cosmos data: "
            f"id={cosmos_data.get('id', 'unknown')}"
        )


class StubRedisConfig:
    """Stub Redis configuration - returns mock data."""

    def __init__(self):
        """Initialize stub redis config."""
        logger.info("Initializing StubRedisConfig (mock mode)")

    async def get_productline(
        self, product_category: str, site: str
    ) -> Optional[str]:
        """Get product line from Redis.

        Returns mock product line.
        """
        # TODO: Enable when environment ready
        return "Laptops"

    async def get_hint_simiarity(self, search_info: str) -> Dict:
        """Get hint similarity from Redis.

        Returns mock similarity data.
        """
        # TODO: Enable when environment ready
        return {
            "faq": "1234567",
            "hints_id": "hint_001",
            "similarity": 0.85,
        }


class StubServiceDiscriminator:
    """Stub service discriminator - returns mock KB results."""

    def __init__(self):
        """Initialize stub service discriminator."""
        logger.info("Initializing StubServiceDiscriminator (mock mode)")

    async def service_discreminator_with_productline(
        self,
        user_question_english: str,
        site: str,
        specific_kb_mappings: Dict,
        productLine: Optional[str],
    ) -> tuple:
        """Discriminate service with product line.

        Returns mock KB search results.
        """
        # TODO: Enable when environment ready
        # Mock response with high similarity
        faq_result = {
            "faq": ["1234567", "1234568", "1234569"],
            "cosineSimilarity": [0.92, 0.88, 0.85],
        }
        faq_result_wo_pl = {
            "faq": ["1234567", "1234568", "1234569", "1234570"],
            "cosineSimilarity": [0.92, 0.88, 0.85, 0.82],
            "productLine": ["Laptops", "Laptops", "Desktop", "Phone"],
        }
        return (faq_result, faq_result_wo_pl)


class StubSentenceGroupClassification:
    """Stub sentence group classification."""

    def __init__(self):
        """Initialize stub sentence group classification."""
        logger.info("Initializing StubSentenceGroupClassification (mock mode)")

    async def sentence_group_classification(
        self, his_inputs: List[str]
    ) -> Dict:
        """Classify sentence groups.

        Returns mock classification result.
        """
        # TODO: Enable when environment ready
        return {"groups": [{"statements": his_inputs}]}


class StubBaseService:
    """Stub base service for GPT calls."""

    def __init__(self):
        """Initialize stub base service."""
        logger.info("Initializing StubBaseService (mock mode)")

    async def GPT41_mini_response(self, prompt: List[Dict]) -> str:
        """Get GPT response.

        Returns mock response.
        """
        # TODO: Enable when environment ready
        # For tech support related question
        return "true"


class StubUserinfoDiscriminator:
    """Stub userinfo discriminator."""

    def __init__(self):
        """Initialize stub userinfo discriminator."""
        logger.info("Initializing StubUserinfoDiscriminator (mock mode)")

    async def reply_with_gpt(self, his_inputs: List[str]) -> tuple:
        """Get user info from GPT.

        Returns mock user info.
        """
        # TODO: Enable when environment ready
        user_info = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": "Laptops",
            "sub_product_category": None,
        }
        return (user_info, "")


class StubFollowUpClassifier:
    """Stub follow-up classifier."""

    def __init__(self):
        """Initialize stub follow-up classifier."""
        logger.info("Initializing StubFollowUpClassifier (mock mode)")

    async def reply_with_gpt(
        self,
        prev_question: str,
        prev_answer: str,
        prev_answer_refs: str,
        new_question: str,
    ) -> Dict:
        """Check if follow-up question.

        Returns mock result.
        """
        # TODO: Enable when environment ready
        return {"is_follow_up": False}


class TechAgentContainer:
    """Container for tech agent dependencies with stub implementations."""

    def __init__(self):
        """Initialize tech agent container with stubs."""
        self.cosmos_settings = StubCosmosConfig()
        self.redis_config = StubRedisConfig()
        self.sd = StubServiceDiscriminator()
        self.sentence_group_classification = StubSentenceGroupClassification()
        self.base_service = StubBaseService()
        self.userinfo_discrimiator = StubUserinfoDiscriminator()
        self.followup_discrimiator = StubFollowUpClassifier()

        # Load mock mappings
        self.rag_mappings: Dict[str, Any] = {}
        self.rag_hint_id_index_mapping: Dict[str, Any] = {}
        self.KB_mappings: Dict[str, Any] = {}
        self.PL_mappings: Dict[str, List[str]] = {
            "tw": ["Laptops", "Desktop", "Phone", "Wearable"],
            "us": ["Laptops", "Desktop", "Phone", "Wearable"],
        }
        self.productline_name_map: Dict[str, str] = {}
        self.specific_kb_mappings: Dict[str, Any] = {}

        # Try to load pickle files if they exist
        self._load_pickle_files()

    def _load_pickle_files(self) -> None:
        """Load pickle files if they exist."""
        project_root = Path(__file__).parent.parent.parent.parent
        config_dir = project_root / "config"

        # Load RAG mappings
        rag_mappings_file = config_dir / "rag_mappings.pkl"
        if rag_mappings_file.exists():
            try:
                with open(rag_mappings_file, "rb") as f:
                    self.rag_mappings = pickle.load(f)
                logger.info(
                    f"Loaded rag_mappings with {len(self.rag_mappings)} "
                    "entries"
                )
            except Exception as e:
                logger.warning(
                    f"Could not load rag_mappings.pkl: {e}, using mock"
                )
        else:
            logger.info("rag_mappings.pkl not found, using mock data")

        # Load RAG hint ID index mapping
        rag_hint_file = config_dir / "rag_hint_id_index_mapping.pkl"
        if rag_hint_file.exists():
            try:
                with open(rag_hint_file, "rb") as f:
                    self.rag_hint_id_index_mapping = pickle.load(f)
                logger.info(
                    f"Loaded rag_hint_id_index_mapping with "
                    f"{len(self.rag_hint_id_index_mapping)} entries"
                )
            except Exception as e:
                logger.warning(
                    f"Could not load rag_hint_id_index_mapping.pkl: {e}, "
                    "using mock"
                )
        else:
            logger.info(
                "rag_hint_id_index_mapping.pkl not found, using mock data"
            )

        # Load KB mappings
        kb_mappings_file = config_dir / "kb_mappings.pkl"
        if kb_mappings_file.exists():
            try:
                with open(kb_mappings_file, "rb") as f:
                    self.KB_mappings = pickle.load(f)
                logger.info(
                    f"Loaded KB_mappings with {len(self.KB_mappings)} "
                    "entries"
                )
            except Exception as e:
                logger.warning(
                    f"Could not load kb_mappings.pkl: {e}, using mock"
                )
        else:
            logger.info("kb_mappings.pkl not found, using mock data")

        # Create mock KB data if no real data exists
        if not self.KB_mappings:
            self._create_mock_kb_data()

    def _create_mock_kb_data(self) -> None:
        """Create mock KB data for testing."""
        mock_kb_ids = ["1234567", "1234568", "1234569"]
        for kb_id in mock_kb_ids:
            for lang in ["zh-tw", "en", "ja"]:
                key = f"{kb_id}_{lang}"
                self.KB_mappings[key] = {
                    "kb_no": kb_id,
                    "title": f"模擬技術支援問題 {kb_id}",
                    "content": "這是模擬的技術支援內容，用於測試系統。",
                    "summary": "模擬摘要",
                }

        # Create mock RAG hints
        for kb_id in mock_kb_ids:
            for site in ["tw", "us"]:
                for idx in ["1", "2"]:
                    key = f"{kb_id}_{site}_{idx}"
                    self.rag_mappings[key] = {
                        "question": f"模擬問題 {kb_id}",
                        "title": "Laptops",
                        "title_name": "筆記型電腦",
                        "icon": "laptop",
                        "ASUS_link": (
                            f"https://www.asus.com/{site}/support/"
                            f"FAQ/{kb_id}"
                        ),
                        "ROG_link": (
                            f"https://rog.asus.com/{site}/support/"
                            f"FAQ/{kb_id}"
                        ),
                    }

        logger.info("Created mock KB data for testing")

    async def initialize(self) -> None:
        """Initialize async components."""
        logger.info("TechAgentContainer initialized (stub mode)")

    async def close(self) -> None:
        """Close and cleanup resources."""
        logger.info("TechAgentContainer closed")
