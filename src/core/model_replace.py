import json
import time
from utils.warper import async_timer
from src.services.base_service import BaseService 

class ModelName(BaseService):
    
    def __init__(self,config):
        BaseService.__init__(self,config)

    async def extract_modelname(self, user_input: str):
        """Extract product names from user input based on predefined rules."""

        system_prompt = """
        You are an AI assistant designed to extract **product names**, **model names**, **series names**, and other brand identifiers from text.

        ### **Extraction Rules**
        1. **General Instructions**
        - Extract product names **exactly as they appear** in the text (preserve original case).
        - Extract the the **original** product names, **do not translate or altering their case (keep the original case as is)**.
        - Return results in JSON format:

            ```json
            {
            "asus_product": ["List of ASUS models or 'None'"],
            "other_brand_product": ["List of non-ASUS models or 'None'"]
            }
            ```

        2. **ASUS Products**
        - Recognize ASUS series: **VivoBook, ZenBook, ROG Phone, Zenfone, VivoWatch, ExpertBook, ProArt**.
        - Extract full model names, including **series, numeric parts, and letter codes** (e.g., "VivoBook S15 S533", "ROG Phone 8").
        - Identify co-branded series:
            - **"EVA"**, **"Gundam"** belong to ASUS.
            - **"西風之神" (Zephyrus)** belongs to ASUS.

        3. **Non-ASUS Products**
        - Extract major competitor models like **iPhone, Galaxy, HP Pavilion**.
        - Recognize major brands:
            - Apple (蘋果), HP (惠普), Dell (戴爾), Lenovo (聯想), Acer (宏碁), MSI (微星), Samsung (三星)
            - Razer (雷蛇), Huawei (華為), Xiaomi (小米), Sony (索尼), LG (樂金), Toshiba (東芝)
            - TP-Link (普聯), Gigabyte (技嘉)

        4. **Processor & GPU Recognition**
        - Extract CPU/GPU names such as **"Intel Core i5-12500H"**, **"AMD Ryzen 7 5800U"**.
        - Identify **series + number** format (e.g., "GeForce RTX 4070 SUPER", "RX 7800 XT").
        - If a word contains **letters + numbers mixed** (e.g., "4070Ti") or includes a **hyphen (-)**, treat it as part of a model name.

        5. **Software Recognition**
        - Identify ASUS software: **Armoury Crate, MyASUS, AURA Creator**.

        6. **Special Cases**
        - If a term includes **both letters and numbers** or contains a **hyphen (-)** (e.g., "k6602he-0122b11900h", "DDR5-4800", "s5507", "UX5406", "X1704VA"), treat it as a model number.
        - If no models are found, return:

        7. If the extracted word contains "asus," it should be classified as an asus_product.
        8. If the extracted word does not contain any competitor brands or competitor model names, or if you are unsure whether it is an ASUS competitor, treat it as an asus_product.        
        9. if you don't find any asus product, please return "None" in the asus_product list.

            ```json
            {
            "asus_product": ["None"],
            "other_brand_product": ["None"]
            }
            ```
        """

        user_prompt = f"Extract product names from the following text and return the response in JSON format: {user_input}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            modelname = await self.GPT41_mini_response(messages, json_mode=True)
            return self.to_json_format(modelname)
        except Exception as e:
            print(f"Error in GPT41_response: {e}")  # 可選，記錄錯誤
            return {
                "asus_product": ["None"],
                "other_brand_product": ["None"]
            }

    def to_json_format(self, x):
        """Convert string to JSON format."""
        if not isinstance(x, dict):
            try:
                x = json.loads(x.replace("jsonl", "").replace("```", "").replace("json", ""))
            except json.JSONDecodeError:
                return x
        return x

    def clean_model_data(self, modelname: str):
        """Extract and clean product data from response."""
        data = self.to_json_format(modelname)
        asus_ = data.get("asus_product", ["None"])
        other_ = data.get("other_brand_product", ["None"])
        return len(asus_) if asus_ != ["None"] else 0, asus_, len(other_) if other_ != ["None"] else 0, other_

    def replace_modelnames(self, user_input: str, asus_: list, other_: list):
        """Replace model names in the user input with placeholders."""
        sentence_ = user_input
        for modelname in asus_:
            sentence_ = sentence_.replace(modelname, "asusspd")
        for modelname in other_:
            sentence_ = sentence_.replace(modelname, "otherspd")
        return sentence_

    # @async_timer.timeit
    async def process_modelnames(self, user_input: str):
        """Extract, clean, and replace model names in the given input."""
        start_time = time.time()
        
        extracted_data = await self.extract_modelname(user_input)
        len_asus, asus_, len_other, other_ = self.clean_model_data(extracted_data)
        replace_sentence = self.replace_modelnames(user_input, asus_, other_)

        execution_time = time.time() - start_time
        
        return {
            "replace_sentence": replace_sentence,
            "product_count": len_asus,
            "extract_modelname": asus_,
            "other_brand_count": len_other,
            "other_brand": other_,
            "execution_time": execution_time
        }

# # usage
# modelname_processor = ModelName()
# user_input = "Zenfone 9 vs iPhone 15, which one has better camera?"
# user_input = '西風之神和macbook有什麼差異'
# user_input='asus acer誰是台灣之光'
# ser_input = 'Can someone tell me if this is better than the MSI crosshair 16 that??s on best buy'
# user_input = 'asus dual geforce rtx 4070 super evo 12gb gddr6x是不是16pin供電介面'

# result = await modelname_processor.process_modelnames(user_input)
# print(json.dumps(result, indent=4, ensure_ascii=False))

