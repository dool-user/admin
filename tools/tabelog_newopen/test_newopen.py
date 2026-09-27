import csv
import json
from datetime import date

import newopen

LIST_HTML = """
<a class="list-rst__rst-name-target" href="https://tabelog.com/tokyo/A1305/A130501/13300001/">新店A</a>
<a href="https://tabelog.com/tokyo/A1305/A130501/13300001/dtlrvwlst/">口コミ</a>
<a class="list-rst__rst-name-target" href="https://tabelog.com/tokyo/A1304/A130401/13300002/">古い店B</a>
<a class="list-rst__rst-name-target" href="https://tabelog.com/tokyo/A1301/A130101/13300003/">電話なしC</a>
"""


def detail(name, opened, phone="03-1234-5678"):
    tel = f'<strong class="rstinfo-table__tel-num">{phone}</strong>' if phone else ""
    return f"""<table class="c-table rstinfo-table__table">
<tr><th>店名</th><td><div><span>{name}</span></div></td></tr>
<tr><th>ジャンル</th><td><span>イタリアン、パスタ</span></td></tr>
<tr><th>予約・お問い合わせ</th><td>{tel}</td></tr>
<tr><th>住所</th><td><p class="rstinfo-table__address">東京都豊島区東池袋3-1-1</p>大きな地図を見る</td></tr>
<tr><th>オープン日</th><td><p class="rstinfo-opened-date">{opened}</p></td></tr>
</table><span class="rdheader-rating__score-val-dtl">3.05</span>"""


class FakeFetcher:
    def __init__(self):
        self.calls = []
        self.pages = {
            "13300001": detail("新店A", "2026年9月20日"),
            "13300002": detail("古い店B", "2019年4月1日"),
            "13300003": detail("電話なしC", "2026年9月", phone=""),
        }

    def get(self, url):
        self.calls.append(url)
        if "/rstLst/1/" in url:
            return LIST_HTML
        if "/rstLst/" in url:
            return "<html></html>"
        return self.pages[url.rstrip("/").rsplit("/", 1)[1]]


def test_parse_open_date():
    assert newopen.parse_open_date("2026年9月20日") == date(2026, 9, 20)
    assert newopen.parse_open_date("2026年 9月") == date(2026, 9, 1)
    assert newopen.parse_open_date("-") is None


def test_parse_restaurant():
    shop = newopen.parse_restaurant(detail("新店A", "2026年9月20日"), "u")
    assert shop["name"] == "新店A"
    assert shop["genre"] == "イタリアン、パスタ"
    assert shop["phone"] == "03-1234-5678"
    assert shop["address"] == "東京都豊島区東池袋3-1-1"
    assert shop["rating"] == "3.05"
    assert shop["open_date"] == date(2026, 9, 20)


def test_run_filters_and_remembers(tmp_path):
    config = {"areas": ["tokyo"], "pages": 2, "days": 30, "phone": "any"}
    fetcher = FakeFetcher()
    found = newopen.run(config, tmp_path, fetcher, today=date(2026, 9, 27))
    assert [s["name"] for s in found] == ["新店A", "電話なしC"]

    rows = list(csv.reader((tmp_path / "2026-09-27.csv").open(encoding="utf-8-sig")))
    assert rows[0] == newopen.CSV_COLUMNS
    assert rows[1][2] == "新店A" and rows[1][1] == "2026-09-20"
    assert set(json.loads((tmp_path / "seen.json").read_text())) == {"13300001", "13300002", "13300003"}

    # 2日目: 既出の店は詳細ページを取り直さず、CSV も作らない
    fetcher2 = FakeFetcher()
    assert newopen.run(config, tmp_path, fetcher2, today=date(2026, 9, 28)) == []
    assert all("/rstLst/" in url for url in fetcher2.calls)
    assert not (tmp_path / "2026-09-28.csv").exists()


def test_phone_filter(tmp_path):
    config = {"areas": ["tokyo"], "pages": 1, "days": 30, "phone": "with"}
    found = newopen.run(config, tmp_path, FakeFetcher(), today=date(2026, 9, 27))
    assert [s["name"] for s in found] == ["新店A"]
