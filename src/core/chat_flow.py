
import base64
import json
import asyncio
from sharedlib.get_translation import *

class ChatFlow:
    def __init__(self, data: dict, last_hint: dict, container: object):
        self.data = data
        self.last_hint = last_hint
        self.default_user_info = {
            "our_brand": "ASUS",
            "location": None,
            "main_product_category": data.product_line,
            "sub_product_category": None,
            "first_time": True,
        }
        self.container = container

        cred_b64 = self.container.creds_trans  # 取得key
        info = json.loads(base64.b64decode(cred_b64))
        self.language_processor = Translator(info=info, client=container._trans_client)

    # @async_timer.timeit
    async def get_bot_scope_chat(
        self, prev_user_info: dict, curr_user_info: dict, last_bot_scope: str
    ):

        # 若用戶點擊了產品線追問提示句, 則配對該提示句的產品線
        if (self.last_hint):
            if self.last_hint.get("hintType") == "productline-reask":
                for hint in self.last_hint["intentHints"]:
                    if self.data.user_input == hint["question"]:
                        bot_scope_chat = hint["title"]
                        return bot_scope_chat

        """3. bot_scope_chat"""

        user_info_string = self.update_UserInfo(prev_user_info, curr_user_info)
        user_info_dict = json.loads(user_info_string)

        site = self.data.websitecode
        # bot_scope = self.data.get('bot_scope')

        if user_info_dict.get("main_product_category"):
            bot_scope_chat = await self.container.redis_config.get_productline(
                user_info_dict.get("main_product_category"), site
            )
        elif user_info_dict.get("sub_product_category"):
            bot_scope_chat = await self.container.redis_config.get_productline(
                user_info_dict.get("sub_product_category"), site
            )
        else:
            bot_scope_chat = self.data.product_line

        if bot_scope_chat not in self.container.PL_mappings[site]:
            bot_scope_chat = last_bot_scope

        return bot_scope_chat

    # @timeit_sync
    def update_UserInfo(self, previous: dict, current: dict):
        # try:
        #     previous = json.loads(previous)
        #     current = json.loads(current)
        # except Exception as e:
        #     print({"update_UserInfo error load previous or current json": e})

        #     pass

        for key, values in current.items():
            if values == "null":
                current[key] = None

        for key, values in previous.items():
            if values == "null":
                previous[key] = None

        # 第一次不更新 GPT 判斷的產品線。
        if previous.get("first_time"):
            first_bot = previous.get("main_product_category")
            del previous["first_time"]

        for key, values in current.items():

            if values:
                previous[key] = values
        # 第一次不更新 GPT 判斷的產品線。
        try:
            if first_bot:
                previous["main_product_category"] = first_bot
        except Exception as e:
            print({"update_UserInfo for user click productline": e})
            pass
        return json.dumps(previous, ensure_ascii=False)

    # @async_timer.timeit
    async def get_userInfo(
        self,
        his_inputs: list,
        # merge_input: str,
    ):
        """Get GPT response"""
        """1. userInfo & 抱怨"""
        # userinfo_gpt就是使用輸入的內容請GPT判斷能取出那些資訊，並使用固定格式回傳
        task_user_info = asyncio.create_task(
            self.container.userinfo_discrimiator.userInfo_GPT(user_inputs=his_inputs)
        )
        # task_user_info_mkt = asyncio.create_task(
        #     self.container.userinfo_discrimiator_mkt.userInfo_GPT_mkt(
        #         his_inputs=his_inputs[-3:]
        #     )
        # )

        result = await asyncio.gather(task_user_info)

        return result

    async def get_searchInfo(self, his_inputs: list, translaor: object = None):

        translaor = translaor or self.language_processor
        # 若用戶點擊了產品線追問提示句, 則抓取原問句的轉譯句
        if (self.last_hint):
            if self.last_hint.get("hintType") == "productline-reask":
                search_info = self.last_hint.get("searchInfo")
                return search_info

        """2. 翻譯"""
        search_info = await translaor.get_translation(his_inputs[-1])
        # search_info = search_info[0].lower()
        return search_info.lower()

    async def is_follow_up(self, prev_question: str, prev_answer: str, prev_answer_refs: str, new_question: str):
        """4. 是否為追問"""
        task_followup = asyncio.create_task(
            self.container.followup_discrimiator.is_follow_up(prev_question, prev_answer, prev_answer_refs, new_question)
        )
        result = await asyncio.gather(task_followup)
        return result[0]
