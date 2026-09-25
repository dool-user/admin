"""
ナレーション音声の生成（Kokoro TTS / 日本語女性音声 jf_alpha）
使い方:
  pip install kokoro-onnx soundfile "misaki[ja]"
  kokoro-v1.0.onnx と voices-v1.0.bin を
  https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 から取得して同じフォルダに置く
  python narration.py   → vo_track_a.wav / vo_track_b.wav / vo_track_c.wav を出力
"""
import re
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from misaki import ja

VOICE, SPEED, SR, TOTAL = 'jf_alpha', 1.18, 24000, 21.0
LINES = {
    'hook_a': '引越し初日の夜、電気つかないんだけど！？',
    'hook_b': '引越し初日の夜。……え、電気つかない。',
    'hook_c': '引越し予定の人、これ忘れると電気つかないよ。',
    'cause': '原因これ。電気の使用開始の申し込み、忘れがちなんだよね。',
    'hassle': 'しかもガスも水道もネットも、連絡先ぜんぶバラバラ。正直めんどい。',
    'solve': 'でも、まとめて頼めるところあるの。相談無料で、土日もオーケー。',
    'cta': '引越し予定の人は、今のうちにチェックしといて！',
}
# 動画のシーン開始（video_*.html の S と合わせる）＋0.1秒で読み始める
START = {'cause': 3.7, 'hassle': 8.0, 'solve': 12.8, 'cta': 17.3}

g2p = ja.JAG2P(version='pyopenjtalk')
tts = Kokoro('kokoro-v1.0.onnx', 'voices-v1.0.bin')


def phonemes(text):
    ps, _ = g2p(text)
    # 末尾の高低記号を外し、モデルの記号表にない文字を置き換える（g→ɡ、ᶉ→ɾj）
    return re.sub(r'[_\-\^j]+$', '', ps).replace('g', 'ɡ').replace('ᶉ', 'ɾj')


def clip(key):
    audio, _ = tts.create(phonemes(LINES[key]), voice=VOICE, speed=SPEED, is_phonemes=True)
    return audio.astype('float32')


for v in 'abc':
    buf = np.zeros(int(SR * TOTAL), dtype='float32')
    for key, at in [(f'hook_{v}', 0.12)] + list(START.items()):
        a = clip(key)
        i = int(at * SR)
        buf[i:i + len(a)] += a[:len(buf) - i]
    sf.write(f'vo_track_{v}.wav', buf, SR)
print('done')
