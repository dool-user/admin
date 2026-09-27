import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import scraper  # noqa: E402
from scraper import Condition, Place  # noqa: E402

DIALOG_TEXT = """オンラインで注文
おだしもん サンシャインシティアルパ池袋店
受け取り
宅配
注文可能プロバイダ:
UberEats
手数料が発生する場合があります
31〜46 分後にお届け予定
出前館
手数料が発生する場合があります
"""


def test_extract_providers():
    assert scraper.extract_providers(DIALOG_TEXT) == ["UberEats", "出前館"]
    assert scraper.extract_providers("注文なし") == []


def test_uber_regex():
    for text in ("UberEats", "Uber Eats", "uber eats", "ウーバーイーツ"):
        assert scraper.UBER_RE.search(text)
    assert not scraper.UBER_RE.search("出前館 / menu")


def test_area_and_phone_filters():
    addr = "〒170-0013 東京都豊島区東池袋３丁目１−１"
    assert scraper.area_matches(addr, "東京都", "豊島区")
    assert not scraper.area_matches(addr, "東京都", "新宿区")
    assert scraper.area_matches(addr, "東京都", "")
    assert scraper.phone_matches("03-1234-5678", "with")
    assert not scraper.phone_matches("", "with")
    assert scraper.phone_matches("", "without")


@pytest.mark.parametrize("order,uber,mode,expected", [
    (True, False, scraper.MODE_ORDER_NO_UBER, True),
    (True, True, scraper.MODE_ORDER_NO_UBER, False),
    (False, False, scraper.MODE_ORDER_NO_UBER, False),
    (False, False, scraper.MODE_NO_UBER, True),
    (True, True, scraper.MODE_NO_UBER, False),
])
def test_uber_mode(order, uber, mode, expected):
    place = Place(address="東京都豊島区", has_online_order=order, has_uber_eats=uber)
    assert scraper.matches(place, Condition("東京都", "豊島区", mode=mode)) is expected


def test_labels_and_rating():
    assert scraper.strip_label("住所: 東京都豊島区") == "東京都豊島区"
    assert scraper.strip_label("電話番号: 03-1234-5678") == "03-1234-5678"
    assert scraper.parse_rating("4.3\n(1,390)") == ("4.3", "1390")


# ------------------------------------------------ 模擬ページでブラウザ操作を確認

PAGE = """<!doctype html><html><body>
<div role="main">
  <h1>{name}</h1>
  <button class="DkEaL">イタリア料理</button>
  <div class="F7nice"><span>4.3</span><span>(390)</span></div>
  <button data-item-id="address" aria-label="住所: 東京都豊島区東池袋３丁目１−１ B1">x</button>
  {phone}
  {order}
  <div class="review">口コミ: Uber Eats でも頼みたい</div>
</div>
<div id="dlg" role="dialog" hidden>
  <h2>オンラインで注文</h2>
  <button id="pick" onclick="show('pick')">受け取り</button>
  <button id="deli" onclick="show('deli')">× 宅配</button>
  <div>注文可能プロバイダ:</div>
  <div id="list"></div>
</div>
<script>
const providers = {providers};
function show(mode) {{
  document.getElementById('list').innerHTML = (providers[mode] || [])
    .map(p => '<div><span>' + p + '</span><div>手数料が発生する場合があります</div><div>31〜46 分後にお届け予定</div></div>').join('');
}}
function openOrder() {{ document.getElementById('dlg').hidden = false; show('deli'); }}
</script>
</body></html>"""

ORDER_BUTTON = '<button onclick="openOrder()">オンラインで注文</button>'
PHONE = '<button data-item-id="phone:tel:0312345678" aria-label="電話番号: 03-1234-5678">x</button>'


@pytest.fixture(scope="module")
def page():
    pytest.importorskip("playwright")
    with scraper.open_browser(headless=True) as p:
        yield p


def _inspect(page, tmp_path, name, providers, order=True, phone=True):
    html = PAGE.format(name=name, phone=PHONE if phone else "", order=ORDER_BUTTON if order else "",
                       providers=providers)
    path = tmp_path / "place.html"
    path.write_text(html, encoding="utf-8")
    return scraper.inspect_place(page, path.as_uri())


def test_place_with_uber(page, tmp_path):
    place = _inspect(page, tmp_path, "おだしもん", '{deli: ["UberEats"], pick: []}')
    assert place.name == "おだしもん"
    assert place.category == "イタリア料理"
    assert place.phone == "03-1234-5678"
    assert place.address.startswith("東京都豊島区")
    assert (place.rating, place.reviews) == ("4.3", "390")
    assert place.has_online_order and place.has_uber_eats
    assert place.providers == ["UberEats"]


def test_uber_only_in_pickup_tab(page, tmp_path):
    place = _inspect(page, tmp_path, "店B", '{deli: ["出前館"], pick: ["Uber Eats"]}')
    assert place.has_uber_eats
    assert place.providers == ["出前館", "Uber Eats"]


def test_place_without_uber(page, tmp_path):
    # 口コミに「Uber Eats」があっても、注文パネル外なので誤判定しない
    place = _inspect(page, tmp_path, "店C", '{deli: ["出前館", "menu"], pick: []}', phone=False)
    assert place.has_online_order and not place.has_uber_eats
    assert place.providers == ["出前館", "menu"]
    assert place.phone == ""
    assert scraper.matches(place, Condition("東京都", "豊島区", phone="without"))


def test_place_without_order_button(page, tmp_path):
    place = _inspect(page, tmp_path, "店D", "{}", order=False)
    assert not place.has_online_order and not place.has_uber_eats
    assert not scraper.matches(place, Condition("東京都", "豊島区"))
    assert scraper.matches(place, Condition("東京都", "豊島区", mode=scraper.MODE_NO_UBER))
