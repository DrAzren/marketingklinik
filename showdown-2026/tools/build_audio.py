"""Build the 75 s soundtrack: re-cut ElevenLabs score + voiceover + synthesised SFX.

- The score (media/music/score.mp3, 120 BPM, 2 s bars) is re-cut on bar lines so
  each musical section lands on its scene (MUSIC_MAP).
- Voiceover lines (media/vo_prep/voN.wav) are placed at VO_AT and the music is
  ducked underneath them.
- SFX (ticks, heartbeat, whooshes, impacts, beeps, risers, sub drops) are
  synthesised here from oscillators/noise: original and royalty-free.

    python3 showdown-2026/tools/build_audio.py  ->  showdown-2026/audio/mix.wav
"""
import json, pathlib, subprocess, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
SR = 48000
DUR = 75.0
N = int(SR * DUR)
rng = np.random.default_rng(2026)
T = json.loads((ROOT / "timeline.json").read_text())


def load(path, ch=2):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).astype(np.float64)


music = np.zeros((N, 2)); vo = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def place(buf, sig, at, gain=1.0, pan=0.0):
    if sig.ndim == 1:
        sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)) * 1.414, sig * np.sqrt(0.5 * (1 + pan)) * 1.414], 1)
    i = int(round(at * SR))
    if i >= N: return
    j = min(N, i + len(sig))
    buf[i:j] += sig[: j - i] * gain


# ---------------- music re-cut ----------------
score = load(ROOT / "media/music/score.mp3")
XF = int(0.03 * SR)
for dest, s0, s1, fade_out in T["music_map"]:
    seg = score[int(s0 * SR): int(s1 * SR)].copy()
    ramp = np.linspace(0, 1, XF)[:, None]
    seg[:XF] *= ramp
    fo = int(fade_out * SR) if fade_out else XF
    seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
    place(music, seg, dest)

# ---------------- voiceover ----------------
vo_env = np.zeros(N)
for k, at in T["vo_at"].items():
    v = load(ROOT / f"media/vo_prep/vo{k}.wav", ch=1)[:, 0]
    place(vo, v, at, gain=1.0)
    i = int(at * SR); vo_env[i:i + len(v)] = np.maximum(vo_env[i:i + len(v)], (np.abs(v) > 0.003))

# smooth the ducking envelope (attack 120 ms, release 450 ms)
def smooth(e, att, rel):
    out = np.empty_like(e); acc = 0.0
    a1, a2 = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    for idx in range(0, len(e), 48):           # block-wise for speed
        tgt = e[idx:idx + 48].max()
        a = a1 if tgt > acc else a2
        acc = tgt + (acc - tgt) * a ** 48
        out[idx:idx + 48] = acc
    return out
duck = smooth(vo_env, 0.12, 0.45)
music *= (1 - 0.62 * duck)[:, None]          # about -8.4 dB under speech

# ---------------- SFX synthesis ----------------
def t_(d): return np.arange(int(SR * d)) / SR
def noise(d): return rng.standard_normal(int(SR * d))
def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc = (1 - a) * v + a * acc; y[i] = acc
    return y
def hp(x, fc): return x - lp(x, fc)

def tick(gain=1.0):
    d = 0.05; t = t_(d)
    s = hp(noise(d), 2500) * np.exp(-t / 0.006) * 0.6 + np.sin(2 * np.pi * 3100 * t) * np.exp(-t / 0.01) * 0.25
    return s * gain
def heartbeat():
    out = np.zeros(int(SR * 0.6))
    for off, g in ((0, 1.0), (0.22, 0.7)):
        t = t_(0.25); s = np.sin(2 * np.pi * (55 - 20 * t) * t) * np.exp(-t / 0.07) * g
        i = int(off * SR); out[i:i + len(s)] += s
    return out
def impact(d=2.5, f=48):
    t = t_(d)
    body = np.sin(2 * np.pi * (f * (1 + 2.5 * np.exp(-t / 0.05))) * t) * np.exp(-t / 0.55)
    crack = lp(noise(d), 1800) * np.exp(-t / 0.08) * 1.4
    return np.tanh((body + crack) * 1.4) * 0.8
def metal(d=1.6):
    t = t_(d); s = np.zeros_like(t)
    for f, dec in ((523, 0.5), (1187, 0.35), (1973, 0.25), (2711, 0.18), (3349, 0.12)):
        s += np.sin(2 * np.pi * f * t) * np.exp(-t / dec)
    s += hp(noise(d), 3000) * np.exp(-t / 0.02) * 2
    return s * 0.18
def whoosh(d=0.9, up=True):
    t = t_(d); n = noise(d)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    # sweep a simple band by mixing two lowpasses
    lo, hi = lp(n, 600), lp(n, 4000)
    mixr = (t / d) if up else (1 - t / d)
    return ((1 - mixr) * lo + mixr * (hi - lo) * 1.5) * env * 0.5
def beep(f=1760, d=0.09):
    t = t_(d); return np.sign(np.sin(2 * np.pi * f * t)) * 0.12 * np.exp(-t / 0.04) + np.sin(2 * np.pi * f * 2 * t) * 0.05 * np.exp(-t / 0.03)
def riser(d=2.0):
    t = t_(d); f = 200 * (12 ** (t / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15
    return (tone + hp(noise(d), 1500) * 0.25 * (t / d) ** 2) * (t / d) ** 1.5
def sub_drop(d=3.0):
    t = t_(d); f = 70 * np.exp(-t / 0.9) + 28
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.1) * 0.9
def glitch(d=0.25):
    t = t_(d); s = np.sign(np.sin(2 * np.pi * 220 * t * (1 + 8 * (t * 37 % 1)))) * 0.08
    return s * (rng.random(len(t)) > 0.35) * np.exp(-t / 0.15)
def shatter(d=1.8):
    t = t_(d); s = hp(noise(d), 4000) * np.exp(-t / 0.35) * 0.5
    for k in range(40):
        at = rng.random() * 0.8; i = int(at * SR); f = 2500 + rng.random() * 5000; tt = t_(0.08)
        p = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.02) * 0.15
        s[i:i + len(p)] += p[: len(s) - i]
    return s

FX = {"tick": tick, "heartbeat": heartbeat, "impact": impact, "metal": metal, "whoosh": whoosh,
      "beep": beep, "riser": riser, "sub": sub_drop, "glitch": glitch, "shatter": shatter}
for at, name, gain, pan, *kw in T["sfx"]:
    sig = FX[name](**(kw[0] if kw else {}))
    place(sfx, sig, at, gain=gain, pan=pan)

# ---------------- mix ----------------
mix = music * 0.9 + vo * 1.55 + sfx * 0.8
mix = np.tanh(mix * 0.95) / np.tanh(0.95)          # soft clip
# final 0.6 s fade-out
fo = int(0.6 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = ROOT / "audio"; out.mkdir(exist_ok=True)
pre = out / "_premix.wav"
with wave.open(str(pre), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
# loudness: two-pass loudnorm to -14 LUFS / -1.5 dBTP
import re
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
m = json.loads(r[r.rfind("{"): r.rfind("}") + 1])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", af, "-ar", str(SR), str(out / "mix.wav")], check=True)
pre.unlink()
print("wrote", out / "mix.wav")
