# from azure.cosmos import CosmosClient 
# from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from typing import Optional
import pandas as pd
from datetime import datetime
import uuid
import json

class MockCosmosClient:
    """模擬 CosmosClient 的行為"""
    def __init__(self, url, credential, consistency_level=None):
        print(f"初始化模擬 CosmosClient: {url}")
        self.url = url
        
    def get_database_client(self, database_name):
        print(f"取得資料庫客戶端: {database_name}")
        return MockDatabaseClient(database_name)

class MockDatabaseClient:
    """模擬 Database 客戶端的行為"""
    def __init__(self, database_name):
        self.database_name = database_name
        
    def get_container_client(self, container_name):
        print(f"取得容器客戶端: {container_name}")
        return MockContainerClient(self.database_name, container_name)

class MockAsyncIterator:
    """模擬異步迭代器"""
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item

class MockContainerClient:
    """模擬 Container 客戶端的行為"""
    def __init__(self, database_name, container_name):
        self.database_name = database_name
        self.container_name = container_name
    
    def query_items(self, query, enable_cross_partition_query=True):
        """模擬同步查詢操作"""
        print(f"執行同步查詢: {query}")
        return [{
            "id": "mock_1",
            "type": "mock_data",
            "content": "這是模擬資料",
            "createDate": "2025-10-28T08:00:00Z",
            "user_info": {"mock_user": "data"},
            "process_info": {
                "bot_scope": "technical-support",
                "merge_user_input": "mock_input"
            },
            "extract": {
                "output": "mock_output"
            }
        }]

    def query_items(self, query, enable_cross_partition_query=True):
        """模擬異步查詢操作，返回異步迭代器"""
        print(f"執行異步查詢: {query}")
        if "ApChatbotKnowledge" in query or "ai-agent-backend" in query:
            mock_data = {
                "faq": ["AAPF-1234", "AAPF-5678", "AAPF-9012"],
                "cosineSimilarity": [0.85, 0.75, 0.65],
                "productLine": ["notebook", "desktop", "accessories"]
            }
            return MockAsyncIterator([mock_data])
        else:
            mock_data = [{
                "id": "mock_1",
                "type": "mock_data",
                "user_input": "mock_input",
                "content": "這是模擬資料",
                "createDate": "2025-10-28T08:00:00Z",
                "user_info": {"mock_user": "data"},
                "process_info": {
                    "bot_scope": "technical-support",
                    "merge_user_input": "mock_input"
                },
                "extract": {
                    "output": {
                        "answer": "這是模擬的回答內容",
                        "intent": "Technical Support",
                        "kb_no": 12345
                    },
                    "policy_violation": False
                }
            }]
            return MockAsyncIterator(mock_data)
    
    async def upsert_item(self, data):
        """模擬寫入操作"""
        print(f"模擬寫入到 {self.container_name}:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return data

class CosmosConfig:
    def __init__(self, config):
        print("初始化模擬 CosmosConfig")
        
        # 儲存設定但不真正使用
        self.url = config.get("TECH_COSMOS_URL", "mock_url")
        self.key = config.get("TECH_COSMOS_KEY", "mock_key")
        
        # 使用模擬的客戶端
        self.client = MockCosmosClient(self.url, self.key, consistency_level="Session")

        self.database_name = config.get("TECH_COSMOS_DB")
        self.lookup_db_name = config.get("TECH_COSMOS_LOOKUP_DB")

        self.container_name = config.get("TECH_COSMOS_CONTAINER")
        self.productid_container_name = config.get("TECH_COSMOS_PRODUCTID_CONTAINER")
        self.recommendation_container_name = config.get("TECH_COSMOS_RECOMMENDATION_CONTAINER")
        self.hint_container_name = config.get("TECH_COSMOS_HINT_CONTAINER")

        # Create the database if it doesn't exist
        self.database = self.client.get_database_client(self.database_name)
        self.lookup_db = self.client.get_database_client(self.lookup_db_name)

        # Create the container with a partition key
        self.container = self.database.get_container_client(self.container_name)
        self.productid_container = self.database.get_container_client(
            self.productid_container_name
        )
        self.recommendation_container = self.database.get_container_client(
            self.recommendation_container_name
        )
        self.hint_container = self.database.get_container_client(
            self.hint_container_name
        )
        
        ###
        # 使用相同的模擬客戶端
        self.async_client = self.client

        # Create the database if it doesn't exist
        self.async_database = self.async_client.get_database_client(self.database_name)
        self.async_lookup_db = self.async_client.get_database_client(self.lookup_db_name)

        # Create the container with a partition key
        self.async_container = self.async_database.get_container_client(self.container_name)
        self.async_productid_container = self.async_database.get_container_client(
            self.productid_container_name
        )
        self.async_recommendation_container = self.async_database.get_container_client(
            self.recommendation_container_name
        )
        self.async_hint_container = self.async_database.get_container_client(
            self.hint_container_name
        )
        
        self.renderlog_container = self.async_database.get_container_client("renderLog")


    def query_cosmos(
            self,
            container_name: str,
            query: Optional[str] = "SELECT * FROM c",
            enable_cross_partition: bool = True
        ) -> pd.DataFrame:
        """
        從 Azure Cosmos DB container 查詢知識庫 (KB) 資料，回傳 DataFrame 格式。

        Args:
            cosmos_client (CosmosClient): 已初始化的 CosmosClient 實例。
            database_name (str): 資料庫名稱。
            container_name (str): 容器 (container) 名稱。
            query (str, optional): SQL 查詢語句，預設為 "SELECT * FROM c"。
            enable_cross_partition (bool, optional): 是否允許跨 partition 查詢。

        Returns:
            pd.DataFrame: 包含查詢結果的 DataFrame。如果查無資料，回傳空 DataFrame。
        """
        try:
            container = self.lookup_db.get_container_client(container_name)

            results = container.query_items(
                query=query,
                enable_cross_partition_query=enable_cross_partition
            )

            data = [item for item in results]
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"❌ 查詢 Cosmos 資料失敗: {e}")
            return pd.DataFrame()
        
    def query_cosmos_AIA(
            self,
            container_name: str,
            query: Optional[str] = "SELECT * FROM c",
            enable_cross_partition: bool = True
        ) -> pd.DataFrame:
        """
        從 Azure Cosmos DB container 查詢知識庫 (KB) 資料，回傳 DataFrame 格式。

        Args:
            cosmos_client (CosmosClient): 已初始化的 CosmosClient 實例。
            database_name (str): 資料庫名稱。
            container_name (str): 容器 (container) 名稱。
            query (str, optional): SQL 查詢語句，預設為 "SELECT * FROM c"。
            enable_cross_partition (bool, optional): 是否允許跨 partition 查詢。

        Returns:
            pd.DataFrame: 包含查詢結果的 DataFrame。如果查無資料，回傳空 DataFrame。
        """
        try:
            container = self.database.get_container_client(container_name)

            results = container.query_items(
                query=query,
                enable_cross_partition_query=enable_cross_partition
            )

            data = [item for item in results]
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"❌ 查詢 Cosmos 資料失敗: {e}")
            return pd.DataFrame()

    # 新增抓取追問資訊 last_ask_flag
    # @async_timer.timeit
    async def create_GPT_messages(self, session_id: str, user_input: str):
        """
        to query chat history from CosmosDB, and append these message for this time.
        (please answer in json format and answer in English) will not recored in GPT's answer,
        and it can return json format. Great!
        """
        messages = []
        # query = """SELECT * FROM c
        #         where c.session_id = "{}"
        #         and c.extract.policy_violation = false
        #         ORDER BY c._ts""".format(
        #     session_id
        # )

        query = """SELECT * FROM c
                where c.session_id = "{}"
                ORDER BY c._ts""".format(
            session_id
        )

        # contanier from chat log db
        # 使用异步迭代器收集结果
        results = []

        # contanier from chat log db
        async for item in self.async_container.query_items(
            query=query
        ):
            results.append(item)
        # print(results)
        chat_count = len(results)
        if len(results) > 0:
            # results =  sorted(results, key=lambda x: x['chat_create_date'])
            user_info = results[-1].get("user_info")
            last_bot_scope = results[-1].get("process_info").get("bot_scope")
            # last_intent = results[-1].get("extract").get("type2")
            # last_product_name = user_info.get("product_name")
            last_merge_user_input = results[-1].get("process_info").get("merge_user_input")
            # last_ask_flag = results[-1].get("extract").get("ask_flag")
            last_extract_output = results[-1].get("extract", {}).get("output", {})

            for item in results:
                messages.append(item.get("user_input"))

            messages.append(user_input)
            return (
                messages,
                chat_count,
                user_info,
                last_bot_scope,
                last_extract_output
                # last_intent,
                # last_product_name,
                # last_merge_user_input,
                # last_ask_flag,
            )

        messages.append(user_input)
        return messages, chat_count, None, None, None#, None, None, None, None

    async def get_latest_hint(self, sessionId):
        """
        to query chat history from CosmosDB, and append these message for this time.
        (please answer in json format and answer in English) will not recored in GPT's answer,
        and it can return json format. Great!
        """
        query = """SELECT TOP 1 c.userInput, c.searchInfo, c.intentHints, c.hintType, c.chatId
                FROM  c
                WHERE c.sessionId = "{}"
                ORDER BY c.ts DESC
                """.format(
            sessionId
        )
        # 使用异步迭代器收集结果
        results = []

        # contanier from chat log db
        async for item in self.async_hint_container.query_items(
            query=query
        ):
            results.append(item)
        # print(results)
        if results:
            return results[0]
        else:
            return None

    async def insert_hint_data(
        self, chatflow_data: dict, intent_hints: list, search_info: str, hint_type: str
    ):
        """sent to CosmosDB
        {
          "id": "deef1e9b-2215-4c80-9afc-f9aceeed25ab",
          "sessionId": "d8f68cf2-e552-45c2-b13f-b5582cd1ad00",
          "chatId": "af7b8c30-e4e3-4675-84cf-008ab83ef951",
          "userInput": "無法開機",
          "searchInfo": "cannot boot up",
          "intentHints":[{
            "id": 1014276, #KB
            "question": "筆記型電腦無法開機。",
            "rag_response": "",
            "title": "notebook", #產品線
            "link": ""
            }, ...],
          "hintType": "productline-reask",
          "createDate": "2024-05-20T10:41:49.0937469Z"
        }"""

        current_datetime = datetime.utcnow()
        # 轉換為 ISO 8601 格式的字符串
        create_date = current_datetime.isoformat() + "Z"
        data = {
            "id": str(uuid.uuid4()),
            "sessionId": chatflow_data.session_id,
            "chatId": chatflow_data.chat_id,
            "userInput": chatflow_data.user_input,
            "searchInfo": search_info,
            "intentHints": intent_hints,
            "hintType": hint_type,
            "createDate": create_date,
        }

        await self.async_hint_container.upsert_item(data)
        print("hint_container.upsert_item success")

    # @async_timer.timeit
    async def insert_data(self, data: dict):
        """sent to CosmosDB"""
        try:
            result = await self.async_container.upsert_item(data)
            print("✅ container.upsert_item 成功")
            return result
        except Exception as e:
            print(f"❌ 寫入 Cosmos 失敗: {e}")
            raise e




    # @async_timer.timeit
    async def insert_user_model_data(self, request_json: dict, m1Id: list, intent: str):
        """sent to CosmosDB
        {
          "id": "deef1e9b-2215-4c80-9afc-f9aceeed25ab",
          "sessionId": "d8f68cf2-e552-45c2-b13f-b5582cd1ad00",
          "chatId": "af7b8c30-e4e3-4675-84cf-008ab83ef951",
          "source": "purchasing-recommendation-of-asus-products",
          "m1Id": [24051,123123],
          "createDate": "2024-05-20T10:41:49.0937469Z"
        }"""

        current_datetime = datetime.utcnow()
        # 轉換為 ISO 8601 格式的字符串
        create_date = current_datetime.isoformat() + "Z"
        data = {
            "id": str(uuid.uuid4()),
            "sessionId": request_json.get("session_id"),
            "chatId": request_json.get("chat_id"),
            "source": intent,
            "m1Id": m1Id,
            "createDate": create_date,
        }

        self.productid_container.upsert_item(data)
        print("productid_container.upsert_item success")

    # @async_timer.timeit
    async def insert_recommendation_data(
        self, request_json: dict, products: dict, intent: str, function_args: dict, product_spec: str, rag_params: dict,overview_search: dict,productname_search:dict
    ):
        """sent to CosmosDB
        {
          "id": "deef1e9b-2215-4c80-9afc-f9aceeed25ab",
          "sessionId": "d8f68cf2-e552-45c2-b13f-b5582cd1ad00",
          "chatId": "af7b8c30-e4e3-4675-84cf-008ab83ef951",
          "source": "purchasing-recommendation-of-asus-products",
          "recommend_products" :[
                      {
                      "brand": "ROG",
                      "m1id": 24055,
                      "title": "rog zephyrus g16 (2024)",
                      "price": "NT$67,999",
                      "available_quantity": 29
                      }
                     ],
          "popularity":[
              {
              "brand": "ROG",
              "m1id": 24055,
              "title": "rog zephyrus g16 (2024)",
              "price": "NT$67,999",
              "available_quantity": 29
              }
              ]
          "createDate": "2024-05-20T10:41:49.0937469Z"


        ...
        ]"""

        # recommend_products = []
        # popularity = []
        # products = rec_response
        if products:
            #     for key in products.keys():
            #         if key == "recommend_products":
            #             for item in products.get(key):

            #                 data = {
            #                     "brand": item.get('brand'),
            #                     "m1id": item.get('m1id'),
            #                     "title": item.get('title'),
            #                     "price": item.get('price'),
            #                     "available_quantity": item.get('available_quantity'),
            #                 }
            #                 recommend_products.append(data)
            #         else:
            #             try:
            #                 item = products.get(key)
            #                 data = {
            #                     "brand": item.get('brand'),
            #                     "m1id": item.get('m1id'),
            #                     "title": item.get('title'),
            #                     "price": item.get('price'),
            #                     "available_quantity": item.get('available_quantity'),
            #                 }
            #                 popularity.append(data)
            #             except Exception as e:
            #                 print('products:',products)
            #                 print({'insert_recommendation_data Error':e})
            #                 data = {
            #                     "brand": '',
            #                     "m1id": None,
            #                     "title": '',
            #                     "price": '',
            #                     "available_quantity": None,
            #                     "product_spec": ''
            #                 }
            #                 popularity.append(data)

            current_datetime = datetime.utcnow()
            # 轉換為 ISO 8601 格式的字符串
            create_date = current_datetime.isoformat() + "Z"
            data = {
                "id": str(uuid.uuid4()),
                "sessionId": request_json.get("session_id"),
                "chatId": request_json.get("chat_id"),
                "source": intent,
                "m1Id": products,
                "function_args": function_args,
                "product_spec": product_spec,
                "recommend_product_similarity":rag_params.get('recommend_product_similarity'),
                "recommend_product_similarity_explanation":rag_params.get('recommend_product_similarity_explanation'),
                "popularity": rag_params.get('popularity'),  # e.g., A score indicating how popular an item is
                "budget": rag_params.get('budget'),  # Retrieving budget from rag_params
                "prices": rag_params.get('prices'),  # Retrieving prices from rag_params
                "titles": rag_params.get('titles'),  # Retrieving titles from rag_params
                "spec": rag_params.get('spec'),  # Retrieving specification from rag_params
                "marketing_scenario": rag_params.get('marketing_scenario'),  # Retrieving marketing scenario from rag_params
                "overview_search": overview_search,  # Retrieving marketing scenario from rag_params
                "productname_search": productname_search,  # Retrieving marketing scenario from rag_params

                "createDate": create_date,
            }
            # product_spec=rag_params.get("params", {}).get("rec_query_result", [""]
            # data = {
            #     "id": str(uuid.uuid4()),
            #     "sessionId": request_json.get("session_id"),
            #     "chatId": request_json.get("chat_id"),
            #     "source": intent,
            #     "m1Id": products,
            #     "function_args": function_args,
            #     "product_spec": product_spec,
            #     "createDate": create_date,
            # }
            await self.async_recommendation_container.upsert_item(data)
            print("recommendation_container.upsert_item success")
        else:
            print("no products")


    def get_language_by_websitecode(self, websitecode: str) -> Optional[str]:
        # query = f"SELECT c.lang FROM c WHERE c.websitecode = '{websitecode}'"
        # df = self.query_cosmos("FAQ_LanguageMapping_ForOpenAI", query)
        # return df.iloc[0]["lang"] if not df.empty else None
        return "es-es"

    def get_kb_article(self,lang: str, kb_no: int) -> Optional[dict]:
        # query = f"SELECT * FROM c WHERE c.lang = '{lang}' AND c.kb_no = {kb_no}"
        # df = self.query_cosmos("ApChatbotKnowledge", query)
        return {
            "id": "1050571_es-es",
            "kb_no": 1050571,
            "lang": "es-es",
            "title": "[Router inalámbrico] Cómo cargar su propio certificado (HTTPS/SSL) en el router ASUS",
            "summary": "ASUS routers may display a warning message when connecting via HTTPS due to the routers self-signed certificate not being trusted by the browsers default SSL security specification. Users can make their connection secure by adjusting router settings or importing their own certificate via the routers DDNS function. The FAQ provides step-by-step instructions on how to import a certificate and troubleshoot any issues that may arise.",
            "content": "Cuando intenta conectarse a un router ASUS a través de HTTPS en su navegador, puede aparecer un mensaje de advertencia \"Su conexión no es privada\", lo que indica que el certificado de seguridad de la URL no es confiable. Esto se debe a que el certificado predeterminado del router está auto firmado, lo que no cumple con la especificación de seguridad SSL predeterminada del navegador. Por lo tanto, puede hacer que la conexión de su página web cumpla con la especificación de seguridad SSL del navegador a través de la configuración del router y establecer una conexión HTTPS segura.Los routers ASUS proporcionan 2 tipos de certificados; consulte las siguientes preguntas frecuentes[Router inalámbrico] ¿Cómo acceder a la página de configuración de la GUI web del router ASUS a través de HTTPS?[Solución de problemas] Cómo solucionar al abrir la GUI WEB del router ASUS aparece \"Su conexión no es privada\"Si desea utilizar su propio certificado para importar al router ASUS, siga los pasos a continuación:Nota: Este método requiere que primero se habilite la función DDNS de ASUS. Para conocer el método de configuración, consulte las preguntas frecuentes sobre la introducción y configuración de DDNS [router inalámbrico].1. Conecte su dispositivo (portátil, teléfono inteligente) al router mediante una conexión por cable o WiFi e ingrese la IP de la LAN del router o la URL del router https://www.asusrouter.com en la GUI WEB.  Consulte [Router inalámbrico] Cómo ingresar a la página de configuración del router (GUI web) para obtener más información.2. Ingrese el nombre de usuario y la contraseña de su router para iniciar sesión.3. Vaya a [WAN] > [DDNS] > seleccione [Importar su propio certificado] en Certificado HTTPS/SSL > haga clic en [Cargar].4. Haga clic en [Elegir archivo] para cargar el archivo que desea importar y haga clic en [Aceptar].5. Haga clic en [Aplicar] para guardar la configuración.Puede ver [Activo] en el estado del certificado del servidor.Preguntas frecuentes (FAQ)1. ¿No se pueden activar las credenciales después de importar las suyas propias? a. Confirme si el archivo de certificado se puede utilizar normalmente en otros dispositivos. b. Utilice las credenciales proporcionadas por el router ASUS. C. Actualice la versión de firmware de su router ASUS a la última versión. Después de actualizar el firmware, se recomienda restaurar el router a los valores predeterminados originales de fábrica.  Para saber cómo restaurar los routers ASUS a los valores predeterminados de fábrica y usar QIS para configurar, consulte los siguientes enlaces de preguntas frecuentes:[Router inalámbrico] ¿Cómo actualizar el firmware de su router a la última versión?[Router inalámbrico] ¿Cómo restablecer el router a la configuración predeterminada de fábrica?[Router inalámbrico] ¿Cómo utilizar QIS (Configuración rápida de Internet) para configurar el router? (GUI web)[Router inalámbrico] ¿Cómo configurar el router Wi-Fi de ASUS a través de la aplicación ASUS Router? (QIS, configuración rápida de Internet)¿Cómo obtener la (Utilidad/Firmware)?Puede descargar los controladores, software, firmware y manuales de usuario más recientes en el Centro de descargas de ASUS .Si necesita más información sobre el Centro de descargas de ASUS , consulte este enlace",
            "_rid": "34UbAN-0IBsBAAAAAAAAAA==",
            "_self": "dbs/34UbAA==/colls/34UbAN-0IBs=/docs/34UbAN-0IBsBAAAAAAAAAA==/",
            "_etag": "\"270032b2-0000-2300-0000-6684f51e0000\"",
            "_attachments": "attachments/",
            "_ts": 1719989534
        }

    async def get_language_by_websitecode_dev(self, websitecode: str) -> Optional[str]:
        # query = f"SELECT c.lang FROM c WHERE c.websitecode = '{websitecode}'"
        # df = self.query_cosmos("FAQ_LanguageMapping_ForOpenAI", query)
        # return df.iloc[0]["lang"] if not df.empty else None
        return "es-es"

    async def get_kb_article_dev(self,lang: str, kb_no: int) -> Optional[dict]:
        # query = f"SELECT * FROM c WHERE c.lang = '{lang}' AND c.kb_no = {kb_no}"
        # df = self.query_cosmos("ApChatbotKnowledge", query)
        # return df.iloc[0].to_dict() if not df.empty else None
        return {
            "id": "1050571_es-es",
            "kb_no": 1050571,
            "lang": "es-es",
            "title": "[Router inalámbrico] Cómo cargar su propio certificado (HTTPS/SSL) en el router ASUS",
            "summary": "ASUS routers may display a warning message when connecting via HTTPS due to the routers self-signed certificate not being trusted by the browsers default SSL security specification. Users can make their connection secure by adjusting router settings or importing their own certificate via the routers DDNS function. The FAQ provides step-by-step instructions on how to import a certificate and troubleshoot any issues that may arise.",
            "content": "Cuando intenta conectarse a un router ASUS a través de HTTPS en su navegador, puede aparecer un mensaje de advertencia \"Su conexión no es privada\", lo que indica que el certificado de seguridad de la URL no es confiable. Esto se debe a que el certificado predeterminado del router está auto firmado, lo que no cumple con la especificación de seguridad SSL predeterminada del navegador. Por lo tanto, puede hacer que la conexión de su página web cumpla con la especificación de seguridad SSL del navegador a través de la configuración del router y establecer una conexión HTTPS segura.Los routers ASUS proporcionan 2 tipos de certificados; consulte las siguientes preguntas frecuentes[Router inalámbrico] ¿Cómo acceder a la página de configuración de la GUI web del router ASUS a través de HTTPS?[Solución de problemas] Cómo solucionar al abrir la GUI WEB del router ASUS aparece \"Su conexión no es privada\"Si desea utilizar su propio certificado para importar al router ASUS, siga los pasos a continuación:Nota: Este método requiere que primero se habilite la función DDNS de ASUS. Para conocer el método de configuración, consulte las preguntas frecuentes sobre la introducción y configuración de DDNS [router inalámbrico].1. Conecte su dispositivo (portátil, teléfono inteligente) al router mediante una conexión por cable o WiFi e ingrese la IP de la LAN del router o la URL del router https://www.asusrouter.com en la GUI WEB.  Consulte [Router inalámbrico] Cómo ingresar a la página de configuración del router (GUI web) para obtener más información.2. Ingrese el nombre de usuario y la contraseña de su router para iniciar sesión.3. Vaya a [WAN] > [DDNS] > seleccione [Importar su propio certificado] en Certificado HTTPS/SSL > haga clic en [Cargar].4. Haga clic en [Elegir archivo] para cargar el archivo que desea importar y haga clic en [Aceptar].5. Haga clic en [Aplicar] para guardar la configuración.Puede ver [Activo] en el estado del certificado del servidor.Preguntas frecuentes (FAQ)1. ¿No se pueden activar las credenciales después de importar las suyas propias? a. Confirme si el archivo de certificado se puede utilizar normalmente en otros dispositivos. b. Utilice las credenciales proporcionadas por el router ASUS. C. Actualice la versión de firmware de su router ASUS a la última versión. Después de actualizar el firmware, se recomienda restaurar el router a los valores predeterminados originales de fábrica.  Para saber cómo restaurar los routers ASUS a los valores predeterminados de fábrica y usar QIS para configurar, consulte los siguientes enlaces de preguntas frecuentes:[Router inalámbrico] ¿Cómo actualizar el firmware de su router a la última versión?[Router inalámbrico] ¿Cómo restablecer el router a la configuración predeterminada de fábrica?[Router inalámbrico] ¿Cómo utilizar QIS (Configuración rápida de Internet) para configurar el router? (GUI web)[Router inalámbrico] ¿Cómo configurar el router Wi-Fi de ASUS a través de la aplicación ASUS Router? (QIS, configuración rápida de Internet)¿Cómo obtener la (Utilidad/Firmware)?Puede descargar los controladores, software, firmware y manuales de usuario más recientes en el Centro de descargas de ASUS .Si necesita más información sobre el Centro de descargas de ASUS , consulte este enlace",
            "_rid": "34UbAN-0IBsBAAAAAAAAAA==",
            "_self": "dbs/34UbAA==/colls/34UbAN-0IBs=/docs/34UbAN-0IBsBAAAAAAAAAA==/",
            "_etag": "\"270032b2-0000-2300-0000-6684f51e0000\"",
            "_attachments": "attachments/",
            "_ts": 1719989534
        }

    async def get_chatfaq(self, limit: int = 1) -> pd.DataFrame:
        """
        從 dev-aocc-ai-assistant 資料庫的 chatfaq 容器中取出資料
        查詢條件: site = 'tw' 且 extract.ask_flag = true
        依照時間戳排序，取得前 limit 筆資料的所有欄位

        Args:
            limit (int): 要取得的資料筆數，預設為 1

        Returns:
            pd.DataFrame: 包含查詢結果的 DataFrame，包含所有欄位
        """
        try:
            query = f"SELECT TOP {limit} * FROM c order by c._ts desc"
            df = self.query_cosmos_AIA("chatfaq", query)
            
            if not df.empty:
                print(f"✅ 成功從 chatfaq 取得資料，共 {len(df)} 筆")
                return df
            else:
                print("❌ 沒有找到符合條件的 chatfaq 資料")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ 查詢 chatfaq 資料失敗: {e}")
            return pd.DataFrame()

    async def get_chatfaq_reask(self, limit: int = None) -> pd.DataFrame:
        """
        基於 get_chatfaq_reask 的條件，找出所有不重複的 session_id，
        然後抓取這些 session_id 的所有資料（不限筆數）
        
        查詢條件: site = 'tw' 且 extract.ask_flag = true 且 cus_id != '' 且不包含 'test'

        Args:
            limit (int, optional): 限制要取得的 session_id 數量，預設為 None（取得全部）

        Returns:
            pd.DataFrame: 包含所有符合條件的 session_id 的完整資料
        """
        try:
            print("🔍 第一步：查詢符合條件的不重複 session_id...")
            
            # 第一步：找出所有符合條件的不重複 session_id
            # 移除 ORDER BY 避免複合索引問題
            if limit:
                session_query = f"""
                    SELECT DISTINCT TOP {limit} *
                    FROM c 
                    WHERE c.site = 'tw' 
                    AND c.extract.ask_flag = true 
                    AND c.cus_id != '' 
                    AND NOT CONTAINS(LOWER(c.session_id), 'test')
                    AND c.extract.type2 like "%technical-support%"
                    order by c._ts desc
                """
            else:
                session_query = """
                    SELECT DISTINCT * 
                    FROM c 
                    WHERE c.site = 'tw' 
                    AND c.extract.ask_flag = true 
                    AND c.cus_id != '' 
                    AND NOT CONTAINS(LOWER(c.session_id), 'test')
                    AND c.extract.type2 like "%technical-support%"
                    order by c._ts desc
                """
            
            reask_df = self.query_cosmos_AIA("chatfaq", session_query)

            if reask_df.empty:
                print("❌ 沒有找到符合條件的 session_id")
                return pd.DataFrame()

            return reask_df
        
        except Exception as e:
            print(f"❌ 查詢所有 session 資料失敗: {e}")
            return pd.DataFrame()

    async def get_chatfaq_all_immed_rag(self, limit: int = None) -> pd.DataFrame:
        """
        基於 get_chatfaq_reask 的條件，找出所有不重複的 session_id，
        然後抓取這些 session_id 的所有資料（不限筆數）
        
        查詢條件: site = 'tw' 且 extract.ask_flag = false 且 cus_id != '' 且不包含 'test'

        Args:
            limit (int, optional): 限制要取得的 session_id 數量，預設為 None（取得全部）

        Returns:
            pd.DataFrame: 包含所有符合條件的 session_id 的完整資料
        """
        try:
            print("🔍 第一步：查詢符合條件的不重複 session_id...")
            
            # 第一步：找出所有符合條件的不重複 session_id
            # 移除 ORDER BY 避免複合索引問題
            if limit:
                session_query = f"""
                    SELECT DISTINCT TOP {limit} *
                    FROM c 
                    WHERE c.site = 'tw'
                    AND c.extract.ask_flag = false
                    AND c.cus_id != ''
                    AND NOT CONTAINS(LOWER(c.session_id), 'test')
                    AND c.extract.type2 like "%technical-support%"
                    AND c.extract.intent_support.response_info.response_source = "immed_rag"
                    AND c.user_input = c.extract.merge_user_input
                    order by c._ts desc
                """
            else:
                session_query = """
                    SELECT DISTINCT *
                    FROM c 
                    WHERE c.site = 'tw' 
                    AND c.extract.ask_flag = false 
                    AND c.cus_id != '' 
                    AND NOT CONTAINS(LOWER(c.session_id), 'test')
                    AND c.extract.type2 like "%technical-support%"
                    AND c.extract.intent_support.response_info.response_source = "immed_rag"
                    AND c.user_input = c.extract.merge_user_input
                    order by c._ts desc
                """
            
            immedrag_df = self.query_cosmos_AIA("chatfaq", session_query)

            if immedrag_df.empty:
                print("❌ 沒有找到符合條件的資料")
                return pd.DataFrame()
            
            return immedrag_df
                
        except Exception as e:
            print(f"❌ 查詢所有 session 資料失敗: {e}")
            return pd.DataFrame()



