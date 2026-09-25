/**
 * LP 運用設定
 * 電話番号・受付時間・フォーム送信先・エリア情報はすべてここで管理します。
 * 本番公開前に「★要変更」の項目を必ず差し替えてください。
 */
window.LP_CONFIG = {
  // サービス名・運営会社
  brand: {
    name: 'でんき開通サポート',
    company: 'グラハムコミュニケーションズ株式会社',
    address: '〒162-0801 東京都新宿区山吹町346-6 KAGURAZAKA VIGAS 5F',
    url: 'https://grahamcommunications.co.jp/',
    license: '（★要変更：取次・代理の根拠となる契約先事業者名や登録・届出番号を正確に記載）',
  },

  // ★要変更：電話番号（通常 / 夜間。?tel=yakan で夜間番号に切替）
  tel: {
    default: { display: '0120-000-000', href: '0120000000', label: '受付 9:00〜20:00（年中無休）' },
    yakan:   { display: '0120-111-111', href: '0120111111', label: '夜間も受付中 20:00〜翌9:00' },
  },

  // 通常番号の受付時間（この時間外は電話ボタンを「Webで受付」優先に自動切替）
  businessHours: { start: 9, end: 20 },

  // ★要変更：フォーム送信先（空のままならデモモードで thanks.html へ遷移）
  // 例）Google Apps Script のWebアプリURL、Formspree、自社API など
  formEndpoint: '',
  thanksUrl: '../thanks.html',

  // 対応エリア（ファーストビューと「ご依頼いただける地域」に表示）
  serviceArea: ['東京都', '神奈川県', '埼玉県', '千葉県', '茨城県', '群馬県', '栃木県'],

  // エリア別設定。/tokyo/ /kanagawa/ などディレクトリ名で切り替え
  areas: {
    tokyo: { name: '東京都', short: '東京' },
  },
};
