<?php
/**
 * 投稿タイプ: よくある質問 / お客様の声 / 申込.
 *
 * @package hikari-navi
 */

defined( 'ABSPATH' ) || exit;

function hn_register_post_types() {
	$common = array(
		'public'        => false,
		'show_ui'       => true,
		'show_in_rest'  => true,
		'supports'      => array( 'title', 'editor', 'page-attributes' ),
		'menu_position' => 25,
	);

	register_post_type(
		'hn_faq',
		$common + array(
			'labels'    => array(
				'name'          => 'よくある質問',
				'singular_name' => 'よくある質問',
				'add_new_item'  => '質問を追加（タイトル＝質問、本文＝回答）',
			),
			'menu_icon' => 'dashicons-editor-help',
		)
	);

	register_post_type(
		'hn_voice',
		$common + array(
			'labels'    => array(
				'name'          => 'お客様の声',
				'singular_name' => 'お客様の声',
				'add_new_item'  => '声を追加（タイトル＝属性 例:30代・戸建て・新規、本文＝コメント）',
			),
			'menu_icon' => 'dashicons-format-quote',
		)
	);

	register_post_type(
		'hn_lead',
		array(
			'labels'          => array(
				'name'          => '申込一覧',
				'singular_name' => '申込',
				'edit_item'     => '申込内容',
			),
			'public'          => false,
			'show_ui'         => true,
			'show_in_rest'    => false,
			'supports'        => array( 'title', 'custom-fields' ),
			'menu_icon'       => 'dashicons-email-alt',
			'menu_position'   => 3,
			'capability_type' => 'post',
			'capabilities'    => array( 'create_posts' => 'do_not_allow' ),
			'map_meta_cap'    => true,
		)
	);
}
add_action( 'init', 'hn_register_post_types' );

/**
 * FAQ（未登録時はデフォルト）.
 *
 * @return array [ [question, answer_html], ... ]
 */
function hn_get_faqs() {
	$posts = get_posts( array( 'post_type' => 'hn_faq', 'numberposts' => 50, 'orderby' => 'menu_order date', 'order' => 'ASC' ) );
	if ( $posts ) {
		return array_map(
			function ( $p ) {
				return array( get_the_title( $p ), apply_filters( 'the_content', $p->post_content ) );
			},
			$posts
		);
	}
	$defaults = array(
		'キャッシュバックはいつ受け取れますか？'   => '開通を確認した月の翌月末〜最短2ヶ月以内にご案内いたします。受け取り手続きはご登録の口座情報をお知らせいただくだけです。',
		'有料オプションへの加入は必要ですか？'     => 'いいえ、当サイト独自特典はオプション加入を条件としておりません。',
		'今使っている回線から乗り換えできますか？' => 'はい。転用・事業者変更の場合、多くは工事不要で切り替えが可能です。現在ご利用中の回線をお知らせください。',
		'提供エリアを確認したいです。'             => 'お申し込みフォームに住所をご入力いただければ、担当者が無料で確認しご連絡いたします。',
		'工事にはどれくらい時間がかかりますか？'   => '通常1〜2時間程度です。立ち会いが必要な場合があります。お申し込みから開通までは約2〜4週間が目安です。',
		'解約時に違約金はかかりますか？'           => '契約プランにより異なります。お申し込み前に担当者より必ずご説明いたします。',
	);
	$out = array();
	foreach ( $defaults as $q => $a ) {
		$out[] = array( $q, '<p>' . esc_html( $a ) . '</p>' );
	}
	return $out;
}

/**
 * お客様の声（未登録時はサンプル）.
 *
 * @return array [ 'items' => [ [attr, text], ... ], 'sample' => bool ]
 */
function hn_get_voices() {
	$posts = get_posts( array( 'post_type' => 'hn_voice', 'numberposts' => 12, 'orderby' => 'menu_order date', 'order' => 'ASC' ) );
	if ( $posts ) {
		return array(
			'sample' => false,
			'items'  => array_map(
				function ( $p ) {
					return array( get_the_title( $p ), wp_strip_all_tags( $p->post_content ) );
				},
				$posts
			),
		);
	}
	return array(
		'sample' => true,
		'items'  => array(
			array( '30代・戸建て・新規', '電話で相談したら工事日の調整までしてくれて、とてもスムーズでした。キャッシュバックも案内どおり届きました。' ),
			array( '40代・マンション・乗り換え', '乗り換えで工事不要だったので、申し込みから1週間ほどで切り替え完了。オプション加入がないのも安心でした。' ),
			array( '20代・マンション・新規', '家電プレゼントでロボット掃除機を選びました。毎月の料金もスマホとのセット割で安くなりました。' ),
		),
	);
}
