import aiohttp, json, asyncio, functools
from utils.warper import async_timer
from aiohttp import ClientError
import requests, json

def async_retry(max_retries=1, delay=0.1):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except ClientError as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"尝试 {attempt + 1} 失败: {str(e)}. 正在重试...")
                    await asyncio.sleep(delay)

        return wrapper

    return decorator

class RedisConfig:
    def __init__(self, config, session: aiohttp.ClientSession):
        self.faq_ver = "4.0"
        self.headers = {
            "accept": "text/plain",
            "apikey": "moneyislife",
            "Content-Type": "application/json",
        }
        self.redis_url = config.get("TECH_REDIS_E50_URL")
        self.session = session  # ✅ 使用 lifespan 傳進來的共用 session

    @async_retry(max_retries=3, delay=1)
    async def get_hint_simiarity(self, search_info):
        data = {
            "websiteCode": "tw",
            "keyword": search_info,
            "productLine": "",
            "version": self.faq_ver,
            "n": 1,
            "hide_min": 0,
            "hide_max": 2001,
        }

        async with self.session.post(self.redis_url, headers=self.headers, data=json.dumps(data)) as response:
            response_json = await response.json()
            top1_faq = response_json.get("result").get("faqs")[0]

        return {
            "faq": top1_faq["kb_no"],
            "cosineSimilarity": top1_faq["cosineSimilarity"],
            "hints_id": top1_faq["key"].split("-")[-1],
        }

    def search_redis(self, query: str):
        url_v2 = 'https://aocc-dev-vector-searching.azurewebsites.net/faq/v2/faqSearch'
        headers = {
            'accept': 'text/plain',
            'Content-Type': 'application/json'
        }
        data = {
            "websiteCode": 'tw',
            "keyword": query.lower(),
            "productLine": 'notebook',
            "version": "4.0",
            "n": 4,
            "hide_min": 0,
            "hide_max": 999
        }

        response = requests.post(url_v2, headers=headers, json=data)

        try:
            response.raise_for_status()
            response_json = response.json()
            faqs = response_json["result"]["faqs"]

            if not faqs:
                return None

            return [
                {
                    "kb_no": faq.get("kb_no"),
                    "key": faq.get("key"),
                    "similarity": faq.get("cosineSimilarity"),
                    "site": faq.get("websiteCode")
                }
                for faq in faqs
            ]

        except (KeyError, IndexError, json.JSONDecodeError):
            print("❌ 資料格式錯誤或查無結果")
            return None

    @async_retry(max_retries=3, delay=1)
    async def get_productline(self, main_product_category, site):
        data = {
            "websiteCode": site,
            "keyword": main_product_category,
            "productLine": "",
            "version": self.faq_ver,
            "n": 1,
            "hide_min": 0,
            "hide_max": 2000,
        }

        async with self.session.post(self.redis_url, headers=self.headers, data=json.dumps(data)) as response:
            response_json = await response.json()
            return response_json.get("result").get("faqs")[0]["productLine"]

    @async_retry(max_retries=3, delay=1)
    async def get_specific_service(self, search_info, site):
        data = {
            "websiteCode": site,
            "keyword": search_info,
            "productLine": "",
            "version": "5.1",
            "n": 1,
            "hide_min": 3001,
            "hide_max": 3012,
        }

        async with self.session.post(self.redis_url, headers=self.headers, data=json.dumps(data)) as response:
            top1_result = (await response.json()).get("result").get("faqs")[0]
            return {
                "service_from_search": self.hide_to_service(top1_result.get("hide")),
                "service_similarity": top1_result.get("cosineSimilarity"),
                "service_pl": top1_result.get("productLine"),
            }

    def hide_to_service(self, hide):
        # （此處略，與你原始內容一致）
        ...

    @async_retry(max_retries=3, delay=1)
    async def get_replace_service(self, replace_sen, site):
        data = {
            "websiteCode": site,
            "keyword": replace_sen,
            "productLine": "",
            "version": "6.0",
            "n": 1,
            "hide_min": 0,
            "hide_max": 1999
        }

        async with self.session.post(self.redis_url, headers=self.headers, data=json.dumps(data)) as response:
            top1_result = (await response.json()).get("result").get("faqs")[0]
            return {
                'service_from_search': self.hide_to_service(top1_result.get('hide')),
                'service_similarity': top1_result.get('cosineSimilarity')
            }

    @async_retry(max_retries=3, delay=1)
    async def get_service(self, search_info, site):
        data = {
            "websiteCode": site,
            "keyword": search_info,
            "productLine": "",
            "version": "5.0",
            "n": 1,
            "hide_min": 0,
            "hide_max": 1999,
        }

        async with self.session.post(self.redis_url, headers=self.headers, data=json.dumps(data)) as response:
            top1_result = (await response.json()).get("result").get("faqs")[0]
            return {
                "service_from_search": self.hide_to_service(top1_result.get("hide")),
                "service_similarity": top1_result.get("cosineSimilarity"),
            }

    @async_retry(max_retries=3, delay=1)
    async def get_faq(self, search_info, site, productLine, top_n=4):
        data = {
            "websiteCode": site,
            "keyword": search_info,
            "productLine": productLine,
            "version": self.faq_ver,
            "n": top_n,
            "hide_min": 0,
            "hide_max": 999,
        }
        # print("Redis FAQ 請求資料:", data)
        try:
            async with self.session.post(self.redis_url, headers=self.headers, data=json.dumps(data), timeout=aiohttp.ClientTimeout(total=20)) as response:
                # 確保 response.json() 成功解析並且包含 "result" 和 "faqs"
                response_json = await response.json()
                
                # print(json.dumps(data))
                # print(response_json)
                if not response_json:
                    raise ValueError("返回的 JSON 資料為空")
                
                result = response_json.get("result")
                if not result or "faqs" not in result:
                    raise KeyError('"faqs" 不存在於返回的結果中')

                faqs = result["faqs"]
                return {
                    "faq": [faq.get("kb_no") for faq in faqs],
                    "cosineSimilarity": [faq.get("cosineSimilarity") for faq in faqs],
                    "productLine": [faq.get("productLine") for faq in faqs],
                }

        except Exception as e:
            print(f"處理 FAQ 時發生錯誤: {e}")
            return {}  # 返回空字典或其他適當的錯誤處理結果

