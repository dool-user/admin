"""選択肢（都道府県・業種）と市区町村の取得"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]

# Google マップの検索語としてそのまま使う。一覧に無い業種は自由入力できる
CATEGORIES = [
    "飲食店", "レストラン", "居酒屋", "ラーメン", "うどん", "そば", "寿司",
    "焼肉", "焼き鳥", "和食", "定食", "丼", "とんかつ", "天ぷら", "お好み焼き",
    "中華料理", "餃子", "韓国料理", "タイ料理", "インド料理", "ベトナム料理",
    "イタリア料理", "パスタ", "ピザ", "フランス料理", "洋食", "ハンバーガー",
    "ステーキ", "カレー", "海鮮", "弁当", "カフェ", "パン屋", "ケーキ屋",
    "スイーツ", "テイクアウト",
]

_CITY_API = "https://geoapi.heartrails.com/api/json?method=getCities&prefecture="


def fetch_cities(prefecture: str) -> list[str]:
    """市区町村の一覧を HeartRails Geo API から取得する。取れなければ空（自由入力にする）"""
    if prefecture not in PREFECTURES:
        return []
    try:
        with urllib.request.urlopen(_CITY_API + urllib.parse.quote(prefecture), timeout=5) as res:
            data = json.load(res)
        return [row["city"] for row in data["response"]["location"]]
    except Exception:
        return []
