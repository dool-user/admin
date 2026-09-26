"""
ナレーション音声の生成（Kokoro TTS / 日本語女性音声 jf_alpha）
「読み上げ感」を減らすため、次の工夫をしています。
  - 話し言葉のセリフを1文ずつ合成し、文ごとに話す速さを変える（前置きは速く、要点は少しゆっくり）
  - 文と文の間を毎回少しずつ変える
  - 読み変換は Kokoro 標準の cutlet 方式（辞書は unidic-lite）
  - 仕上げでスマホ自撮り風の音にする（短い部屋の響き・かすかな環境音・EQ）→ build.sh 側
使い方:
  pip install kokoro-onnx soundfile "misaki[ja]" unidic-lite
  （pip の unidic パッケージが入っている場合はアンインストールする。unidic-lite を使わせるため）
  kokoro-v1.0.onnx と voices-v1.0.bin を
  https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 から取得して同じフォルダに置く
  python narration.py   → vo_track_a.wav / vo_track_b.wav / vo_track_c.wav を出力
"""
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from misaki import ja

SR = 24000
rng = np.random.default_rng(7)
g2p = ja.JAG2P()  # cutlet 方式
tts = Kokoro('kokoro-v1.0.onnx', 'voices-v1.0.bin')

# 1文ごとに (テキスト, 速さ)
LINES={
 'hook_a':[('え、待って。',1.12),('引越し初日なのに、電気つかないんだけど！？',1.12)],
 'hook_b':[('引越し初日の夜。',1.08),('あれ？',1.02),('電気つかないんだけど。',1.1)],
 'hook_c':[('ねえねえ、',1.05),('引越し予定の人。',1.12),('これ忘れると、電気つかないよ？',1.08)],
 'cause': [('原因はこれ。',1.2),('電気の使用開始の申し込み。',1.02),('これほんと、忘れがちなんだよね。',1.2)],
 'hassle':[('しかもさ、',1.3),('ガスも水道もネットも、連絡先ぜんぶバラバラ。',1.15),('正直、めんどくない？',1.08)],
 'solve': [('でもね、',1.25),('まとめて頼めるところがあるの。',1.08),('相談無料だし、土日もオッケー。',1.15)],
 'cta':   [('引越し予定の人は、',1.18),('今のうちにチェックしといてね！',1.1)],
}

# シーンの区切り（video_*.html の S と同じ値にする）
TIMELINE = {"a": [[0, 4.2], [4.2, 9.7], [9.7, 15.8], [15.8, 21.3], [21.3, 25.4]], "b": [[0, 4.3], [4.3, 9.8], [9.8, 15.9], [15.9, 21.4], [21.4, 25.5]], "c": [[0, 4.8], [4.8, 10.3], [10.3, 16.4], [16.4, 21.9], [21.9, 26.0]]}


def synth(text, speed):
    ps, _ = g2p(text)
    audio, _ = tts.create(ps, voice='jf_alpha', speed=speed, is_phonemes=True)
    return audio.astype('float32')


def trim(a, th=0.008):
    idx = np.where(np.abs(a) > th)[0]
    return a[max(0, idx[0] - int(.02 * SR)):idx[-1] + int(.06 * SR)] if len(idx) else a


def line(key):
    out = []
    for i, (text, speed) in enumerate(LINES[key]):
        if i:
            out.append(np.zeros(int(SR * rng.uniform(.08, .22)), dtype='float32'))  # 毎回ちがう間
        out.append(trim(synth(text, speed)))
    return np.concatenate(out)


# 部屋の響き（短い残響）
n = int(.28 * SR); t = np.arange(n) / SR
ir = rng.standard_normal(n) * np.exp(-t / 0.07) * 0.35; ir[0] = 1.0
for d, g in [(.011, .35), (.019, .25), (.027, .18)]:
    ir[int(d * SR)] += g
ir /= np.abs(ir).sum() ** .5

for v, S in TIMELINE.items():
    buf = np.zeros(int(SR * S[-1][1]), dtype='float32')
    for key, at in [(f'hook_{v}', .12), ('cause', S[1][0] + .1), ('hassle', S[2][0] + .1), ('solve', S[3][0] + .1), ('cta', S[4][0] + .1)]:
        a = line(key); i = int(at * SR); buf[i:i + len(a)] += a[:len(buf) - i]
    wet = np.convolve(buf, ir)[:len(buf)]
    mixed = .82 * buf + .18 * wet / (np.abs(wet).max() + 1e-9) * np.abs(buf).max()
    sf.write(f'vo_track_{v}.wav', mixed.astype('float32'), SR)
print('done')
