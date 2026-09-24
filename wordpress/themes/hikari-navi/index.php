<?php
/**
 * 汎用テンプレート（プライバシーポリシー・特商法表記・会社概要などの固定ページ用）.
 *
 * @package hikari-navi
 */

get_header();
?>
<main class="section page">
  <div class="container container--narrow">
    <?php
    while ( have_posts() ) :
        the_post();
        ?>
      <article <?php post_class( 'page__body' ); ?>>
        <h1 class="page__title"><?php the_title(); ?></h1>
        <div class="entry"><?php the_content(); ?></div>
      </article>
    <?php endwhile; ?>
    <?php if ( ! have_posts() ) : ?>
      <p class="center">ページが見つかりませんでした。</p>
    <?php endif; ?>
    <p class="center"><a class="btn btn--primary" href="<?php echo esc_url( home_url( '/' ) ); ?>">トップへ戻る</a></p>
  </div>
</main>
<?php
get_footer();
