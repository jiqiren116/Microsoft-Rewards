import json
import logging
import random
import time
from datetime import date, timedelta

import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.browser import Browser

LOG_TAG = "[CMY]"
PAUSE_TIME = 10  # 每隔5次搜索的暂停时间，单位为 分钟
INTERVAL_NUMBER = 4  # 每隔多少次搜索暂停一次

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


            "吾生也有涯，而知无涯", "纸上得来终觉浅，绝知此事要躬行", "学无止境", "己所不欲，勿施于人", "天将降大任于斯人也", "鞠躬尽瘁，死 afterwards.", "书到用时方恨少", "天下兴亡，匹夫有责",
            "人无远慮，必有近憂", "为中华之崛起而读书", "一日无书，百事荒废", "岂能尽如人意，但求无愧我心", "人生自古谁无死，留取丹心照汗青", "吾生也有涯，而知无涯", "生于忧患，死于安乐",
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
        
        # 如果所有搜索词来源都失败，则返回默认搜索词
        logging.info(f"{LOG_TAG} 获取热门搜索词失败，使用默认搜索词！")
        return default_search_words

    def bingSearches(self, currentAccount: str, numberOfSearches: int, pointsCounter: int = 0):
        DesktopOrMobile = self.browser.browserType.capitalize()
        logging.info(
            "[BING] "
            + f"===== Starting [{currentAccount}] [{DesktopOrMobile}] Edge Bing searches... "
            + f"剩余搜索次数为: {numberOfSearches} ====="
        )

        search_terms = self.getHotSearch()

        if len(search_terms) < numberOfSearches:
            logging.info(f"[BING][{DesktopOrMobile}]获取到的搜索词个数小于需要搜索的个数，不满足需求!!!!!!!!!!!!!!!!!!!!!!!!")
            # 如果不够就再加上一段
            search_terms += self.getHotSearch()
        else:
            logging.info(f"[BING][{DesktopOrMobile}]获取到的搜索词个数为:{len(search_terms)},大于等于需要搜索的个数:{numberOfSearches}，满足需求")

        i = 0
        while True:
            # 每隔4次搜索暂停10分钟
            if i != 0 and i % INTERVAL_NUMBER == 0:
                (
                    remainingSearches,
                    remainingSearchesM,
                ) = self.browser.utils.getRemainingSearches() 

                if (DesktopOrMobile == 'Mobile' and remainingSearchesM == 0) or (DesktopOrMobile == 'Desktop' and remainingSearches == 0):
                    logging.info(
                        f"[BING] [{currentAccount}] [{DesktopOrMobile}] 中，剩余搜索已完成，总积分为:{pointsCounter}"
                    )
                    break
                if DesktopOrMobile == 'Mobile':
                    logging.info(
                        f"[BING] [{DesktopOrMobile}]中，剩余搜索次数为:{remainingSearchesM}"
                    )
                else:
                    logging.info(
                        f"[BING] [{DesktopOrMobile}]中，剩余搜索次数为:{remainingSearches}"
                    )
                logging.info(
                    f"[BING][{DesktopOrMobile}] 暂停{PAUSE_TIME}分钟"
                )
                time.sleep(PAUSE_TIME * 60)
            
            # 如果search_terms列表为空，则重新获取
            if not search_terms:
                logging.info(f"[BING][{DesktopOrMobile}] search_terms列表为空，重新获取")
                search_terms = self.getHotSearch()
                time.sleep(5) # 避免请求过快，导致请求失败
            search_word = search_terms.pop(0)  # 从列表中取出第一个元素作为搜索词
            points = self.bingSearch(search_word)
            time.sleep(random.randint(15, 30))  # 随机等待20-30秒

            i += 1
            # 正确更新总积分
            if points > pointsCounter:
                logging.info(f"[BING][{DesktopOrMobile}] 第{i}次搜索 SUCCESS，搜索词:[{search_word}] \n搜索词:[{search_word}] 搜索前积分:{pointsCounter}, 搜索后积分:{points}\n")
                pointsCounter = points
            else:
                logging.info(f"[BING][{DesktopOrMobile}] 第{i}次搜索 FAIL，搜索词:[{search_word}] \n")

        logging.info(
            f"[BING] ===== Finished [{currentAccount}] [{DesktopOrMobile}] Edge Bing searches ! ====="
        )
        return pointsCounter

    def bingSearch(self, word: str):
        max_retries = 3  # 设置最大重试次数
        retries = 0
        while retries < max_retries:
            try:
                self.webdriver.get("https://bing.com")
                # 等待搜索框元素可见
                searchbar = WebDriverWait(self.webdriver, 40).until(
                    EC.visibility_of_element_located((By.ID, "sb_form_q"))
                )
                searchbar.send_keys(word)
                time.sleep(random.randint(3, 5))
                searchbar.submit()
                time.sleep(random.randint(15, 30))  
                return self.browser.utils.getBingAccountPoints()
            except TimeoutException:
                retries += 1
                logging.error(f"[BING] Timeout, retrying {retries}/{max_retries} in 5 seconds...")
                time.sleep(5)
            except Exception as e:  # 捕获其他异常
                retries += 1
                logging.error(f"[BING] An unexpected error occurred: {str(e)}, retrying {retries}/{max_retries} in 5 seconds...")
                time.sleep(5)
        logging.error(f"[BING] Failed after {max_retries} retries.")
        return 0  # 重试失败后返回 0