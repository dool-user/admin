<?php
/**
 * LP本体（トップページ）.
 *
 * @package hikari-navi
 */

get_header();

$hn_tel    = hn_opt( 'tel' );
$hn_points = array( hn_opt( 'point1' ), hn_opt( 'point2' ), hn_opt( 'point3' ) );
$hn_voices = hn_get_voices();
$hn_icons  = array(
	'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.1-.4-.4-2.1z"/></svg>',
	'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 6.5h11v9.5h-11zM13.5 10h4l3.5 3.5V16h-7.5"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/></svg>',
	'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/></svg>'
);
$hn_error  = isset( $_GET['form_error'] ) ? sanitize_key( $_GET['form_error'] ) : ''; // phpcs:ignore WordPress.Security.NonceVerification
$hn_sent   = isset( $_GET['sent'] ); // phpcs:ignore WordPress.Security.NonceVerification
$hn_errmsg = array(
	'required' => '未入力の必須項目があります。',
	'invalid'  => '電話番号・メールアドレスの形式、または同意チェックをご確認ください。',
	'spam'     => '送信できませんでした。お手数ですが、少し時間をおいて再度お試しください。',
	'limit'    => '短時間に送信が集中しています。お電話でお問い合わせください。',
);
$hn_prices = array(
	'house'   => array( '戸建てタイプ', hn_opt( 'price_house_1g' ), hn_opt( 'price_house_10g' ), '動画・テレワークに十分な速度', 'ゲーム・大容量通信に最適' ),
	'mansion' => array( 'マンションタイプ', hn_opt( 'price_mansion_1g' ), hn_opt( 'price_mansion_10g' ), '集合住宅向けプラン', '※対応物件のみ' ),
);
?>
<main>
<!-- ===== ファーストビュー ===== -->
<section class="hero">
  <div class="hero__inner">
    <div class="hero__head">
      <p class="hero__badge"><?php echo esc_html( hn_opt( 'hero_badge' ) ); ?></p>
      <h1 class="hero__title">
        <span class="hero__sub">光回線のお申し込みで</span>
        <span class="hero__main"><span class="hero__max">最大</span><strong><?php echo esc_html( hn_yen( hn_opt( 'max_cashback' ) ) ); ?></strong><em>円</em></span>
        <span class="hero__main2">キャッシュバック<i>!</i></span>
      </h1>
      <p class="hero__or"><span class="hero__or-tag">または</span>最新家電プレゼントから選べる!</p>
    </div>
    <div class="hero-art">
<?php get_template_part( 'template-parts/hero-illust' ); ?>
    </div>
    <div class="hero__foot">
      <ul class="hero__points">
<?php
        foreach ( $hn_points as $hn_i => $hn_p ) :
            $hn_pp = array_pad( explode( '|', $hn_p ), 2, '' );
            ?>
        <li><span class="hero__ico"><?php echo $hn_icons[ $hn_i % 3 ]; // phpcs:ignore WordPress.Security.EscapeOutput -- 固定SVG ?></span><span><b><?php echo esc_html( $hn_pp[0] ); ?></b><?php echo esc_html( $hn_pp[1] ); ?></span></li>
        <?php endforeach; ?>
      </ul>
      <div class="hero__cta">
        <a href="#apply" class="btn btn--primary btn--lg">Webで今すぐ申し込む<small>24時間受付・最短3分</small></a>
        <a href="<?php echo esc_attr( hn_tel_href() ); ?>" class="btn btn--tel btn--lg" data-track="tel">電話で申し込む<small><?php echo esc_html( $hn_tel ); ?></small></a>
      </div>
      <p class="note"><?php echo esc_html( hn_opt( 'cp_note' ) ); ?></p>
    </div>
  </div>
</section>

<!-- ===== 選ばれる理由 ===== -->
<section class="section reasons" id="reasons">
  <div class="container">
    <h2 class="section__title"><span>REASON</span><?php echo esc_html( hn_opt( 'brand' ) ); ?>が選ばれる<em>3つの理由</em></h2>
    <div class="reasons__grid">
      <article class="reason">
        <div class="reason__num">01</div>
        <h3>業界最高水準の特典</h3>
        <p>公式キャンペーンに加え、当サイト独自のキャッシュバックを上乗せ。面倒なオプション加入は一切不要です。</p>
      </article>
      <article class="reason">
        <div class="reason__num">02</div>
        <h3>特典のお届けが早い</h3>
        <p>開通確認後、最短2ヶ月でお届け。申請忘れで受け取れない…といった複雑な手続きもありません。</p>
      </article>
      <article class="reason">
        <div class="reason__num">03</div>
        <h3>専門スタッフが丁寧サポート</h3>
        <p>エリア確認・工事日の調整・プロバイダ選びまで、光回線に詳しいスタッフが無料でご案内します。</p>
      </article>
    </div>
  </div>
</section>

<!-- ===== キャンペーン ===== -->
<section class="section campaign" id="campaign">
  <div class="container">
    <h2 class="section__title"><span>CAMPAIGN</span>選べる<em>2つの特典</em></h2>
    <div class="campaign__grid">
      <div class="cp-card cp-card--cash">
        <div class="cp-card__label">特典A</div>
        <h3>現金キャッシュバック</h3>
        <p class="cp-card__amount">最大<strong><?php echo esc_html( hn_yen( hn_opt( 'max_cashback' ) ) ); ?></strong>円</p>
        <ul class="check">
          <li>指定口座へお振込み</li>
          <li>開通月の翌月末までにご案内</li>
          <li>オプション加入条件なし</li>
        </ul>
      </div>
      <div class="cp-card cp-card--gift">
        <div class="cp-card__label">特典B</div>
        <h3>最新家電プレゼント</h3>
        <p class="cp-card__amount">お好きな<strong>1点</strong>を選べる</p>
        <ul class="gifts">
          <?php foreach ( hn_rows( 'gifts' ) as $hn_g ) : ?>
            <li><span class="gift-ico"><?php echo esc_html( $hn_g[0] ); ?></span><?php echo esc_html( isset( $hn_g[1] ) ? $hn_g[1] : '' ); ?></li>
          <?php endforeach; ?>
        </ul>
      </div>
    </div>

    <h3 class="sub-title">サービス別キャッシュバック額</h3>
    <div class="table-wrap">
      <table class="cp-table">
        <thead><tr><th>サービス</th><th>新規</th><th>乗り換え（転用・事業者変更）</th><th>スマホセット割</th></tr></thead>
        <tbody>
          <?php
          foreach ( hn_rows( 'cp_table' ) as $hn_r ) :
              $hn_r   = array_pad( $hn_r, 5, '' );
              $hn_pop = '1' === $hn_r[4];
              ?>
            <tr<?php echo $hn_pop ? ' class="is-pickup"' : ''; ?>>
              <th><?php echo esc_html( $hn_r[0] ); ?><?php echo $hn_pop ? ' <span class="tag">人気</span>' : ''; ?></th>
              <td><?php echo is_numeric( $hn_r[1] ) ? '<b>' . esc_html( hn_yen( $hn_r[1] ) ) . '円</b>' : esc_html( $hn_r[1] ); ?></td>
              <td><?php echo is_numeric( $hn_r[2] ) ? '<b>' . esc_html( hn_yen( $hn_r[2] ) ) . '円</b>' : esc_html( $hn_r[2] ); ?></td>
              <td><?php echo esc_html( $hn_r[3] ); ?></td>
            </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
    </div>
    <p class="note"><?php echo esc_html( hn_opt( 'cp_note' ) ); ?></p>
  </div>
</section>

<!-- ===== 中間CTA ===== -->
<section class="cta-band">
  <div class="container cta-band__inner">
    <p class="cta-band__text">＼ 提供エリア確認・お見積りは <b>無料</b> ／</p>
    <div class="hero__cta">
      <a href="#apply" class="btn btn--primary btn--lg">Webで申し込む<small>24時間受付</small></a>
      <a href="<?php echo esc_attr( hn_tel_href() ); ?>" class="btn btn--tel btn--lg" data-track="tel">電話で相談する<small><?php echo esc_html( $hn_tel ); ?></small></a>
    </div>
  </div>
</section>

<!-- ===== 料金 ===== -->
<section class="section price" id="price">
  <div class="container">
    <h2 class="section__title"><span>PRICE</span>月額<em>料金</em></h2>
    <div class="tabs" role="tablist">
      <?php $hn_first = true; foreach ( $hn_prices as $hn_k => $hn_v ) : ?>
        <button class="tabs__btn<?php echo $hn_first ? ' is-active' : ''; ?>" role="tab" data-tab="<?php echo esc_attr( $hn_k ); ?>" aria-selected="<?php echo $hn_first ? 'true' : 'false'; ?>"><?php echo esc_html( $hn_v[0] ); ?></button>
      <?php $hn_first = false; endforeach; ?>
    </div>
    <?php $hn_first = true; foreach ( $hn_prices as $hn_k => $hn_v ) : ?>
      <div class="tabs__panel<?php echo $hn_first ? ' is-active' : ''; ?>" id="tab-<?php echo esc_attr( $hn_k ); ?>">
        <div class="price__grid">
          <div class="price-card"><h3>1ギガプラン</h3><p class="price-card__val"><strong><?php echo esc_html( hn_yen( $hn_v[1] ) ); ?></strong>円<small>/月(税込)</small></p><p>最大通信速度 1Gbps<br><?php echo esc_html( $hn_v[3] ); ?></p></div>
          <div class="price-card price-card--rec"><span class="ribbon">おすすめ</span><h3>10ギガプラン</h3><p class="price-card__val"><strong><?php echo esc_html( hn_yen( $hn_v[2] ) ); ?></strong>円<small>/月(税込)</small></p><p>最大通信速度 10Gbps<br><?php echo esc_html( $hn_v[4] ); ?></p></div>
        </div>
      </div>
    <?php $hn_first = false; endforeach; ?>
    <dl class="price__extra">
      <div><dt>初期工事費</dt><dd><?php echo wp_kses( hn_opt( 'price_setup' ), array( 'b' => array() ) ); ?></dd></div>
      <div><dt>契約事務手数料</dt><dd><?php echo wp_kses( hn_opt( 'price_fee' ), array( 'b' => array() ) ); ?></dd></div>
      <div><dt>Wi-Fiルーター</dt><dd><?php echo wp_kses( hn_opt( 'price_router' ), array( 'b' => array() ) ); ?></dd></div>
    </dl>
    <p class="note">※最大通信速度はベストエフォートであり、実際の速度を保証するものではありません。</p>
  </div>
</section>

<!-- ===== 開通までの流れ ===== -->
<section class="section flow" id="flow">
  <div class="container">
    <h2 class="section__title"><span>FLOW</span>お申し込みから<em>開通までの流れ</em></h2>
    <ol class="flow__list">
      <li><div class="flow__step">STEP<b>1</b></div><h3>お申し込み</h3><p>Webフォームまたはお電話で。所要時間は最短3分です。</p></li>
      <li><div class="flow__step">STEP<b>2</b></div><h3>確認のご連絡</h3><p>担当者よりエリア確認とご希望工事日のご連絡をいたします。</p></li>
      <li><div class="flow__step">STEP<b>3</b></div><h3>開通工事</h3><p>工事は約1〜2時間。乗り換えの場合、工事不要なケースもあります。</p></li>
      <li><div class="flow__step">STEP<b>4</b></div><h3>特典お受け取り</h3><p>開通確認後、最短2ヶ月でキャッシュバック・家電をお届け。</p></li>
    </ol>
  </div>
</section>

<!-- ===== お客様の声 ===== -->
<section class="section voice">
  <div class="container">
    <h2 class="section__title"><span>VOICE</span>ご利用者の<em>声</em></h2>
    <?php if ( $hn_voices['sample'] && current_user_can( 'edit_posts' ) ) : ?>
      <p class="note center">【管理者のみ表示】サンプルを表示中です。管理画面「お客様の声」から実際の声を登録してください。</p>
    <?php endif; ?>
    <div class="voice__grid">
      <?php foreach ( $hn_voices['items'] as $hn_vc ) : ?>
        <blockquote class="voice-card"><p><?php echo esc_html( $hn_vc[1] ); ?></p><footer><?php echo esc_html( $hn_vc[0] ); ?></footer></blockquote>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<!-- ===== FAQ ===== -->
<section class="section faq" id="faq">
  <div class="container container--narrow">
    <h2 class="section__title"><span>FAQ</span>よくある<em>質問</em></h2>
    <div class="faq__list">
      <?php foreach ( hn_get_faqs() as $hn_f ) : ?>
        <details><summary><?php echo esc_html( $hn_f[0] ); ?></summary><div><?php echo wp_kses_post( $hn_f[1] ); ?></div></details>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<!-- ===== 申込フォーム ===== -->
<section class="section apply" id="apply">
  <div class="container container--narrow">
    <h2 class="section__title"><span>ENTRY</span>Web<em>お申し込み</em>フォーム</h2>

    <?php if ( $hn_sent ) : ?>
      <div class="form__done" id="formDone" data-sent="1">
        <h3>お申し込みありがとうございます</h3>
        <p>担当者より1営業日以内にご連絡いたします。<br>ご登録のメールアドレスに確認メールをお送りしました。</p>
      </div>
    <?php elseif ( hn_opt( 'cf7_shortcode' ) ) : ?>
      <p class="center">以下をご入力のうえ送信してください。担当者より<b>1営業日以内</b>にご連絡いたします。</p>
      <div class="form"><?php echo do_shortcode( hn_opt( 'cf7_shortcode' ) ); ?></div>
    <?php else : ?>
      <p class="center">以下をご入力のうえ送信してください。担当者より<b>1営業日以内</b>にご連絡いたします。</p>
      <?php get_template_part( 'template-parts/form' ); ?>
      <?php if ( $hn_error && isset( $hn_errmsg[ $hn_error ] ) ) : ?>
        <script>document.addEventListener('DOMContentLoaded',function(){var e=document.getElementById('formError');e.textContent=<?php echo wp_json_encode( $hn_errmsg[ $hn_error ] ); ?>;e.hidden=false;});</script>
      <?php endif; ?>
    <?php endif; ?>
  </div>
</section>
</main>
<?php
get_footer();
