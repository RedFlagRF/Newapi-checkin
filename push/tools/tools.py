import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handler(fn):
    def inner(*args, **kwargs):
        res = fn(*args, **kwargs)
        if res is None:
            return None

        if len(res.get('message',''))>0:
            content = [
                {
                    "h4": {
                        "content": f"bilibili {res.get('name')}",
                    },
                },
                {
                    "txt": {
                        "content": f"{res.get('message')}",
                    },
                },

            ]
            return content
        content = [
            {
                "h4": {
                    "content": f"bilibili {res['name']}",
                },
            },
            {
                "txt": {
                    "content": f"等级: {res['level']}",
                },
            },
            {
                "txt": {
                    "content": f"硬币: {res['coin']}",
                },
            },
            {
                "txt": {
                    "content": f"经验: {res['exp']}",
                },
            },
        ]

        watch = res.get("watch")

        if watch is not None:
            content.append(
                {
                    "txt": {
                        "content": watch,
                    }
                }
            )

        share = res.get("share")

        if share is not None:
            content.append(
                {
                    "txt": {
                        "content": f"分享视频: {share}",
                        # "content": f"分享视频成功",
                    }
                }
            )

        coins = res.get("coins")

        if coins is not None:
            content.append(
                {
                    "h5": {
                        "content": "投币",
                    },
                    "orderedList": {
                        "content": coins,
                    },
                }
            )

        comics = res.get("comics")

        if comics is not None:
            content.extend(
                [
                    {
                        "h5": {
                            "content": "漫画签到",
                        },
                        "txt": {
                            "content": f"连续签到 {comics} 天",
                        },
                    },
                ]
            )

        lb = res.get("lb")

        if lb is not None:
            content.extend(
                [
                    {
                        "h5": {
                            "content": "直播",
                        },
                        "txt": {
                            "content": lb["raward"],
                        },
                    },
                ]
            )

        toCoin = res.get("toCoin")

        if toCoin is not None:
            content.append(
                {
                    "h5": {
                        "content": "银瓜子兑换硬币",
                    },
                    "txt": {
                        "content": toCoin,
                    },
                }
            )

        return content

    return inner


def failed(*args, **kwargs):
    print("[\033[31mfailed\033[0m]  ", end="")
    print(*args, **kwargs)
    logging.error(f"打印日志 {args}---- {kwargs}")


def success(*args, **kwargs):
    print("[\033[32msuccess\033[0m] ", end="")
    logging.debug(f"打印日志 {args}---- {kwargs}")
    print(*args, **kwargs)


def info(*args, **kwargs):
    print("[\033[34minfo\033[0m]    ", end="")
    logging.info(f"打印日志 {args}---- {kwargs}")
    print(*args, **kwargs)