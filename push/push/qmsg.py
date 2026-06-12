import socket
import time

from .decorator import catchException
from .push import Push
import requests as re


class Qmsg(Push):
    """
    offical address: https://qmsg.zendee.cn/api
    """
    socket.setdefaulttimeout(60)
    url = f"https://qmsg.zendee.cn:443/send"

    def __init__(self, key: str) -> None:
        super().__init__(key)

    @catchException
    def send(self, msg: str, **kwargs) -> None:
        params = {"msg": msg}
        for i in range(3):
            try:
                res = re.get(f"{self.url}/{self.key}", params=params, timeout=60).json()
            except Exception as e:
                print(f'签到出错%s"', e)
                time.sleep(10)
                continue
            if res.get("code") == 0:
                self.success()
            else:
                raise Exception(res.get("reason"))
            break
