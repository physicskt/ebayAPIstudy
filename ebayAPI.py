import requests
import csv
import os
from urllib.parse import urlencode
from datetime import datetime, timedelta, UTC
from base64 import b64encode
from dotenv import load_dotenv
load_dotenv()


# === ハードコード設定===
# support にbuy.marketplace.insights の使用申請を
# Production環境のeBay API設定
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

def get_access_token():
    token_url = "https://api.ebay.com/identity/v1/oauth2/token"
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    basic_auth = b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic_auth}"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope/buy.marketplace.insights"
    }

    res = requests.post(token_url, headers=headers, data=data)
    res.raise_for_status()
    return res.json()["access_token"]

ACCESS_TOKEN = get_access_token()  # アクセストークンを取得

QUERY = "M51828"  # カスタムラベル等
ITEM_ID = "v1|1234567890|0"  # 調査対象のeBay itemId
# BASE_TIME_ISO = "2025-06-14T12:00:00Z"  # 基準となる販売日時
BASE_TIME_ISO = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")  # 今現在のUTC時刻
FLUCTUATION_SECONDS = 30  # ±何秒ゆらがせるか
MAX_RANK = 20  # 圏内とする最大順位
LIMIT = 200  # 1ページの取得件数（最大200）
OUTPUT_FILE = "fluctuated_result.csv"

# === 固定ヘッダー ===

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
}

# === 検索処理本体 ===

def build_last_sold_filter(base_time: str, fluctuation_seconds: int):
    dt = datetime.strptime(base_time, "%Y-%m-%dT%H:%M:%SZ")
    from_time = (dt - timedelta(seconds=fluctuation_seconds)).isoformat() + "Z"
    to_time = (dt + timedelta(seconds=fluctuation_seconds)).isoformat() + "Z"
    return f"lastSoldDate:[{from_time}..{to_time}]"

def check_item_once(query, item_id, base_time, fluctuation_seconds, max_rank, limit):
    filter_clause = build_last_sold_filter(base_time, fluctuation_seconds)
    filter_clause += ",itemLocationCountry:US,priceCurrency:USD"

    params = {
        "q": query,
        "limit": limit,
        "offset": 0,
        "filter": filter_clause,
        "sort": "price"
    }

    url = f"https://api.ebay.com/buy/marketplace_insights/v1_beta/item_sales/search?{urlencode(params)}"
    res = requests.get(url, headers=HEADERS)
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

# === 実行＆出力 ===

result = check_item_once(QUERY, ITEM_ID, BASE_TIME_ISO, FLUCTUATION_SECONDS, MAX_RANK, LIMIT)

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["label", "item_id", "rank", "top_price", "status"])
    writer.writerow(result)

print(f"結果を {OUTPUT_FILE} に書き出しました。")
