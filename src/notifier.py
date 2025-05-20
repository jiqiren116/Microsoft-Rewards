import requests
from pathlib import Path
import json
import logging
from src.utils import Utils

MAX_LENGTHS = {
    "telegram": 4096,
    "discord": 2000,
}


class Notifier:
    def __init__(self, args):
        self.args = {
            key: value
            for key, value in vars(args).items()
            if key in MAX_LENGTHS.keys() and value is not None
        }
        # 调用 Utils 类的静态方法读取配置文件
        self.config = Utils.load_config()

    def send(self, message: str):
        for type in self.args:
            if len(message) > MAX_LENGTHS[type]:
                for i in range(0, len(message), MAX_LENGTHS[type]):
                    self.send(message[i : i + MAX_LENGTHS[type]])
                return
            else:
                getattr(self, type)(message)

    def telegram(self, message):
        token, chat_id = self.args["telegram"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data)

    def discord(self, message):
        url = self.args["discord"]
        data = {"username": "Microsoft Rewards Farmer", "content": message}
        requests.post(url, data=data)

    def wechat(self, current_email, message):
        # 发送方法为get，格式为https://www.pushplus.plus/send?token=xxxx&title=XXX&content=XXX&template=html
        # 使用 get 方法获取 pushplus_token，若键不存在则返回空字符串
        pushplus_token = self.config.get("pushplus_token", "")
        # 如果没有配置pushplus_token，则不发送
        if not pushplus_token:
            logging.warning("未配置pushplus_token，跳过发送微信消息")
            return
        url = f"https://www.pushplus.plus/send?token={pushplus_token}&title={current_email}&content={message}&template=html"
        # 根据requests.get(url)的返回值判断是否发送成功，若返回值为200，则发送成功，否则发送失败
        if requests.get(url).status_code == 200:
            logging.info("发送微信消息成功")
        else:
            logging.error("发送微信消息失败")
