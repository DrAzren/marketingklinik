"""Soundtrack for The Final Piece briefing (101 s).

- Music: the original score made for the teaser (ElevenLabs Music, re-used, no new
  credits) re-cut on its 2 s bar grid into the scene lengths (timeline.json music_map:
  dest, src_in, src_out, fade_out, gain).
- Narration: media/vo_prep/lNN.wav at timeline.json vo_at, music ducked ~11 dB under it.
- SFX: synthesised here (ticks, UI beeps, holo sweeps, mechanical opening, impacts,
  error buzzer, victory sting, sub drop). Original and royalty-free.

    python3 tools/build_audio.py  ->  audio/mix.wav (-14 LUFS, -1.5 dBTP)
"""
import json, pathlib, subprocess, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
T = json.loads((ROOT / "timeline.json").read_text())
SR = 48000
DUR = T["duration"]
N = int(SR * DUR)
rng = np.random.default_rng(2501)


def load(path, ch=2):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).astype(np.float64)


music = np.zeros((N, 2)); vo = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def place(buf, sig, at, gain=1.0, pan=0.0):
    if sig.ndim == 1:
        sig = np.stack([sig * np.sqrt(1 - pan), sig * np.sqrt(1 + pan)], 1)
    i = int(round(at * SR))
    if i >= N: return
    j = min(N, i + len(sig))
    buf[i:j] += sig[: j - i] * gain


score = load(ROOT / "media/score.mp3")
XF = int(0.03 * SR)
for dest, s0, s1, fade, gain in T["music_map"]:
    seg = score[int(s0 * SR): int(s1 * SR)].copy()
    seg[:XF] *= np.linspace(0, 1, XF)[:, None]
    fo = int(fade * SR) if fade else XF
    seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
    place(music, seg * gain, dest)

vo_env = np.zeros(N)
for k, at in T["vo_at"].items():
    v = load(ROOT / f"media/vo_prep/l{int(k):02d}.wav", ch=1)[:, 0]
    place(vo, v, at)
    i = int(at * SR); vo_env[i:i + len(v)] = 1.0          # duck for the whole line, pauses included


def smooth(e, att, rel, blk=48):
    out = np.empty_like(e); acc = 0.0
    a1, a2 = np.exp(-blk / (att * SR)), np.exp(-blk / (rel * SR))
    for idx in range(0, len(e), blk):
        tgt = e[idx:idx + blk].max()
        acc = tgt + (acc - tgt) * (a1 if tgt > acc else a2)
        out[idx:idx + blk] = acc
    return out
music *= (1 - 0.72 * smooth(vo_env, 0.25, 0.6))[:, None]   # about -11 dB under narration


# ---------------- SFX ----------------
def t_(d): return np.arange(int(SR * d)) / SR
def noise(d): return rng.standard_normal(int(SR * d))
def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc = (1 - a) * v + a * acc; y[i] = acc
    return y
def hp(x, fc): return x - lp(x, fc)

def tick(g=1.0):
    t = t_(0.05); return (hp(noise(0.05), 2500) * np.exp(-t / 0.006) * 0.6 + np.sin(2 * np.pi * 3100 * t) * np.exp(-t / 0.01) * 0.25) * g
def beep(f=1760, d=0.09):
    t = t_(d); return np.sin(2 * np.pi * f * t) * 0.22 * np.exp(-t / 0.05) + np.sin(2 * np.pi * f * 2 * t) * 0.06 * np.exp(-t / 0.03)
def blip2(f=1320):
    out = np.zeros(int(SR * 0.2)); a = beep(f, 0.07); b = beep(f * 1.5, 0.08)
    out[:len(a)] += a; out[int(0.09 * SR):int(0.09 * SR) + len(b)] += b; return out
def holo(d=0.7):
    t = t_(d); f = 400 + 2600 * (t / d) ** 2
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.08 * np.sin(np.pi * t / d) + hp(noise(d), 5000) * 0.05 * np.sin(np.pi * t / d)
def impact(d=2.5, f=48):
    t = t_(d)
    body = np.sin(2 * np.pi * (f * (1 + 2.5 * np.exp(-t / 0.05))) * t) * np.exp(-t / 0.55)
    return np.tanh((body + lp(noise(d), 1800) * np.exp(-t / 0.08) * 1.4) * 1.4) * 0.8
def mech(d=1.4):
    t = t_(d); s = lp(noise(d), 900) * (0.4 + 0.6 * (np.sin(2 * np.pi * 9 * t) > 0)) * np.exp(-t / 0.6) * 0.5
    for at in (0.0, 0.35, 0.9):
        i = int(at * SR); k = metal(0.6); s[i:i + len(k)] += k[: len(s) - i] * 0.8
    return s
def metal(d=1.2):
    t = t_(d); s = np.zeros_like(t)
    for f, dec in ((523, 0.4), (1187, 0.3), (1973, 0.2), (2711, 0.14)): s += np.sin(2 * np.pi * f * t) * np.exp(-t / dec)
    return (s + hp(noise(d), 3000) * np.exp(-t / 0.02) * 2) * 0.16
def whoosh(d=0.6):
    t = t_(d); n = noise(d); env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return (lp(n, 600) * (1 - t / d) + (lp(n, 4000) - lp(n, 600)) * 1.5 * (t / d)) * env * 0.45
def buzzer(d=0.7):
    t = t_(d); s = np.sign(np.sin(2 * np.pi * 110 * t)) * 0.18 + np.sign(np.sin(2 * np.pi * 116 * t)) * 0.12
    gate = ((t % 0.25) < 0.2).astype(float)
    return lp(s * gate, 2500) * np.exp(-t / 1.2)
def victory():
    out = np.zeros(int(SR * 2.2))
    for k, (f, at) in enumerate(((523.3, 0), (659.3, 0.11), (784, 0.22), (1046.5, 0.36))):
        d = 1.8 - at; t = t_(d)
        tone = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) + 0.2 * np.sin(2 * np.pi * 3 * f * t)) * np.exp(-t / 0.9) * 0.12
        i = int(at * SR); out[i:i + len(tone)] += tone
    return out
def riser(d=2.0):
    t = t_(d); f = 200 * (12 ** (t / d))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.13 + hp(noise(d), 1500) * 0.22 * (t / d) ** 2) * (t / d) ** 1.5
def sub(d=3.0):
    t = t_(d); f = 70 * np.exp(-t / 0.9) + 28
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.1) * 0.9

def shatter_fx(d=1.6):
    t = t_(d); s = hp(noise(d), 4000) * np.exp(-t / 0.3) * 0.45
    for k in range(30):
        at = rng.random() * 0.7; i = int(at * SR); f = 2500 + rng.random() * 5000; tt = t_(0.08)
        p = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.02) * 0.15
        s[i:i + len(p)] += p[: len(s) - i]
    return s
def heartbeat():
    out = np.zeros(int(SR * 0.6))
    for off, g in ((0, 1.0), (0.22, 0.7)):
        t = t_(0.25); s = np.sin(2 * np.pi * (55 - 20 * t) * t) * np.exp(-t / 0.07) * g
        i = int(off * SR); out[i:i + len(s)] += s
    return out
def cloth(d=1.2):
    t = t_(d); return lp(noise(d), 1200) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5 * 0.5
def scribble(d=0.5):
    t = t_(d); return hp(noise(d), 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t)) * 0.12

def click(g=1.0):
    t = t_(0.04); return (hp(noise(0.04), 3000) * np.exp(-t / 0.004) * 0.7 + np.sin(2 * np.pi * 1800 * t) * np.exp(-t / 0.008) * 0.3) * g

S = []
S += [(0.0, impact, 0.6, 0), (0.6, tick, 0.7, 0), (1.1, tick, 0.6, 0), (1.0, holo, 0.6, 0), (2.4, mech, 0.6, 0)]
S += [(3.4, impact, 0.8, 0), (3.4, shatter_fx, 0.8, 0), (4.8, impact, 0.8, 0), (4.85, metal, 0.7, 0), (7.4, blip2, 0.5, 0)]
S += [(13.3, whoosh, 0.8, 0), (13.9, impact, 0.5, -0.6), (14.4, impact, 0.5, 0.6), (15.6, metal, 0.8, 0), (15.6, impact, 0.8, 0), (17.0, blip2, 0.6, 0), (18.4, blip2, 0.6, 0)]
S += [(21.9, whoosh, 0.8, 0), (22.4, mech, 0.7, 0), (23.0, beep, 0.5, 0), (24.5, beep, 0.5, 0), (26.0, beep, 0.5, 0)]
S += [(26.6, click, 0.9, 0), (27.6, click, 0.9, 0), (28.4, buzzer, 0.25, 0), (29.2, click, 0.9, 0), (30.0, click, 0.9, 0), (31.0, click, 0.9, 0), (31.8, victory, 0.6, 0)]
S += [(33.9, whoosh, 0.8, 0), (34.3, beep, 0.8, 0, ), (35.0, beep, 0.8, 0), (35.7, beep, 0.8, 0), (36.4, impact, 0.9, 0), (36.4, blip2, 0.9, 0)]
S += [(37.0 + k * 0.5, tick, 0.4, 0) for k in range(22)] + [(37.4 + k * 0.62, click, 0.6, -0.6 + 1.2 * (k % 2)) for k in range(16)]
S += [(47.9, whoosh, 0.7, 0), (48.4, holo, 0.6, 0), (51.0, buzzer, 0.45, 0.4), (53.2, buzzer, 0.45, 0.4), (55.3, shatter_fx, 0.5, 0.4), (56.6, buzzer, 0.45, 0.4), (58.6, mech, 0.5, 0.4), (59.3, buzzer, 0.4, 0.4), (60.2, blip2, 0.5, 0)]
S += [(61.5, whoosh, 0.7, 0)] + [(61.9 + k * 0.45, click, 0.6, -0.6 + 1.2 * (k % 2)) for k in range(8)] + [(65.6, click, 1.0, 0.5), (66.4, impact, 0.9, 0.4), (66.45, metal, 0.7, 0.4)]
S += [(67.2, holo, 0.7, 0.4), (69.8, victory, 1.0, 0), (69.8, impact, 0.6, 0), (70.4, blip2, 0.6, 0), (72.0, metal, 0.7, 0)]
S += [(76.3, whoosh, 0.8, 0), (76.8, impact, 0.6, 0), (78.0, blip2, 0.7, 0), (79.2, blip2, 0.7, 0)] + [(80.8 + k * 0.18, tick, 0.5, 0) for k in range(12)] + [(83.0, buzzer, 0.7, 0), (83.4, impact, 0.9, 0), (84.2, mech, 0.6, 0)]
S += [(86.3, whoosh, 0.9, 0), (87.0, impact, 0.4, 0), (88.4, impact, 0.4, 0), (89.8, impact, 0.5, 0), (90.9, holo, 0.8, 0), (91.4, riser, 0.35, 0)]
S += [(96.0, riser, 0.5, 0), (97.7, impact, 1.0, 0), (97.7, sub, 1.0, 0), (98.4, metal, 0.7, 0)]
for at, fn, g, pan in S:
    place(sfx, fn(), at, gain=g, pan=pan)

mix = music * 0.85 + vo * 1.25 + sfx * 0.8
mix = np.tanh(mix * 0.95) / np.tanh(0.95)
fo = int(1.4 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = ROOT / "audio"; out.mkdir(exist_ok=True)
pre = out / "_premix.wav"
with wave.open(str(pre), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
m = json.loads(r[r.rfind("{"): r.rfind("}") + 1])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", af, "-ar", str(SR), str(out / "mix.wav")], check=True)
pre.unlink()
# stems check: narration vs ducked music loudness
for name, buf in (("vo", vo * 1.25), ("music", music * 0.85)):
    p = out / f"_{name}.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes())
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(p), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(name, [l.strip() for l in r.splitlines() if l.strip().startswith("I:")][-1])
    p.unlink()
print("wrote", out / "mix.wav")
