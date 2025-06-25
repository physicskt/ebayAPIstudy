import csv
from datetime import datetime, timedelta, UTC
from urllib.parse import urlencode
import requests

from ebay_api import EbayAPI


# === パラメータ ===
ENV = "PROD"  # 'SANDBOX' も選択可能
QUERY = "M51828"  # カスタムラベル
ITEM_ID = "v1|1234567890|0"  # 調査するeBay itemId

BASE_TIME_ISO = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")  # 現在時刻
FLUCTUATION_SECONDS = 30  # ±何秒
MAX_RANK = 20  # 圏内順位
LIMIT = 200  # 最大取得件数
OUTPUT_FILE = "result.csv"


# === 関数 ===
def build_last_sold_filter(base_time: str, fluctuation_seconds: int) -> str:
    dt = datetime.strptime(base_time, "%Y-%m-%dT%H:%M:%SZ")
    from_time = (dt - timedelta(seconds=fluctuation_seconds)).isoformat() + "Z"
    to_time = (dt + timedelta(seconds=fluctuation_seconds)).isoformat() + "Z"
    return f"lastSoldDate:[{from_time}..{to_time}]"


def check_item_once(api: EbayAPI, query, item_id, base_time, fluctuation_seconds, max_rank, limit):
    filter_clause = build_last_sold_filter(base_time, fluctuation_seconds)
    filter_clause += ",itemLocationCountry:US,priceCurrency:USD"

    params = {
        "q": query,
        "limit": limit,
        "offset": 0,
        "filter": filter_clause,
        "sort": "price"
    }

    url = f"{api.api_url}/buy/marketplace_insights/v1_beta/item_sales/search?{urlencode(params)}"
    res = requests.get(url, headers=api.get_headers())
    res.raise_for_status()
    data = res.json()

    items = data.get("itemSales", [])
    top_price = None
    rank = 1

    if items:
        price_info = items[0].get("lastSoldPrice", {})
        top_price = f"{price_info.get('value')} {price_info.get('currency')}"

        for item in items:
            if item.get("itemId") == item_id:
                status = "圏内" if rank <= max_rank else "圏外"
                return query, item_id, rank, top_price, status
            rank += 1

        return query, item_id, None, top_price, "圏外"

    return query, item_id, None, None, "未検出"


# === 実行 ===
if __name__ == "__main__":
    ebay = EbayAPI(env=ENV)

    result = check_item_once(
        ebay, QUERY, ITEM_ID,
        BASE_TIME_ISO, FLUCTUATION_SECONDS,
        MAX_RANK, LIMIT
    )

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["label", "item_id", "rank", "top_price", "status"])
        writer.writerow(result)

    print(f"結果を {OUTPUT_FILE} に書き出しました。")
