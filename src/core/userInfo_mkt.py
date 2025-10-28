# -*- coding: utf-8 -*-
"""
Created on Thu May 30 20:46:07 2024

@author: Billy_Hsu
"""
# flake8: noqa: E501

import json
from src.services.base_service import BaseService
from utils.warper import async_timer


# 20240620 add NUC
class UserinfoDiscriminator_MKT(BaseService):

    def __init__(self,config):
        super().__init__(config)

        self.empty_userInfo = {
            "productline_mkt": [],
            # "product_accessories": None,
            "product_name": [],
            "mentioned_accessories": [],
            "lastest_product": False,
            "gaming_product": False
        }

        self.system_messages = [
            {
                "role": "system",
                "content": """Your role as an AI assistant is to parse information from product descriptions and categorize it accurately in JSON format. You need to extract details such as product line, product names, and any associated accessories.

Context and Definitions:
- Software names include 'Armoury Crate', 'MyASUS', 'AURA Creator'.
- '手機' translates to 'Phone'.
- BTF means HIDDEN-CONNECTOR DESIGN, is an important feature of products. you should collect it in product name.
- EVA series, Gundum series are co-branded products.
- 西風之神是 ROG Zephyrus laptops.
- ASUS AirVision M1 is 智慧眼鏡.
- NUC (Next Unit of Computing) is a series of small-sized barebone computers designed by ASUS.
- NUCs is Product of ASUS, not Intel!

Product Knowledge:
- Latest ProArt Laptops is ProArt PZ13, ProArt PX13, ProArt P16.
- If user do not mention other spec or request and only finding proart laptop, product name using ProArt PZ13, ProArt PX13, ProArt P16 instead of proart laptop.
- AI PC should add `(copilot+ pc)` after product_name. For example: user: AI PCs. product_name should be AI PCs(copilot+ PC). 

ProductLine Categorization Tips:
For laptops inquiries, even if a GPU issue is mentioned, the category remains 'laptops'.
-'電競掌機', 'ROG Ally', and 'Ally' should be categorized under 'gamig-handhelds'.
-'電競手機', '手機','screenpad' and 'screen pad' are categorized as 'phones'.
-'西風之神',"AI PC","AI 電腦","Copilot PC" and "Copilot+ PC" should be categorized as 'laptops'.
- "顯示器" should be categorized as 'monitors'.
-'工作站',"work station","主機" should be categorized as "desktops".
-"主機殼","機殼","Computer Case","Liquid Cooling System","Sound cards","音效卡","光碟機" should be categorized under 'motherboards'.
- "Kunai","headphone", "headset", "cetra true wireless", "power-supply-units", "streaming-kits", "gaming-handhelds", "basketball","controllers", "fans", "jacket", "t-shirt", "phone-case", "sweatshirt", "power-banks", "caps", "bags", "stylus","hard drive","storage", "luggage", "backpack", "laptop-bag", "phone-charging-cable","chair","mice", "mouse-pads" are categorized as 'accessories'.
-'Zenbo' is an intelligent robot, categorized under 'zenbo'.
-The term "pad" refers to tablets, which should be explicitly mentioned.
-'vivowatch', 'health hub' and 'handheld ultrasound' should be categorized under 'wearable-healthcare'.
-'clothing','coat', 'keyboard cap', 'microphone','stylus' and 'streaming kits' should be categorized under 'accessories'.
-'顯卡','顯示卡' should be categorized as 'graphics-cards'.
-'伺服器','server' should be categorized as 'servers'.
-"智慧家居", "smart home"," 活氧水殺菌機","PureGO","蔬果洗淨偵測器","Fruits and vegetable Cleanliness Detetor" should be categorized as 'aiot'
-"Etherent Calbe","Network Cable","Access Points","AP","Netword Card","有線網路卡","無線網卡" should be categorized as "networking"
-"Tinker Board" should be categorized as "iot".
-"SSD", "HDD" storage should be categorized as "accessories".
-Do not default productline for user, if only say latest products.
- ASUS AirVision M1 should be categorized as "glasses".
- NUC should be categorized as "nucs".
- "mini desktop" or "mini pc" should be categorized as "mini-pcs".

Step-by-Step Instructions for Information Extraction:
1.Review Inquiry: Carefully read the latest user inquiry to grasp the context and specifics.
2.Product Line Categorization: Assign the product to its correct productline category based on the inquiry context and details, including any mentioned accessories.
3.Accessory Name and Product Name Identification: List any mentioned products and accessories, keeping them in separate categories.
4.Sorting Rules for productline (IMPORTANT!):
  - Sort the productline array according to the order in which the user mentions them.
  - If two or more product lines are mentioned, place the one the user truly wants a recommendation for at the END of the list (even if it was mentioned earlier).

Expected Output Format:
```json
{
"productline_mkt": "Return a Python list with only one element containing the identified product categories based on user inquiry (e.g., ["phones", "desktops", "accessories", "aiot", "motherboards","nucs", "wearable-healthcare", "iot", "networking", "monitors", "projectors", "mini-pcs", "laptops", "tablets", "gaming-handhelds", "all-in-one pcs", "zenbo", "servers", "graphics-cards"]). If no specific product category is mentioned or if it is unclear, return an empty list [].",
"product_name": "List all mentioned product names in a Python list format. Format the product names with proper capitalization and spacing (e.g., 'rog phone8' should be 'ROG Phone 8'). If no product name is mentioned, return []."
"mentioned_accessories": "List all mentioned accessories in English, using a Python list format. Ensure the response is in English or translate into English. If no accessories are mentioned, return an empty list [].",
"lastest_product": Boolean, if user mention latest product, return True, otherwise return False.,
"gaming_product": Boolean, if user mention gaming product, return True, otherwise return False. If user only mention GPU, return False. ProArt,Zenbook, Vivobook are not gaming laptops,but they are equipped with powerful GPUs.
}

Good Examples:
1.User Inquiry: Recommend me a laptop with the most powerful graphics card. Expected Output:{'productline_mkt': ['laptops'], 'product_name': [], 'mentioned_accessories': [''],'lastest_product': False,'gaming_product': False}
2.User Inquiry: Recommend me a laptop with the NVDIA or AMD graphics card. Expected Output:{'productline_mkt': ['laptops'], 'product_name': [], 'mentioned_accessories': [''],'lastest_product': False,'gaming_product': False}
3.User Inquiry: I need a ROG product, i need a 1080p gpu that performs over 100 fps. Expected Output:{'productline_mkt': ['graphics-cards'], 'product_name': [], 'mentioned_accessories': [''],'lastest_product': False,'gaming_product': True}
4.User Inquiry: Recommend me notebook's accessories. Expected Output:{'productline_mkt': ['accessories'], 'product_name': [], 'mentioned_accessories': ['notebook accessories'],'lastest_product': False,'gaming_product': False}
5.User Inquiry: Recommend me keyboards. Expected Output:{'productline_mkt': ['accessories'], 'product_name': [], 'mentioned_accessories': ['keyboard'],'lastest_product': False,'gaming_product': False}
6.User Inquiry: Recommend me notebooks. Expected Output:{'productline_mkt': ['laptops'], 'product_name': [], 'mentioned_accessories': [],'lastest_product': False,'gaming_product': False}
7.User Inquiry: Recommend me a BTF product. Expected Output:{'productline_mkt': [], 'product_name': [], 'mentioned_accessories': [],'lastest_product': False,'gaming_product': False}
8.User Inquiry: Which stylus is compatible with zenbook 13 oled and where can i purchase it?. Expected Output:{'productline_mkt': ['laptops', 'accessories'], 'product_name': ['zenbook 13 oled'], 'mentioned_accessories': ['stylus'],'lastest_product': False,'gaming_product': False}
9.User Inquiry: Recommend me a copilot pc. Expected Output:{'productline_mkt': ['laptops'], 'product_name': ['copilot pc'], 'mentioned_accessories': [],'lastest_product': False,'gaming_product': False}
10.User Inquiry: Recommend me adaptor for vivobook k513e. Expected Output:{'productline_mkt': ['laptops', 'accessories'], 'product_name': ['Vivobook K513E'], 'mentioned_accessories': ['adaptor'],'lastest_product': False,'gaming_product': False}
11.User Inquiry: which NUC is the best to pair with ROG swift OLED monitor?. Expected Output:{'productline_mkt': ['monitors','nucs'], 'product_name': [], 'mentioned_accessories': [],'lastest_product': False,'gaming_product': False}

Special Case:
1.User Inquiry: 問我有一台ASUS Transformer Book T100HA，已無法充電，請問我想買？款顯示器可以折抵?. Expected Output:{'productline_mkt': ['laptops'], 'product_name': [], 'mentioned_accessories': [],'lastest_product': False,'gaming_product': False}
2.User Inquiry: 請推薦我獨立顯卡、i7的桌上型電腦. Expected Output:{'productline_mkt': ['desktops'], 'product_name': [], 'mentioned_accessories': [],'lastest_product': False,'gaming_product': False}
3.User Inquiry: 有支援UX3405MA-0152S155H的外接顯卡嗎. Expected Output:{'productline_mkt': ['graphics-cards'], 'product_name': [], 'mentioned_accessories': [],'lastest_product': False,'gaming_product': False}

Additional Notes:
If accessories are mentioned but do not appear in 'productline_mkt', ensure they are captured in 'mentioned_accessories'.
Use context from the product descriptions to accurately categorize and list the products and accessories.
```""",
            }
        ]

    @async_timer.timeit
    async def userInfo_GPT_mkt(self, his_inputs: list, merge_input: str):
        messages = self.system_messages.copy()
        for i, user_input in enumerate(his_inputs):

            if i == len(his_inputs) - 1:
                messages.extend(
                    [
                        {
                            "role": "user",
                            "content": """Please fill the information accroding to Step-by-Step Instructions for Information Extraction, and respond in a detailed JSON format in English. Here is my inquiry: {}""".format(
                                merge_input
                            ),
                        }
                    ]
                )
                # messages.extend([{'role':'user','content':'''{}'''.format(user_input)}])
            else:
                messages.extend(
                    [{"role": "user", "content": """{}""".format(user_input)}]
                )
        # print(messages)
        try:
            response = await self.GPT41_mini_response(messages, json_mode=True)
            # response = await self.GPT_response(messages)
            # print('userInfo Response',response)

            response = self.get_content(response)
        except Exception as e:
            print({"userInfo_GPT_mkt error": e})
            response = self.handle_gpt_error_response()
        # print('userInfo Response',response)
        try:
            response = json.loads(response)
            response = self.text_process(response)
            return response
        except Exception as e:
            print({"userInfo_GPT_mkt json decode error": e})
            try:
                response = self.extract_braces_content(response)
                response = self.text_process(response)
                return response
            except Exception as e:
                print({"userInfo_GPT_mkt json decode error": e})
                try:
                    response = eval(response)
                    response = self.text_process(response)
                    return response
                except Exception as e:
                    print({"userInfo_GPT_mkt json decode error": e})
                    return self.empty_userInfo

    def text_process(self, response: dict):
        response["productline_mkt"] = [
            i.lower().replace(" ", "-") for i in response["productline_mkt"]
        ]
        return response

    def get_content(self, response: dict):
        try:
            content = response
        except Exception as e:
            print({"userInfo_GPT_mkt json decode error (get_content)": e})
            content = self.handle_gpt_error_response()
        return content

    def handle_gpt_error_response(self):
        response = json.dumps(self.empty_userInfo)
        return response

if __name__ == "__main__":
    import os
    import asyncio
    from config import config_loader  # 使用相对导入 config_loader 模块
    import nest_asyncio
    nest_asyncio.apply()
    
    os.environ["CURRENT_ENV"] = "dev"
    env = os.environ.get("CURRENT_ENV", "dev")
    config_loader.env_config = config_loader.load_config()
    cfg = config_loader.env_config

    async def main():
        os.environ["CURRENT_ENV"] = "dev"
        env = os.environ.get("CURRENT_ENV", "dev")
        config_loader.env_config = config_loader.load_config()
        cfg = config_loader.env_config
    
        userinfo_mkt = UserinfoDiscriminator_MKT(cfg)
        # print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['請推薦我眼鏡'], merge_input='請推薦我智慧眼鏡'))
        # print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['latest proart laptops'], merge_input='latest proart laptops'))
        # print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['recommend me proart ai pc'], merge_input='recommend me proart ai pc'))
        # print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['recommend me ai pc'], merge_input='recommend me ai pc'))
        # print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['recommend me ROG ai pc'], merge_input='recommend me ROG ai pc'))
        # print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['recommend me ASUS ai pc'], merge_input='recommend me ASUS ai pc'))
        # print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['adaptor for vivobook k513e'], merge_input='adaptor for vivobook k513e'))
        # print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['which NUC is the best to pair with ROG swift OLED monitor'], merge_input='which NUC is the best to pair with ROG swift OLED monitor'))
        # print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['which Notebook is the best to pair with ROG swift OLED monitor'], merge_input='which Notebook is the best to pair with ROG swift OLED monitor'))
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['recommend me a laptop with the most powerful graphics card'], merge_input='recommend me a laptop with the most powerful graphics card'))
        # 測試 latest product
        print("測試 latest product:")
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['show me the latest laptops'], merge_input='show me the latest laptops'))
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['what are the newest asus products'], merge_input='what are the newest asus products'))
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['latest rog products'], merge_input='latest rog products'))
        
        # 測試 gaming product
        print("\n測試 gaming product:")
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['recommend gaming laptop'], merge_input='recommend gaming laptop'))
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['best gaming monitor'], merge_input='best gaming monitor'))
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['gaming accessories'], merge_input='gaming accessories'))
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['rog gaming desktop'], merge_input='rog gaming desktop'))

        # 測試 ProArt 產品
        print("\n測試 ProArt 產品:")
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['proart laptop with rtx 4090'], merge_input='proart laptop with rtx 4090'))
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['proart desktop with nvidia gpu'], merge_input='proart desktop with nvidia gpu'))
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['proart monitor for graphic design'], merge_input='proart monitor for graphic design'))
        print(await userinfo_mkt.userInfo_GPT_mkt(his_inputs=['proart workstation with high performance gpu'], merge_input='proart workstation with high performance gpu'))
    asyncio.run(main())
