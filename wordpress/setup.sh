#!/usr/bin/env bash
# WordPress 初期セットアップ（テーマ有効化・プラグイン導入・必須ページ作成）
#
# 使い方:
#   本番サーバー（wp-cli が使える環境。エックスサーバー/ConoHa WING 等はSSHで利用可）:
#     ./setup.sh
#   ローカル Docker:
#     docker compose up -d && WP="docker compose run --rm cli wp" ./setup.sh --install
#
# オプション:
#   --install        WordPress 本体のインストールも行う（ローカル用）
#   --no-plugins     プラグインを入れない
set -euo pipefail

WP=${WP:-wp}
URL=${URL:-http://localhost:8080}
TITLE=${TITLE:-ヒカリナビ}
ADMIN_USER=${ADMIN_USER:-admin}
ADMIN_PASS=${ADMIN_PASS:-change-me-$(date +%s)}
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}

INSTALL=0; PLUGINS=1
for a in "$@"; do
  case $a in
    --install) INSTALL=1 ;;
    --no-plugins) PLUGINS=0 ;;
  esac
done

if [ "$INSTALL" = 1 ] && ! $WP core is-installed 2>/dev/null; then
  $WP core install --url="$URL" --title="$TITLE" --admin_user="$ADMIN_USER" \
    --admin_password="$ADMIN_PASS" --admin_email="$ADMIN_EMAIL" --skip-email
  echo "管理者: $ADMIN_USER / $ADMIN_PASS （ログイン後に必ず変更してください）"
  # 環境によってURLにパスが付くことがあるため明示的に設定
  $WP option update home "$URL" >/dev/null
  $WP option update siteurl "$URL" >/dev/null
  # 初期サンプル投稿・ページを削除
  $WP post delete 1 2 --force >/dev/null 2>&1 || true
fi

# 日本語化・タイムゾーン・パーマリンク
$WP language core install ja --activate || true
$WP option update timezone_string 'Asia/Tokyo'
$WP option update date_format 'Y/m/d'
$WP option update blog_public 1
$WP rewrite structure '/%postname%/' --hard

# テーマ
$WP theme activate hikari-navi

# プラグイン
if [ "$PLUGINS" = 1 ]; then
  # 必須
  $WP plugin install --activate \
    wp-mail-smtp \
    seo-simple-pack \
    siteguard \
    updraftplus \
    ewww-image-optimizer
  # 任意（必要に応じてコメントアウトを外す）
  # $WP plugin install --activate contact-form-7   # 内蔵フォームの代わりにCF7を使う場合
  # $WP plugin install --activate litespeed-cache  # LiteSpeedサーバー（ConoHa WING等）の場合
  # $WP plugin install --activate google-site-kit  # GA4/Search Console連携
fi

# ページ作成（既にあればスキップ）
# slug のページが無ければ作成、下書き（WP初期の Privacy Policy 等）なら内容を入れて公開。
# 公開済みページは編集済みの可能性があるので触らない。
create_page () { # slug title content
  local id status
  # post list --name は未ログイン扱いだと下書きを返さないため get_page_by_path で探す
  id=$($WP eval "\$p = get_page_by_path( '$1' ); echo \$p ? \$p->ID : '';")
  if [ -z "$id" ]; then
    $WP post create --post_type=page --post_status=publish --post_name="$1" --post_title="$2" --post_content="$3" --porcelain
    return
  fi
  status=$($WP post get "$id" --field=post_status)
  if [ "$status" != "publish" ]; then
    $WP post update "$id" --post_status=publish --post_title="$2" --post_content="$3" >/dev/null
  fi
  echo "$id"
}

HOME_ID=$(create_page home "トップページ" "")
PRIVACY_ID=$(create_page privacy-policy "プライバシーポリシー" "<!-- wp:paragraph --><p>【要編集】株式会社〇〇〇〇（以下「当社」）は、お客様の個人情報を以下のとおり取り扱います。</p><!-- /wp:paragraph --><!-- wp:heading --><h2>利用目的</h2><!-- /wp:heading --><!-- wp:paragraph --><p>光回線サービスのお申し込み受付、ご連絡、キャンペーン特典のお届けのために利用します。</p><!-- /wp:paragraph --><!-- wp:heading --><h2>第三者提供</h2><!-- /wp:heading --><!-- wp:paragraph --><p>お申し込み手続きに必要な範囲で、回線事業者・プロバイダへ提供します。法令に基づく場合を除き、それ以外の第三者へは提供しません。</p><!-- /wp:paragraph --><!-- wp:heading --><h2>お問い合わせ窓口</h2><!-- /wp:heading --><!-- wp:paragraph --><p>【要編集】電話番号・メールアドレス・住所</p><!-- /wp:paragraph -->")
TOKUSHO_ID=$(create_page tokushoho "特定商取引法に基づく表記" "<!-- wp:table --><figure class=\"wp-block-table\"><table><tbody><tr><th>販売業者</th><td>【要編集】</td></tr><tr><th>運営責任者</th><td>【要編集】</td></tr><tr><th>所在地</th><td>【要編集】</td></tr><tr><th>電話番号</th><td>【要編集】</td></tr><tr><th>電気通信事業届出番号</th><td>【要編集】</td></tr><tr><th>料金・契約条件</th><td>各サービスの提供条件に準じます。</td></tr></tbody></table></figure><!-- /wp:table -->")
COMPANY_ID=$(create_page company "運営会社" "<!-- wp:paragraph --><p>【要編集】会社概要</p><!-- /wp:paragraph -->")
TERMS_ID=$(create_page campaign-terms "キャンペーン規約" "<!-- wp:paragraph --><p>【要編集】特典の適用条件・受取方法・受取期限・対象外となる条件を記載してください。</p><!-- /wp:paragraph -->")

$WP option update show_on_front page
$WP option update page_on_front "$HOME_ID"
$WP option update wp_page_for_privacy_policy "$PRIVACY_ID"

# フッターメニュー
if ! $WP menu list --fields=name --format=csv | grep -q '^フッター$'; then
  $WP menu create "フッター"
  for id in $COMPANY_ID $PRIVACY_ID $TOKUSHO_ID $TERMS_ID; do
    $WP menu item add-post "フッター" "$id"
  done
  $WP menu location assign "フッター" footer
fi

echo
echo "✅ セットアップ完了: $URL"
echo "   次にやること: 管理画面 > 外観 > カスタマイズ > LP設定 で電話番号・特典額・会社情報を入力"
