from openai import AsyncAzureOpenAI
from src.integrations.Redis_process import RedisConfig
from src.integrations.cosmos_process import CosmosConfig
from src.services.sentence_group_classification import SentenceGroupClassification
from src.services.service_discriminator_merge_input import ServiceDiscriminator
from src.services.content_policy_check import ContentPolicyCheck
from src.core.userInfo_discriminator import UserinfoDiscriminator, FollowUpClassifierFunctionOnly
from src.services.base_service import BaseService
import os
# from src.core.config_loader import load_config
from src.core.config_loader import * 

# ========================
# ✅ 環境與設定初始化
# ========================
os.environ["CURRENT_ENV"] = "dev"
# env = os.getenv("CURRENT_ENV", "dev")
# env_config = load_config()
# cfg = env_config

class DependencyContainer:
    def __init__(self):
        self.cfg = config
        self.aiohttp_session = None  # 暫不初始化

        # 共用設定與資源先留空
        self.redis_config = None
        self.cosmos_settings = None
        self.sentence_group_classification = None
        self.lookup_db = None

        # 工具類也先留空
        self.base_service = None
        self.merge_user_input = None
        self.sd = None
        self.content_policy_check = None
        self.userinfo_discrimiator = None
        self.userinfo_discrimiator_mkt = None
        self.followup_discrimiator = None

        # 暫存資料
        self.rag_mappings = {}
        self.rag_hint_id_index_mapping = {}
        self.KB_mappings = {}
        self.PL_mappings = {}
        self.productline_name_map = {}
        self.specific_kb_mappings = {}

        trans_endpoint     = require(f"TECH_OPENAI_GPT41MINI_PAYGO_EU_AZURE_ENDPOINT").rstrip("/")
        openai_api_key     = require(f"TECH_OPENAI_GPT41MINI_PAYGO_EU_API_KEY")
        openai_api_version = require(f"TECH_OPENAI_GPT41MINI_PAYGO_EU_API_VERSION")
        self._trans_client = AsyncAzureOpenAI(
            azure_endpoint=trans_endpoint,
            api_key=openai_api_key,
            api_version=openai_api_version,
        )
        self.creds_trans = require("TECH_TRANSLATE_CREDENTIALS")

    async def init_async(self, aiohttp_session):
        # 非同步初始化 aiohttp session
        self.aiohttp_session = aiohttp_session

        # 依賴初始化（需要 session 的）
        self.redis_config = RedisConfig(config=self.cfg, session=self.aiohttp_session)
        self.cosmos_settings = CosmosConfig(config=self.cfg)
        self.sentence_group_classification = SentenceGroupClassification(config=self.cfg)
        # self.lookup_db = self.cosmos_settings.lookup_db # gina 為了測試copilot 暫時不跑

        self.base_service = BaseService(config=self.cfg)
        self.sd = ServiceDiscriminator(self.redis_config, self.base_service)
        self.content_policy_check = ContentPolicyCheck(config=self.cfg)
        self.userinfo_discrimiator = UserinfoDiscriminator(config=self.cfg)
        self.followup_discrimiator = FollowUpClassifierFunctionOnly(config=self.cfg)

    async def close(self):
        if self.aiohttp_session:
            await self.aiohttp_session.close()

    def load_rag_pickle(self, rag_data, rag_index):
        self.rag_mappings = rag_data
        self.rag_hint_id_index_mapping = rag_index

    def load_kb_mappings(self, kb_mappings):
        self.KB_mappings = kb_mappings

    def load_pl_mappings(self, pl_mappings, pl_name_map):
        self.PL_mappings = pl_mappings
        self.productline_name_map = pl_name_map

    def load_specific_kb(self, specific_kb):
        self.specific_kb_mappings = specific_kb