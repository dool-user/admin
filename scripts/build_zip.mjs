// 郵便番号データ（lp/assets/zip/*.json）を作り直す
//   日本郵便「郵便番号データ（読み仮名データの促音・拗音を小書きで表記するもの）」を収録した
//   npm パッケージ jp-postal（MIT）から、上2桁ごとの JSON を生成する。
// 使い方：
//   npm install --no-save jp-postal@latest && node scripts/build_zip.mjs
// 出力形式： { "下5桁": ["都道府県", "市区町村", "町域"] }（町域が特定できない番号は2要素）
import fs from 'fs';
import path from 'path';
import postal from 'jp-postal';

const out = path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'lp', 'assets', 'zip');
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });

// 「以下に掲載がない場合」「〇〇村一円」などは町域なし、（ ）内の補足は削除
const cleanTown = (t) => {
  if (/以下に掲載がない場合|次に番地がくる場合/.test(t) || /一円$/.test(t)) return '';
  return t.replace(/[（(].*$/, '');
};

const groups = {};
for (const [zip, rows] of Object.entries(postal)) {
  const [pref, city] = rows[0];
  const sameCity = rows.every((r) => r[0] === pref && r[1] === city);
  const towns = [...new Set(rows.map((r) => cleanTown(r[2])))];
  const town = sameCity && towns.length === 1 ? towns[0] : '';
  (groups[zip.slice(0, 2)] ||= {})[zip.slice(2)] = town ? [pref, city, town] : [pref, sameCity ? city : ''];
}

for (const [g, map] of Object.entries(groups)) fs.writeFileSync(path.join(out, g + '.json'), JSON.stringify(map));
console.log(Object.keys(groups).length + ' files, ' + Object.keys(postal).length + ' codes');
