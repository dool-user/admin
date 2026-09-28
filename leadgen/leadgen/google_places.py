"""Googleマップの店舗を Google Places API (New) の Text Search で取得する

Googleマップの画面を自動操作して抜き出すのは Google の利用規約で禁止されているため、公式 API を使います。
  https://developers.google.com/maps/documentation/places/web-service/text-search
- 1回の検索で最大20件 × 3ページ（計60件）まで
- 電話番号（nationalPhoneNumber）を取るため、料金は Text Search Enterprise の区分になります
- 環境変数 GOOGLE_MAPS_API_KEY に API キーを設定してください
"""
import os
import re

import requests

from .models import Shop

ENDPOINT = 'https://places.googleapis.com/v1/places:searchText'
FIELDS = ','.join([
    'places.id', 'places.displayName', 'places.formattedAddress', 'places.nationalPhoneNumber',
    'places.location', 'places.googleMapsUri', 'places.primaryTypeDisplayName', 'places.businessStatus',
    'places.rating', 'nextPageToken',
])


def clean_address(addr):
    """「日本、〒160-0022 東京都新宿区…」→「東京都新宿区…」"""
    addr = re.sub(r'^日本[、,]\s*', '', addr or '')
    return re.sub(r'^〒?\d{3}-?\d{4}\s*', '', addr).strip()


def to_shop(p):
    return Shop(
        source='Googleマップ',
        name=(p.get('displayName') or {}).get('text', ''),
        url=p.get('googleMapsUri', ''),
        genre=(p.get('primaryTypeDisplayName') or {}).get('text', ''),
        address=clean_address(p.get('formattedAddress', '')),
        phone=p.get('nationalPhoneNumber', ''),
        lat=(p.get('location') or {}).get('latitude'),
        lng=(p.get('location') or {}).get('longitude'),
        rating=str(p.get('rating', '')),
        source_id=p.get('id', ''),
    )


class PlacesClient:
    def __init__(self, api_key=None, session=None, log=print):
        self.api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY', '')
        if not self.api_key:
            raise RuntimeError('Googleマップを使うには環境変数 GOOGLE_MAPS_API_KEY に API キーを設定してください')
        self.session = session or requests.Session()
        self.log = log

    def search(self, query, max_results=60):
        """テキスト検索。営業中（OPERATIONAL）の店舗だけ返す"""
        shops, token = [], None
        while len(shops) < max_results:
            body = {'textQuery': query, 'languageCode': 'ja', 'regionCode': 'JP', 'pageSize': 20}
            if token:
                body['pageToken'] = token
            r = self.session.post(ENDPOINT, json=body, timeout=30, headers={
                'X-Goog-Api-Key': self.api_key, 'X-Goog-FieldMask': FIELDS,
            })
            if r.status_code != 200:
                raise RuntimeError(f'Places API エラー {r.status_code}: {r.text[:300]}')
            data = r.json()
            for p in data.get('places', []):
                if p.get('businessStatus', 'OPERATIONAL') == 'OPERATIONAL':
                    shops.append(to_shop(p))
            token = data.get('nextPageToken')
            if not token:
                break
        return shops[:max_results]
