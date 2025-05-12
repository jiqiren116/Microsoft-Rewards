import argparse
import json
import logging
import logging.handlers as handlers
import random
import sys
from pathlib import Path

from src import Browser, DailySet, Login, MorePromotions, PunchCards, Searches
from src.constants import VERSION
from src.loggingColoredFormatter import ColoredFormatter
from src.notifier import Notifier

POINTS_COUNTER = 0

LOG_TAG = "[CMY]"

def setupConfig() -> dict:
    """
    检查 config.json 文件是否存在，若不存在则创建默认配置文件，最后读取并返回配置内容。

    Returns:
        dict: 从 config.json 文件中读取的配置信息。
    """
    configPath = Path(__file__).resolve().parent / "config.json"
    if not configPath.exists():
        # 创建默认配置文件 add_visible_flag为true表示默认开启-v参数，代表浏览器可见
        default_config = {
            "driver_executable_path": "your driver path",
            "browser_executable_path": "your browser path",
            "add_visible_flag": True,
            "pushplus_token": "your pushplus token"
        }
        configPath.write_text(
            json.dumps(default_config, indent=4),
            encoding="utf-8"
        )
        noConfigNotice = """
    [CONFIG] Configuration file "config.json" not found.
    [CONFIG] A new file has been created, please edit with your settings and save.
    """
        logging.warning(noConfigNotice)
        exit()
    loadedConfig = json.loads(configPath.read_text(encoding="utf-8"))
    return loadedConfig

def main():
    setupLogging()
    logging.info(f"{LOG_TAG} setupLogging done")
    # 调用新函数设置配置
    config = setupConfig()
    # 根据配置决定是否添加 -v 参数
    if config.get("add_visible_flag", False) and '-v' not in sys.argv and '--visible' not in sys.argv:
        sys.argv.append('-v')
    args = argumentParser()
    logging.info(f"{LOG_TAG} argumentParser done")
    notifier = Notifier(args)
    loadedAccounts = setupAccounts()
    logging.info(f"{LOG_TAG} setupAccounts done")
    for currentAccount in loadedAccounts:
        try:
            executeBot(currentAccount, notifier, args)
        except Exception as e:
            logging.exception(f"{e.__class__.__name__}: {e}")


def setupLogging():
    format = "%(asctime)s [%(levelname)s] %(message)s"
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(ColoredFormatter(format))

    (Path(__file__).resolve().parent / "logs").mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                "logs/activity.log",
                when="midnight",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            ),
            terminalHandler,
        ],
    )


def argumentParser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Microsoft Rewards Farmer")
    parser.add_argument(
        "-v", "--visible", action="store_true", help="Optional: Visible browser"
    )
    parser.add_argument(
        "-l", "--lang", type=str, default=None, help="Optional: Language (ex: en)"
    )
    parser.add_argument(
        "-g", "--geo", type=str, default=None, help="Optional: Geolocation (ex: US)"
    )
    parser.add_argument(
        "-p",
        "--proxy",
        type=str,
        default=None,
        help="Optional: Global Proxy (ex: http://user:pass@host:port)",
    )
    parser.add_argument(
        "-t",
        "--telegram",
        metavar=("TOKEN", "CHAT_ID"),
        nargs=2,
        type=str,
        default=None,
        help="Optional: Telegram Bot Token and Chat ID (ex: 123456789:ABCdefGhIjKlmNoPQRsTUVwxyZ 123456789)",
    )
    parser.add_argument(
        "-d",
        "--discord",
        type=str,
        default=None,
        help="Optional: Discord Webhook URL (ex: https://discord.com/api/webhooks/123456789/ABCdefGhIjKlmNoPQRsTUVwxyZ)",
    )
    return parser.parse_args()


def bannerDisplay():
    farmerBanner = """
    ███╗   ███╗███████╗    ███████╗ █████╗ ██████╗ ███╗   ███╗███████╗██████╗
    ████╗ ████║██╔════╝    ██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝██╔══██╗
    ██╔████╔██║███████╗    █████╗  ███████║██████╔╝██╔████╔██║█████╗  ██████╔╝
    ██║╚██╔╝██║╚════██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║██╔══╝  ██╔══██╗
    ██║ ╚═╝ ██║███████║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗██║  ██║
    ╚═╝     ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝"""
    logging.error(farmerBanner)
    logging.warning(
        f"        by Charles Bel (@charlesbel)               version {VERSION}\n"
    )


def setupAccounts() -> dict:
    accountPath = Path(__file__).resolve().parent / "accounts.json"
    if not accountPath.exists():
        accountPath.write_text(
            json.dumps(
                [{"username": "Your Email", "password": "Your Password"}], indent=4
            ),
            encoding="utf-8",
        )
        noAccountsNotice = """
    [ACCOUNT] Accounts credential file "accounts.json" not found.
    [ACCOUNT] A new file has been created, please edit with your credentials and save.
    """
        logging.warning(noAccountsNotice)
        exit()
    loadedAccounts = json.loads(accountPath.read_text(encoding="utf-8"))
    random.shuffle(loadedAccounts)
    return loadedAccounts


def executeBot(currentAccount, notifier: Notifier, args: argparse.Namespace):
    logging.info(
        f'********************{currentAccount.get("username", "")}********************'
    )
    with Browser(mobile=False, account=currentAccount, args=args) as desktopBrowser:
        accountPointsCounter = Login(desktopBrowser).login()
        logging.info(f"{LOG_TAG} Login(desktopBrowser).login() done")
        startingPoints = accountPointsCounter
        logging.info(
            f"[POINTS] You have {desktopBrowser.utils.formatNumber(accountPointsCounter)} points on your account !"
        )
        DailySet(desktopBrowser).completeDailySet()
        PunchCards(desktopBrowser).completePunchCards()
        MorePromotions(desktopBrowser).completeMorePromotions()
        (
            remainingSearches,
            remainingSearchesM,
        ) = desktopBrowser.utils.getRemainingSearches()
        if remainingSearches != 0:
            accountPointsCounter = Searches(desktopBrowser).bingSearches(
                False,
                remainingSearches
            )

        if remainingSearchesM != 0:
            desktopBrowser.closeBrowser()
            with Browser(
                mobile=True, account=currentAccount, args=args
            ) as mobileBrowser:
                accountPointsCounter = Login(mobileBrowser).login()
                accountPointsCounter = Searches(mobileBrowser).bingSearches(
                    True,
                    remainingSearchesM
                )

        earnedPoints = int(desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints))
        havePoints = int(desktopBrowser.utils.formatNumber(accountPointsCounter))
        logging.info(
            f"[POINTS] You have earned {earnedPoints} points today !"
        )
        logging.info(
            f"[POINTS] You are now at {havePoints} points !\n"
        )

        notifier.wechat(f"今天获得积分：{earnedPoints}，总积分：{havePoints}")

if __name__ == "__main__":
    main()
