<?php
/**
 * Header.
 *
 * @package hikari-navi
 */

$hn_home = is_front_page() ? '' : home_url( '/' );
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<header class="header">
  <div class="header__inner">
    <a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="logo">
      <?php if ( has_custom_logo() ) : ?>
        <?php echo wp_get_attachment_image( get_theme_mod( 'custom_logo' ), 'full', false, array( 'class' => 'logo__img', 'alt' => hn_opt( 'brand' ) ) ); ?>
      <?php else : ?>
        <span class="logo__mark"><?php echo esc_html( mb_substr( hn_opt( 'brand' ), 0, 1 ) ); ?></span>
      <?php endif; ?>
      <span class="logo__text"><?php echo esc_html( hn_opt( 'brand' ) ); ?><small><?php echo esc_html( hn_opt( 'brand_sub' ) ); ?></small></span>
    </a>
    <nav class="gnav" id="gnav">
      <a href="<?php echo esc_url( $hn_home ); ?>#campaign">キャンペーン</a>
      <a href="<?php echo esc_url( $hn_home ); ?>#price">料金</a>
      <a href="<?php echo esc_url( $hn_home ); ?>#flow">開通までの流れ</a>
      <a href="<?php echo esc_url( $hn_home ); ?>#faq">よくある質問</a>
      <a href="<?php echo esc_url( $hn_home ); ?>#apply" class="gnav__cta">Web申込</a>
    </nav>
    <a href="<?php echo esc_attr( hn_tel_href() ); ?>" class="header__tel" data-track="tel">
      <span class="header__tel-label">お電話でのお申し込み・ご相談</span>
      <span class="header__tel-num"><?php echo esc_html( hn_opt( 'tel' ) ); ?></span>
      <span class="header__tel-time">受付 <?php echo esc_html( hn_opt( 'tel_hours' ) ); ?></span>
    </a>
    <button class="menu-btn" id="menuBtn" aria-label="メニュー" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</header>
