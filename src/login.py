import contextlib
import logging
import time
import urllib.parse

from selenium.webdriver.common.by import By

from src.browser import Browser

LOG_TAG = "[CMY]"

class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils

    def login(self):
        logging.info("[LOGIN] " + "Logging-in...")
        self.webdriver.get("https://login.live.com/")
        alreadyLoggedIn = False # 初始化已登录状态为 False
        while True:
            try:
                # 尝试等待页面加载出表示已登录的元素
                self.utils.waitUntilVisible(
                    By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 5
                )
                # 若找到元素，说明用户已登录，更新状态并跳出循环
                alreadyLoggedIn = True
                break
            except Exception:  # pylint: disable=broad-except
                try:
                    # 若未找到已登录元素，尝试等待登录页面的头部元素
                    self.utils.waitUntilVisible(By.ID, "usernameEntry", 5)
                    # 若找到登录头部元素，说明用户未登录，跳出循环
                    logging.info(f"{LOG_TAG} '用户未登录，继续执行登录流程...'")
                    break
                except Exception:  # pylint: disable=broad-except
                    # 若既未找到已登录元素也未找到登录头部元素，尝试关闭所有弹窗
                    if self.utils.tryDismissAllMessages():
                        continue
        # 如果用户未登录，则执行登录流程
        if not alreadyLoggedIn:
            self.executeLogin()
        # 尝试关闭页面的 Cookie 横幅
        self.utils.tryDismissCookieBanner()

        logging.info("[LOGIN] " + "Logged-in !")

        self.utils.goHome()
        points = self.utils.getAccountPoints()
        logging.info(
            f"[POINTS] You have {self.utils.formatNumber(points)} points on your account!"
        )

        logging.info("[LOGIN] " + "Ensuring login on Bing...")
        self.checkBingLogin()
        logging.info("[LOGIN] Logged-in successfully !")
        return points

    def executeLogin(self):
        self.utils.waitUntilVisible(By.ID, "usernameEntry", 10)
        logging.info("[LOGIN] " + "Writing email...")
        self.webdriver.find_element(By.ID, "usernameEntry").send_keys(
            self.browser.username
        )
        # 找到data-testid="primaryButton"的元素并点击它
        self.utils.waitUntilClickable(By.CSS_SELECTOR, '[data-testid="primaryButton"]', 10)
        self.webdriver.find_element(By.CSS_SELECTOR, '[data-testid="primaryButton"]').click()

        try:
            self.enterPassword(self.browser.password)
        except Exception:  # pylint: disable=broad-except
            logging.error("[LOGIN] " + "2FA required !")
            with contextlib.suppress(Exception):
                code = self.webdriver.find_element(
                    By.ID, "idRemoteNGC_DisplaySign"
                ).get_attribute("innerHTML")
                logging.error("[LOGIN] " + f"2FA code: {code}")
            logging.info("[LOGIN] Press enter when confirmed...")
            input()

        while not (
            urllib.parse.urlparse(self.webdriver.current_url).path == "/"
            and urllib.parse.urlparse(self.webdriver.current_url).hostname
            == "account.microsoft.com"
        ):
            self.utils.tryDismissAllMessages()
            time.sleep(1)

        self.utils.waitUntilVisible(
            By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 10
        )

    def enterPassword(self, password):
        self.utils.waitUntilClickable(By.NAME, "passwd", 10)
        self.utils.waitUntilClickable(By.CSS_SELECTOR, '[data-testid="primaryButton"]', 10)
        # browser.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        # If password contains special characters like " ' or \, send_keys() will not work
        password = password.replace("\\", "\\\\").replace('"', '\\"')

        self.webdriver.find_element(By.NAME, "passwd").send_keys(password)

        logging.info("[LOGIN] " + "Writing password...")
        self.webdriver.find_element(By.CSS_SELECTOR, '[data-testid="primaryButton"]').click()
        time.sleep(5)

    def checkBingLogin(self):
        self.webdriver.get(
            "https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F"
        )
        while True:
            currentUrl = urllib.parse.urlparse(self.webdriver.current_url)
            if currentUrl.hostname == "www.bing.com" and currentUrl.path == "/":
                time.sleep(3)
                self.utils.tryDismissBingCookieBanner()
                with contextlib.suppress(Exception):
                    if self.utils.checkBingLogin():
                        logging.info("[LOGIN] " + "Bing login successful!")
                        return
            time.sleep(1)
