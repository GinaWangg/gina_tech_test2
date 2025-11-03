from azure.cosmos import CosmosClient 
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from typing import Optional
import pandas as pd
from datetime import datetime
import uuid

class CosmosConfig:
    def __init__(self, config):

        self.url = config.get("TECH_COSMOS_URL")
        # self.key = config.get("TECH_COSMOS_KEY")
        # self.client = CosmosClient(
        #     self.url, credential=self.key, consistency_level="Session"
        # )

        # self.database_name = config.get("TECH_COSMOS_DB")
        # self.lookup_db_name = config.get("TECH_COSMOS_LOOKUP_DB")

        # self.container_name = config.get("TECH_COSMOS_CONTAINER")
        # self.productid_container_name = config.get("TECH_COSMOS_PRODUCTID_CONTAINER")
        # self.recommendation_container_name = config.get("TECH_COSMOS_RECOMMENDATION_CONTAINER")
        # self.hint_container_name = config.get("TECH_COSMOS_HINT_CONTAINER")

        # # Create the database if it doesn't exist
        # self.database = self.client.get_database_client(self.database_name)
        # self.lookup_db = self.client.get_database_client(self.lookup_db_name)

        # # Create the container with a partition key
        # self.container = self.database.get_container_client(self.container_name)
        # self.productid_container = self.database.get_container_client(
        #     self.productid_container_name
        # )
        # self.recommendation_container = self.database.get_container_client(
        #     self.recommendation_container_name
        # )
        # self.hint_container = self.database.get_container_client(
        #     self.hint_container_name
        # )
        
        # ##
        # self.async_client = AsyncCosmosClient(
        #     self.url, credential=self.key, consistency_level="Session"
        # )

        # # Create the database if it doesn't exist
        # self.async_database = self.async_client.get_database_client(self.database_name)
        # self.async_lookup_db = self.async_client.get_database_client(self.lookup_db_name)

        # # Create the container with a partition key
        # self.async_container = self.async_database.get_container_client(self.container_name)
        # self.async_productid_container = self.async_database.get_container_client(
        #     self.productid_container_name
        # )
        # self.async_recommendation_container = self.async_database.get_container_client(
        #     self.recommendation_container_name
        # )
        # self.async_hint_container = self.async_database.get_container_client(
        #     self.hint_container_name
        # )
        
        # self.renderlog_container = self.async_database.get_container_client("renderLog")
    
    def _print_sample(self, tag: str, data, limit: int = 10):
        """統一列印幾筆樣本資料，方便之後 copy 當 mock"""
        try:
            print(f"\n===== [COSMOS SAMPLE] {tag} =====")
            if isinstance(data, pd.DataFrame):
                # 盡量用 JSON，之後貼回程式比較方便
                print(data.head(limit).to_json(orient="records", force_ascii=False, indent=2))
            elif isinstance(data, list):
                import json
                print(json.dumps(data[:limit], ensure_ascii=False, indent=2))
            else:
                print(str(data)[:2000])  # 保底
            print("===== [END SAMPLE] =====\n")
        except Exception as e:
            print(f"[WARN] print sample failed for {tag}: {e}")

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
        # try:
        #     container = self.lookup_db.get_container_client(container_name)

        #     results = container.query_items(
        #         query=query,
        #         enable_cross_partition_query=enable_cross_partition
        #     )

        #     data = [item for item in results]
        #     df = pd.DataFrame(data)
        #     return df

        # except Exception as e:
        #     print(f"❌ 查詢 Cosmos 資料失敗: {e}")
        #     return pd.DataFrame()
        print("query_cosmos is disabled for testing. gina")
        
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
        # try:
        #     container = self.database.get_container_client(container_name)

        #     results = container.query_items(
        #         query=query,
        #         enable_cross_partition_query=enable_cross_partition
        #     )

        #     data = [item for item in results]
        #     df = pd.DataFrame(data)
        #     return df

        # except Exception as e:
        #     print(f"❌ 查詢 Cosmos 資料失敗: {e}")
        #     return pd.DataFrame()
        print("query_cosmos_AIA is disabled for testing. gina")

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
        # results = []
        results = [{'id': 'test-f6b3ddd8-6c55-4edc-9cf0-8408664cb89d-09cfda05-6096-4501-b720-d6aaab6be8d7', 'cus_id': 'test', 'session_id': 'f6b3ddd8-6c55-4edc-9cf0-8408664cb89d', 'chat_id': '09cfda05-6096-4501-b720-d6aaab6be8d7', 'createDate': '2025-10-29T07:59:53.475521Z', 'user_input': '筆電可以開機，風扇也有運轉，但螢幕一直是黑的，發生甚麼問題了?', 'websitecode': 'tw', 'product_line': '', 'system_code': 'rog', 'user_info': {'main_product_category': 'notebook', 'sub_product_category': 'Display'}, 'process_info': {'bot_scope': 'notebook', 'search_info': "the laptop can be turned on and the fan is running, but the screen remains black. what's wrong?", 'is_follow_up': False, 'faq_pl': {'faq': [1014276, 1042613, 1015072, 1038855], 'cosineSimilarity': [0.803633332253, 0.682648062706, 0.681610226631, 0.669006764889], 'productLine': ['chromebook,desktop,gaming_handhelds,notebook,nuc', 'chromebook,desktop,gaming_handhelds,notebook', 'chromebook,desktop,gaming_handhelds,notebook', 'chromebook,desktop,gaming_handhelds,notebook,nuc']}, 'faq_wo_pl': {'faq': [1014276, 1012723, 1016113, 1042632], 'cosineSimilarity': [0.803705453873, 0.7156489491460001, 0.6922438740729999, 0.691635489464], 'productLine': ['chromebook,desktop,gaming_handhelds,notebook,nuc', 'lcd', 'lcd,motherboard', 'motherboard']}, 'language': 'zh-tw', 'last_info': {'prev_q': '', 'prev_a': '', 'kb_no': ''}}, 'final_result': {'status': 200, 'message': 'OK', 'result': {'renderTime': 1761724793, 'render': [{'renderId': '5559d783-2b70-4f8b-a277-ade67e608f73', 'stream': False, 'type': 'avatarTechnicalSupport', 'message': '哈囉！筆電有電、風扇也轉，結果螢幕卻黑屏，吼～這狀況真的讓人有點慌耶。別擔心，我們有個超詳 細的常見問題解答，剛好對應到你的問題喔！你可以先看看螢幕上的資訊，有幾種狀況排除方式可以試試看。如果還有疑問，隨時都能找現場工作人員，他們很 樂意幫你喔！', 'remark': [], 'option': [{'type': 'faqcards', 'cards': [{'link': 'https://rog.asus.com/tw/support/FAQ/1014276', 'title': '疑難排解 - 裝置無法開機，或開機後螢幕沒有畫面（黑畫面）', 'content': '適用產品：筆記型電腦、桌上型電腦、All-in-One PC、電競掌機、MiniPC、ASUS NUC為了提供給您更清楚的操作說明，您也可點擊下方YouTube影片連結，觀看如何解決筆電無法開機且螢幕沒有任何反應 操作步驟的影片。https://www.youtube.com/watch?v=ADSvlvRuiGI如果您的裝置在開機時遇到無法啟動或開機後螢幕顯示黑畫面的問題。根據你的情境，請參考以下解決方案：情境一：遇到問題前，曾 經斷開電池接口、更換記憶體、或執行重設嵌入式控制器（EC reset）、即時時鐘（RTC），可能是因為記憶體訓練造成的開機沒有畫面（或顯示Working on Memory Training）。以下疑難排解僅適用於您的裝置開機時沒有畫面（或顯示Working on Memory Training），但是電源指示燈有亮，且如果您的裝置在遇到這個 問題前，您曾經操作過以下其中一項步驟，請參考下方說明：斷開電池接口或更換電池（含鈕扣電池）更換不同容量或不同品牌的記憶體清除嵌入式控制器（EC reset）、即時時鐘（RTC），以將裝置中的硬體恢復到預設狀態。您可以參考以下文章以了解如何清除：筆記型電腦/All-in-One PC/電競掌機：如何重設嵌入式控制器(EC reset)、即時時鐘(RTC)、硬重設(Hard reset)桌上型電腦：請問Clear CMOS步驟為何如果您曾經執行過上述三種操作之一，裝置在下次開機時需要先完整執行過一次記憶體訓練（Memory training）。記憶體訓練過程中，裝置不會有畫面顯示，而訓練所需時間約1~3分鐘，時間長短取決於您系統記憶體的大小 。在此期間，請您將裝置接上電源且不要強制關機，讓裝置自行完成記憶體訓練並等待畫面出現。註：如果您的裝置搭載的是Intel Lunar Lake CPU平台或更高 版本，並且螢幕解析度低於2880x1800及更新率低於120 Hz，當系統進行記憶體訓練時，螢幕上可能會顯示「Working on Memory Training」等文字。請您耐心等待，讓裝置自行完成記憶體訓練後，即可進入作業系統。如果您的裝置不符合這些硬體規格，進行記憶體訓練時則不會顯示任何畫面。如果等待超過3分鐘仍然沒有畫面，請參考常見的無法開機解決方式。情境二：遇到問題前曾經更新BIOS，且由於BIOS更新失敗（如強制關機）而導致開機時無法進入Windows作業系統。如果您曾經在BIOS更新過程中如不慎關機而導致無法進入Windows作業系統，請參考以下三種不同的開機畫面，以繼續完成BIOS更新。待BIOS更新完成後即可順利進入Windows作業系統。請注意：在BIOS更新過程中，請確保裝置有接上電源且不要強制關機，以避免發生異常問題。畫面1：如果您遇到以下畫面，表示由於BIOS 更新失敗，請等待60秒或點擊畫面上的「Yes」，系統將自動重新進行BIOS更新。（確保裝置已連接電源線）畫面2：如果您遇到以下畫面，表示由於BIOS更新失 敗，請按照以下步驟完成BIOS更新：使用另一台電腦前往華碩支援網站，下載與您的機種相對應的BIOS檔案。下載完成後，將BIOS檔案放到格式為FAT32的USB隨 身碟的根目錄中。您可以參考這篇文章了解如何將下載的BIOS檔案儲存至USB隨身碟裡。註：如果您的裝置有顯示建議的BIOS版本，請下載該版本。如果沒有，請下載最新版本的BIOS。了解更多：如何搜尋與下載BIOS檔案。關閉出現上述畫面的裝置。長按電源鍵15秒，直到電源燈熄滅。將內含BIOS檔案的USB隨身碟連接至裝置，並確保電源線已接上。將裝置開機，系統將會自動完成BIOS更新程序。註：如果裝置重新開機後直接進入華碩韌體更新畫面（ASUS EZ Flash），您可以參考這篇文章了解如何使用EZ Flash更新BIOS檔案 (如果您的電腦是桌上型電腦，請參考ASUS Motherboard EZ Flash 3 介紹)。畫面3：如果您因為BIOS更新失敗 ，且遇到的情況是開機後黑屏（電源燈有亮起，但畫面中沒有顯示任何文字），您可以嘗試執行嵌入式控制器（EC reset）、即時時鐘（RTC）清除以解決問題：筆記型電腦/All-in-One PC/電競掌機：如何重設嵌入式控制器(EC reset)、即時時鐘(RTC)、硬重設(Hard reset)桌上型電腦：請問Clear CMOS步驟為何情境三 ：遇到問題前，曾經加裝或更換獨立顯示卡（僅限桌上型電腦產品）對於搭載Intel 13代CPU（及其後平台）的桌上型電腦，如果您曾加裝或更換獨立顯示卡且螢幕顯示輸出連接的是獨立顯示卡的連接埠，可能會遇到開機無畫面的情況。這是因為首次使用獨立顯示卡（或不同的獨立顯示卡）時，系統需要先辨識到顯示卡 後才能正常輸出畫面。如遇到上述情況，請按照以下步驟操作：連接內建顯示卡：請先將螢幕顯示輸出連接至內建顯示卡（主機板上的連接埠）。開機：將電腦 開機，系統應能正常進入。確認辨識顯示卡：進入裝置管理員，若出現「Microsoft基本顯示卡」，表示系統已辨識到新的獨立顯示卡。註：如果新的顯示卡沒有出現，請參考這篇文章：疑難排解 - 偵測不到顯示卡。更換顯示輸出：此時即可將螢幕顯示輸出更換至獨立顯示卡的連接埠。安裝驅動程式：安裝顯示卡的驅動程式。新的顯示卡即可正常使用。這樣即可解決開機無畫面的問題，並正常使用您的獨立顯示卡。如果您未曾遇到上述情境，請查看其他常見的無法開機解決方 式當您的裝置無法開機（不開機/開不了機），請依據電源指示燈或顯示畫面而參考下列不同的解決方式：註：不同產品或型號的電源指示燈會有差異（下圖以筆記型電腦作為範例），詳細資訊請參考您裝置型號的使用手冊。請參考這篇文章以了解如何搜尋與下載使用手冊。按下開機按鈕後，螢幕沒有畫面、電源指示燈 沒有亮電源指示燈沒有亮，可能是變壓器無法供電或主要元件異常而造成無法開機，請執行以下步驟：請檢查連接裝置的電源線、變壓器、延長線、及壁面插座 已確實妥善接上。若使用延長線，請確認延長線開關為開啟狀態。請使用原廠配置且規格正確的變壓器及電源線。檢查電源接頭是否有鬆脫，或更換其他延長線 及插座進行問題排除。如下圖電源線端、插座端、裝置端皆確實連接。註：電源變壓器樣式可能因型號不同而有差異，請參考使用手冊說明。 檢查變壓器或電源線材是否有破損現象，若有發生建議前往維修中心進行更換。請移除所有外接裝置，包含鍵盤、滑鼠、外接硬碟、印表機、記憶卡、光碟機內的光碟片、也包含 讀卡機內的轉接卡等等。註：同時移除所有外接顯示器。若是桌上型電腦，則先連接一部外接顯示器以確認電腦能正常開機並顯示畫面。問題發生前，是否進行 過擴充硬碟或記憶體。若有，請先將該硬體移除或恢復至出廠預設狀態。移除變壓器或電源線，然後執行嵌入式控制器（EC reset）、即時時鐘（RTC）清除，以將裝置中的硬體恢復到預設狀態。您可以參考相關文章以了解如何清除：筆記型電腦/All-in-One PC/電競掌機：如何重設嵌入式控制器(EC reset)、即時時鐘(RTC)、硬重設(Hard reset)桌上型電腦：請問Clear CMOS步驟為何連接變壓器或電源線，然後按下電源按鈕確認是否可以正常開機。按下開機按鈕後，螢幕沒有畫面、電源指示燈有亮電源指示燈有亮，代表主機板有過電，但可能因為部分裝置造成無法開機。根據您使用的產品，請執行適用的解決方法：筆記型電腦、All-in-One PC、電競掌機如果您有外部顯示器，請嘗試將裝置連接到外部顯示器，並使用快捷鍵Windows標誌鍵 + P鍵切換顯示模式，以確認外部顯示器是否能正常顯示。若您沒有外部顯示器，或是外部顯示器也沒有畫面，請繼續下一步。若外部顯示器正常運作，請嘗試前往華碩支援網站下載顯示卡驅動程式並安裝，瞭解更 多如何搜尋與下載驅動程式。註：如果您的裝置配備兩個顯示卡（俗稱為內顯及獨顯，例如Intel & NVIDIA），可在裝置管理員內檢視。請確認皆更新至華碩官 網發布的最新版本。請嘗試執行Microsoft的快捷鍵：Windows標誌鍵 + Ctrl + Shift + B鍵，這個快捷鍵可以還原顯示相關的設定，有時可以解決顯示問題。請移除所有外接裝置，包含鍵盤、滑鼠、外接硬碟、印表機、記憶卡、光碟機內的光碟片、也包含讀卡機內的轉接卡等等。註：同時移除所有外接顯示器。問題發 生前，是否進行過擴充硬碟或記憶體。若有，請先將該硬體移除或恢復至出廠預設狀態。移除變壓器或電源線，然後執行嵌入式控制器（EC reset）、即時時鐘 （RTC）清除，以將裝置中的硬體恢復到預設狀態。您可以參考這篇文章，以更了解如何清除：如何重設嵌入式控制器(EC reset)、即時時鐘(RTC)、硬重設(Hard reset)。連接變壓器或電源線，然後按下電源按鈕確認是否可以正常開機。若您已嘗試了前述的解決方式仍無法解決開機問題，您可以嘗試使用BIOS復原模式以更新裝置中的BIOS。以下是詳細步驟：註：您需要使用另一台電腦下載BIOS檔案和一個隨身碟（隨身碟必須使用FAT32的格式）存放BIOS檔案。瞭解更多如何轉換隨身碟的格式為FAT32。請依照您裝置目前的Windows作業系統版本，前往相對應的操作說明：Windows 11作業系統前往華碩支援網站，在BIOS類別中找到ASUS EZ Flash Utility的最新BIOS版本檔案，瞭解更多如何搜尋與下載BIOS檔案。（以下以X1505ZA型號作為範例）下載完成後，滑鼠右鍵點擊所下載的BIOS檔案①，然 後點選[解壓縮全部]②。點選[解壓縮]③。解壓縮完成後，將檔案的副檔名重新命名為「.bin」。滑鼠右鍵點擊已解壓縮的檔案④，然後點選[重新命名]⑤。將機種 型號之後的檔案名稱修改為「.bin」。（範例：X1505ZAAS.309 → Z1505ZA.bin）重新命名完成後，將隨身碟連接至裝置，滑鼠右鍵點擊「.bin」檔案⑥，選擇[顯示其他選項]⑦，然後在傳送到的選項中選擇您的隨身碟⑧。這樣就可以將BIOS檔案複製到隨身碟的根目錄下。註：隨身碟的格式需使用FAT32的格式。瞭解更多如 何轉換隨身碟的格式為FAT32。連接隨身碟至出現開機問題的裝置，然後將裝置開機，並於開機後連續按下快捷鍵（Ctrl + R）。如果成功進入BIOS復原模式，裝置將會重新開機並進入華碩韌體更新畫面（ASUS EZ Flash）。進入BIOS設定畫面後，將會有UEFI介面及MyASUS in UEFI兩種型式。請依據您裝置的BIOS畫面參考以下步驟：如何在UEFI介面中更新BIOS進入華碩韌體更新畫面（ASUS EZ Flash）後，選擇隨身碟中的「.bin」檔案⑨。點選[Yes]⑩以開始執行BIOS更新。註：在BIOS更新期間，裝置須保持電量於20%以上，同時保持電源連接且不要強制關機，以避免發生異常問題。BIOS更新完成後，裝置將自動重新開機。請再次確認您的 問題是否已經解決。如何在MyASUS in UEFI介面中更新BIOS進入華碩韌體更新畫面（ASUS EZ Flash）後，選擇隨身碟中的「.bin」檔案⑨。點選[確認]⑩以開始執行BIOS更新。註：在BIOS更新期間，裝置須保持電量於20%以上，同時保持電源連接且不要強制關機，以避免發生異常問題。BIOS更新完成後，裝置將自動重新開機。請再次確認您的問題是否已經解決。Windows 10作業系統前往華碩支援網站，在BIOS類別中找到ASUS EZ Flash Utility的最新BIOS版本檔案，瞭解更多如何搜尋與下載BIOS檔案。（以下以B9450FA型號作為範例）下載完成後，滑鼠右鍵點擊所下載的BIOS檔案①，然後點選[解壓縮全部]②。點選[解壓縮]③。解壓縮完成 後，將檔案的副檔名重新命名為「.bin」。滑鼠右鍵點擊已解壓縮的檔案④，然後點選[重新命名]⑤。將機種型號之後的檔案名稱修改為「.bin」。（範例：B9450FAAS.305 → B9450FA.bin）重新命名完成後，將隨身碟連接至裝置，滑鼠右鍵點擊「.bin」檔案⑥，選擇[傳送到]⑦，然後選擇您的隨身碟⑧。這樣就可以將BIOS檔案複製到隨身碟的根目錄下。註：隨身碟的格式需使用FAT32的格式。瞭解更多如何轉換隨身碟的格式為FAT32。連接隨身碟至出現開機問題的裝置，然後將裝置 開機，並於開機後連續按下快捷鍵（Ctrl + R）。如果成功進入BIOS復原模式，裝置將會重新開機並進入華碩韌體更新畫面（ASUS EZ Flash）。進入BIOS設定畫面後，將會有UEFI介面及MyASUS in UEFI兩種型式。請依據您裝置的BIOS畫面參考以下步驟：如何在UEFI介面中更新BIOS進入華碩韌體更新畫面（ASUS EZ Flash）後，選擇隨身碟中的「.bin」檔案⑨。點選[Yes]⑩以開始執行BIOS更新。註：在BIOS更新期間，裝置須保持電量於20%以上，同時保持電源連接且不要強制關機 ，以避免發生異常問題。BIOS更新完成後，裝置將自動重新開機。請再次確認您的問題是否已經解決。如何在MyASUS in UEFI介面中更新BIOS進入華碩韌體更新 畫面（ASUS EZ Flash）後，選擇隨身碟中的「.bin」檔案⑨。點選[確認]⑩以開始執行BIOS更新。註：在BIOS更新期間，裝置須保持電量於20%以上，同時保持電 源連接且不要強制關機，以避免發生異常問題。BIOS更新完成後，裝置將自動重新開機。請再次確認您的問題是否已經解決。桌上型電腦、MiniPC確認外部顯示 器的訊號線和電源線已正確連接。如果可能，嘗試將電腦連接至另一台外部顯示器，以確認問題是否與顯示器本身有關。桌上型電腦連接外部顯示器的方式有區 分內建顯示卡或獨立顯示卡的接口，請根據電腦支援的狀態連接至正確的接口，詳細連接方式請參考您的產品使用手冊。註：電腦是否支援內建顯示卡或獨立顯 示卡將依據型號不同而有所差異。如果您已確認顯示輸出連接埠正確，或者沒有其他外部顯示器可供測試，請繼續下一步。嘗試執行Microsoft的快捷鍵：Windows標誌鍵 + Ctrl + Shift + B鍵，這個快捷鍵可以還原顯示相關的設定，有時可以解決顯示問題。移除所有外接裝置，包含鍵盤、滑鼠、外接硬碟、印表機、記 憶卡、光碟機內的光碟片、以及讀卡機中的轉接卡等等。註：請將桌上型電腦只連接一部外接顯示器，以確認電腦能正常開機並顯示畫面。問題發生前，是否進 行過擴充硬碟或記憶體。若有，請先將該硬體移除或恢復至出廠預設狀態。移除電源線，然後執行CMOS清除，以將電腦中的硬體恢復到預設狀態。您可以參考這 篇文章：請問Clear CMOS步驟為何。連接電源線，然後按下電源按鈕確認是否可以正常開機。按下開機按鈕後，螢幕沒有畫面、電源指示燈或電池燈閃爍電源指 示燈或電池燈有亮並閃爍時，代表主機板有過電，且此時BIOS ROM 正在準備執行復原，因此螢幕畫面會呈現黑色狀態，請稍待約5-8分鐘直到BIOS ROM復原機制 的進度視窗顯示。註: 筆記型電腦產品為電池燈閃爍、桌上型電腦產品為電源指示燈閃爍。待BIOS ROM復原視窗出現，請參考系統預估的復原處理時間(約2.5到3.5小時)，之後系統將自動進行修復。請注意：在復原過程中，請確保裝置有接上電源且不要強制關機，以避免發生異常問題。按下開機按鈕後，出現白字黑底畫面裝置開機後，如果出現黑底白字畫面，請先查看情境二：BIOS更新過程中如不慎關機且機台不開機問題的章節，以確認是否有符合您裝置所顯示的畫面。如果 沒有符合，請繼續以下步驟。如果畫面顯示「S.M.A.R.T Status Bad」，您可以參考這篇文章解決問題：開機顯示錯誤訊息「S.M.A.R.T Status Bad」。若開機 時顯示錯誤並提示需要按F1進行設置，這表示在開機期間BIOS偵測到硬體設置有問題。畫面上的提示將指出哪個硬體設置不正常，您可以按照提示進行修正。另 外，您也可以嘗試按F1進入BIOS設定畫面，然後將BIOS設定恢復至原廠狀態。您可以參考這篇文章了解還原BIOS設定：如何還原BIOS設定。（桌上型電腦請參考 ：如何還原BIOS設定值）按下開機按鈕後，開機有畫面，進入桌面後無畫面如果開機時可以看到Windows的歡迎圖示，但進入桌面後就一片黑，可能是顯示卡驅動引起的問題。建議進入安全模式，進入安全模式可參考這篇文章：無法進入系統時，如何進入安全模式。進入安全模式後，重新安裝顯示卡驅動，您可以參考這 篇文章了解如何搜尋與下載驅動程式。如果上述步驟無法解決您的問題，請聯繫當地華碩客服中心尋求技術支援'}]}]}]}}, 'extract': {'status': 200, 'type': 'answer', 'message': 'RAG Response', 'output': {'answer': '根據您的問題，底下有一些技術文章供您參考 :\n您好，針對筆電開機後風扇運轉但螢幕 無顯示的情況，請您參考以下步驟進行故障排除：1. 嘗試將筆電連接至外部顯示器，並使用快捷鍵「Windows標誌鍵 + P」切換顯示模式，以確認外部顯示器是 否能正常顯示。2. 您可以按下快捷鍵「Windows標誌鍵 + Ctrl + Shift + B」鍵，這有助於還原顯示相關設定。3. 請移除所有外接裝置，包括鍵盤、滑鼠、外 接硬碟、印表機等。4. 如果問題發生前曾擴充硬碟或記憶體，請先將該硬體移除或恢復至出廠預設狀態。5. 移除變壓器或電源線後，執行嵌入式控制器（EC reset）或即時時鐘（RTC）清除，以將裝置硬體恢復到預設狀態，然後再重新連接電源嘗試開機。6. 若上述步驟仍無法解決問題，您可以嘗試使用BIOS復原模式來更新裝置中的BIOS。', 'ask_flag': False, 'hint_candidates': [], 'kb': {'kb_no': '1014276', 'title': '疑難排解 - 裝置無法開機，或開機後螢幕沒有畫面（黑畫面）', 'similarity': 0.803633332253, 'source': 'immed_rag', 'exec_time': 7.2}}}, 'total_time': 27.42, '_rid': 'zPFjAObJuB5SAQAAAAAAAA==', '_self': 'dbs/zPFjAA==/colls/zPFjAObJuB4=/docs/zPFjAObJuB5SAQAAAAAAAA==/', '_etag': '"1700e644-0000-2300-0000-6901c9790000"', '_attachments': 'attachments/', '_ts': 1761724793}, {'id': 'test-f6b3ddd8-6c55-4edc-9cf0-8408664cb89d-97953787-f01c-4f76-88d6-ebf5fecd27d6', 'cus_id': 'test', 'session_id': 'f6b3ddd8-6c55-4edc-9cf0-8408664cb89d', 'chat_id': '97953787-f01c-4f76-88d6-ebf5fecd27d6', 'createDate': '2025-10-29T08:02:42.479691Z', 'user_input': '我的筆電卡在登入畫面，完全沒有反應。', 'websitecode': 'tw', 'product_line': '', 'system_code': 'rog', 'user_info': {'main_product_category': 'notebook', 'sub_product_category': None}, 'process_info': {'bot_scope': 'notebook', 'search_info': "my laptop is stuck on the login screen and there's no response at all.", 'is_follow_up': True, 'faq_pl': {'faq': [1051479, 1038855, 1046480, 1042613], 'cosineSimilarity': [0.816743731499, 0.751851916313, 0.701354265213, 0.700322508812], 'productLine': ['chromebook,desktop,gaming_handhelds,motherboard,notebook', 'chromebook,desktop,gaming_handhelds,notebook,nuc', 'chromebook,desktop,gaming_handhelds,motherboard,notebook,nuc', 'chromebook,desktop,gaming_handhelds,notebook']}, 'faq_wo_pl': {'faq': [1051479, 1038855, 1046480, 1042613], 'cosineSimilarity': [0.816867470741, 0.75192964077, 0.701384782791, 0.700292348862], 'productLine': ['chromebook,desktop,gaming_handhelds,motherboard,notebook', 'chromebook,desktop,gaming_handhelds,notebook,nuc', 'chromebook,desktop,gaming_handhelds,motherboard,notebook,nuc', 'chromebook,desktop,gaming_handhelds,notebook']}, 'language': 'zh-tw', 'last_info': {'prev_q': '筆電可以開機，風扇也有運轉，但螢幕一直是黑的，發生甚麼問題了?', 'prev_a': '根據您 的問題，底下有一些技術文章供您參考 :\n您好，針對筆電開機後風扇運轉但螢幕無顯示的情況，請您參考以下步驟進行故障排除：1. 嘗試將筆電連接至外部顯示器，並使用快捷鍵「Windows標誌鍵 + P」切換顯示模式，以確認外部顯示器是否能正常顯示。2. 您可以按下快捷鍵「Windows標誌鍵 + Ctrl + Shift + B」 鍵，這有助於還原顯示相關設定。3. 請移除所有外接裝置，包括鍵盤、滑鼠、外接硬碟、印表機等。4. 如果問題發生前曾擴充硬碟或記憶體，請先將該硬體移 除或恢復至出廠預設狀態。5. 移除變壓器或電源線後，執行嵌入式控制器（EC reset）或即時時鐘（RTC）清除，以將裝置硬體恢復到預設狀態，然後再重新連 接電源嘗試開機。6. 若上述步驟仍無法解決問題，您可以嘗試使用BIOS復原模式來更新裝置中的BIOS。', 'kb_no': '1014276'}}, 'final_result': {'status': 200, 'message': 'OK', 'result': {'renderTime': 1761724962, 'render': [{'renderId': '2372775c-c43c-4c09-ab94-0a420e8b072f', 'stream': False, 'type': 'avatarTechnicalSupport', 'message': '喔，嗨！你的筆電卡在登入畫面沒反應，這可真讓人頭大對吧？別擔心，我們這裡有找到一篇超實用的技術文章，應該能幫你解決喔。\n\n你可以直接看看螢幕上的資訊，那邊有詳細的步驟。如果試了還是卡關，沒關係，就直接問問店裡的夥伴，他們都很樂意幫忙的 啦！加油囉！', 'remark': [], 'option': [{'type': 'faqcards', 'cards': [{'link': 'https://rog.asus.com/tw/support/FAQ/1051479', 'title': '[Windows 11/10] 疑難排解 - 裝置無法進入Windows系統', 'content': '適用產品：筆記型電腦、桌上型電腦、All-in-One PC、電競掌機、主機板、顯示卡這篇文 章提供裝置開機時無法正常進入Windows系統的常見解決方法。您可能遇到的問題現象是，裝置開機並出現ASUS或ROG標誌畫面後，停駐在Window歡迎畫面，而無 法登入Windows系統。請依序參考本文的步驟進行問題排解。註：如果您的裝置無法開機，請參考這篇文章：疑難排解 - 電腦無法開機，或開機後螢幕沒有畫面 （黑畫面）。註：如果您的裝置開機時停駐在ASUS或ROG標誌畫面，請參考這篇文章：疑難排解 - 開機時卡在ASUS/ROG標誌畫面。註：如果您的裝置開機時出現 自動修復的藍色或黑色畫面，請參考這篇文章：疑難排解 - 開機時出現自動修復。註：如果您的裝置開機時出現UEFI/BIOS/Aptio Setup Utility畫面，請參考 這篇文章：疑難排解 - 如何解決開機直接進入BIOS/Aptio Setup Utility畫面。解決方法1：移除外接設備並重新開機關閉裝置電源。長按電源鍵直到電源燈熄 滅，即可關閉裝置。請移除所有外接設備，包含鍵盤、滑鼠、外接硬碟、印表機、記憶卡、光碟機內的光碟片、也包含讀卡機內的轉接卡等等。有時候可能是因 為外接設備導致您的裝置無法正常進入Windows系統。註：同時移除所有外接顯示器。若是桌上型電腦，則先連接一部外接顯示器以確認電腦能正常開機並顯示畫面。開啟裝置電源。解決方法2：執行CMOS清除（EC重設）請嘗試強制關機。長按電源鍵直到電源燈熄滅，即可關閉裝置。執行嵌入式控制器（EC reset）、即時時鐘（RTC）清除，以將裝置中的硬體恢復到預設狀態。您可以參考相關文章以了解如何清除：筆記型電腦/All-in-One PC/電競掌機：如何重設嵌入式控制器(EC reset)、即時時鐘(RTC)、硬重設(Hard reset)桌上型電腦：請問Clear CMOS步驟為何解決方法3：執行BIOS重置BIOS中的開機設定若不正確，可能會導致開機至Windows系統時出現問題。您可以嘗試以下步驟，以將BIOS還原至預設值。將裝置進入BIOS設定畫面。請先將裝置關機。若您的裝置已經卡在Windows畫面中，請 長按電源鍵直到電源燈熄滅，靜置數秒後先按住鍵盤上的[F2]鍵不放，然後按下電源鍵開機，直到BIOS設定畫面出現後即可放開[F2]鍵。瞭解更多如何進入BIOS 設定畫面。註：對於一些較舊型號的桌上型電腦，可能需要在開機時按住「Del」鍵，才能進入BIOS設定畫面。註：電競掌機需要在開機時按住音量減少鍵「-」 ，然後按下電源鍵。進入BIOS設定畫面後，請參考這篇文章：如何還原BIOS設定。解決方法4：修復Windows系統無法進入Windows系統有可能是因為Windows系統 檔案已遺失或毀損。您可以嘗試使用Windows內建的修復工具，以自動檢測、識別並修復這些問題。更多自動修復的說明，您可以參考Microsoft官方文件。手動 將裝置進入Windows修復環境(WinRE)。在裝置未開機時，先按住鍵盤上的F9不放，然後再按一下電源鍵將裝置啟動。註：有些機種可能需透過鍵盤上的F12才可進入Windows修復環境。若是F9無法成功，請使用F12來替換F9的操作以進入Windows修復環境。直到以下Windows修復環境的畫面出現後再將F9/F12放開。註：當系 統啟動失敗兩次時，第三次啟動裝置後，系統將會導引至Windows修復環境。如果透過鍵盤的方式無法進入Windows修復環境，您也可以嘗試以下方法：A. 裝置開機後，按住電源按鈕15秒以強制關閉裝置。B. 再次按電源按鈕以開啟裝置。C. 初次出現ASUS logo在畫面上時，按住電源按鈕15秒以強制關閉裝置。D. 再次按 電源按鈕以開啟裝置。E. 當Windows重新啟動時，按住電源按鈕15秒以強制關閉裝置。F. 再次按電源按鈕以開啟裝置。G. 您的裝置將會完全重新開機並進入Windows修復環境。在選擇選項畫面中，選取[疑難排解]①。在疑難排解畫面中，選取[進階選項]②。在進階選項畫面中，選取[啟動修復]③。依照畫面上的指示進行，Windows 將會嘗試尋找並修正問題。解決方法5：執行系統還原如果問題是最近才開始發生，且如果您先前已經有建立系統還原點、或是系統建立的自動還原點，則可以嘗試將系統還原至問題開始前的時間點來解決問題。註：執行系統還原不會變更您的個人檔案，但可能會移除最近安裝的應用程式與驅動程式。再次透過 手動方式進入Windows修復環境(WinRE)。詳細進入Windows修復環境的步驟請參考解決方法4。進入Windows修復環境後，在選擇選項畫面中選取[疑難排解]①。在 疑難排解畫面中，選取[進階選項]②。在進階選項畫面中，選取[系統還原]③。依照畫面上的指示進行，並選擇問題開始前的還原點來解決問題。瞭解更多如何從 已建立的系統還原點還原系統。解決方法6：執行Windows系統還原如果所有疑難排解步驟已完成，但問題仍然存在，請嘗試重新安裝作業系統，以將系統還原至 原始組態。使用Windows內建的重設功能時，您可以選擇從兩種不同的選項中進行重設：保留我的檔案：這個選項將重新安裝Windows並移除您安裝的應用程式和 所有個人設定，但保留您的個人文件和檔案。移除所有項目：這個選項將在重新安裝Windows之前徹底刪除所有個人檔案、應用程式和設定。再次透過手動方式進入Windows修復環境(WinRE)。詳細進入Windows修復環境的步驟請參考解決方法4。進入Windows修復環境後，在選擇選項畫面中選取[疑難排解]①。在疑難排解畫 面中，選取[重設此電腦]②。選擇您要保留個人檔案或移除所有項目③，然後依照畫面上的指示進行。瞭解更多如何還原(重灌)系統。若您的問題並未解決，請聯 繫華碩客服中心，取得進一步的資訊'}]}]}]}}, 'extract': {'status': 200, 'type': 'answer', 'message': 'RAG Response', 'output': {'answer': '根據您的問題，底下有一些技術文章供您參考 :\n[Windows 11/10] 疑難排解 - 裝置無法進入Windows系統\n本文提供裝置開機時無法正常進入Windows系統的常見解決方法，包括移除外接設備、執行CMOS清除、執行BIOS重置、修復Windows系統、執行系統還原和執行Windows系統還原等。建議依序參考本文的步驟進行問題排 解。', 'ask_flag': False, 'hint_candidates': [], 'kb': {'kb_no': '1051479', 'title': '[Windows 11/10] 疑難排解 - 裝置無法進入Windows系統', 'similarity': 0.816743731499, 'source': 'summary', 'exec_time': 7.9}}}, 'total_time': 36.91, '_rid': 'zPFjAObJuB5TAQAAAAAAAA==', '_self': 'dbs/zPFjAA==/colls/zPFjAObJuB4=/docs/zPFjAObJuB5TAQAAAAAAAA==/', '_etag': '"17001d47-0000-2300-0000-6901ca220000"', '_attachments': 'attachments/', '_ts': 1761724962}, {'id': 'test-f6b3ddd8-6c55-4edc-9cf0-8408664cb89d-c516e816-0ad1-44f1-9046-7878bd78b3bc', 'cus_id': 'test', 'session_id': 'f6b3ddd8-6c55-4edc-9cf0-8408664cb89d', 'chat_id': 'c516e816-0ad1-44f1-9046-7878bd78b3bc', 'createDate': '2025-10-29T08:07:27.758027Z', 'user_input': '我的筆電卡在登入畫面，完全沒有反應。', 'websitecode': 'tw', 'product_line': '', 'system_code': 'rog', 'user_info': {'main_product_category': 'notebook', 'sub_product_category': None}, 'process_info': {'bot_scope': 'notebook', 'search_info': "my laptop is stuck on the login screen and there's no response at all.", 'is_follow_up': True, 'faq_pl': {'faq': [1051479, 1038855, 1046480, 1042613], 'cosineSimilarity': [0.816743731499, 0.751851916313, 0.701354265213, 0.700322508812], 'productLine': ['chromebook,desktop,gaming_handhelds,motherboard,notebook', 'chromebook,desktop,gaming_handhelds,notebook,nuc', 'chromebook,desktop,gaming_handhelds,motherboard,notebook,nuc', 'chromebook,desktop,gaming_handhelds,notebook']}, 'faq_wo_pl': {'faq': [1051479, 1038855, 1046480, 1042613], 'cosineSimilarity': [0.816743731499, 0.751851916313, 0.701354265213, 0.700322508812], 'productLine': ['chromebook,desktop,gaming_handhelds,motherboard,notebook', 'chromebook,desktop,gaming_handhelds,notebook,nuc', 'chromebook,desktop,gaming_handhelds,motherboard,notebook,nuc', 'chromebook,desktop,gaming_handhelds,notebook']}, 'language': 'zh-tw', 'last_info': {'prev_q': '我的筆電卡在登入畫面，完全沒有反應。', 'prev_a': '根據您的問題，底下有一些技術文章供您參考 :\n[Windows 11/10] 疑難排解 - 裝置無法進入Windows系統\n本文提供裝置開機時無法正常進入Windows系統的常見解決方法，包括移除外接設備、執行CMOS清除、執行BIOS重置、修復Windows系統、執行系統還原和執行Windows系統還原等。建議依序參考本文的步驟進行問題排解。', 'kb_no': '1051479'}}, 'final_result': {'status': 200, 'message': 'OK', 'result': {'renderTime': 1761725247, 'render': [{'renderId': 'bd562d3e-1e03-469e-8654-25a06d55f528', 'stream': False, 'type': 'avatarTechnicalSupport', 'message': '喔不，筆電卡在登入畫面，動不了，這真的蠻讓人心煩的！別急，你看，畫面上有篇相關的教學文可 以幫到你喔。如果看了還是搞不定，沒關係，直接找店員問問，他們都很專業。別擔心，我們都會幫忙的啦！', 'remark': [], 'option': [{'type': 'faqcards', 'cards': [{'link': 'https://rog.asus.com/tw/support/FAQ/1051479', 'title': '[Windows 11/10] 疑難排解 - 裝置無法進入Windows系統', 'content': '適用產品：筆記型電腦、桌上型電腦、All-in-One PC、電競掌機、主機板、顯示卡這篇文章提供裝置開機時無法正常進入Windows系統的常見解決方法。您 可能遇到的問題現象是，裝置開機並出現ASUS或ROG標誌畫面後，停駐在Window歡迎畫面，而無法登入Windows系統。請依序參考本文的步驟進行問題排解。註： 如果您的裝置無法開機，請參考這篇文章：疑難排解 - 電腦無法開機，或開機後螢幕沒有畫面（黑畫面）。註：如果您的裝置開機時停駐在ASUS或ROG標誌畫面 ，請參考這篇文章：疑難排解 - 開機時卡在ASUS/ROG標誌畫面。註：如果您的裝置開機時出現自動修復的藍色或黑色畫面，請參考這篇文章：疑難排解 - 開機 時出現自動修復。註：如果您的裝置開機時出現UEFI/BIOS/Aptio Setup Utility畫面，請參考這篇文章：疑難排解 - 如何解決開機直接進入BIOS/Aptio Setup Utility畫面。解決方法1：移除外接設備並重新開機關閉裝置電源。長按電源鍵直到電源燈熄滅，即可關閉裝置。請移除所有外接設備，包含鍵盤、滑鼠、外接 硬碟、印表機、記憶卡、光碟機內的光碟片、也包含讀卡機內的轉接卡等等。有時候可能是因為外接設備導致您的裝置無法正常進入Windows系統。註：同時移除所有外接顯示器。若是桌上型電腦，則先連接一部外接顯示器以確認電腦能正常開機並顯示畫面。開啟裝置電源。解決方法2：執行CMOS清除（EC重設）請嘗試強制關機。長按電源鍵直到電源燈熄滅，即可關閉裝置。執行嵌入式控制器（EC reset）、即時時鐘（RTC）清除，以將裝置中的硬體恢復到預設狀態。您可以參考相關文章以了解如何清除：筆記型電腦/All-in-One PC/電競掌機：如何重設嵌入式控制器(EC reset)、即時時鐘(RTC)、硬重設(Hard reset)桌上型電腦：請問Clear CMOS步驟為何解決方法3：執行BIOS重置BIOS中的開機設定若不正確，可能會導致開機至Windows系統時出現問題。您可以嘗試以下步驟，以將BIOS還原至預設值。將裝置進入BIOS設定畫面。請先將裝置關機。若您的裝置已經卡在Windows畫面中，請長按電源鍵直到電源燈熄滅，靜置數秒後先按住鍵盤上的[F2]鍵不放，然後按下電源鍵開機，直到BIOS設定畫面出現後即可放開[F2]鍵。瞭解更多如何進入BIOS設定畫面。註：對於一些較舊型號的桌上型電腦，可能需要在開機時 按住「Del」鍵，才能進入BIOS設定畫面。註：電競掌機需要在開機時按住音量減少鍵「-」，然後按下電源鍵。進入BIOS設定畫面後，請參考這篇文章：如何還 原BIOS設定。解決方法4：修復Windows系統無法進入Windows系統有可能是因為Windows系統檔案已遺失或毀損。您可以嘗試使用Windows內建的修復工具，以自動檢測、識別並修復這些問題。更多自動修復的說明，您可以參考Microsoft官方文件。手動將裝置進入Windows修復環境(WinRE)。在裝置未開機時，先按住鍵盤上的F9不放，然後再按一下電源鍵將裝置啟動。註：有些機種可能需透過鍵盤上的F12才可進入Windows修復環境。若是F9無法成功，請使用F12來替換F9的操作以進入Windows修復環境。直到以下Windows修復環境的畫面出現後再將F9/F12放開。註：當系統啟動失敗兩次時，第三次啟動裝置後，系統將會導引至Windows修復環境。如果透過鍵盤的方式無法進入Windows修復環境，您也可以嘗試以下方法：A. 裝置開機後，按住電源按鈕15秒以強制關閉裝置。B. 再次按電源按鈕以開啟裝置。C. 初次出現ASUS logo在畫面上時，按住電源按鈕15秒以強制關閉裝置。D. 再次按電源按鈕以開啟裝置。E. 當Windows重新啟動時，按住電源按鈕15秒以強制關閉裝置。F. 再次按電源按鈕以開啟裝置。G. 您的裝置將會完全重新開機並進入Windows修復環境。在選擇選項畫面中，選取[疑難排解]①。在疑難排解畫面 中，選取[進階選項]②。在進階選項畫面中，選取[啟動修復]③。依照畫面上的指示進行，Windows 將會嘗試尋找並修正問題。解決方法5：執行系統還原如果問題是最近才開始發生，且如果您先前已經有建立系統還原點、或是系統建立的自動還原點，則可以嘗試將系統還原至問題開始前的時間點來解決問題。註：執行系 統還原不會變更您的個人檔案，但可能會移除最近安裝的應用程式與驅動程式。再次透過手動方式進入Windows修復環境(WinRE)。詳細進入Windows修復環境的步驟請參考解決方法4。進入Windows修復環境後，在選擇選項畫面中選取[疑難排解]①。在疑難排解畫面中，選取[進階選項]②。在進階選項畫面中，選取[系統還原]③。依照畫面上的指示進行，並選擇問題開始前的還原點來解決問題。瞭解更多如何從已建立的系統還原點還原系統。解決方法6：執行Windows系統還原如果所 有疑難排解步驟已完成，但問題仍然存在，請嘗試重新安裝作業系統，以將系統還原至原始組態。使用Windows內建的重設功能時，您可以選擇從兩種不同的選項中進行重設：保留我的檔案：這個選項將重新安裝Windows並移除您安裝的應用程式和所有個人設定，但保留您的個人文件和檔案。移除所有項目：這個選項將在重新安裝Windows之前徹底刪除所有個人檔案、應用程式和設定。再次透過手動方式進入Windows修復環境(WinRE)。詳細進入Windows修復環境的步驟請參考解決 方法4。進入Windows修復環境後，在選擇選項畫面中選取[疑難排解]①。在疑難排解畫面中，選取[重設此電腦]②。選擇您要保留個人檔案或移除所有項目③，然後依照畫面上的指示進行。瞭解更多如何還原(重灌)系統。若您的問題並未解決，請聯繫華碩客服中心，取得進一步的資訊'}]}]}]}}, 'extract': {'status': 200, 'type': 'answer', 'message': 'RAG Response', 'output': {'answer': '根據您的問題，底下有一些技術文章供您參考 :\n[Windows 11/10] 疑難排解 - 裝置無法進入Windows系統\n本文提供裝置開機時無法正常進入Windows系統的常見解決方法，包括移除外接設備、執行CMOS清除、執行BIOS重置、修復Windows系統、執行系統還原和執行Windows系統還原等。建議依序參考本文的步驟進行問題排解。', 'ask_flag': False, 'hint_candidates': [], 'kb': {'kb_no': '1051479', 'title': '[Windows 11/10] 疑難排解 - 裝置無法進入Windows系統', 'similarity': 0.816743731499, 'source': 'summary', 'exec_time': 19.6}}}, 'total_time': 98.12, '_rid': 'zPFjAObJuB5UAQAAAAAAAA==', '_self': 'dbs/zPFjAA==/colls/zPFjAObJuB4=/docs/zPFjAObJuB5UAQAAAAAAAA==/', '_etag': '"17002c4b-0000-2300-0000-6901cb3f0000"', '_attachments': 'attachments/', '_ts': 1761725247}, {'id': 'GINA_TEST-f6b3ddd8-6c55-4edc-9cf0-8408664cb89d-c516e816-0ad1-44f1-9046-7878bd78b3bc', 'cus_id': 'GINA_TEST', 'session_id': 'f6b3ddd8-6c55-4edc-9cf0-8408664cb89d', 'chat_id': 'c516e816-0ad1-44f1-9046-7878bd78b3bc', 'createDate': '2025-10-30T09:30:39.906320Z', 'user_input': '我的筆電卡在登入畫面，完全沒有反應。', 'websitecode': 'tw', 'product_line': '', 'system_code': 'rog', 'user_info': {'main_product_category': 'notebook', 'sub_product_category': None}, 'process_info': {'bot_scope': 'notebook', 'search_info': "my laptop is stuck on the login screen and there's no response at all.", 'is_follow_up': False, 'faq_pl': {'faq': [1051479, 1038855, 1046480, 1042613], 'cosineSimilarity': [0.816743731499, 0.751851916313, 0.701354265213, 0.700322508812], 'productLine': ['chromebook,desktop,gaming_handhelds,motherboard,notebook', 'chromebook,desktop,gaming_handhelds,notebook,nuc', 'chromebook,desktop,gaming_handhelds,motherboard,notebook,nuc', 'chromebook,desktop,gaming_handhelds,notebook']}, 'faq_wo_pl': {'faq': [1051479, 1038855, 1046480, 1042613], 'cosineSimilarity': [0.816743731499, 0.751851916313, 0.701354265213, 0.700322508812], 'productLine': ['chromebook,desktop,gaming_handhelds,motherboard,notebook', 'chromebook,desktop,gaming_handhelds,notebook,nuc', 'chromebook,desktop,gaming_handhelds,motherboard,notebook,nuc', 'chromebook,desktop,gaming_handhelds,notebook']}, 'language': 'zh-tw', 'last_info': {'prev_q': '我的筆電卡在登入 畫面，完全沒有反應。', 'prev_a': '', 'kb_no': '1051479'}}, 'final_result': {'status': 200, 'message': 'OK', 'result': [{'renderId': '5c72c8bd-2432-44d4-9921-2247324a32b8', 'stream': False, 'type': 'avatarText', 'message': '喔，筆電卡在登入畫面喔，這真的有點麻煩耶。嗯...', 'remark': [], 'option': []}, {'renderId': '5c72c8bd-2432-44d4-9921-2247324a32b8', 'stream': False, 'type': 'avatarAsk', 'message': '你可以告訴我像是產品全名、型號，或你想問的活動名稱～比如「ROG Flow X16」或「我想查產品保固到期日」。給我多一點線索，我就能更快幫你找到對的資料，也不會漏掉重點 ！', 'remark': [], 'option': [{'name': '我想知道 ROG FLOW X16 的規格', 'value': '我想知道 ROG FLOW X16 的規格', 'answer': [{'type': 'inquireMode', 'value': 'intent'}, {'type': 'inquireKey', 'value': 'specification-consultation'}, {'type': 'mainProduct', 'value': 25323}]}, {'name': '請幫我推薦16吋筆電', 'value': '請幫我推薦16吋筆電', 'answer': [{'type': 'inquireMode', 'value': 'intent'}, {'type': 'inquireKey', 'value': 'purchasing-recommendation-of-asus-products'}]}, {'name': '請幫我介紹 ROG Phone 8 的特色', 'value': '請幫我介紹 ROG Phone 8 的特色', 'answer': [{'type': 'inquireMode', 'value': 'intent'}, {'type': 'inquireKey', 'value': 'specification-consultation'}, {'type': 'mainProduct', 'value': 25323}]}]}]}, 'extract': {'status': 200, 'type': 'handoff', 'message': '相似度低，建議轉人工', 'output': {'answer': '', 'ask_flag': False, 'hint_candidates': [], 'kb': {'kb_no': '1051479', 'title': '', 'similarity': 0.816743731499, 'source': '', 'exec_time': 0}}}, 'total_time': 13.57, '_rid': 'zPFjAObJuB5dAQAAAAAAAA==', '_self': 'dbs/zPFjAA==/colls/zPFjAObJuB4=/docs/zPFjAObJuB5dAQAAAAAAAA==/', '_etag': '"1b00d3a6-0000-2300-0000-690330400000"', '_attachments': 'attachments/', '_ts': 1761816640}]

        # contanier from chat log db
        # async for item in self.async_container.query_items(
        #     query=query
        # ):
        #     results.append(item)

        chat_count = len(results)
        if len(results) > 0:
            # results =  sorted(results, key=lambda x: x['chat_create_date'])
            user_info = results[-1].get("user_info")
            last_bot_scope = results[-1].get("process_info").get("bot_scope")
            # last_intent = results[-1].get("extract").get("type2")
            # last_product_name = user_info.get("product_name")
            last_merge_user_input = results[-1].get("process_info").get("merge_user_input")
            # last_ask_flag = results[-1].get("extract").get("ask_flag")
            last_extract_output = results[-1].get("extract").get("output")

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
        # async for item in self.async_hint_container.query_items(
        #     query=query
        # ):
        #     results.append(item)
        # if results:
        #     return results[0]
        # else:
        #     return None
        print("get_latest_hint is disabled for testing. gina")
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
        # print(result)
        # await self.async_hint_container.upsert_item(data)
        print("hint_container.upsert_item success")

    # @async_timer.timeit
    async def insert_data(self, data: dict):
        """sent to CosmosDB"""
        try:
            # result = await self.async_container.upsert_item(data)  # 確認這段有跑
            print("✅ container.upsert_item 成功")
            result = 'success'
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

        # self.productid_container.upsert_item(data)
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
            # await self.async_recommendation_container.upsert_item(data)
            print("recommendation_container.upsert_item success")
        else:
            print("no products")


    def get_language_by_websitecode(self, websitecode: str) -> Optional[str]:
        query = f"SELECT c.lang FROM c WHERE c.websitecode = '{websitecode}'"
        # df = self.query_cosmos("FAQ_LanguageMapping_ForOpenAI", query) # gina 確認有跑
        # return df.iloc[0]["lang"] if not df.empty else None
        return "zh-tw"

    def get_kb_article(self,lang: str, kb_no: int) -> Optional[dict]:
        query = f"SELECT * FROM c WHERE c.lang = '{lang}' AND c.kb_no = {kb_no}"
        # df = self.query_cosmos("ApChatbotKnowledge", query)
        # return df.iloc[0].to_dict() if not df.empty else None
        print("get_kb_article is disabled for testing. gina")

    async def get_language_by_websitecode_dev(self, websitecode: str) -> Optional[str]:
        query = f"SELECT c.lang FROM c WHERE c.websitecode = '{websitecode}'"
        # df = self.query_cosmos("FAQ_LanguageMapping_ForOpenAI", query) # gina 確認有跑
        # return df.iloc[0]["lang"] if not df.empty else None
        return "zh-tw"

    async def get_kb_article_dev(self,lang: str, kb_no: int) -> Optional[dict]:
        query = f"SELECT * FROM c WHERE c.lang = '{lang}' AND c.kb_no = {kb_no}"
        # df = self.query_cosmos("ApChatbotKnowledge", query)
        # return df.iloc[0].to_dict() if not df.empty else None
        print("get_kb_article_dev is disabled for testing. gina")

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
        # try:
        #     query = f"SELECT TOP {limit} * FROM c order by c._ts desc"
        #     df = self.query_cosmos_AIA("chatfaq", query)
            
        #     if not df.empty:
        #         print(f"✅ 成功從 chatfaq 取得資料，共 {len(df)} 筆")
        #         return df
        #     else:
        #         print("❌ 沒有找到符合條件的 chatfaq 資料")
        #         return pd.DataFrame()
                
        # except Exception as e:
        #     print(f"❌ 查詢 chatfaq 資料失敗: {e}")
        #     return pd.DataFrame()
        print("get_chatfaq is disabled for testing. gina")

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
        # try:
        #     print("🔍 第一步：查詢符合條件的不重複 session_id...")
            
        #     # 第一步：找出所有符合條件的不重複 session_id
        #     # 移除 ORDER BY 避免複合索引問題
        #     if limit:
        #         session_query = f"""
        #             SELECT DISTINCT TOP {limit} *
        #             FROM c 
        #             WHERE c.site = 'tw' 
        #             AND c.extract.ask_flag = true 
        #             AND c.cus_id != '' 
        #             AND NOT CONTAINS(LOWER(c.session_id), 'test')
        #             AND c.extract.type2 like "%technical-support%"
        #             order by c._ts desc
        #         """
        #     else:
        #         session_query = """
        #             SELECT DISTINCT * 
        #             FROM c 
        #             WHERE c.site = 'tw' 
        #             AND c.extract.ask_flag = true 
        #             AND c.cus_id != '' 
        #             AND NOT CONTAINS(LOWER(c.session_id), 'test')
        #             AND c.extract.type2 like "%technical-support%"
        #             order by c._ts desc
        #         """
            
        #     reask_df = self.query_cosmos_AIA("chatfaq", session_query)

        #     if reask_df.empty:
        #         print("❌ 沒有找到符合條件的 session_id")
        #         return pd.DataFrame()

        #     return reask_df
        
        # except Exception as e:
        #     print(f"❌ 查詢所有 session 資料失敗: {e}")
        #     return pd.DataFrame()
        print("get_chatfaq_reask is disabled for testing. gina")

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
        # try:
        #     print("🔍 第一步：查詢符合條件的不重複 session_id...")
            
        #     # 第一步：找出所有符合條件的不重複 session_id
        #     # 移除 ORDER BY 避免複合索引問題
        #     if limit:
        #         session_query = f"""
        #             SELECT DISTINCT TOP {limit} *
        #             FROM c 
        #             WHERE c.site = 'tw'
        #             AND c.extract.ask_flag = false
        #             AND c.cus_id != ''
        #             AND NOT CONTAINS(LOWER(c.session_id), 'test')
        #             AND c.extract.type2 like "%technical-support%"
        #             AND c.extract.intent_support.response_info.response_source = "immed_rag"
        #             AND c.user_input = c.extract.merge_user_input
        #             order by c._ts desc
        #         """
        #     else:
        #         session_query = """
        #             SELECT DISTINCT *
        #             FROM c 
        #             WHERE c.site = 'tw' 
        #             AND c.extract.ask_flag = false 
        #             AND c.cus_id != '' 
        #             AND NOT CONTAINS(LOWER(c.session_id), 'test')
        #             AND c.extract.type2 like "%technical-support%"
        #             AND c.extract.intent_support.response_info.response_source = "immed_rag"
        #             AND c.user_input = c.extract.merge_user_input
        #             order by c._ts desc
        #         """
            
        #     immedrag_df = self.query_cosmos_AIA("chatfaq", session_query)

        #     if immedrag_df.empty:
        #         print("❌ 沒有找到符合條件的資料")
        #         return pd.DataFrame()
            
        #     return immedrag_df
                
        # except Exception as e:
        #     print(f"❌ 查詢所有 session 資料失敗: {e}")
        #     return pd.DataFrame()
        print("get_chatfaq_all_immed_rag is disabled for testing. gina")


