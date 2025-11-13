"""
Cosmos DB repository for tech_agent.
Handles all Cosmos DB operations with stubbed implementations.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from api_structure.core.logger import logger


class CosmosRepository:
    """Repository for Cosmos DB operations."""

    def __init__(self):
        """Initialize Cosmos repository."""
        self.KB_mappings: Dict[str, Any] = {}
        self.PL_mappings: Dict[str, List[str]] = {}
        self.specific_kb_mappings: Dict[str, Any] = {}
        
        # Mock data for testing
        self._init_mock_data()

    def _init_mock_data(self) -> None:
        """Initialize mock data for stubbed operations."""
        # Mock KB mappings
        self.KB_mappings = {
            "1234_zh-tw": {
                "title": "筆電登入問題",
                "content": "如果筆電卡在登入畫面，請嘗試重新啟動電腦。",
                "summary": "處理筆電登入畫面卡住的問題",
                "link": "https://www.asus.com/support/FAQ/1234"
            }
        }
        
        # Mock PL mappings
        self.PL_mappings = {
            "tw": ["notebook", "desktop", "phone", "monitor"],
            "us": ["notebook", "desktop", "phone", "monitor"]
        }

    async def create_gpt_messages(
        self, session_id: str, user_input: str
    ) -> Tuple[List[str], int, Optional[Dict], Optional[str], Optional[Dict]]:
        """
        Create GPT messages from chat history.
        
        Args:
            session_id: Session identifier
            user_input: Current user input
            
        Returns:
            Tuple of (his_inputs, chat_count, user_info, 
                      last_bot_scope, last_extract_output)
        """
        # TODO: Enable when environment ready
        # result = await cosmos_client.query_messages(session_id)
        
        # Mock response
        his_inputs = [user_input]
        chat_count = 1
        user_info = None
        last_bot_scope = None
        last_extract_output = None
        
        logger.info(
            f"[Cosmos] create_gpt_messages (MOCK): session={session_id}"
        )
        
        return (
            his_inputs, chat_count, user_info, 
            last_bot_scope, last_extract_output
        )

    async def get_latest_hint(
        self, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get latest hint from session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Latest hint data or None
        """
        # TODO: Enable when environment ready
        # result = await cosmos_client.query_hint(session_id)
        
        # Mock response
        logger.info(
            f"[Cosmos] get_latest_hint (MOCK): session={session_id}"
        )
        return None

    async def get_language_by_websitecode(
        self, websitecode: str
    ) -> str:
        """
        Get language code from website code.
        
        Args:
            websitecode: Website code (e.g., 'tw', 'us')
            
        Returns:
            Language code (e.g., 'zh-tw', 'en-us')
        """
        # TODO: Enable when environment ready
        # result = await cosmos_client.query_language(websitecode)
        
        # Mock mapping
        lang_map = {
            "tw": "zh-tw",
            "cn": "zh-cn",
            "us": "en-us",
            "uk": "en-gb",
            "jp": "ja-jp"
        }
        
        lang = lang_map.get(websitecode.lower(), "zh-tw")
        logger.info(
            f"[Cosmos] get_language_by_websitecode (MOCK): "
            f"{websitecode} -> {lang}"
        )
        return lang

    async def insert_hint_data(
        self,
        chatflow_data: Any,
        intent_hints: List[Dict[str, Any]],
        search_info: str,
        hint_type: str
    ) -> None:
        """
        Insert hint data to Cosmos DB.
        
        Args:
            chatflow_data: Chat flow data
            intent_hints: Intent hint candidates
            search_info: Search information
            hint_type: Type of hint
        """
        # TODO: Enable when environment ready
        # await cosmos_client.insert_hint({
        #     "session_id": chatflow_data.session_id,
        #     "intentHints": intent_hints,
        #     "searchInfo": search_info,
        #     "hintType": hint_type
        # })
        
        logger.info(
            f"[Cosmos] insert_hint_data (MOCK): "
            f"type={hint_type}, hints_count={len(intent_hints)}"
        )

    async def insert_data(self, cosmos_data: Dict[str, Any]) -> None:
        """
        Insert conversation data to Cosmos DB.
        
        Args:
            cosmos_data: Complete conversation data to store
        """
        # TODO: Enable when environment ready
        # await cosmos_client.upsert_item(cosmos_data)
        
        logger.info(
            f"[Cosmos] insert_data (MOCK): "
            f"id={cosmos_data.get('id', 'unknown')}"
        )

    def get_kb_content(
        self, kb_no: str, lang: str
    ) -> Optional[Dict[str, str]]:
        """
        Get KB content by number and language.
        
        Args:
            kb_no: KB number
            lang: Language code
            
        Returns:
            KB content dict or None
        """
        key = f"{kb_no}_{lang}"
        content = self.KB_mappings.get(key)
        
        if not content:
            logger.warning(
                f"[Cosmos] KB content not found (MOCK): {key}"
            )
            return {
                "title": "知識庫內容",
                "content": "這是模擬的知識庫內容。",
                "summary": "模擬摘要",
                "link": f"https://www.asus.com/support/FAQ/{kb_no}"
            }
        
        return content

    def get_pl_list(self, site: str) -> List[str]:
        """
        Get product line list for site.
        
        Args:
            site: Website code
            
        Returns:
            List of product lines
        """
        return self.PL_mappings.get(site, [])
