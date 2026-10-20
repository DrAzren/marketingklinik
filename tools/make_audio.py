"""Synthesise the 20 s soundtrack (music bed + beat-synced SFX) for the story.

Everything is generated from oscillators and noise, so the audio is original and
royalty-free. Output: audio/soundtrack.wav (44.1 kHz stereo, 16-bit).

    python3 tools/make_audio.py
"""
import pathlib
import wave

import numpy as np

SR = 44100
DUR = 20.0
# Scene cuts - keep in sync with index.html (D, T2, T3, TP, T4)
T2, T3, TP, T4 = 2.0, 6.5, 12.5, 16.0
BPM = 120
BEAT = 60 / BPM  # 0.5 s, so every scene cut (1.5 / 6.5 / 11.5 s) lands on a beat
N = int(SR * DUR)
rng = np.random.default_rng(7)  # fixed seed -> identical file on every run

L = np.zeros(N)
R = np.zeros(N)


def t_(d):
    return np.arange(int(SR * d)) / SR


def place(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    L[i : i + len(sig)] += sig * np.sqrt(0.5 * (1 - pan))
    R[i : i + len(sig)] += sig * np.sqrt(0.5 * (1 + pan))


def onepole_lp(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def hp(x, cutoff):
    return x - onepole_lp(x, cutoff)


def env(d, a=0.005, decay=None):
    t = t_(d)
    e = np.minimum(t / a, 1.0) if a > 0 else np.ones_like(t)
    if decay:
        e *= np.exp(-t / decay)
    return e


def note(n):  # MIDI -> Hz
    return 440 * 2 ** ((n - 69) / 12)


# ---------------------------------------------------------------- instruments
def kick(d=0.35):
    t = t_(d)
    f = 50 + 120 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)


def clap(d=0.25):
    n = hp(rng.standard_normal(int(SR * d)), 900)
    e = np.zeros_like(n)
    for o in (0, 0.012, 0.024):
        i = int(o * SR)
        e[i:] += np.exp(-np.arange(len(n) - i) / SR / 0.05)
    return n * e * 0.5


def hat(d=0.06):
    return hp(rng.standard_normal(int(SR * d)), 6000) * env(d, 0.001, 0.015)


def bass(n, d):
    t = t_(d)
    f = note(n)
    s = 0.7 * np.sin(2 * np.pi * f * t) + 0.3 * np.sign(np.sin(2 * np.pi * f * t))
    return onepole_lp(s, 400) * env(d, 0.004, 0.18)


def pluck(n, d=0.22):
    t = t_(d)
    f = note(n)
    s = 2 * (t * f % 1) - 1  # saw
    return onepole_lp(s, 2600) * env(d, 0.002, 0.07)


def pad(ns, d):
    t = t_(d)
    s = sum(np.sin(2 * np.pi * note(n) * t + 0.3 * np.sin(2 * np.pi * 0.4 * t)) for n in ns)
    e = np.minimum(t / 0.25, 1) * np.minimum((d - t) / 0.3, 1)
    return s / len(ns) * e


# ---------------------------------------------------------------- SFX
def impact():
    d = 1.2
    t = t_(d)
    sub = np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-t / 0.08)) / SR) * np.exp(-t / 0.45)
    crack = onepole_lp(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.05)
    return 1.1 * sub + 0.6 * crack


def slam():
    d = 0.5
    t = t_(d)
    body = np.sin(2 * np.pi * np.cumsum(70 + 160 * np.exp(-t / 0.02)) / SR) * np.exp(-t / 0.12)
    snap = hp(rng.standard_normal(len(t)), 1500) * np.exp(-t / 0.03)
    return 0.9 * body + 0.5 * snap


def whoosh(d=0.45, up=True):
    t = t_(d)
    n = rng.standard_normal(len(t))
    sweep = np.linspace(400, 5000, len(t)) if up else np.linspace(5000, 400, len(t))
    out = np.empty_like(n)
    acc = 0.0
    for i, v in enumerate(n):  # swept one-pole low-pass
        a = np.exp(-2 * np.pi * sweep[i] / SR)
        acc = (1 - a) * v + a * acc
        out[i] = acc
    shape = np.sin(np.pi * t / d) ** 2
    return hp(out, 200) * shape * 1.6


def tick():
    d = 0.05
    t = t_(d)
    return (np.sin(2 * np.pi * 3200 * t) + 0.5 * np.sin(2 * np.pi * 5400 * t)) * np.exp(-t / 0.006)


def click():
    d = 0.04
    t = t_(d)
    return hp(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.005) + 0.5 * np.sin(2 * np.pi * 1800 * t) * np.exp(-t / 0.008)


def pop(f0=500):
    d = 0.18
    t = t_(d)
    f = f0 + 900 * np.exp(-t / 0.015)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, 0.001, 0.05)


def chime():
    d = 1.6
    t = t_(d)
    s = np.zeros_like(t)
    for k, (n, off) in enumerate([(84, 0), (88, 0.08), (91, 0.16), (96, 0.24)]):
        tt = np.clip(t - off, 0, None)
        s += (t >= off) * np.sin(2 * np.pi * note(n) * tt) * np.exp(-tt / 0.6) * (0.8 - 0.1 * k)
        s += (t >= off) * 0.25 * np.sin(2 * np.pi * note(n) * 2.01 * tt) * np.exp(-tt / 0.3)
    return s * 0.6


def riser(d):
    t = t_(d)
    f = np.linspace(300, 2400, len(t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2 * 0.25 + hp(rng.standard_normal(len(t)), 3000) * (t / d) ** 3 * 0.2


# ---------------------------------------------------------------- music bed
# C - G - Am - F, one chord per bar (2 s). Music proper starts on the scene-2 cut.
prog = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
arp_pat = [0, 1, 2, 1, 2, 0, 1, 2]
START, END = T2, DUR
bar = START
i = 0
while bar < END:
    root, ch = prog[i % 4]
    d = min(4 * BEAT, END - bar)
    place(pad(ch, d), bar, 0.10)
    for b in range(4):
        tb = bar + b * BEAT
        if tb >= END:
            break
        place(kick(), tb, 0.55)
        if b % 2 == 1:
            place(clap(), tb, 0.30)
        place(bass(root, 0.24), tb, 0.30)
        place(bass(root + 12 if b == 3 else root, 0.2), tb + BEAT / 2, 0.22)
        for h in range(2):
            place(hat(), tb + h * BEAT / 2 + BEAT / 4, 0.10, pan=0.3)
    for s in range(8):  # eighth-note pluck arp
        ts = bar + s * BEAT / 2
        if ts < END:
            place(pluck(ch[arp_pat[s]] + 12), ts, 0.10, pan=-0.35 if s % 2 else 0.35)
    bar += 4 * BEAT
    i += 1

# Hook bed: riser under the opening titles.
place(riser(T2 - 0.05), 0.05, 0.6)

# ---------------------------------------------------------------- SFX cue sheet
# Times match the GSAP timeline in index.html.
cues = [
    (0.00, impact, 0.85, 0.0),
    (0.32, lambda: whoosh(0.35), 0.40, -0.2),
    (0.55, slam, 0.70, 0.0),
    (0.95, slam, 0.70, 0.0),
    (T2 - 0.28, lambda: whoosh(0.35), 0.45, 0.2),
    (T2, impact, 0.35, 0.0),
    # scene 2 - schedule
    (T2 + 0.15, pop, 0.30, 0.0),
    (T2 + 0.60, lambda: whoosh(0.25), 0.28, -0.4),
    (T2 + 0.75, click, 0.45, -0.2),
    (T2 + 1.10, lambda: whoosh(0.25), 0.28, 0.4),
    (T2 + 1.25, click, 0.45, 0.2),
    (T2 + 1.60, lambda: whoosh(0.25), 0.28, -0.4),
    (T2 + 1.75, click, 0.45, -0.2),
    (T3 - 0.35, lambda: whoosh(0.5), 0.50, 0.0),
    # scene 3 - services
    (T3 + 0.12, pop, 0.30, 0.0),
    (T3 + 0.45, lambda: pop(420), 0.40, 0.0),
    (TP - 0.30, lambda: whoosh(0.4), 0.40, 0.0),
    # scene 3b - panels
    (TP + 0.05, pop, 0.32, 0.0),
    (T4 - 0.30, lambda: whoosh(0.5), 0.50, 0.0),
    # scene 4 - CTA
    (T4 + 0.20, lambda: whoosh(0.45), 0.35, 0.0),
    (T4 + 0.65, slam, 0.40, 0.0),
    (T4 + 0.95, click, 0.35, 0.0),
    (T4 + 1.15, click, 0.35, 0.0),
    (T4 + 1.35, click, 0.35, 0.0),
    (T4 + 1.60, pop, 0.40, 0.0),
    (T4 + 2.25, chime, 0.55, 0.0),
]
# Service chips cascade (16 chips, 0.11 s apart) and panel tiles flip (12 tiles, 0.09 s apart).
for n in range(16):
    cues.append((T3 + 0.95 + n * 0.11, (lambda f: lambda: pop(f))(560 + 25 * n), 0.16, 0.3 if n % 2 else -0.3))
for n in range(12):
    cues.append((TP + 0.25 + n * 0.09, click, 0.28, (n % 3 - 1) * 0.4))
for at, fn, g, pan in cues:
    place(fn(), at, g, pan)
# Digital clock ticks through the schedule scene.
for k in range(int((T3 - 0.4 - (T2 + 0.25)) / BEAT) + 1):
    place(tick(), T2 + 0.25 + k * BEAT, 0.18, 0.5 if k % 2 else -0.5)

# ---------------------------------------------------------------- master
t = np.arange(N) / SR
fade = np.clip((DUR - t) / 0.6, 0, 1)  # gentle tail fade over the final 0.6 s
mix = np.stack([L, R], axis=1) * fade[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)  # soft clip
mix *= 0.89 / np.max(np.abs(mix))

out = pathlib.Path(__file__).resolve().parent.parent / "audio" / "soundtrack.wav"
out.parent.mkdir(exist_ok=True)
with wave.open(str(out), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(out)
