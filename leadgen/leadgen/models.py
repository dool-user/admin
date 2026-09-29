from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))

# Uber Eats の確認結果
UBER_NOT_FOUND = '未掲載'
UBER_FOUND = '掲載あり'
UBER_UNKNOWN = '要確認'
UBER_SKIPPED = '未確認'


def now_jst():
    return datetime.now(JST)


@dataclass
class Shop:
    source: str                 # 食べログ / Googleマップ / 両方
    name: str
    url: str = ''               # 食べログの店舗ページ or GoogleマップのURL
    genre: str = ''
    prefecture: str = ''
    city: str = ''
    address: str = ''
    phone: str = ''
    lat: float | None = None
    lng: float | None = None
    open_date: str = ''         # 食べログの「オープン日」
    rating: str = ''
    source_id: str = ''         # 食べログの店舗ID / Google の place_id
    other_url: str = ''         # 両方で見つかった場合のもう一方のURL
    ubereats_status: str = UBER_SKIPPED
    ubereats_hit: str = ''      # 掲載ありと判定した Uber Eats 上の店名
    ubereats_url: str = ''
    website: str = ''           # 店の公式サイト
    instagram: str = ''         # Instagram アカウントのURL
    form_url: str = ''          # 問い合わせフォームのURL
    contact_ng: str = ''        # 「営業お断り」などの表記（あれば送らない）
    channel: str = ''           # 送る手段：フォーム / Instagram DM / 空（送らない）
    fetched_at: str = field(default_factory=lambda: now_jst().strftime('%Y-%m-%d %H:%M'))

    @property
    def has_phone(self):
        return bool(self.phone.strip())


# CSV の列（左：項目名、右：Shop の属性）
COLUMNS = [
    ('取得元', 'source'), ('店名', 'name'), ('ジャンル', 'genre'), ('都道府県', 'prefecture'), ('市区町村', 'city'),
    ('住所', 'address'), ('電話番号', 'phone'), ('オープン日', 'open_date'), ('評価', 'rating'),
    ('Uber Eats', 'ubereats_status'), ('Uber Eats 該当店', 'ubereats_hit'), ('Uber Eats URL', 'ubereats_url'),
    ('送る手段', 'channel'), ('問い合わせフォーム', 'form_url'), ('Instagram', 'instagram'), ('営業お断り表記', 'contact_ng'),
    ('公式サイト', 'website'), ('URL', 'url'), ('URL（もう一方）', 'other_url'), ('ID', 'source_id'), ('取得日時', 'fetched_at'),
]


def to_row(shop):
    d = asdict(shop)
    return {label: d[key] for label, key in COLUMNS}
