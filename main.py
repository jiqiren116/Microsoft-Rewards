import argparse
import json
import logging
import logging.handlers as handlers
import random
import sys
from pathlib import Path
import threading  

from src import Browser, DailySet, Login, MorePromotions, PunchCards, Searches
from src.constants import VERSION
from src.loggingColoredFormatter import ColoredFormatter
from src.notifier import Notifier
from src.utils import Utils

POINTS_COUNTER = 0

LOG_TAG = "[CMY]"

# 全局变量声明
config = None

def setupConfig() -> dict:
    """
    检查 config.json 文件是否存在，若不存在则创建默认配置文件，最后读取并返回配置内容。

    Returns:
        dict: 从 config.json 文件中读取的配置信息。
    """
    configPath = Path(__file__).resolve().parent / "config.json"
    if not configPath.exists():
        # 创建默认配置文件 add_visible_flag为false表示默认不开启-v参数，浏览器无头模式，代表浏览器不可见
        # target_point为17925，表示目标积分为17925，17925是100元天猫卡
        default_config = {
            "driver_executable_path": "your driver path",
            "browser_executable_path": "your browser path",
            "add_visible_flag": False,
            "pushplus_token": "your pushplus token",
            "target_point": 17925
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
    global config
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
    logging.info(f"{LOG_TAG} loadedAccounts: {loadedAccounts}")
    # 定义一个变量来收集每个账号的结果
    all_account_results = []
    for currentAccount in loadedAccounts:
        try:
            account_result = executeBot(currentAccount, notifier, args)
            if account_result:
                all_account_results.append(account_result)
        except Exception as e:
            logging.exception(f"{e.__class__.__name__}: {e}")
            account_result = f"{currentAccount.get('username', '未知账号')} 执行失败: {str(e)}"
            all_account_results.append(account_result)
    # 拼接所有账号的结果信息
    result_message = "\n".join(all_account_results)
    notifier.wechat("执行完成", f"所有账号执行结果如下：\n{result_message}")
    logging.info(f"{LOG_TAG} 账号全部执行完成")


def setupLogging():
    format = "%(asctime)s [%(levelname)s] %(message)s"
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(ColoredFormatter(format))

    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "activity.log"

    logging.basicConfig(
        level=logging.INFO,
        format=format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                log_file,
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
    random.shuffle(loadedAccounts) # 怀疑这里打乱顺序会导致浏览器打开失败，因此注释
    return loadedAccounts


def executeBot(currentAccount, notifier: Notifier, args: argparse.Namespace):
    global config
    # 获取当前的邮箱账号
    current_email = currentAccount.get("username", "")

    logging.info(
        f'********************{current_email}********************'
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

        # 创建线程锁
        lock = threading.Lock()

        def desktop_search():
            nonlocal accountPointsCounter
            try:
                logging.info("[BING] DESKTOP_SEARCH thread started")
                if remainingSearches != 0:
                    points = Searches(desktopBrowser).bingSearches(
                        current_email,
                        remainingSearches
                    )
                    logging.info("[BING] DESKTOP_SEARCH finished")

                    with lock:
                        accountPointsCounter = max(accountPointsCounter, points)
            except Exception as e:
                logging.exception(f"Desktop search failed: {e}")

        def mobile_search():
            nonlocal accountPointsCounter
            try:
                logging.info("[BING] MOBILE_SEARCH thread started")
                if remainingSearchesM != 0:
                    with Browser(
                        mobile=True, account=currentAccount, args=args
                    ) as mobileBrowser:
                        Login(mobileBrowser).login()
                        mobile_points = Searches(mobileBrowser).bingSearches(
                            current_email,
                            remainingSearchesM
                        )
                        logging.info("[BING] MOBILE_SEARCH finished")
                        with lock:
                            accountPointsCounter = max(accountPointsCounter, mobile_points)
            except Exception as e:
                logging.exception(f"Mobile search failed: {e}")

        # 创建线程
        desktop_thread = threading.Thread(target=desktop_search)
        mobile_thread = threading.Thread(target=mobile_search)

        # 启动线程
        desktop_thread.start()
        mobile_thread.start()

        # 等待线程完成
        desktop_thread.join()
        mobile_thread.join()

    earnedPoints = desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints)
    havePoints = desktopBrowser.utils.formatNumber(accountPointsCounter)
    logging.info(
        f"[POINTS] Earned {earnedPoints} points today, total points: {havePoints}\n")

    # 截取current_email的邮箱种类，不包含.com
    email_type = current_email.split('@')[1].split('.')[0]
    message_title = f"{email_type}邮箱 积分：{earnedPoints}"
    # 注释掉原来单独发送消息的代码
    # notifier.wechat(message_title, f"本次获得积分：{earnedPoints}，总积分：{havePoints}")

    # 从配置文件中读取target_point,如果不存在或者为0，则不发送通知
    if config is not None:
        target_point = config.get("target_point", 0)
        # 移除 havePoints 中的逗号再转换为整数
        have_points_int = int(havePoints.replace(',', ''))
        if target_point > 0 and have_points_int >= target_point:
            notifier.wechat(current_email, f"已达到目标积分：{target_point}，可以兑换了！")
    # 返回当前账号的执行结果
    return f"{message_title}，本次获得积分：{earnedPoints}，总积分：{havePoints} "

if __name__ == "__main__":
    main()
