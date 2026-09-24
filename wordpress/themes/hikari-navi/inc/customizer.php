<?php
/**
 * カスタマイザー（外観 > カスタマイズ > LP設定）.
 *
 * @package hikari-navi
 */

defined( 'ABSPATH' ) || exit;

/**
 * 設定項目の定義: key => [label, default, type, section].
 */
function hn_fields() {
	return array(
		// 基本情報.
		'brand'            => array( 'サイト名（ロゴ表示）', 'ヒカリナビ', 'text', 'basic' ),
		'brand_sub'        => array( 'ロゴ下の小見出し', '光回線 正規販売代理店', 'text', 'basic' ),
		'tel'              => array( '電話番号', '0120-000-000', 'text', 'basic' ),
		'tel_hours'        => array( '電話受付時間', '10:00〜19:00（日曜・年末年始除く）', 'text', 'basic' ),
		'company'          => array( '運営会社表記（フッター）', '株式会社〇〇〇〇 ／ 電気通信事業届出番号 A-00-00000 ／ 〇〇〇〇 正規販売代理店', 'textarea', 'basic' ),
		'meta_description' => array( 'meta description', '光回線の新規・乗り換えなら正規販売代理店のヒカリナビ。最大80,000円キャッシュバック、または最新家電プレゼント。工事費実質無料、最短2ヶ月で特典お届け。', 'textarea', 'basic' ),

		// キャンペーン.
		'hero_badge'       => array( 'FV上部バッジ', '新規・乗り換え・プロバイダ変更 すべて対象', 'text', 'campaign' ),
		'max_cashback'     => array( '最大キャッシュバック額（円・数字）', '80000', 'text', 'campaign' ),
		'point1'           => array( 'FV訴求1（強調|補足）', '工事費|実質無料', 'text', 'campaign' ),
		'point2'           => array( 'FV訴求2（強調|補足）', '最短2ヶ月|で特典お届け', 'text', 'campaign' ),
		'point3'           => array( 'FV訴求3（強調|補足）', 'オプション|加入不要', 'text', 'campaign' ),
		'cp_table'         => array(
			'サービス別キャッシュバック表（1行1サービス：サービス名|新規|乗り換え|セット割|人気なら1）',
			"光回線A（戸建て）|60000|40000|—|\n光回線A（マンション）|50000|30000|—|\n光コラボB|80000|50000|キャリアA|1\n光コラボC|70000|45000|キャリアB|\n光コラボD|55000|35000|キャリアC|",
			'textarea',
			'campaign',
		),
		'gifts'            => array( 'プレゼント家電（1行1つ：絵文字|名前）', "📺|液晶テレビ\n🎮|ゲーム機\n💻|タブレット\n🧹|ロボット掃除機\n☕|コーヒーメーカー\n🔊|スマートスピーカー", 'textarea', 'campaign' ),
		'cp_note'          => array( 'キャンペーン注記', '※特典額はサービス・プラン・お申し込み条件により異なります。詳しくはキャンペーン規約をご確認ください。', 'textarea', 'campaign' ),

		// 料金.
		'price_house_1g'   => array( '戸建て 1ギガ（円/月）', '5720', 'text', 'price' ),
		'price_house_10g'  => array( '戸建て 10ギガ（円/月）', '6380', 'text', 'price' ),
		'price_mansion_1g' => array( 'マンション 1ギガ（円/月）', '4180', 'text', 'price' ),
		'price_mansion_10g'=> array( 'マンション 10ギガ（円/月）', '5500', 'text', 'price' ),
		'price_setup'      => array( '初期工事費', '22,000円 → <b>実質0円</b>', 'text', 'price' ),
		'price_fee'        => array( '契約事務手数料', '3,300円', 'text', 'price' ),
		'price_router'     => array( 'Wi-Fiルーター', '<b>無料レンタル</b>', 'text', 'price' ),

		// フォーム・計測.
		'cf7_shortcode'    => array( 'Contact Form 7 ショートコード（空欄ならテーマ内蔵フォーム）', '', 'text', 'form' ),
		'notify_email'     => array( '申込通知の送信先メール（空欄なら管理者メール）', '', 'text', 'form' ),
		'autoreply'        => array( '自動返信メールを送る（1=送る／0=送らない）', '1', 'text', 'form' ),
		'gtm_id'           => array( 'Googleタグマネージャー ID（GTM-XXXX）', '', 'text', 'form' ),
	);
}

/**
 * 設定値を取得.
 *
 * @param string $key Field key.
 * @return string
 */
function hn_opt( $key ) {
	$fields  = hn_fields();
	$default = isset( $fields[ $key ] ) ? $fields[ $key ][1] : '';
	return (string) get_theme_mod( 'hn_' . $key, $default );
}

/**
 * 1行1レコードの "a|b|c" 形式を配列に.
 *
 * @param string $key Field key.
 * @return array
 */
function hn_rows( $key ) {
	$rows = array();
	foreach ( preg_split( '/\r\n|\r|\n/', hn_opt( $key ) ) as $line ) {
		if ( '' !== trim( $line ) ) {
			$rows[] = array_map( 'trim', explode( '|', $line ) );
		}
	}
	return $rows;
}

/**
 * Register customizer.
 *
 * @param WP_Customize_Manager $wp_customize Manager.
 */
function hn_customize_register( $wp_customize ) {
	$wp_customize->add_panel( 'hn_panel', array( 'title' => 'LP設定', 'priority' => 20 ) );
	$sections = array(
		'basic'    => '基本情報・電話番号',
		'campaign' => 'キャンペーン・特典',
		'price'    => '料金',
		'form'     => 'フォーム・計測タグ',
	);
	foreach ( $sections as $id => $title ) {
		$wp_customize->add_section( 'hn_' . $id, array( 'title' => $title, 'panel' => 'hn_panel' ) );
	}
	foreach ( hn_fields() as $key => $f ) {
		$wp_customize->add_setting(
			'hn_' . $key,
			array(
				'default'           => $f[1],
				'sanitize_callback' => 'textarea' === $f[2] ? 'hn_sanitize_textarea' : 'hn_sanitize_text',
			)
		);
		$wp_customize->add_control(
			'hn_' . $key,
			array(
				'label'   => $f[0],
				'section' => 'hn_' . $f[3],
				'type'    => $f[2],
			)
		);
	}
}
add_action( 'customize_register', 'hn_customize_register' );

/**
 * 強調用の <b> のみ許可.
 *
 * @param string $v Value.
 * @return string
 */
function hn_sanitize_text( $v ) {
	return wp_kses( trim( (string) $v ), array( 'b' => array(), 'br' => array() ) );
}

function hn_sanitize_textarea( $v ) {
	return wp_kses( (string) $v, array( 'b' => array(), 'br' => array() ) );
}
