"""
Tech Agent Pipeline - Orchestration layer.
Coordinates handlers to process tech agent requests.
"""

import json
import time
from datetime import datetime
from typing import Any, Dict

from api_structure.core.logger import logger
from api_structure.core.timer import timed
from api_structure.src.schemas.tech_agent_schemas import (
    TechAgentInput,
    CosmosLogData,
    ProcessInfo
)
from api_structure.src.handlers.tech_agent_handlers import (
    ChatInitHandler,
    HistoryProcessHandler,
    UserInfoHandler,
    KBSearchHandler,
    ResponseGenerationHandler
)


class TechAgentPipeline:
    """Pipeline for processing tech agent requests."""

    def __init__(
        self,
        cosmos_repo: Any,
        redis_repo: Any,
        kb_repo: Any
    ):
        """
        Initialize pipeline with repositories.
        
        Args:
            cosmos_repo: Cosmos DB repository
            redis_repo: Redis repository
            kb_repo: Knowledge base repository
        """
        self.cosmos_repo = cosmos_repo
        self.redis_repo = redis_repo
        self.kb_repo = kb_repo

        # Initialize handlers
        self.chat_init_handler = ChatInitHandler(
            cosmos_repo, redis_repo, kb_repo
        )
        self.history_handler = HistoryProcessHandler()
        self.user_info_handler = UserInfoHandler(redis_repo, cosmos_repo)
        self.kb_search_handler = KBSearchHandler(kb_repo)
        self.response_handler = ResponseGenerationHandler(
            cosmos_repo, redis_repo, kb_repo
        )

    @timed(task_name="tech_agent_pipeline_run")
    async def run(
        self, user_input: TechAgentInput, log_record: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the complete tech agent pipeline.
        
        Args:
            user_input: User input data
            log_record: Whether to log to Cosmos DB
            
        Returns:
            Final response data
        """
        start_time = time.perf_counter()
        
        log_json = json.dumps(
            user_input.model_dump(), ensure_ascii=False, indent=2
        )
        logger.info(f"\n[Pipeline Started] Input: {log_json}")

        # Step 1: Initialize chat
        init_data = await self.chat_init_handler.initialize_chat(
            user_input
        )

        # Step 2: Process history
        history_data = await self.history_handler.process_history(
            his_inputs=init_data["his_inputs"],
            last_extract_output=init_data["last_extract_output"],
            kb_mappings=self.cosmos_repo.KB_mappings,
            lang=init_data["lang"]
        )

        # Step 3: Get user info and bot scope
        user_scope_data = await self.user_info_handler.get_user_and_scope_info(
            his_inputs=history_data["processed_inputs"],
            user_info=init_data["user_info"],
            last_bot_scope=init_data["last_bot_scope"],
            last_hint=init_data["last_hint"],
            product_line=user_input.product_line,
            websitecode=user_input.websitecode
        )

        # Step 4: Search knowledge base
        kb_data = await self.kb_search_handler.search_knowledge_base(
            search_info=user_scope_data["search_info"],
            websitecode=user_input.websitecode,
            bot_scope_chat=user_scope_data["bot_scope_chat"],
            specific_kb_mappings=self.cosmos_repo.specific_kb_mappings
        )

        # Step 5: Generate response
        response_result = await self.response_handler.generate_response(
            bot_scope_chat=user_scope_data["bot_scope_chat"],
            top1_kb=kb_data["top1_kb"],
            top1_kb_sim=kb_data["top1_kb_sim"],
            top4_kb_list=kb_data["top4_kb_list"],
            faqs_wo_pl=kb_data["faqs_wo_pl"],
            his_inputs=history_data["processed_inputs"],
            search_info=user_scope_data["search_info"],
            lang=init_data["lang"],
            websitecode=user_input.websitecode,
            system_code=user_input.system_code,
            user_input_text=user_input.user_input,
            render_id=init_data["render_id"]
        )

        # Calculate execution time
        end_time = time.perf_counter()
        exec_time = round(end_time - start_time, 2)
        logger.info(f"\n[Pipeline Completed] Execution time: {exec_time}s\n")

        # Log to Cosmos DB if requested
        if log_record:
            await self._log_to_cosmos(
                user_input=user_input,
                init_data=init_data,
                user_scope_data=user_scope_data,
                kb_data=kb_data,
                history_data=history_data,
                response_result=response_result,
                exec_time=exec_time
            )

        return response_result["final_result"]

    async def _log_to_cosmos(
        self,
        user_input: TechAgentInput,
        init_data: Dict[str, Any],
        user_scope_data: Dict[str, Any],
        kb_data: Dict[str, Any],
        history_data: Dict[str, Any],
        response_result: Dict[str, Any],
        exec_time: float
    ) -> None:
        """
        Log conversation data to Cosmos DB.
        
        Args:
            user_input: Original user input
            init_data: Initialization data
            user_scope_data: User scope data
            kb_data: KB search data
            history_data: History data
            response_result: Response result
            exec_time: Execution time
        """
        cosmos_data = {
            "id": f"{init_data['cus_id']}-{init_data['session_id']}-{init_data['chat_id']}",
            "cus_id": init_data["cus_id"],
            "session_id": init_data["session_id"],
            "chat_id": init_data["chat_id"],
            "createDate": datetime.utcnow().isoformat() + "Z",
            "user_input": user_input.user_input,
            "websitecode": user_input.websitecode,
            "product_line": user_input.product_line,
            "system_code": user_input.system_code,
            "user_info": user_scope_data["user_info_dict"],
            "process_info": {
                "bot_scope": user_scope_data["bot_scope_chat"],
                "search_info": user_scope_data["search_info"],
                "is_follow_up": history_data["is_follow_up"],
                "faq_pl": kb_data["faq_result"],
                "faq_wo_pl": kb_data["faq_result_wo_pl"],
                "language": init_data["lang"],
                "last_info": {
                    "prev_q": history_data["prev_q"],
                    "prev_a": history_data["prev_a"],
                    "kb_no": history_data["kb_no"],
                },
            },
            "final_result": response_result["final_result"],
            "extract": response_result["response_data"],
            "total_time": exec_time
        }

        await self.cosmos_repo.insert_data(cosmos_data)

        log_json = json.dumps(cosmos_data, ensure_ascii=False, indent=2)
        logger.info(f"\n[Cosmos Log] Data: {log_json}\n")
