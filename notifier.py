import json

import requests


def send_wechat(summary_text, data, config):
    """通过 Server酱 推送到微信"""
    send_key = config["serverchan"]["send_key"]
    url = f"https://sctapi.ftqq.com/{send_key}.send"

    date_str = data["date"]
    title = f"📈 每日金融速报 - {date_str}"

    # 截取摘要前50字作为描述
    desc = summary_text[:100].replace("\n", " ")

    payload = {
        "title": title,
        "desp": summary_text.replace("\n", "\n\n"),
        "short": desc,
    }

    resp = requests.post(url, data=payload, timeout=15)
    result = resp.json()
    if result.get("code") == 0:
        print(f"[推送成功] {date_str}")
    else:
        print(f"[推送失败] {result.get('message', '未知错误')}")
    return result
