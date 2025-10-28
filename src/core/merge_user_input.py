#!/usr/bin/env python
# coding: utf-8

# flake8: noqa: E501

from src.services.base_service import BaseService
from utils.warper import async_timer


class MergeUserInput(BaseService):  # BaseService

    def __init__(self,config):
        super().__init__(config)
    @async_timer.timeit
    async def merge_user_input_GPT(self, user_input, prev_merge_input=[]):
        # Prompt
        chat_history_str = "\n".join(prev_merge_input)

        messages = [
            {
                "role": "system",
                "content": '''
                    # Task
                    Generate a standalone question which is based on the New Question plus the Chat History. Just create the standalone question without commentary.
                    New Question will either be a follow-up question or a new topic. Chat History is the conversation history between the user and the chatbot.
                    If the New Question is a follow-up question, then the context of the standalone question should be based on the Chat History.
                    If the New Question is a new topic, then the standalone question should directly be based on the New Question.
                    Make sure you don't change the main purpose from the New Question and Chat History.

                    # Note
                    1.Since you work in ASUS, all of the products user mentioned are ASUS products. You can use ASUS products' names directly.
                    2.The order of Chat History is from the oldest to the newest, make sure you consider the latest information.
                    3.If the New Question is totally irrelevant to the Chat History, please output the New Question directly.
                    4.If the New Question is asking to transfer to real person or agent, please output the New Question directly.

                    # Example
                    New_Question = "I am a professional lawyer . what laptop could you recommend to me ?"
                    Chat_History = ""
                    Standalone_Question = "What ASUS laptop can you recommend for a professional lawyer?"

                    New_question = "介紹一下螢幕"
                    Chat_History = "ROG Phone 8有現貨嗎?"
                    Standalone_Question = "介紹一下ROG Phone 8的螢幕"

                    New_question = "可以再加入 ROG Phone 8 比較嗎?"
                    Chat_History = "請問 Zenfone 11 Ultra 跟 Zenfone 10 的差異?"
                    Standalone_Question = "請問 ROG Phone 8, Zenfone 11 Ultra 跟 Zenfone 10的差異?"

                    New_question = "怎麼查發票"
                    Chat_History = "訂單編號是3000013492。"
                    Standalone_Question = "怎麼查訂單編號3000013492的發票?"

                    New_question = "我想查詢訂單的最新進度，請問現在處於什麼階段？"
                    Chat_History = "ID: 3000013492"
                    Standalone_Question = "請問訂單ID: 3000013492的最新進度是什麼？"

                    New_Question = "He like to play the game on the PC."
                    Chat_HIstory = "What laptop can you recommend for a junior high school graduate that costs between 20,000 to 30,000?"
                    Standalone_Question = "What laptop can you recommend for a junior high school graduate that costs between 20,000 to 30,000 and he likes to play the game on the PC?"

                    New_Question = "Are you selling any accessories?"
                    Chat_History = "Can you recommend some of the AI PCs that were launched by ASUS at Computex?", "purchasing-recommendation-of-asus-products", "What CPU is equipped in the ASUS ROG G14 2024?", "specification-consultation"
                    Standalone_Question = "Is ASUS selling any accessories?"

                    New_Question = "thx!"
                    Chat_History = "What laptop can you recommend for a junior high school graduate that costs between 20,000 to 30,000?", "purchasing-recommendation-of-asus-products", "What laptop can you recommend for a junior high school graduate who likes to play games on the PC, with a budget between 20,000 to 30,000?", "purchasing-recommendation-of-asus-products"
                    Standalone_Question = "Thank you!"''',
                                },
                                {
                                    "role": "user",
                                    "content": f"""
                    # New Question
                    {user_input}

                    # Chat History
                    {chat_history_str}""",
            },
        ]
        try:
            response = await self.GPT41_mini_response(messages, max_tokens=500)
            merge_result = response.strip().strip("'\"")
        except Exception as e:
            if (
                "The response was filtered due to the prompt triggering Azure OpenAI's content management policy."
                in str(e)
            ):
                merge_result = {user_input}
            else:
                merge_result = {user_input}

        return merge_result

    async def merge_user_input(self, user_input, prev_merge_input=[]):
        output = await self.merge_user_input_GPT(user_input, prev_merge_input)
        if isinstance(output, set):
            return ", ".join(output)

        else:
            return str(output)
    
