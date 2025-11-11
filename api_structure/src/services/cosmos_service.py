"""Cosmos database service (stubbed for testing)."""

from typing import Any, Dict, List, Optional


class CosmosService:
    """Service for Cosmos DB operations.

    All operations are stubbed with mock data until environment is ready.
    """

    def __init__(self):
        """Initialize Cosmos service."""
        # TODO: Enable when environment ready
        # self.url = config.get("TECH_COSMOS_URL")
        # self.key = config.get("TECH_COSMOS_KEY")
        # self.client = CosmosClient(self.url, credential=self.key)
        pass

    async def create_gpt_messages(
        self, session_id: str, user_input: str
    ) -> tuple[List[str], int, Dict[str, Any], str, Dict[str, Any]]:
        """Create GPT messages from session history.

        Args:
            session_id: Session identifier.
            user_input: Current user input.

        Returns:
            Tuple of (his_inputs, chat_count, user_info,
                      last_bot_scope, last_extract_output)
        """
        # TODO: Enable when environment ready
        # Original: Query Cosmos for session history
        # result = await self.async_container.query_items(
        #     query=..., partition_key=session_id
        # )
        # For now, return mock data
        his_inputs = [user_input]
        chat_count = 1
        user_info = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": None,
            "sub_product_category": None,
            "first_time": True,
        }
        last_bot_scope = ""
        last_extract_output = {}

        return his_inputs, chat_count, user_info, last_bot_scope, last_extract_output

    async def get_latest_hint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get latest hint for session.

        Args:
            session_id: Session identifier.

        Returns:
            Latest hint data or None.
        """
        # TODO: Enable when environment ready
        # Original: Query hint_container for latest hint
        # For now, return None (no hint)
        return None

    async def get_language_by_websitecode(self, websitecode: str) -> str:
        """Get language code from website code.

        Args:
            websitecode: Website code (e.g., 'tw').

        Returns:
            Language code (e.g., 'zh-tw').
        """
        # TODO: Enable when environment ready
        # Original: Lookup in Cosmos lookup database
        # For now, return mock mapping
        website_lang_map = {
            "tw": "zh-tw",
            "cn": "zh-cn",
            "us": "en-us",
            "jp": "ja-jp",
        }
        return website_lang_map.get(websitecode, "zh-tw")

    async def insert_hint_data(
        self,
        chatflow_data: Any,
        intent_hints: List[Dict[str, Any]],
        search_info: str,
        hint_type: str,
    ) -> None:
        """Insert hint data into Cosmos.

        Args:
            chatflow_data: Chat flow data object.
            intent_hints: List of intent hints.
            search_info: Search information.
            hint_type: Type of hint.
        """
        # TODO: Enable when environment ready
        # Original: Insert into hint_container
        # hint_data = {
        #     "id": f"{chatflow_data.cus_id}-{chatflow_data.session_id}-hint",
        #     "session_id": chatflow_data.session_id,
        #     "hintType": hint_type,
        #     "intentHints": intent_hints,
        #     "searchInfo": search_info,
        #     "createDate": datetime.utcnow().isoformat() + "Z"
        # }
        # await self.async_hint_container.create_item(hint_data)
        pass  # Mock: Do nothing

    async def insert_data(self, cosmos_data: Dict[str, Any]) -> None:
        """Insert conversation data into Cosmos.

        Args:
            cosmos_data: Complete conversation data to store.
        """
        # TODO: Enable when environment ready
        # Original: Insert into main container
        # await self.async_container.create_item(cosmos_data)
        pass  # Mock: Do nothing

    async def query_sentence_groups(
        self, his_inputs: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Query sentence group classification.

        Args:
            his_inputs: Historical inputs.

        Returns:
            Sentence group classification result or None.
        """
        # TODO: Enable when environment ready
        # Original: GPT-based sentence grouping
        # For now, return None (no grouping)
        return None
