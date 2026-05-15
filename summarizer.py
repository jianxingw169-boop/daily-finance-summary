import json

import requests


SYSTEM_PROMPT = """你是一位资深金融分析师。请根据提供的今日市场数据，生成一份每日金融市场总结，包含投资参考建议。

要求：
1. 用中文输出，语言精炼专业
2. 格式包含以下部分（用 markdown）：
   - **📊 主要指数**：列出各指数涨跌情况及技术面简析
   - **🔥 热点板块**：今日涨幅居前的板块，分析背后驱动逻辑
   - **📉 弱势板块**：今日跌幅居前的板块及原因
   - **💰 北向资金**：北向资金流向及信号含义
   - **📰 要闻速览**：重要财经新闻摘要（3-5条关键信息）
   - **💡 市场简评**：市场情绪、资金面、政策面综合分析（2-3句）
   - **🎯 投资参考**：基于今日行情给出 3 条具体的投资建议或风险提示。可以是短期关注方向、避险提醒、行业轮动判断、操作策略建议等。每条建议一句话，需注明是基于数据还是基于分析推测。严禁给出"买入/卖出"等具体操作指令，仅提供参考方向。
3. 总字数控制在 700 字以内
4. 严格基于提供的数据进行分析，不编造数据
5. 文末加一句免责声明："⚠️ 以上分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。"""


def summarize(data, config):
    """调用 DeepSeek API 生成总结"""
    api_key = config["deepseek"]["api_key"]
    model = config["deepseek"]["model"]
    base_url = config["deepseek"]["base_url"]

    user_msg = json.dumps(data, ensure_ascii=False, indent=2)

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"今日市场数据如下：\n\n{user_msg}"},
            ],
            "temperature": 0.7,
            "max_tokens": 1536,
        },
        timeout=60,
    )
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"]
