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
        try:
            self.webdriver.get("https://login.live.com/")
        except Exception:  # pylint: disable=broad-except
            logging.exception(f"{LOG_TAG} '无法打开登录页面 https://login.live.com/，尝试刷新页面...', Exception: {str(e)}")
            self.webdriver.refresh()
            time.sleep(10)
        alreadyLoggedIn = False # 初始化已登录状态为 False
        while True:
            try:
                # 尝试等待页面加载出表示已登录的元素
                self.utils.waitUntilVisible(
                    By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 5
                )
                # 若找到元素，说明用户已登录，更新状态并跳出循环
                alreadyLoggedIn = True
                logging.info(f"用户已登录，跳过登录流程...")
                break
            except Exception:  # pylint: disable=broad-except
                try:
                    # 若未找到已登录元素，尝试等待登录页面的头部元素
                    self.utils.waitUntilVisible(By.ID, "usernameEntry", 5)
                    # 若找到登录头部元素，说明用户未登录，跳出循环
                    logging.info(f"{LOG_TAG} '用户未登录，继续执行登录流程...'")
                    break
                except Exception:  # pylint: disable=broad-except
                    logging.info(f"{LOG_TAG} '未找到已登录元素或登录头部元素，继续尝试...'")
                    # 若既未找到已登录元素也未找到登录头部元素，尝试关闭所有弹窗
                    if self.utils.tryDismissAllMessages():
                        # 刷新页面
                        self.webdriver.refresh()
                        # 等待10s
                        time.sleep(10)
                        continue
        # 如果用户未登录，则执行登录流程
        if not alreadyLoggedIn:
            self.executeLogin()
        # 尝试关闭页面的 Cookie 横幅
        self.utils.tryDismissCookieBanner()

        logging.info("[LOGIN] " + "Logged-in !")

        self.utils.goHome()
        logging.info("[LOGIN] " + "after goHome in login")
        points = self.utils.getAccountPoints()
        logging.info(
            f"[POINTS] You have {self.utils.formatNumber(points)} points on your account!"
        )

        logging.info("[LOGIN] " + "Ensuring login on Bing...")
        self.checkBingLogin()
        logging.info("[LOGIN] Logged-in successfully !")
        return points

    def executeLogin(self):
        self.utils.waitUntilVisible(By.ID, "usernameEntry", 30)
        logging.info("[LOGIN] " + "Writing email...")
        self.webdriver.find_element(By.ID, "usernameEntry").send_keys(
            self.browser.username
        )
        logging.info("[LOGIN] " + "finded usernameEntry")
        # 找到data-testid="primaryButton"的元素并点击它
        self.utils.waitUntilClickable(By.CSS_SELECTOR, '[data-testid="primaryButton"]', 30)
        self.webdriver.find_element(By.CSS_SELECTOR, '[data-testid="primaryButton"]').click()
        logging.info("[LOGIN] " + "finded primaryButton")

        time.sleep(5)
        # 尝试跳过 [获取用于登录的代码] 选择框
        # 找到所有data-testid="title"的元素
        title_elements = self.webdriver.find_elements(By.CSS_SELECTOR, '[data-testid="title"]')
        # 遍历所有data-testid="title"的元素,判断文本中是否包含"获取用于登录的代码",尝试跳过
        for title_element in title_elements:
            if "获取用于登录的代码" in title_element.text:
                logging.info(f"[LOGIN] 登录有密码和邮箱两种")
                try:
                    # 使用 CSS 选择器结合 xpath 定位包含 "使用密码" 文本的按钮
                    view_footer = self.webdriver.find_element(By.CSS_SELECTOR, '[data-testid="viewFooter"]')
                    password_button = view_footer.find_element(By.XPATH, ".//span[contains(text(), '使用密码')]")
                    if password_button.is_displayed() and password_button.is_enabled():
                        password_button.click()
                        logging.info("[LOGIN] Clicked '使用密码' button.")
                except Exception as e:
                    logging.error(f"[LOGIN] Failed to find or click '使用密码' button: {e}")
        logging.info("[LOGIN] " + "after for title_element")

        try:
            self.enterPassword(self.browser.password)
            logging.info("[LOGIN] You hava entered your password!")

            # 尝试跳过输入密码后出现的 [使用人脸、指纹或 PIN 更快地登录] 选择框
            # 找到所有data-testid="title"的元素
            title_elements = self.webdriver.find_elements(By.CSS_SELECTOR, '[data-testid="title"]')
            # 遍历所有data-testid="title"的元素,判断文本中是否包含"获取用于登录的代码",尝试跳过
            for title_element in title_elements:
                if "使用人脸、指纹或 PIN 更快地登录" in title_element.text:
                    logging.info(f"[LOGIN] 使用人脸、指纹或 PIN 更快地登录 选择框出现")
                    try:
                        # 找到data-testid="secondaryButton"的元素并点击它, 这是跳过按钮
                        self.utils.waitUntilClickable(By.CSS_SELECTOR, '[data-testid="secondaryButton"]', 30)
                        self.webdriver.find_element(By.CSS_SELECTOR, '[data-testid="secondaryButton"]').click()
                        time.sleep(10)
                        logging.info("[LOGIN] Clicked '跳过' button.")
                    except Exception as e:
                        logging.error(f"[LOGIN] Failed to find or click '跳过' button: {e}")
        except Exception:  # pylint: disable=broad-except
            logging.error("[LOGIN] " + "2FA required !")
            with contextlib.suppress(Exception):
                code = self.webdriver.find_element(
                    By.ID, "idRemoteNGC_DisplaySign"
                ).get_attribute("innerHTML")
                logging.error("[LOGIN] " + f"2FA code: {code}")
            logging.info("[LOGIN] Press enter when confirmed...")
            input()

        matrix = 0 #避免死循环
        if self.webdriver is not None:
            logging.info("OUT 尝试跳转到account.microsoft.com")
            try:
                self.webdriver.get("https://account.microsoft.com/")
            except Exception:  # pylint: disable=broad-except
                logging.exception(f"{LOG_TAG} '无法打开登录页面 https://account.microsoft.com/，尝试刷新页面...', Exception: {str(e)}")
                self.webdriver.refresh()
            time.sleep(15)
        while not (
            urllib.parse.urlparse(self.webdriver.current_url).path == "/"
            and urllib.parse.urlparse(self.webdriver.current_url).hostname
            == "account.microsoft.com"
        ):
            # 打印当前的URL 之前第一次打印的uri为  https://login.live.com/ppsecure/post.srf?contextid=31365397EB6A09FD&opid=E9743DD0F2561F73&bk=1748483451&uaid=e6bea1540dbe4227b90fd19ec1331b3e&pid=0
            logging.info(f"[LOGIN] 当前的URL: {self.webdriver.current_url}")
            try:   
                # 检测元素是否可见（超时时间设为1秒，非阻塞）
                element = self.utils.waitUntilVisible(
                    By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 20
                )
                if element:  # 元素存在时
                    logging.info("[LOGIN] 检测到目标元素，终止循环")
                    break  # 跳出循环
                # 如果当前url包括 account.microsoft.com 则终止循环
                if "account.microsoft.com" in self.webdriver.current_url:
                    logging.info("[LOGIN] 检测到目标元素account.microsoft.com，终止循环")
                    break  # 跳出循环
            except:
                # 元素未找到时不做处理，继续循环
                pass

            logging.info(f"[LOGIN] 第{matrix}次：is in account.microsoft.com, waiting...")
            self.utils.tryDismissAllMessages()
            time.sleep(15)

            matrix += 1
            # 尝试跳转到网页 https://account.microsoft.com/
            if self.webdriver is not None:
                logging.info("尝试跳转到account.microsoft.com")
                try:
                    self.webdriver.get("https://account.microsoft.com/")
                except Exception:  # pylint: disable=broad-except
                    # 如果出现异常，打印错误信息，并刷新页面
                    logging.exception(f"{LOG_TAG} '无法打开登录页面 https://account.microsoft.com/，尝试刷新页面...', Exception: {str(e)}")
                    self.webdriver.refresh()
                time.sleep(15)
            else:
                logging.error("[LOGIN] WebDriver is None, cannot proceed to navigate.")
                raise RuntimeError("WebDriver is not initialized.")
            

            if matrix > 10:
                logging.error("[LOGIN] " + "matrix > 10, exiting...")
                break
        
        logging.info("[LOGIN] " + "after is in account.microsoft.com")

        self.utils.waitUntilVisible(
            By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 30
        )

    def enterPassword(self, password):
        self.utils.waitUntilClickable(By.NAME, "passwd", 30)
        logging.info("[LOGIN] " + "waitUntilClickable(By.NAME, 'passwd', 10)")
        self.utils.waitUntilClickable(By.CSS_SELECTOR, '[data-testid="primaryButton"]', 30)
        logging.info("[LOGIN] " + "waitUntilClickable(By.CSS_SELECTOR, '[data-testid=\"primaryButton\"]', 10)")
        # browser.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        # If password contains special characters like " ' or \, send_keys() will not work
        password = password.replace("\\", "\\\\").replace('"', '\\"')

        self.webdriver.find_element(By.NAME, "passwd").send_keys(password)

        logging.info("[LOGIN] " + "Writing password...")
        self.webdriver.find_element(By.CSS_SELECTOR, '[data-testid="primaryButton"]').click()
        logging.info("[LOGIN] " + "Clicking login button...")
        time.sleep(5)

    def checkBingLogin(self):
        max_retries = 30  # 最大重试次数
        retry_count = 0
        try:
            self.webdriver.get(
                "https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F"
            )
        except Exception:  # pylint: disable=broad-except
            logging.exception(f"{LOG_TAG} '无法打开登录页面 https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F，尝试刷新页面...', Exception: {str(e)}")
            self.webdriver.refresh()
        while retry_count < max_retries:
            logging.info(
                f"[LOGIN][checkBingLogin] " + f"Bing login attempt {retry_count + 1}/{max_retries}"
            )
            currentUrl = urllib.parse.urlparse(self.webdriver.current_url)
            logging.info(
                f"[LOGIN][checkBingLogin] " + f"Current URL: {currentUrl}" )
            if currentUrl.hostname == "cn.bing.com" and currentUrl.path == "/":
                logging.info("[LOGIN] " + "currentUrl.hostname == 'cn.bing.com' and currentUrl.path == '/'")
                time.sleep(3)
                self.utils.tryDismissBingCookieBanner()
                with contextlib.suppress(Exception):
                    if self.utils.checkBingLogin():
                        logging.info("[LOGIN] " + "Bing login successful!")
                        return
            time.sleep(1)
            retry_count += 1
            try:
                self.webdriver.get("https://cn.bing.com/")
            except Exception:  # pylint: disable=broad-except
                logging.exception(f"{LOG_TAG} '无法打开登录页面 https://cn.bing.com/，尝试刷新页面...', Exception: {str(e)}")
                self.webdriver.refresh()
            time.sleep(10)
        logging.error("[LOGIN] Bing login failed after multiple attempts.")