import contextlib
import json
import locale as pylocale
import time
import urllib.parse
from pathlib import Path

import requests
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import WebDriverException

from .constants import BASE_URL

import logging

LOG_TAG = "[CMY]"


class Utils:
    def __init__(self, webdriver: WebDriver):
        self.webdriver = webdriver
        with contextlib.suppress(Exception):
            locale = pylocale.getdefaultlocale()[0]
            pylocale.setlocale(pylocale.LC_NUMERIC, locale)

    def waitUntilVisible(self, by: str, selector: str, timeToWait: float = 10):
        WebDriverWait(self.webdriver, timeToWait).until(
            ec.visibility_of_element_located((by, selector))
        )

    def waitUntilClickable(
        self, by: str, selector: str, timeToWait: float = 10
    ) -> WebElement:
        return WebDriverWait(self.webdriver, timeToWait).until(
            ec.element_to_be_clickable((by, selector))
        )
    
    def waitForMSRewardElement(self, by: str, selector: str):
        loadingTimeAllowed = 5
        refreshsAllowed = 5

        checkingInterval = 0.5
        checks = loadingTimeAllowed / checkingInterval

        tries = 0
        refreshCount = 0
        while True:
            try:
                self.webdriver.find_element(by, selector)
                return True
            except Exception:  # pylint: disable=broad-except
                if tries < checks:
                    tries += 1
                    time.sleep(checkingInterval)
                elif refreshCount < refreshsAllowed:
                    self.webdriver.refresh()
                    refreshCount += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False

    def waitUntilQuestionRefresh(self):
        return self.waitForMSRewardElement(By.CLASS_NAME, "rqECredits")

    def waitUntilQuizLoads(self):
        return self.waitForMSRewardElement(By.XPATH, '//*[@id="rqStartQuiz"]')

    def resetTabs(self):
        try:
            curr = self.webdriver.current_window_handle

            for handle in self.webdriver.window_handles:
                if handle != curr:
                    self.webdriver.switch_to.window(handle)
                    time.sleep(0.5)
                    self.webdriver.close()
                    time.sleep(0.5)

            self.webdriver.switch_to.window(curr)
            time.sleep(0.5)
            self.goHome()
        except Exception:  # pylint: disable=broad-except
            self.goHome()

    def goHome(self):
        reloadThreshold = 5
        reloadInterval = 10
        targetUrl = urllib.parse.urlparse(BASE_URL)
        try:
            self.webdriver.get(BASE_URL)
        except WebDriverException as e:
            logging.exception(f"WebDriver异常: 无法导航到主页 {BASE_URL}: {e}")
            self.webdriver.refresh()
            time.sleep(10)
        except Exception as e:
            logging.exception(f"未知异常: 无法导航到主页 {BASE_URL}: {e}")
            self.webdriver.refresh()
            time.sleep(10)
        reloads = 0
        interval = 15
        intervalCount = 0

        while True:
            self.tryDismissCookieBanner()
            try:
                # 使用 WebDriverWait 等待元素出现，设置超时时间为 5 秒
                WebDriverWait(self.webdriver, 15).until(
                    ec.presence_of_element_located((By.ID, "reward_header_rewards"))
                )
                break
            except Exception as e:
                # 输出详细的错误信息
                logging.warning(f"Element 'reward_header_rewards' not found: {e}")

            currentUrl = urllib.parse.urlparse(self.webdriver.current_url)
            if (
                currentUrl.hostname != targetUrl.hostname
            ) and self.tryDismissAllMessages():
                logging.info("Current URL doesn't match target URL. Navigating back to home.")
                time.sleep(10)
                try:
                    self.webdriver.get(BASE_URL)
                except WebDriverException as e:
                    logging.exception(f"WebDriver异常: 无法导航到主页: {e}")
                    self.webdriver.refresh()
                    time.sleep(10)
                except Exception as e:
                    logging.exception(f"未知异常: 无法导航到主页: {e}")
                    self.webdriver.refresh()
                    time.sleep(10)

            time.sleep(interval)
            intervalCount += 1
            if intervalCount >= reloadInterval:
                intervalCount = 0
                reloads += 1
                logging.info(f"Refreshing page. Reload count: {reloads}")
                self.webdriver.refresh()
                if reloads >= reloadThreshold:
                    logging.info("Reached reload threshold. Exiting goHome loop.")
                    break

    def getAnswerCode(self, key: str, string: str) -> str:
        t = sum(ord(string[i]) for i in range(len(string)))
        t += int(key[-2:], 16)
        return str(t)

    def getDashboardData(self) -> dict:
        # 在获取dashboard时必须确保页面已经在rewards界面，否则会报错。在执行每日活动时是正常的，但是在搜索时是不在reward界面，因此改为每次获取dashboard时都先跳转到reward界面
        self.goHome()
        # 等到8s
        time.sleep(8)
        return self.webdriver.execute_script("return dashboard")

    def getBingInfo(self):
        cookieJar = self.webdriver.get_cookies()
        cookies = {cookie["name"]: cookie["value"] for cookie in cookieJar}
        tries = 0
        maxTries = 5
        while tries < maxTries:
            with contextlib.suppress(Exception):
                response = requests.get(
                    "https://cn.bing.com/rewards/panelflyout/getuserinfo",
                    cookies=cookies,
                )
                if response.status_code == requests.codes.ok:
                    data = response.json()
                    return data
                else:
                    pass
            tries += 1
            time.sleep(1)
        logging.info(f"{LOG_TAG} Failed to get Bing info!")
        return None

    def checkBingLogin(self):
        data = self.getBingInfo()
        if data:
            return data["userInfo"]["isRewardsUser"]
        else:
            return False

    def getAccountPoints(self) -> int:
        return self.getDashboardData()["userStatus"]["availablePoints"]

    def getBingAccountPoints(self) -> int:
        data = self.getBingInfo()
        if data:
            return data["userInfo"]["balance"]
        else:
            return 0

    def tryDismissAllMessages(self):
        buttons = [
            (By.ID, "iLandingViewAction"),
            (By.ID, "iShowSkip"),
            (By.ID, "iNext"),
            (By.ID, "iLooksGood"),
            (By.ID, "idSIButton9"),
            (By.CSS_SELECTOR, ".ms-Button.ms-Button--primary"),
            (By.CSS_SELECTOR, '[data-testid="primaryButton"]'),
        ]
        result = False
        for button in buttons:
            try:
                self.webdriver.find_element(button[0], button[1]).click()
                result = True
            except Exception:  # pylint: disable=broad-except
                continue
        return result

    def tryDismissCookieBanner(self):
        with contextlib.suppress(Exception):
            self.webdriver.find_element(By.ID, "cookie-banner").find_element(
                By.TAG_NAME, "button"
            ).click()
            time.sleep(2)

    def tryDismissBingCookieBanner(self):
        with contextlib.suppress(Exception):
            self.webdriver.find_element(By.ID, "bnp_btn_accept").click()
            time.sleep(2)

    def switchToNewTab(self, timeToWait: int = 0):
        time.sleep(0.5)
        self.webdriver.switch_to.window(window_name=self.webdriver.window_handles[1])
        if timeToWait > 0:
            time.sleep(timeToWait)

    def closeCurrentTab(self):
        self.webdriver.close()
        time.sleep(0.5)
        self.webdriver.switch_to.window(window_name=self.webdriver.window_handles[0])
        time.sleep(0.5)

    def visitNewTab(self, timeToWait: int = 0):
        self.switchToNewTab(timeToWait)
        self.closeCurrentTab()

    def getRemainingSearches(self):
        dashboard = self.getDashboardData()
        searchPoints = 3 # 目前每次搜索获得的积分为3
        counters = dashboard["userStatus"]["counters"]

        if "pcSearch" not in counters:
            return 0, 0
        progressDesktop = 0

        for item in counters['pcSearch']:
            progressDesktop += item.get('pointProgress', 0)

        targetDesktop = 0

        for item in counters['pcSearch']:
            targetDesktop += item.get('pointProgressMax', 0)
        # logging.info(f"[BING] targetDesktop: {targetDesktop}, progressDesktop: {progressDesktop}")

        remainingDesktop = int((targetDesktop - progressDesktop) / searchPoints)
        remainingMobile = 0
        if dashboard["userStatus"]["levelInfo"]["activeLevel"] != "Level1":
            progressMobile = counters["mobileSearch"][0]["pointProgress"]
            targetMobile = counters["mobileSearch"][0]["pointProgressMax"]
            remainingMobile = int((targetMobile - progressMobile) / searchPoints)
        return remainingDesktop, remainingMobile

    def formatNumber(self, number):
        """
        将输入的数字转换为不包含小数位的格式化字符串。

        Args:
            number (int or float): 输入的数字。

        Returns:
            str: 不包含小数位的格式化字符串。
        """
        return pylocale.format_string("%10d", int(number), grouping=True).strip()

    @staticmethod
    def getBrowserConfig(sessionPath: Path) -> dict:
        configFile = sessionPath.joinpath("config.json")
        if configFile.exists():
            with open(configFile, "r") as f:
                config = json.load(f)
                return config
        else:
            return {}

    @staticmethod
    def saveBrowserConfig(sessionPath: Path, config: dict):
        configFile = sessionPath.joinpath("config.json")
        with open(configFile, "w") as f:
            json.dump(config, f)

    @staticmethod
    def load_config():
        """
        读取项目根目录下的 config.json 文件。

        :return: 配置文件中的数据，如果文件不存在则返回空字典。
        """
        config_path = Path(__file__).parent.parent / "config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}