# In[1]:
# flake8: noqa: E501

import json
from src.services.base_service import BaseService
from utils.warper import async_timer


class SentenceGroupClassification(BaseService):  # BaseService

    def __init__(self, config):
        super().__init__(config)

    @async_timer.timeit
    async def sentence_group_classification(self, his_inputs):
        messages = [
            {
                "role": "system",
                "content": """You are an intelligent assistant designed to identify if various statements refer to the same product. Your task is to analyze each statement and determine if they refer to the same product based on context and details provided. Consider product names, models, specifications, and related attributes. If the statements refer to the same product, group them together in the order they are provided; if not, keep them separate. Ensure that groups consist of consecutive statements only. Output the results in a JSON format.

            Example Statements:
            [
            "請問購買螢幕可以宅配到府嗎?",
            "我可以從國外訂購螢幕到台灣嗎",
            "我的螢幕通電後不會亮怎麼辦",
            "我的螢幕是TUF Gaming VG27VQ3B 我想問她有支援4K畫質嗎",
            "介紹TUF Gaming VG27VQ3B的特點",
            "我購買這台的話有甚麼優惠",
            "如果我購買螢幕的話有甚麼活動",
            "如果我現在購買螢幕的話有甚麼活動",
            "請問手機可以送到我家附近的便利商店嗎",
            "我想購買手機配件這裡有賣嗎",
            "我像賣Type-C充電器",
            "我能在台灣購買美國的手機嗎",
            "所以是不行嗎",
            "如何設定手機的Wi-Fi",
            "請問曲面螢幕有賣嗎",
            "可以推薦我一台35吋的曲面螢幕",
            "可以推薦我一台30吋以上Gaming系列的曲面螢幕",
            "我想知道 2024 的新機",
            "筆電",
            "請推薦適合工作的筆電",
            "這三款哪一個最熱賣",
            "哪一款最輕?",
            "請推薦我好用的滑鼠",
            "有更便宜的嗎?",
            ]
            Instructions:
            Identify and group statements referring to the same product based on context clues such as product names, models, or types.
            Ensure each group consists of consecutive statements as they appear in the list.
            Provide the results in JSON format, with each group containing its respective statements.

            You need to know:
            `新機` means `latest products`

            Example Output:
            {"groups": [
            {"group": 1, "statements": ["請問購買螢幕可以宅配到府嗎?", "我可以從國外訂購螢幕到台灣嗎"]},
            {"group": 2, "statements": ["我的螢幕通電後不會亮怎麼辦"]},
            {"group": 3, "statements": ["我的螢幕是TUF Gaming VG27VQ3B 我想問她有支援4K畫質嗎", "介紹TUF Gaming VG27VQ3B的特點", "我購買這台的話有甚麼優惠"]},
            {"group": 4, "statements": ["如果我購買螢幕的話有甚麼活動", "如果我現在購買螢幕的話有甚麼活動"]},
            {"group": 5, "statements": ["請問手機可以送到我家附近的便利商店嗎", "我想購買手機配件這裡有賣嗎", "我像賣Type-C充電器", "我能在台灣購買美國的手機嗎", "所以是不行嗎", "如何設定手機的Wi-Fi"]},
            {"group": 6, "statements": ["請問曲面螢幕有賣嗎", "可以推薦我一台35吋的曲面螢幕", "可以推薦我一台30吋以上Gaming系列的曲面螢幕"]},
            {"group": 7, "statements": ["我想知道 2024 的新機", "筆電"]},
            {"group": 8, "statements": ["請推薦適合工作的筆電", "這三款哪一個最熱賣","哪一款最輕?"]},
            {"group": 9, "statements": ["請推薦我好用的滑鼠", "有更便宜的嗎?"]}
            ]}
            """,
            },
            {
                "role": "user",
                "content": """My Statements:{}.(Please identify the group base on my Statements. Ensure each group consists of consecutive statements as they appear in the list.)""".format(
                    his_inputs
                ),
            },
        ]

        try:
            response = await self.GPT41_mini_response(
                messages, json_mode=True, max_tokens=600
            )
            response = json.loads(response)
            return response
        except Exception as e:
            print({"sentence_group_classification error": e})
            except_return = {"groups": [{"group": 1, "statements": his_inputs}]}
            return except_return


# inputs = pd.read_excel(r"C:\Users\billy_hsu\Downloads\測試題組_result_chinese2 1 (1).xlsx",sheet_name= '題組_意圖_產品測試')
# user_inputs = inputs[['user_input']]
# user_inputs
# # user_inputs = ['第 idx 句: ' + sen for idx,sen in enumerate(user_inputs)]

# sentence_group_classification = SentenceGroupClassification()

# results = []
# for i in range(len(user_inputs)):
#     start = 0 if i - 10 <0 else i -10
#     result = await sentence_group_classification.sentence_group_classification(user_inputs[start:i+1])
#     print(result)
#     results.append(result)


# results2 = ['請問rog phone 8的特色有甚麼?']

# for i in range(len(results)-1):
#     results2.append(results[i].get('groups')[-1].get('statements'))

# inputs['group'] = results2
# inputs.to_excel('group_results.xlsx')


# result = await sentence_group_classification.sentence_group_classification(['我想知道 2024 的新機','筆電'])
# result
#
