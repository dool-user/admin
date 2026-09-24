<?php
/**
 * Hikari Navi LP theme.
 *
 * @package hikari-navi
 */

defined( 'ABSPATH' ) || exit;

define( 'HN_VERSION', '1.0.0' );

require get_template_directory() . '/inc/customizer.php';
require get_template_directory() . '/inc/post-types.php';
require get_template_directory() . '/inc/leads.php';

/**
 * Theme setup.
 */
function hn_setup() {
	add_theme_support( 'title-tag' );
	add_theme_support( 'custom-logo', array( 'height' => 80, 'width' => 240, 'flex-width' => true ) );
	add_theme_support( 'html5', array( 'search-form', 'gallery', 'caption', 'style', 'script' ) );
	register_nav_menus( array( 'footer' => 'フッターメニュー' ) );
}
add_action( 'after_setup_theme', 'hn_setup' );

/**
 * Assets.
 */
function hn_enqueue() {
	wp_enqueue_style( 'hn-fonts', 'https://fonts.googleapis.com/css2?family=Montserrat:wght@800&family=Noto+Sans+JP:wght@400;500;700;900&display=swap', array(), null );
	wp_enqueue_style( 'hn-main', get_template_directory_uri() . '/assets/css/main.css', array(), HN_VERSION );
	wp_enqueue_script( 'hn-main', get_template_directory_uri() . '/assets/js/main.js', array(), HN_VERSION, true );
}
add_action( 'wp_enqueue_scripts', 'hn_enqueue' );

/**
 * Google Tag Manager (カスタマイザーでID設定時のみ出力).
 */
function hn_gtm_head() {
	$id = hn_opt( 'gtm_id' );
	if ( ! $id ) {
		return;
	}
	?>
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','<?php echo esc_js( $id ); ?>');</script>
	<?php
}
add_action( 'wp_head', 'hn_gtm_head', 1 );

function hn_gtm_body() {
	$id = hn_opt( 'gtm_id' );
	if ( $id ) {
		printf( '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=%s" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>', esc_attr( $id ) );
	}
}
add_action( 'wp_body_open', 'hn_gtm_body' );

/**
 * Meta description / OGP (SEOプラグイン未導入時のみ).
 */
function hn_meta() {
	if ( defined( 'WPSEO_VERSION' ) || class_exists( 'SEO_SIMPLE_PACK' ) || defined( 'RANK_MATH_VERSION' ) ) {
		return;
	}
	$desc = hn_opt( 'meta_description' );
	if ( ! is_front_page() || ! $desc ) {
		return;
	}
	printf( '<meta name="description" content="%s">' . "\n", esc_attr( $desc ) );
	printf( '<meta property="og:title" content="%s">' . "\n", esc_attr( wp_get_document_title() ) );
	printf( '<meta property="og:description" content="%s">' . "\n", esc_attr( $desc ) );
	echo '<meta property="og:type" content="website">' . "\n";
	printf( '<meta property="og:url" content="%s">' . "\n", esc_url( home_url( '/' ) ) );
}
add_action( 'wp_head', 'hn_meta', 2 );

/**
 * Helpers.
 */
function hn_tel_href() {
	return 'tel:' . preg_replace( '/[^0-9+]/', '', hn_opt( 'tel' ) );
}

function hn_yen( $n ) {
	return number_format( (int) preg_replace( '/[^0-9]/', '', (string) $n ) );
}
