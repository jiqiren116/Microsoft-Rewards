import json
import logging
import random
import time
from datetime import date, timedelta

import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from src.browser import Browser

LOG_TAG = "[CMY]"
PAUSE_TIME = 10  # 每隔5次搜索的暂停时间，单位为 分钟

class Searches:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def getRelatedTerms(self, word: str) -> list:
        try:
            r = requests.get(
                f"https://api.bing.com/osjson.aspx?query={word}",
                headers={"User-agent": self.browser.userAgent},
            )
            return r.json()[1]
        except Exception:  # pylint: disable=broad-except
            return []

    def getHotSearch(self):
        # 默认搜索词，热门搜索词请求失败时使用
        default_search_words = ["盛年不重来，一日难再晨", "千里之行，始于足下", "少年易学老难成，一寸光阴不可轻", "敏而好学，不耻下问", "海内存知已，天涯若比邻", "三人行，必有我师焉",
            "莫愁前路无知已，天下谁人不识君", "人生贵相知，何用金与钱", "天生我材必有用", "海纳百川有容乃大；壁立千仞无欲则刚", "穷则独善其身，达则兼济天下", "读书破万卷，下笔如有神",
            "学而不思则罔，思而不学则殆", "一年之计在于春，一日之计在于晨", "莫等闲，白了少年头，空悲切", "少壮不努力，老大徒伤悲", "一寸光阴一寸金，寸金难买寸光阴", "近朱者赤，近墨者黑",
            "吾生也有涯，而知也无涯", "纸上得来终觉浅，绝知此事要躬行", "学无止境", "己所不欲，勿施于人", "天将降大任于斯人也", "鞠躬尽瘁，死而后已", "书到用时方恨少", "天下兴亡，匹夫有责",
            "人无远虑，必有近忧", "为中华之崛起而读书", "一日无书，百事荒废", "岂能尽如人意，但求无愧我心", "人生自古谁无死，留取丹心照汗青", "吾生也有涯，而知也无涯", "生于忧患，死于安乐",
            "言必信，行必果", "读书破万卷，下笔如有神", "夫君子之行，静以修身，俭以养德", "老骥伏枥，志在千里", "一日不读书，胸臆无佳想", "王侯将相宁有种乎", "淡泊以明志。宁静而致远,", "卧龙跃马终黄土"]
        Hot_words_apis = "https://api.gmya.net/Api/" # 故梦热门词API接口网站
        keywords_source = ['BaiduHot', 'TouTiaoHot', 'DouYinHot', 'WeiBoHot']
        # 打乱keywords_source列表的顺序
        random.shuffle(keywords_source)
        current_source_index = 0; # 当前搜索词来源的索引
    
        while current_source_index < len(keywords_source): # 循环遍历所有搜索词来源
            source = keywords_source[current_source_index] # 获取当前搜索词来源
            url = Hot_words_apis + source # 构造请求URL
            response = requests.get(url, timeout=10) # 发送GET请求
            if response.status_code == 200: # 如果请求成功
                data = response.json() # 解析JSON数据
                if data['code'] == 200: # 如果数据获取成功
                    # 获取data中所有的title值，并存入一个列表中
                    search_words = [item['title'] for item in data['data']]
                    # 随机打乱列表顺序
                    random.shuffle(search_words)
                    logging.info(f"{LOG_TAG} 获取热门搜索词成功！")
                    return search_words # 返回搜索词列表
            else: # 如果请求失败
                current_source_index += 1 # 切换到下一个搜索词来源
                continue # 跳过当前循环，继续下一次循环
        
        # 如果所有搜索词来源都失败，则返回默认搜索词
        logging.info(f"{LOG_TAG} 获取热门搜索词失败，使用默认搜索词！")
        return default_search_words

    def bingSearches(self, numberOfSearches: int, pointsCounter: int = 0):
        logging.info(
            "[BING] "
            + f"Starting {self.browser.browserType.capitalize()} Edge Bing searches... "
            + f"剩余搜索次数为: {numberOfSearches}"
        )

        temp_numberOfSearches = numberOfSearches  # 临时变量，用于记录剩余搜索次数，方便循环时退出

        search_terms = self.getHotSearch()
        # 统计search_terms中的元素个数，然后跟numberOfSearches作比较，打印log
        logging.info(f"[BING] 获取到的搜索词个数为：{len(search_terms)}, 需要搜索的个数为：{numberOfSearches}")

        if len(search_terms) < numberOfSearches:
            logging.info(f"[BING] 获取到的搜索词个数小于需要搜索的个数，不满足需求!!!!!!!!!!!!!!!!!!!!!!!!")
            # 如果不够就再加上一段
            search_terms += self.getHotSearch()

        else:
            logging.info(f"[BING] 获取到的搜索词个数大于等于需要搜索的个数，满足需求")

        i = 0
        for word in search_terms:
            # 如果剩余搜索次数小于等于0，退出循环
            if temp_numberOfSearches <= 0:
                logging.info(f"[BING] 剩余搜索次数为0，退出循环")
                break

            i += 1
            # 每隔4次搜索暂停10分钟
            if i % 4 == 0:
                logging.info(f"[BING] 已搜索 {i} 次，暂停 {PAUSE_TIME} 分钟...")
                time.sleep(PAUSE_TIME * 60)

            logging.info("[BING] " + f"{i}/{numberOfSearches}, 搜索词：{word}")
            points = self.bingSearch(word)
            logging.info(f"[BING] 搜索前的积分：{pointsCounter}, 搜索后的积分：{points}")
            if points <= pointsCounter:
                relatedTerms = self.getRelatedTerms(word)
                logging.info(f"[BING] 搜索词：{word} 搜索失败，尝试获取相关搜索词, 相关搜索词为：{relatedTerms}")
                for term in relatedTerms:
                    points = self.bingSearch(term)
                    time.sleep(3 * 60)
                    if not points <= pointsCounter:
                        logging.info(f"[BING] 相关搜索词：{term} 搜索成功，搜索前的积分：{pointsCounter}，搜索后的积分：{points}")
                        temp_numberOfSearches -= 1  # 减少剩余搜索次数
                        break
                    else:
                        logging.info(f"[BING] 相关搜索词：{term} 搜索失败")
            else:
                temp_numberOfSearches -= 1  # 减少剩余搜索次数
                logging.info(f"[BING] 搜索词：{word} 搜索成功，不需要获取相关搜索词")
            if points > 0:
                pointsCounter = points
            else:
                break
        logging.info(
            f"[BING] Finished {self.browser.browserType.capitalize()} Edge Bing searches !"
        )
        return pointsCounter

    def bingSearch(self, word: str):
        while True:
            try:
                self.webdriver.get("https://bing.com")
                self.browser.utils.waitUntilClickable(By.ID, "sb_form_q")
                searchbar = self.webdriver.find_element(By.ID, "sb_form_q")
                searchbar.send_keys(word)
                searchbar.submit()
                time.sleep(random.randint(18, 30))  # 随机等待18-30秒
                return self.browser.utils.getBingAccountPoints()
            except TimeoutException:
                logging.error("[BING] " + "Timeout, retrying in 5 seconds...")
                time.sleep(5)
                continue
