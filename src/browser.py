import contextlib
import logging
import random
import uuid
import json
import shutil
from pathlib import Path
from typing import Any
from selenium.common.exceptions import SessionNotCreatedException

import ipapi
import seleniumwire.undetected_chromedriver as webdriver
from selenium.webdriver.chrome.webdriver import WebDriver

from src.userAgentGenerator import GenerateUserAgent
from src.utils import Utils

LOG_TAG = "[CMY]"

class Browser:
    """WebDriver wrapper class."""

    def __init__(self, mobile: bool, account, args: Any) -> None:
        self.mobile = mobile
        self.browserType = "mobile" if mobile else "desktop"
        self.headless = not args.visible
        self.username = account["username"]
        self.password = account["password"]
        self.localeLang, self.localeGeo = self.getCCodeLang(args.lang, args.geo)
        self.proxy = None
        if args.proxy:
            self.proxy = args.proxy
        elif account.get("proxy"):
            self.proxy = account["proxy"]
        self.userDataDir = self.setupProfiles()
        self.browserConfig = Utils.getBrowserConfig(self.userDataDir)
        (
            self.userAgent,
            self.userAgentMetadata,
            newBrowserConfig,
        ) = GenerateUserAgent().userAgent(self.browserConfig, mobile)
        logging.info(f"{LOG_TAG} GenerateUserAgent().userAgent done")
        if newBrowserConfig:
            self.browserConfig = newBrowserConfig
            Utils.saveBrowserConfig(self.userDataDir, self.browserConfig)
        # 读取配置文件
        config_path = Path(__file__).parent.parent / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.webdriver = self.browserSetup()
        self.utils = Utils(self.webdriver)

    def __enter__(self) -> "Browser":
        return self

    def __exit__(self, *args: Any) -> None:
        self.closeBrowser()

    def closeBrowser(self) -> None:
        """Perform actions to close the browser cleanly."""
        if self.webdriver:
            try:
                self.webdriver.quit()
            except OSError as e:
                logging.error(f"{LOG_TAG} Error closing browser: {e}")
            except Exception as general_e:
                logging.error(f"{LOG_TAG} Unexpected error closing browser: {general_e}")
            finally:
                self.webdriver = None

    def browserSetup(self) -> WebDriver:
        options = webdriver.ChromeOptions()
        options.headless = self.headless
        options.add_argument(f"--lang={self.localeLang}")
        options.add_argument("--log-level=3")

        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-certificate-errors-spki-list")
        options.add_argument("--ignore-ssl-errors")

        seleniumwireOptions: dict[str, Any] = {"verify_ssl": False}

        if self.proxy:
            seleniumwireOptions["proxy"] = {
                "http": self.proxy,
                "https": self.proxy,
                "no_proxy": "localhost,127.0.0.1",
            }

        try:
            driver = webdriver.Chrome(
                options=options,
                seleniumwire_options=seleniumwireOptions,
                # 注释user_data_dir原因，这里大概是跟读取session文件夹有关，因为总是会遇到关于session有关的报错，因此注释
                # user_data_dir=self.userDataDir.as_posix(),
                # 从配置文件中获取路径
                driver_executable_path=self.config["driver_executable_path"],
                browser_executable_path=self.config["browser_executable_path"],
            )
            logging.info(f"{LOG_TAG} webdriver.Chrome done")
        except SessionNotCreatedException as e:
            logging.info(f"{LOG_TAG} 尝试删除sessions文件夹来解决问题，记得在任务管理器中把关于chrome的进程都关掉才能删除成功")
            logging.error(f"{LOG_TAG} Session creation failed: {e}")
            # 重新抛出异常，让上层代码处理
            raise

        seleniumLogger = logging.getLogger("seleniumwire")
        seleniumLogger.setLevel(logging.ERROR)

        if self.browserConfig.get("sizes"):
            deviceHeight = self.browserConfig["sizes"]["height"]
            deviceWidth = self.browserConfig["sizes"]["width"]
        else:
            if self.mobile:
                deviceHeight = random.randint(568, 1024)
                deviceWidth = random.randint(320, min(576, int(deviceHeight * 0.7)))
            else:
                deviceWidth = random.randint(1024, 2560)
                deviceHeight = random.randint(768, min(1440, int(deviceWidth * 0.8)))
            self.browserConfig["sizes"] = {
                "height": deviceHeight,
                "width": deviceWidth,
            }
            Utils.saveBrowserConfig(self.userDataDir, self.browserConfig)

        if self.mobile:
            screenHeight = deviceHeight + 146
            screenWidth = deviceWidth
        else:
            screenWidth = deviceWidth + 55
            screenHeight = deviceHeight + 151

        logging.info(f"Screen size: {screenWidth}x{screenHeight}")
        logging.info(f"Device size: {deviceWidth}x{deviceHeight}")

        if self.mobile:
            driver.execute_cdp_cmd(
                "Emulation.setTouchEmulationEnabled",
                {
                    "enabled": True,
                },
            )

        driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": deviceWidth,
                "height": deviceHeight,
                "deviceScaleFactor": 0,
                "mobile": self.mobile,
                "screenWidth": screenWidth,
                "screenHeight": screenHeight,
                "positionX": 0,
                "positionY": 0,
                "viewport": {
                    "x": 0,
                    "y": 0,
                    "width": deviceWidth,
                    "height": deviceHeight,
                    "scale": 1,
                },
            },
        )

        driver.execute_cdp_cmd(
            "Emulation.setUserAgentOverride",
            {
                "userAgent": self.userAgent,
                "platform": self.userAgentMetadata["platform"],
                "userAgentMetadata": self.userAgentMetadata,
            },
        )

        return driver

    def setupProfiles(self) -> Path:
        """
        Sets up the sessions profile for the chrome browser.
        Uses the username to create a unique profile for the session.

        Returns:
            Path
        """
        currentPath = Path(__file__)
        parent = currentPath.parent.parent
        sessionsDir = parent / "sessions"

        sessionUuid = uuid.uuid5(uuid.NAMESPACE_DNS, self.username)
        sessionsDir = sessionsDir / str(sessionUuid) / self.browserType
        sessionsDir.mkdir(parents=True, exist_ok=True)
        return sessionsDir

    def getCCodeLang(self, lang: str, geo: str) -> tuple:
        if lang is None or geo is None:
            try:
                nfo = ipapi.location()
                if isinstance(nfo, dict):
                    if lang is None:
                        lang = nfo["languages"].split(",")[0].split("-")[0]
                    if geo is None:
                        geo = nfo["country"]
            except Exception:  # pylint: disable=broad-except
                return ("en", "US")
        return (lang, geo)
