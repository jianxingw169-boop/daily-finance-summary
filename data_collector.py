import re
from datetime import datetime

from curl_cffi import requests as cr
import akshare as ak

IMPERSONATE = "chrome120"
TIMEOUT = 15

HEADERS_SINA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://finance.sina.com.cn/",
}

HEADERS_EM = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://data.eastmoney.com/",
}


# ── 指数行情 ────────────────────────────────────────────

def fetch_indices(index_list):
    """获取指数行情 — 新浪财经"""
    code_map = {
        "1.000001": "s_sh000001",  # 上证
        "0.399001": "s_sz399001",  # 深证
        "0.399006": "s_sz399006",  # 创业板
        "0.000688": "s_sh000688",  # 科创50
        "1.000300": "s_sh000300",  # 沪深300
        "0.399005": "s_sz399005",  # 中小100
        "1.000905": "s_sh000905",  # 中证500
        "1.000852": "s_sh000852",  # 中证1000
    }

    codes = [code_map.get(item["code"]) for item in index_list if item["code"] in code_map]
    if not codes:
        return []

    url = f"http://hq.sinajs.cn/list={','.join(codes)}"
    resp = cr.get(url, headers=HEADERS_SINA, impersonate=IMPERSONATE, timeout=TIMEOUT)

    results = []
    for line in resp.text.strip().split("\n"):
        m = re.match(r'var hq_str_s_[hs]z?\w+="(.*)"', line)
        if not m:
            continue
        parts = m.group(1).split(",")
        if len(parts) < 4:
            continue
        results.append({
            "name": parts[0],
            "price": float(parts[1]) if parts[1] else 0,
            "change_pct": float(parts[3]) if parts[3] else 0,
            "change_val": float(parts[2]) if parts[2] else 0,
        })
    return results


# ── 板块排名 ────────────────────────────────────────────

def _get_sina_board_nodes():
    url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodes"
    resp = cr.get(url, headers=HEADERS_SINA, impersonate=IMPERSONATE, timeout=TIMEOUT)
    nodes = re.findall(r'"new_(\w+)"', resp.text)
    return [f"new_{n}" for n in nodes]


def fetch_sector_ranking(top_n=5):
    nodes = _get_sina_board_nodes()
    if not nodes:
        return {"top_gainers": [], "top_losers": []}

    sectors = []
    for i in range(0, len(nodes), 30):
        batch = nodes[i:i + 30]
        codes = ",".join(f"bk_{n}" for n in batch)
        url = f"http://hq.sinajs.cn/list={codes}"
        resp = cr.get(url, headers=HEADERS_SINA, impersonate=IMPERSONATE, timeout=TIMEOUT)
        for line in resp.text.strip().split("\n"):
            m = re.match(r'var hq_str_bk_\w+="(.*)"', line)
            if not m:
                continue
            parts = m.group(1).split(",")
            if len(parts) < 6:
                continue
            try:
                sectors.append({
                    "name": parts[1],
                    "change_pct": float(parts[5]),
                })
            except (ValueError, IndexError):
                continue

    sectors.sort(key=lambda x: x["change_pct"], reverse=True)
    return {
        "top_gainers": sectors[:top_n],
        "top_losers": sectors[-top_n:][::-1],
    }


# ── 北向资金 ────────────────────────────────────────────

def fetch_north_flow():
    """获取北向资金 — 多个来源依次尝试"""
    # 方案1: 东方财富 push2（可能被反爬）
    try:
        url = (
            "https://push2.eastmoney.com/api/qt/kamt.kline/get?"
            "fields1=f1,f2,f3&fields2=f51,f52,f53&klt=101&lmt=2"
        )
        resp = cr.get(url, headers=HEADERS_EM, impersonate=IMPERSONATE, timeout=10)
        data = resp.json()
        total_net = 0
        if data.get("data"):
            for key in ("hk2sh", "hk2sz"):
                if data["data"].get(key):
                    latest = data["data"][key][-1]
                    parts = latest.split(",")
                    if len(parts) >= 3:
                        total_net += float(parts[1])
        return {"north_net_flow": total_net}
    except Exception:
        pass

    # 方案2: AKShare 北向资金
    try:
        df = ak.stock_hsgt_hist_em(symbol="沪股通")
        if len(df) > 0:
            net = float(df.iloc[-1]["当日净买额"]) if "当日净买额" in df.columns else 0
            return {"north_net_flow": net}
    except Exception:
        pass

    return {"north_net_flow": None}


# ── 财经新闻 ────────────────────────────────────────────

def fetch_news_headlines(limit=15):
    try:
        df = ak.stock_info_global_em()
        titles = df["标题"].tolist()
        return titles[:limit]
    except Exception:
        return []


# ── 主入口 ──────────────────────────────────────────────

def collect_all(config):
    indices_cfg = config.get("data", {}).get("indices", [])
    top_n = config.get("data", {}).get("top_sectors", 5)

    print("[1/4] 获取指数行情...")
    indices = fetch_indices(indices_cfg)

    print("[2/4] 获取板块排名...")
    sectors = fetch_sector_ranking(top_n)

    print("[3/4] 获取北向资金...")
    north = fetch_north_flow()

    print("[4/4] 获取财经新闻...")
    news = fetch_news_headlines()

    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "indices": indices,
        "sectors": sectors,
        "north_flow": north,
        "news": news,
    }
