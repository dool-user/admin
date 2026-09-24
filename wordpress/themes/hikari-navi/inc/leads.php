<?php
/**
 * 内蔵申込フォーム: 受付・保存・メール通知・CSV出力.
 *
 * ページキャッシュ（WP Rocket等）と併用しても壊れないよう、nonceではなく
 * ハニーポット＋入力所要時間＋IP単位の連投制限でスパムを防ぐ。
 *
 * @package hikari-navi
 */

defined( 'ABSPATH' ) || exit;

/**
 * フォーム項目: key => [label, required].
 */
function hn_lead_fields() {
	return array(
		'type'    => array( 'お申し込み区分', true ),
		'house'   => array( 'お住まい', true ),
		'gift'    => array( 'ご希望の特典', true ),
		'name'    => array( 'お名前', true ),
		'tel'     => array( '電話番号', true ),
		'email'   => array( 'メールアドレス', true ),
		'zip'     => array( '郵便番号', false ),
		'address' => array( 'ご住所', true ),
		'time'    => array( 'ご連絡希望時間帯', false ),
		'message' => array( 'ご質問・ご要望', false ),
	);
}

function hn_handle_apply() {
	$back = home_url( '/' );
	$fail = function ( $code ) use ( $back ) {
		wp_safe_redirect( add_query_arg( 'form_error', $code, $back ) . '#apply' );
		exit;
	};

	// ハニーポット（botのみ入力する隠し項目）.
	if ( ! empty( $_POST['hn_website'] ) ) {
		$fail( 'spam' );
	}
	// ページ表示から3秒未満の送信はbotとみなす（経過時間はJSで計測）.
	$elapsed = isset( $_POST['hn_elapsed'] ) ? (int) $_POST['hn_elapsed'] : 0;
	if ( $elapsed < 3000 ) {
		$fail( 'spam' );
	}
	// 同一IPから10分に5件まで.
	$ip  = isset( $_SERVER['REMOTE_ADDR'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ) ) : '';
	$key = 'hn_rl_' . md5( $ip );
	$cnt = (int) get_transient( $key );
	if ( $cnt >= 5 ) {
		$fail( 'limit' );
	}

	$data = array();
	foreach ( hn_lead_fields() as $k => $f ) {
		$raw        = isset( $_POST[ $k ] ) ? wp_unslash( $_POST[ $k ] ) : '';
		$data[ $k ] = 'message' === $k ? sanitize_textarea_field( $raw ) : sanitize_text_field( $raw );
		if ( $f[1] && '' === $data[ $k ] ) {
			$fail( 'required' );
		}
	}
	if ( empty( $_POST['agree'] ) || ! is_email( $data['email'] ) || ! preg_match( '/^[0-9\-]{10,13}$/', $data['tel'] ) ) {
		$fail( 'invalid' );
	}

	set_transient( $key, $cnt + 1, 10 * MINUTE_IN_SECONDS );

	$post_id = wp_insert_post(
		array(
			'post_type'   => 'hn_lead',
			'post_status' => 'private',
			'post_title'  => wp_date( 'Y/m/d H:i' ) . ' ' . $data['name'] . '（' . $data['type'] . '）',
		)
	);
	if ( $post_id && ! is_wp_error( $post_id ) ) {
		foreach ( $data as $k => $v ) {
			update_post_meta( $post_id, 'hn_' . $k, $v );
		}
		update_post_meta( $post_id, 'hn_status', '未対応' );
		update_post_meta( $post_id, 'hn_referer', isset( $_POST['hn_ref'] ) ? esc_url_raw( wp_unslash( $_POST['hn_ref'] ) ) : '' );
	}

	// 通知メール.
	$body = '';
	foreach ( hn_lead_fields() as $k => $f ) {
		$body .= "【{$f[0]}】{$data[$k]}\n";
	}
	$to = hn_opt( 'notify_email' );
	$to = is_email( $to ) ? $to : get_option( 'admin_email' );
	wp_mail( $to, '【' . hn_opt( 'brand' ) . '】新しいお申し込みがありました', $body . "\n管理画面: " . admin_url( 'edit.php?post_type=hn_lead' ), array( 'Reply-To: ' . $data['email'] ) );

	if ( '1' === hn_opt( 'autoreply' ) ) {
		$reply  = "{$data['name']} 様\n\nこの度は" . hn_opt( 'brand' ) . "にお申し込みいただき、誠にありがとうございます。\n";
		$reply .= "担当者より1営業日以内にご連絡いたします。\n\n---- お申し込み内容 ----\n{$body}\n";
		$reply .= "お急ぎの方はお電話でもご連絡ください。\n" . hn_opt( 'tel' ) . '（受付 ' . hn_opt( 'tel_hours' ) . "）\n";
		wp_mail( $data['email'], '【' . hn_opt( 'brand' ) . '】お申し込みありがとうございます', $reply );
	}

	wp_safe_redirect( add_query_arg( 'sent', '1', $back ) . '#apply' );
	exit;
}
add_action( 'admin_post_nopriv_hn_apply', 'hn_handle_apply' );
add_action( 'admin_post_hn_apply', 'hn_handle_apply' );

/**
 * 申込一覧のカラム.
 */
add_filter(
	'manage_hn_lead_posts_columns',
	function () {
		return array(
			'cb'        => '<input type="checkbox" />',
			'title'     => '申込',
			'hn_status' => '対応状況',
			'hn_tel'    => '電話番号',
			'hn_email'  => 'メール',
			'hn_house'  => 'お住まい',
			'hn_gift'   => '特典',
			'date'      => '日時',
		);
	}
);
add_action(
	'manage_hn_lead_posts_custom_column',
	function ( $col, $post_id ) {
		echo esc_html( get_post_meta( $post_id, $col, true ) );
	},
	10,
	2
);

/**
 * 申込詳細メタボックス（対応状況・メモを編集可）.
 */
add_action(
	'add_meta_boxes_hn_lead',
	function () {
		remove_meta_box( 'postcustom', 'hn_lead', 'normal' );
		add_meta_box( 'hn_lead_detail', '申込内容', 'hn_lead_box', 'hn_lead', 'normal', 'high' );
	}
);

function hn_lead_box( $post ) {
	wp_nonce_field( 'hn_lead_save', 'hn_lead_nonce' );
	echo '<table class="widefat striped"><tbody>';
	foreach ( hn_lead_fields() as $k => $f ) {
		printf( '<tr><th style="width:180px">%s</th><td>%s</td></tr>', esc_html( $f[0] ), nl2br( esc_html( get_post_meta( $post->ID, 'hn_' . $k, true ) ) ) );
	}
	printf( '<tr><th>流入元</th><td>%s</td></tr>', esc_html( get_post_meta( $post->ID, 'hn_referer', true ) ) );
	$status = get_post_meta( $post->ID, 'hn_status', true );
	echo '<tr><th>対応状況</th><td><select name="hn_status">';
	foreach ( array( '未対応', '連絡済み', '申込完了', '開通済み', '特典送付済み', 'キャンセル' ) as $s ) {
		printf( '<option%s>%s</option>', selected( $status, $s, false ), esc_html( $s ) );
	}
	echo '</select></td></tr>';
	printf( '<tr><th>社内メモ</th><td><textarea name="hn_memo" rows="4" style="width:100%%">%s</textarea></td></tr>', esc_textarea( get_post_meta( $post->ID, 'hn_memo', true ) ) );
	echo '</tbody></table>';
}

add_action(
	'save_post_hn_lead',
	function ( $post_id ) {
		if ( ! isset( $_POST['hn_lead_nonce'] ) || ! wp_verify_nonce( sanitize_key( $_POST['hn_lead_nonce'] ), 'hn_lead_save' ) || ! current_user_can( 'edit_post', $post_id ) ) {
			return;
		}
		if ( isset( $_POST['hn_status'] ) ) {
			update_post_meta( $post_id, 'hn_status', sanitize_text_field( wp_unslash( $_POST['hn_status'] ) ) );
		}
		if ( isset( $_POST['hn_memo'] ) ) {
			update_post_meta( $post_id, 'hn_memo', sanitize_textarea_field( wp_unslash( $_POST['hn_memo'] ) ) );
		}
	}
);

/**
 * CSV出力（申込一覧の上部ボタン）.
 */
add_action(
	'manage_posts_extra_tablenav',
	function ( $which ) {
		if ( 'top' !== $which || 'hn_lead' !== get_current_screen()->post_type ) {
			return;
		}
		printf(
			'<a class="button" style="margin-left:6px" href="%s">CSVダウンロード</a>',
			esc_url( wp_nonce_url( admin_url( 'admin-post.php?action=hn_export_leads' ), 'hn_export' ) )
		);
	}
);

add_action(
	'admin_post_hn_export_leads',
	function () {
		if ( ! current_user_can( 'edit_others_posts' ) || ! check_admin_referer( 'hn_export' ) ) {
			wp_die( '権限がありません。' );
		}
		$keys = array_merge( array_keys( hn_lead_fields() ), array( 'status', 'memo', 'referer' ) );
		header( 'Content-Type: text/csv; charset=UTF-8' );
		header( 'Content-Disposition: attachment; filename="leads-' . wp_date( 'Ymd-His' ) . '.csv"' );
		$out = fopen( 'php://output', 'w' );
		fwrite( $out, "\xEF\xBB\xBF" ); // Excel用BOM.
		$labels = array_map(
			function ( $f ) {
				return $f[0];
			},
			hn_lead_fields()
		);
		fputcsv( $out, array_merge( array( '日時' ), array_values( $labels ), array( '対応状況', '社内メモ', '流入元' ) ), ",", "\"", "" );
		$posts = get_posts( array( 'post_type' => 'hn_lead', 'post_status' => 'any', 'numberposts' => -1 ) );
		foreach ( $posts as $p ) {
			$row = array( get_the_date( 'Y/m/d H:i', $p ) );
			foreach ( $keys as $k ) {
				$v = (string) get_post_meta( $p->ID, 'hn_' . $k, true );
				// CSVインジェクション対策.
				$row[] = preg_match( '/^[=+\-@\t\r]/', $v ) ? "'" . $v : $v;
			}
			fputcsv( $out, $row, ",", "\"", "" );
		}
		fclose( $out );
		exit;
	}
);
