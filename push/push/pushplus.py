import logging

from .decorator import catchException
from .push import Push
import requests as re
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

params = ("title", "channel", "topic", "webhook", "template")


def isParams(k: str) -> bool:
    return k in params


class Pushplus(Push):
    """
    offical address: https://www.pushplus.plus
    """

    url = "http://www.pushplus.plus/send"

    def __init__(self, key: str):
        super().__init__(key)

    @catchException
    def send(self, msg: str, **kwargs):
        params = {
            "token": self.key,
            "content": msg,
        }

        for keys, values in kwargs.items():
            if isParams(keys):
                params.update({keys: values})
        logging.debug(f"准备推送消息【{params}】")
        res = re.post(self.url, json=params).json()
        logging.debug(f"推送消息响应【{params}】")
        if res.get("code") == 200:
            self.success()
        else:
            raise Exception(res.get("msg"))
