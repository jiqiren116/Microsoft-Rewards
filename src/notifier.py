import requests
from pathlib import Path
import json

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
        # 读取配置文件
        config_path = Path(__file__).parent.parent / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

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
        pushplus_token = self.config["pushplus_token"]
        url = f"https://www.pushplus.plus/send?token={pushplus_token}&title=MS {current_email}&content={message}&template=html"
        requests.get(url)
