"""見出し画像に入れる「本題に近い絵」（SVG のイラスト）と、記事のタイトルから絵を選ぶルール

色はクラスで指定する：a＝アカウントの色／s＝その薄い色／t＝背景の色／y＝黄／w＝白／k＝文字の色
絵はすべて viewBox 0 0 600 600。build_note_images.py の見出し画像の右側に大きく置く。
"""
import re

SCENES = {
    # Claude Code・権限・安全（鍵と盾、ターミナル）
    'shield': '''<rect x="60" y="90" width="400" height="290" rx="26" class="k"/><rect x="60" y="90" width="400" height="54" rx="26" class="a"/>
      <circle cx="98" cy="117" r="10" class="w"/><circle cx="130" cy="117" r="10" class="y"/><circle cx="162" cy="117" r="10" class="s"/>
      <path d="M100 190l40 30-40 30" fill="none" stroke-width="16" class="ln-y"/><rect x="160" y="240" width="120" height="16" rx="8" class="w"/>
      <rect x="100" y="290" width="220" height="14" rx="7" class="s"/><rect x="100" y="320" width="160" height="14" rx="7" class="s"/>
      <path d="M400 230c60 22 110 22 140 18v110c0 88-62 140-140 172-78-32-140-84-140-172V248c30 4 80 4 140-18z" class="a"/>
      <path d="M400 268c42 14 74 16 98 14v80c0 60-40 98-98 122-58-24-98-62-98-122v-80c24 2 56 0 98-14z" class="w"/>
      <rect x="362" y="352" width="76" height="62" rx="10" class="a"/><path d="M376 352v-20a24 24 0 0 1 48 0v20" fill="none" stroke-width="14" class="ln-a"/>
      <circle cx="400" cy="380" r="9" class="y"/>''',
    # AI の営業チーム（組織図）
    'team': '''<rect x="230" y="60" width="140" height="110" rx="22" class="a"/><circle cx="300" cy="104" r="24" class="w"/><rect x="262" y="132" width="76" height="24" rx="12" class="w"/>
      <path d="M300 170v60M120 230h360M120 230v50M240 230v50M360 230v50M480 230v50" fill="none" stroke-width="12" class="ln-k"/>
      <g class="s"><rect x="70" y="280" width="100" height="90" rx="18"/><rect x="190" y="280" width="100" height="90" rx="18"/><rect x="310" y="280" width="100" height="90" rx="18"/><rect x="430" y="280" width="100" height="90" rx="18"/></g>
      <g class="a"><circle cx="120" cy="312" r="18"/><circle cx="240" cy="312" r="18"/><circle cx="360" cy="312" r="18"/><circle cx="480" cy="312" r="18"/></g>
      <g class="k"><rect x="98" y="338" width="44" height="14" rx="7"/><rect x="218" y="338" width="44" height="14" rx="7"/><rect x="338" y="338" width="44" height="14" rx="7"/><rect x="458" y="338" width="44" height="14" rx="7"/></g>
      <path d="M120 370v50M240 370v50M360 370v50M480 370v50" fill="none" stroke-width="10" class="ln-s"/>
      <g class="w"><rect x="80" y="420" width="80" height="100" rx="12"/><rect x="200" y="420" width="80" height="100" rx="12"/><rect x="320" y="420" width="80" height="100" rx="12"/><rect x="440" y="420" width="80" height="100" rx="12"/></g>
      <g class="a"><rect x="94" y="440" width="52" height="10" rx="5"/><rect x="214" y="440" width="52" height="10" rx="5"/><rect x="334" y="440" width="52" height="10" rx="5"/><rect x="454" y="440" width="52" height="10" rx="5"/></g>
      <g class="s"><rect x="94" y="462" width="40" height="10" rx="5"/><rect x="214" y="462" width="40" height="10" rx="5"/><rect x="334" y="462" width="40" height="10" rx="5"/><rect x="454" y="462" width="40" height="10" rx="5"/></g>
      <circle cx="430" cy="90" r="34" class="y"/><path d="M415 90l11 11 20-22" fill="none" stroke-width="10" class="ln-w"/>''',
    # ルールの書類（CLAUDE.md・review.md）
    'docs': '''<rect x="150" y="70" width="300" height="400" rx="24" class="s"/><rect x="110" y="110" width="300" height="400" rx="24" class="w"/>
      <rect x="110" y="110" width="300" height="70" rx="24" class="a"/><rect x="140" y="135" width="150" height="20" rx="10" class="w"/>
      <g class="s"><rect x="140" y="210" width="220" height="14" rx="7"/><rect x="140" y="290" width="200" height="14" rx="7"/><rect x="140" y="370" width="230" height="14" rx="7"/></g>
      <g class="k"><rect x="140" y="240" width="160" height="14" rx="7"/><rect x="140" y="320" width="180" height="14" rx="7"/><rect x="140" y="400" width="130" height="14" rx="7"/></g>
      <circle cx="430" cy="430" r="90" class="a"/><path d="M390 432l28 28 54-58" fill="none" stroke-width="22" class="ln-w"/>
      <path d="M470 120l40-40M500 160h50M470 90V40" fill="none" stroke-width="14" class="ln-y"/>''',
    # 失敗の記録（ノートとペン）
    'notebook': '''<rect x="110" y="80" width="340" height="440" rx="24" class="a"/><rect x="140" y="80" width="310" height="440" rx="20" class="w"/>
      <g class="s"><rect x="180" y="150" width="230" height="12" rx="6"/><rect x="180" y="210" width="230" height="12" rx="6"/><rect x="180" y="270" width="230" height="12" rx="6"/><rect x="180" y="330" width="230" height="12" rx="6"/><rect x="180" y="390" width="230" height="12" rx="6"/></g>
      <path d="M180 200l22-22M180 178l22 22" fill="none" stroke-width="10" class="ln-k"/><path d="M180 316l14 14 26-28" fill="none" stroke-width="10" class="ln-a"/>
      <rect x="400" y="200" width="44" height="300" rx="10" transform="rotate(28 422 350)" class="y"/><path d="M455 470l40 60-60-20z" class="k"/>''',
    # フォーム営業（入力フォームと送信）
    'form': '''<rect x="70" y="90" width="360" height="420" rx="28" class="w"/><rect x="70" y="90" width="360" height="64" rx="28" class="a"/>
      <rect x="100" y="114" width="140" height="16" rx="8" class="w"/>
      <g class="s"><rect x="100" y="190" width="300" height="46" rx="10"/><rect x="100" y="260" width="300" height="46" rx="10"/><rect x="100" y="330" width="300" height="90" rx="10"/></g>
      <g class="k"><rect x="116" y="206" width="110" height="14" rx="7"/><rect x="116" y="276" width="150" height="14" rx="7"/><rect x="116" y="346" width="200" height="12" rx="6"/><rect x="116" y="372" width="160" height="12" rx="6"/></g>
      <rect x="250" y="440" width="150" height="46" rx="23" class="a"/><rect x="285" y="456" width="80" height="14" rx="7" class="w"/>
      <path d="M440 300l120-60-40 140-30-50z" class="y"/><path d="M490 330l70-90" fill="none" stroke-width="10" class="ln-k"/>''',
    # 点検・チェック（クリップボードと虫めがね）
    'check': '''<rect x="100" y="90" width="320" height="430" rx="26" class="w"/><rect x="200" y="62" width="120" height="56" rx="16" class="a"/>
      <g class="a"><rect x="130" y="170" width="40" height="40" rx="8"/><rect x="130" y="260" width="40" height="40" rx="8"/><rect x="130" y="350" width="40" height="40" rx="8"/></g>
      <path d="M138 190l10 10 16-18M138 280l10 10 16-18" fill="none" stroke-width="7" class="ln-w"/>
      <g class="s"><rect x="190" y="182" width="190" height="16" rx="8"/><rect x="190" y="272" width="170" height="16" rx="8"/><rect x="190" y="362" width="200" height="16" rx="8"/></g>
      <rect x="133" y="353" width="34" height="34" rx="6" class="w"/>
      <circle cx="430" cy="380" r="86" class="y"/><circle cx="430" cy="380" r="58" class="w"/><path d="M490 440l70 70" fill="none" stroke-width="34" class="ln-k"/>''',
    # Instagram DM（スマホと吹き出し）
    'phone': '''<rect x="170" y="50" width="260" height="500" rx="40" class="k"/><rect x="186" y="90" width="228" height="420" rx="14" class="w"/>
      <rect x="260" y="64" width="80" height="12" rx="6" class="s"/>
      <rect x="206" y="120" width="150" height="56" rx="20" class="s"/><rect x="246" y="196" width="150" height="76" rx="20" class="a"/>
      <rect x="206" y="292" width="120" height="50" rx="20" class="s"/><rect x="266" y="362" width="130" height="56" rx="20" class="a"/>
      <g class="w"><rect x="266" y="216" width="100" height="12" rx="6"/><rect x="266" y="238" width="70" height="12" rx="6"/><rect x="286" y="382" width="80" height="12" rx="6"/></g>
      <path d="M470 150c50 0 90 32 90 72s-40 72-90 72c-12 0-24-2-34-6l-40 22 12-38c-18-14-28-32-28-50 0-40 40-72 90-72z" class="y"/>
      <path d="M440 222a12 12 0 1 0 0.1 0M470 222a12 12 0 1 0 0.1 0M500 222a12 12 0 1 0 0.1 0" class="k"/>''',
    # Googleマップ集客（地図とピンと店）
    'map': '''<path d="M40 150l170-60 180 60 170-60v360l-170 60-180-60-170 60z" class="w"/>
      <path d="M210 90v360M390 150v360" fill="none" stroke-width="6" class="ln-s"/>
      <path d="M40 330c120-40 220 60 360 10s160-60 160-60" fill="none" stroke-width="22" class="ln-s"/>
      <rect x="90" y="380" width="120" height="80" rx="10" class="a"/><path d="M80 380h140l-14-36H94z" class="y"/><rect x="132" y="410" width="36" height="50" class="w"/>
      <path d="M380 70c-62 0-104 48-104 104 0 80 104 190 104 190s104-110 104-190c0-56-42-104-104-104z" class="a"/>
      <circle cx="380" cy="172" r="44" class="w"/><path d="M380 146l10 20 22 3-16 15 4 22-20-11-20 11 4-22-16-15 22-3z" class="y"/>''',
    # 口コミ（星と吹き出し）
    'review': '''<rect x="70" y="130" width="420" height="250" rx="34" class="w"/><path d="M140 380l-20 80 90-80z" class="w"/>
      <g class="y"><path d="M150 210l14 30 32 4-24 22 6 32-28-16-28 16 6-32-24-22 32-4z"/><path d="M250 210l14 30 32 4-24 22 6 32-28-16-28 16 6-32-24-22 32-4z"/><path d="M350 210l14 30 32 4-24 22 6 32-28-16-28 16 6-32-24-22 32-4z"/></g>
      <path d="M450 210l14 30 32 4-24 22 6 32-28-16-28 16 6-32-24-22 32-4z" class="s"/>
      <g class="s"><rect x="120" y="320" width="300" height="14" rx="7"/></g>
      <circle cx="480" cy="440" r="70" class="a"/><path d="M450 440h60M480 410v60" fill="none" stroke-width="16" class="ln-w"/>''',
    # お店の情報が勝手に変わった・停止（ピンと警告）
    'alert': '''<path d="M40 150l170-60 180 60 170-60v360l-170 60-180-60-170 60z" class="w"/>
      <path d="M210 90v360M390 150v360" fill="none" stroke-width="6" class="ln-s"/>
      <path d="M250 80c-62 0-104 48-104 104 0 80 104 190 104 190s104-110 104-190c0-56-42-104-104-104z" class="a"/>
      <circle cx="250" cy="182" r="44" class="w"/><rect x="226" y="176" width="48" height="12" rx="6" class="a"/>
      <path d="M440 250l110 190H330z" class="y"/><rect x="432" y="310" width="16" height="70" rx="8" class="k"/><circle cx="440" cy="408" r="11" class="k"/>
      <path d="M90 420c40-20 70 10 100-6" fill="none" stroke-width="12" class="ln-s"/>''',
    # 引越し（段ボールとトラック）
    'truck': '''<rect x="40" y="250" width="330" height="200" rx="16" class="a"/><path d="M370 300h110l70 80v70H370z" class="a"/>
      <path d="M392 320h80l46 54H392z" class="w"/>
      <circle cx="140" cy="460" r="46" class="k"/><circle cx="140" cy="460" r="18" class="w"/><circle cx="450" cy="460" r="46" class="k"/><circle cx="450" cy="460" r="18" class="w"/>
      <rect x="80" y="130" width="130" height="120" rx="8" class="y"/><path d="M80 170h130M145 130v40" fill="none" stroke-width="8" class="ln-k"/>
      <rect x="220" y="160" width="110" height="90" rx="8" class="s"/><path d="M220 192h110M275 160v32" fill="none" stroke-width="8" class="ln-a"/>
      <rect x="90" y="300" width="160" height="16" rx="8" class="w"/>''',
    # 部屋探し（鍵と建物）
    'key': '''<rect x="70" y="120" width="240" height="400" rx="14" class="a"/>
      <g class="w"><rect x="105" y="160" width="60" height="60" rx="8"/><rect x="215" y="160" width="60" height="60" rx="8"/><rect x="105" y="250" width="60" height="60" rx="8"/><rect x="215" y="250" width="60" height="60" rx="8"/><rect x="105" y="340" width="60" height="60" rx="8"/><rect x="215" y="340" width="60" height="60" rx="8"/></g>
      <rect x="160" y="430" width="60" height="90" class="y"/>
      <circle cx="430" cy="210" r="80" class="y"/><circle cx="430" cy="210" r="34" class="w"/>
      <path d="M430 290v230M430 420h50M430 470h70" fill="none" stroke-width="30" class="ln-y"/>
      <path d="M340 90l20-40M380 110l40-20" fill="none" stroke-width="12" class="ln-s"/>''',
    # 電気・ガス・水道（電球・炎・しずく）
    'utility': '''<circle cx="170" cy="170" r="96" class="y"/><rect x="132" y="252" width="76" height="56" rx="10" class="k"/><path d="M144 326h52" fill="none" stroke-width="14" class="ln-k"/>
      <path d="M178 120l-36 60h32l-12 50 40-66h-32z" class="w"/>
      <path d="M400 120c50 70 110 120 110 200 0 66-50 110-110 110s-110-44-110-110c0-40 20-70 40-90 0 40 20 60 40 60-10-60 0-110 30-170z" class="a"/>
      <path d="M400 300c20 30 40 46 40 72 0 24-18 40-40 40s-40-16-40-40c0-26 20-42 40-72z" class="y"/>
      <path d="M190 400c40 56 64 86 64 116a64 64 0 0 1-128 0c0-30 24-60 64-116z" class="a"/><path d="M168 500a24 24 0 0 0 24 24" fill="none" stroke-width="10" class="ln-w"/>''',
    # ネット回線（ルーターと電波）
    'wifi': '''<rect x="110" y="330" width="380" height="140" rx="30" class="a"/>
      <circle cx="170" cy="400" r="14" class="y"/><circle cx="220" cy="400" r="14" class="w"/><circle cx="270" cy="400" r="14" class="w"/>
      <rect x="350" y="390" width="100" height="20" rx="10" class="s"/>
      <path d="M170 330V230M430 330V230" fill="none" stroke-width="16" class="ln-k"/>
      <path d="M190 190a160 160 0 0 1 220 0M230 230a100 100 0 0 1 140 0" fill="none" stroke-width="26" class="ln-y"/>
      <circle cx="300" cy="275" r="22" class="y"/>
      <path d="M150 500h300" fill="none" stroke-width="12" class="ln-s"/>''',
    # 季節・段取り（カレンダー）
    'calendar': '''<rect x="80" y="110" width="380" height="380" rx="28" class="w"/><rect x="80" y="110" width="380" height="90" rx="28" class="a"/>
      <rect x="150" y="80" width="26" height="70" rx="13" class="k"/><rect x="364" y="80" width="26" height="70" rx="13" class="k"/>
      <g class="s"><rect x="120" y="230" width="60" height="50" rx="8"/><rect x="200" y="230" width="60" height="50" rx="8"/><rect x="280" y="230" width="60" height="50" rx="8"/><rect x="360" y="230" width="60" height="50" rx="8"/>
      <rect x="120" y="300" width="60" height="50" rx="8"/><rect x="280" y="300" width="60" height="50" rx="8"/><rect x="360" y="300" width="60" height="50" rx="8"/>
      <rect x="120" y="370" width="60" height="50" rx="8"/><rect x="200" y="370" width="60" height="50" rx="8"/><rect x="280" y="370" width="60" height="50" rx="8"/></g>
      <rect x="200" y="300" width="60" height="50" rx="8" class="y"/><rect x="360" y="370" width="60" height="50" rx="8" class="a"/>
      <circle cx="480" cy="460" r="70" class="y"/><path d="M480 420v44l28 18" fill="none" stroke-width="12" class="ln-k"/>''',
}

# タイトルの言葉 → 絵（上から順に見て、最初に当たったもの）。引越し（A11）は MOVING を先に見る
MOVING = [
    (r'お湯が出ない|開栓', 'utility'),
    (r'住所変更|転入届|郵便の転送', 'docs'),
    (r'部屋を決める', 'key'),
    (r'ネット|回線|Wi-?Fi', 'wifi'),
    (r'電気|ガス|水道|ライフライン|ウォーターサーバー', 'utility'),
    (r'部屋探し|仲介手数料|内見|物件|退去', 'key'),
    (r'3月|秋冬|繁忙期', 'calendar'),
    (r'引越し|見積もり|キャンセル', 'truck'),
]
RULES = [
    (r'勝手に変わ|停止|制限|再審査', 'alert'),
    (r'口コミ|レビュー|★', 'review'),
    (r'Googleマップ|MEO|ビジネスプロフィール|店舗が今日', 'map'),
    (r'Instagram|DM', 'phone'),
    (r'フォーム営業|問い合わせフォーム|文面', 'form'),
    (r'消されない|権限|安全|事故', 'shield'),
    (r'点検|SV|チェック', 'check'),
    (r'営業チーム|組織|人の', 'team'),
    (r'mistakes', 'notebook'),
    (r'CLAUDE\.md|review\.md|仕事の渡し方', 'docs'),
    (r'失敗|ミス', 'notebook'),
    (r'ルール', 'docs'),
]
FALLBACK = {'A01': 'team', 'A02': 'form', 'A03': 'map', 'A11': 'truck'}


def pick(title, acc):
    for pat, name in (MOVING if acc == 'A11' else []) + RULES:
        if re.search(pat, title):
            return name
    return FALLBACK.get(acc, 'docs')
