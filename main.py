import csv
from datetime import datetime, timedelta, UTC
from urllib.parse import urlencode
import requests

from ebay_api import EbayAPI


# === パラメータ ===
ENV = "SANDBOX"  # 'SANDBOX' も選択可能
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
    # price フィルターを追加
    filter_clause = "itemLocationCountry:US,priceCurrency:USD,price:[0.01..]"
    
    params = {
        "q": query,
        "limit": limit,
        "offset": 0,
        "filter": filter_clause,
        "sort": "price"  # price でソートする場合は price フィルターが必要
    }
    
    # デバッグ出力
    full_url = f"{api.api_url}/buy/marketplace_insights/v1_beta/item_sales/search?{urlencode(params)}"
    print(f"リクエストURL: {full_url}")
    
    res = requests.get(full_url, headers=api.get_headers())
    
    # エラーの詳細情報を取得
    if not res.ok:
        print(f"エラーコード: {res.status_code}")
        print(f"エラー詳細: {res.text}")
        return query, item_id, None, None, f"エラー: {res.status_code}"  # エラー時にも結果を返す
    
    data = res.json()
    items = data.get("itemSales", [])
    top_price = None
    rank = 1

    if items:
        price_info = items[0].get("lastSoldPrice", {})
        top_price = f"{price_info.get('value')} {price_info.get('currency')}"


if __name__ == "__main__":
    api = EbayAPI(env=ENV)
    
    # ヘッダーの準備
    headers = ["query", "item_id", "top_price", "rank", "error"]
    
    # CSVファイルの初期化
    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        
        # 一度だけアイテムをチェック
        result = check_item_once(api, QUERY, ITEM_ID, BASE_TIME_ISO, FLUCTUATION_SECONDS, MAX_RANK, LIMIT)
        print(result)
        # writer.writerow(result)  # 結果を書き込む