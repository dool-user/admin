<?php
/**
 * 内蔵申込フォーム.
 *
 * @package hikari-navi
 */

$hn_privacy = get_privacy_policy_url();
?>
<form class="form" id="applyForm" method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" novalidate>
  <input type="hidden" name="action" value="hn_apply">
  <input type="hidden" name="hn_elapsed" value="0">
  <input type="hidden" name="hn_ref" value="">
  <div class="hn-hp" aria-hidden="true"><label>Website<input type="text" name="hn_website" tabindex="-1" autocomplete="off"></label></div>

  <div class="form__row">
    <label>お申し込み区分<span class="req">必須</span></label>
    <div class="radios">
      <label><input type="radio" name="type" value="新規" checked> 新規</label>
      <label><input type="radio" name="type" value="乗り換え"> 乗り換え</label>
      <label><input type="radio" name="type" value="まずは相談"> まずは相談</label>
    </div>
  </div>
  <div class="form__row">
    <label>お住まい<span class="req">必須</span></label>
    <div class="radios">
      <label><input type="radio" name="house" value="戸建て" checked> 戸建て</label>
      <label><input type="radio" name="house" value="マンション・アパート"> マンション・アパート</label>
    </div>
  </div>
  <div class="form__row">
    <label>ご希望の特典<span class="req">必須</span></label>
    <div class="radios">
      <label><input type="radio" name="gift" value="キャッシュバック" checked> キャッシュバック</label>
      <label><input type="radio" name="gift" value="家電プレゼント"> 家電プレゼント</label>
    </div>
  </div>
  <div class="form__row">
    <label for="f-name">お名前<span class="req">必須</span></label>
    <input id="f-name" name="name" type="text" placeholder="例）山田 太郎" required autocomplete="name">
  </div>
  <div class="form__row">
    <label for="f-tel">電話番号<span class="req">必須</span></label>
    <input id="f-tel" name="tel" type="tel" placeholder="例）09012345678" required pattern="[0-9\-]{10,13}" autocomplete="tel">
  </div>
  <div class="form__row">
    <label for="f-mail">メールアドレス<span class="req">必須</span></label>
    <input id="f-mail" name="email" type="email" placeholder="例）info@example.com" required autocomplete="email">
  </div>
  <div class="form__row">
    <label for="f-zip">郵便番号<span class="opt">任意</span></label>
    <input id="f-zip" name="zip" type="text" placeholder="例）1000001" inputmode="numeric" autocomplete="postal-code">
  </div>
  <div class="form__row">
    <label for="f-addr">ご住所<span class="req">必須</span></label>
    <input id="f-addr" name="address" type="text" placeholder="例）東京都千代田区〇〇1-2-3" required autocomplete="street-address">
  </div>
  <div class="form__row">
    <label for="f-time">ご連絡希望時間帯<span class="opt">任意</span></label>
    <select id="f-time" name="time">
      <option>いつでも可</option><option>10:00〜12:00</option><option>12:00〜15:00</option><option>15:00〜17:00</option><option>17:00〜19:00</option>
    </select>
  </div>
  <div class="form__row">
    <label for="f-msg">ご質問・ご要望<span class="opt">任意</span></label>
    <textarea id="f-msg" name="message" rows="4" placeholder="現在ご利用中の回線など"></textarea>
  </div>
  <div class="form__agree">
    <label><input type="checkbox" name="agree" value="1" required>
      <?php if ( $hn_privacy ) : ?>
        <a href="<?php echo esc_url( $hn_privacy ); ?>" target="_blank" rel="noopener">個人情報の取り扱い</a>に同意する
      <?php else : ?>
        個人情報の取り扱いに同意する
      <?php endif; ?>
    </label>
  </div>
  <p class="form__error" id="formError" role="alert" hidden></p>
  <button type="submit" class="btn btn--primary btn--lg btn--block">入力内容を送信する</button>
</form>
