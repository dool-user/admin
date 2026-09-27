"""店名の表記ゆれを吸収して同じ店かどうかを判定する"""
import re
import unicodedata
from difflib import SequenceMatcher

_BRACKETS = re.compile(r'[（(【\[「『].*?[）)】\]」』]')
_SYMBOLS = re.compile(r'[\s・･\-‐－ー—_.,、。!！?？&＆\'’"“”/／:：~〜]')
_BRANCH = re.compile(r'(本店|総本店|支店|[^\s]{1,12}?店)$')


def normalize(name):
    s = unicodedata.normalize('NFKC', name or '').lower()
    s = _BRACKETS.sub(' ', s)
    return _SYMBOLS.sub('', s)


def core_name(name):
    """支店名を落とした店名：「らーめん一蘭 新宿中央東口店」→「らーめん一蘭」"""
    s = unicodedata.normalize('NFKC', name or '')
    s = _BRACKETS.sub(' ', s).strip()
    parts = s.split()
    if len(parts) > 1 and _BRANCH.search(parts[-1]):
        parts = parts[:-1]
    return normalize(' '.join(parts))


def same_shop(a, b, threshold=0.85):
    """a, b が同じ店（またはチェーン）とみなせるか"""
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    ca, cb = core_name(a), core_name(b)
    if ca and ca == cb:
        return True
    # 支店名を除いた店名が相手に含まれる（2文字以下の短い名前は誤判定が多いので完全一致のみ）
    if len(ca) >= 3 and ca in nb:
        return True
    if len(cb) >= 3 and cb in na:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= threshold
