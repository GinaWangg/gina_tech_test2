"""
Repository for external dependencies (stubbed for now).
Handles Cosmos DB, Redis, and other data access.
"""

import asyncio
import pickle
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class DataRepository:
    """
    Central repository for all data access.
    Contains stubbed versions of external dependencies.
    """
    
    def __init__(self):
        """Initialize the repository with config mappings."""
        self.KB_mappings: Dict[str, Any] = {}
        self.rag_mappings: Dict[str, Any] = {}
        self.rag_hint_id_index_mapping: Dict[str, Any] = {}
        self.PL_mappings: Dict[str, Any] = {}
        self.productline_name_map: Dict[str, str] = {}
        self.specific_kb_mappings: Dict[str, Any] = {}
        
        # Load data during initialization
        self._load_config_data()
    
    def _load_config_data(self):
        """Load configuration data from pickle files."""
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        
        try:
            # Load RAG mappings
            rag_hint_path = project_root / "config" / "rag_hint_id_index_mapping.pkl"
            rag_map_path = project_root / "config" / "rag_mappings.pkl"
            
            if rag_hint_path.exists():
                with open(rag_hint_path, "rb") as f:
                    self.rag_hint_id_index_mapping = pickle.load(f)
            
            if rag_map_path.exists():
                with open(rag_map_path, "rb") as f:
                    self.rag_mappings = pickle.load(f)
            
            # Load KB mappings
            kb_path = project_root / "config" / "kb_mappings.pkl"
            if kb_path.exists():
                with open(kb_path, "rb") as f:
                    self.KB_mappings = pickle.load(f)
                    
        except Exception as e:
            print(f"Warning: Could not load config data: {e}")
    
    async def create_gpt_messages(
        self,
        session_id: str,
        user_input: str
    ) -> Tuple[List[str], int, Optional[Dict], Optional[str], Dict]:
        """
        Create GPT messages from chat history.
        
        # TODO: Enable when environment ready
        # Original implementation would query Cosmos DB for history
        # and build conversation context
        
        Returns:
            Tuple of (his_inputs, chat_count, user_info, 
                     last_bot_scope, last_extract_output)
        """
        # Stubbed: Return minimal history
        his_inputs = [user_input]
        chat_count = 1
        user_info = None
        last_bot_scope = None
        last_extract_output = {}
        
        return (his_inputs, chat_count, user_info, 
                last_bot_scope, last_extract_output)
    
    async def get_latest_hint(self, session_id: str) -> Optional[Dict]:
        """
        Get latest hint for the session.
        
        # TODO: Enable when environment ready
        # Would query Cosmos for the latest hint data
        
        Returns:
            Hint data or None
        """
        return None
    
    async def get_language_by_websitecode(
        self, 
        websitecode: str
    ) -> str:
        """
        Get language code by website code.
        
        # TODO: Enable when environment ready
        # Would query configuration DB for language mapping
        
        Returns:
            Language code (e.g., 'zh-tw', 'en')
        """
        # Stubbed mapping
        lang_map = {
            "tw": "zh-tw",
            "cn": "zh-cn",
            "us": "en",
            "jp": "ja",
        }
        return lang_map.get(websitecode.lower(), "zh-tw")
    
    async def get_productline(
        self,
        category: str,
        site: str
    ) -> Optional[str]:
        """
        Get product line from category.
        
        # TODO: Enable when environment ready
        # Would query Redis/DB for product line mapping
        
        Returns:
            Product line string or None
        """
        # Stubbed: Simple mapping
        pl_map = {
            "notebook": "notebook",
            "desktop": "desktop",
            "phone": "phone",
            "motherboard": "motherboard",
        }
        return pl_map.get(category)
    
    async def get_hint_similarity(
        self,
        search_info: str
    ) -> Dict[str, Any]:
        """
        Get hint similarity result.
        
        # TODO: Enable when environment ready
        # Would query vector DB for hint similarity
        
        Returns:
            Dict with faq and hints_id
        """
        return {"faq": None, "hints_id": None}
    
    async def service_discriminator_with_productline(
        self,
        user_question_english: str,
        site: str,
        specific_kb_mappings: Dict,
        productLine: Optional[str] = None
    ) -> Tuple[Dict, Dict]:
        """
        Search knowledge base with product line filter.
        
        # TODO: Enable when environment ready
        # Would call external API for knowledge base search
        
        Returns:
            Tuple of (faq_result, faq_result_wo_pl)
        """
        # Stubbed: Return mock FAQ results
        faq_result = {
            "faq": [1051479, 1038855, 1046480, 1042613],
            "cosineSimilarity": [
                0.816743731499,
                0.751851916313,
                0.701354265213,
                0.700322508812
            ],
            "productLine": [
                "chromebook,desktop,gaming_handhelds,motherboard,notebook",
                "chromebook,desktop,gaming_handhelds,notebook,nuc",
                "chromebook,desktop,gaming_handhelds,motherboard,notebook,nuc",
                "chromebook,desktop,gaming_handhelds,notebook"
            ]
        }
        
        faq_result_wo_pl = {
            "faq": [1051479, 1038855, 1046480, 1042613],
            "cosineSimilarity": [
                0.816743731499,
                0.751851916313,
                0.701354265213,
                0.700322508812
            ],
            "productLine": [
                "chromebook,desktop,gaming_handhelds,motherboard,notebook",
                "chromebook,desktop,gaming_handhelds,notebook,nuc",
                "chromebook,desktop,gaming_handhelds,motherboard,notebook,nuc",
                "chromebook,desktop,gaming_handhelds,notebook"
            ]
        }
        
        return (faq_result, faq_result_wo_pl)
    
    async def insert_hint_data(
        self,
        chatflow_data: Any,
        intent_hints: List[Dict],
        search_info: str,
        hint_type: str
    ) -> None:
        """
        Insert hint data to Cosmos DB.
        
        # TODO: Enable when environment ready
        # await cosmos_client.insert_hint(...)
        
        Args:
            chatflow_data: Chat flow data
            intent_hints: List of intent hints
            search_info: Search information
            hint_type: Type of hint
        """
        # Stubbed: No actual insert
        pass
    
    async def insert_data(self, cosmos_data: Dict) -> None:
        """
        Insert data to Cosmos DB.
        
        # TODO: Enable when environment ready
        # await cosmos_client.insert(...)
        
        Args:
            cosmos_data: Data to insert
        """
        # Stubbed: No actual insert
        print(f"[STUB] Would insert to Cosmos: {cosmos_data.get('id')}")
    
    async def sentence_group_classification(
        self,
        inputs: List[str]
    ) -> Dict:
        """
        Classify sentence groups.
        
        # TODO: Enable when environment ready
        # Would call GPT for sentence grouping
        
        Returns:
            Classification result with groups
        """
        # Stubbed: Return single group
        return {
            "groups": [
                {
                    "statements": inputs
                }
            ]
        }
    
    async def gpt_call(
        self,
        prompt: List[Dict[str, str]],
        model: str = "gpt-4"
    ) -> str:
        """
        Call GPT model.
        
        # TODO: Enable when environment ready
        # result = await openai_client.chat.completions.create(...)
        
        Returns:
            GPT response text
        """
        # Stubbed response
        return "true"
    
    async def translate_text(
        self,
        text: str,
        target_lang: str
    ) -> str:
        """
        Translate text to target language.
        
        # TODO: Enable when environment ready
        # result = await translator.translate(...)
        
        Returns:
            Translated text
        """
        # Stubbed: Return original text
        return text
