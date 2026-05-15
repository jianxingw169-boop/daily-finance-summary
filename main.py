import os
import sys
import time
import argparse
import traceback

import yaml

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from data_collector import collect_all
from summarizer import summarize
from notifier import send_wechat


def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 环境变量优先（用于 GitHub Actions 等云端环境）
    if os.getenv("DEEPSEEK_API_KEY"):
        config["deepseek"]["api_key"] = os.getenv("DEEPSEEK_API_KEY")
    if os.getenv("SERVERCHAN_SEND_KEY"):
        config["serverchan"]["send_key"] = os.getenv("SERVERCHAN_SEND_KEY")

    return config


def validate_config(config):
    errors = []
    if config["deepseek"]["api_key"] in ("your-deepseek-api-key", ""):
        errors.append("DeepSeek API Key 未配置（config.yaml 或环境变量 DEEPSEEK_API_KEY）")
    if config["serverchan"]["send_key"] in ("your-send-key", ""):
        errors.append("Server酱 SendKey 未配置（config.yaml 或环境变量 SERVERCHAN_SEND_KEY）")
    if errors:
        print("配置错误：")
        for e in errors:
            print(f"  - {e}")
        print("\n获取方式：")
        print("  DeepSeek API Key: https://platform.deepseek.com/api_keys")
        print("  Server酱 SendKey: https://sct.ftqq.com/")
        sys.exit(1)


def run_once(config):
    """执行一次完整的收集-总结-推送流程"""
    print("=" * 50)
    print("Daily Finance Summary -", config.get("schedule", {}).get("time", "10:00"))
    print("=" * 50)

    try:
        data = collect_all(config)
    except Exception as e:
        print(f"[数据收集失败] {e}")
        traceback.print_exc()
        return

    if not data.get("indices"):
        print("[数据收集结果] 未获取到指数数据，今天可能是非交易日")
        # 非交易日也发一条简短通知
        try:
            send_wechat("今日非交易日，暂无市场数据。", data, config)
        except Exception:
            pass
        return

    print("\n--- 指数行情 ---")
    for idx in data["indices"]:
        arrow = ">>" if idx["change_pct"] >= 0 else "<<"
        print(f"  {idx['name']:6s}  {idx['price']:>10.2f}  {arrow} {idx['change_pct']:+.2f}%")

    print("\n--- 板块排行 ---")
    for s in data["sectors"]["top_gainers"]:
        print(f"  +{s['name']}: {s['change_pct']:+.2f}%")
    print("  ...")
    for s in data["sectors"]["top_losers"]:
        print(f"  -{s['name']}: {s['change_pct']:+.2f}%")

    print(f"\n--- 北向资金 ---")
    nf = data["north_flow"]["north_net_flow"]
    if nf is not None:
        direction = "流入" if nf >= 0 else "流出"
        print(f"  净{direction}: {abs(nf)/1e8:.2f} 亿")
    else:
        print("  暂无数据")

    print(f"\n--- 财经新闻 ({len(data['news'])}条) ---")
    for i, n in enumerate(data["news"][:5], 1):
        print(f"  {i}. {n}")

    print("\n--- 正在通过 DeepSeek 生成总结 ---")
    try:
        summary = summarize(data, config)
        print(summary)
    except Exception as e:
        print(f"[AI总结失败] {e}")
        traceback.print_exc()
        return

    print("\n--- 推送微信通知 ---")
    try:
        send_wechat(summary, data, config)
    except Exception as e:
        print(f"[推送失败] {e}")
        traceback.print_exc()
        return

    print("\n✓ 完成")


def is_trading_day(data):
    """简单判断是否为交易日（有指数数据且有涨跌变化一般就是交易日）"""
    if not data.get("indices"):
        return False
    # 如果所有指数涨跌幅都为 0，可能是非交易日
    changes = [idx["change_pct"] for idx in data["indices"]]
    return any(abs(c) > 0.001 for c in changes)


def main():
    parser = argparse.ArgumentParser(description="每日金融总结推送")
    parser.add_argument("--once", action="store_true", help="立即执行一次")
    parser.add_argument("--schedule", action="store_true", help="启动定时任务模式（本地用）")
    args = parser.parse_args()

    config = load_config()
    validate_config(config)

    if args.schedule:
        import schedule
        run_time = config.get("schedule", {}).get("time", "10:00")
        print(f"定时任务已启动，每天 {run_time} 推送一次。按 Ctrl+C 停止。")
        schedule.every().day.at(run_time).do(run_once, config=config)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_once(config)


if __name__ == "__main__":
    main()
