<?php
/**
 * Footer.
 *
 * @package hikari-navi
 */

?>
<footer class="footer">
  <div class="container">
    <div class="footer__tel">
      <p>お電話でのお申し込み・ご相談（通話無料）</p>
      <a href="<?php echo esc_attr( hn_tel_href() ); ?>" data-track="tel"><?php echo esc_html( hn_opt( 'tel' ) ); ?></a>
      <small>受付時間 <?php echo esc_html( hn_opt( 'tel_hours' ) ); ?></small>
    </div>
    <?php
    if ( has_nav_menu( 'footer' ) ) {
        wp_nav_menu(
            array(
                'theme_location' => 'footer',
                'container'      => 'nav',
                'container_class'=> 'footer__nav',
                'items_wrap'     => '%3$s',
                'depth'          => 1,
            )
        );
    } else {
        echo '<nav class="footer__nav">';
        $privacy = get_privacy_policy_url();
        if ( $privacy ) {
            printf( '<a href="%s">プライバシーポリシー</a>', esc_url( $privacy ) );
        }
        echo '</nav>';
    }
    ?>
    <p class="footer__legal"><?php echo wp_kses( nl2br( hn_opt( 'company' ) ), array( 'br' => array(), 'b' => array() ) ); ?></p>
    <p class="footer__copy">&copy; <?php echo esc_html( wp_date( 'Y' ) . ' ' . hn_opt( 'brand' ) ); ?> All Rights Reserved.</p>
  </div>
</footer>

<?php if ( is_front_page() ) : ?>
<div class="fixed-cta" id="fixedCta">
  <a href="<?php echo esc_attr( hn_tel_href() ); ?>" class="fixed-cta__tel" data-track="tel">📞 電話で申込</a>
  <a href="#apply" class="fixed-cta__web">Webで申込 ›</a>
</div>
<?php endif; ?>

<?php wp_footer(); ?>
</body>
</html>
