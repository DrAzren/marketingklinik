"""Synthesise the 15 s soundtrack (music bed + beat-synced SFX) for the weight-loss ad.

Everything is generated from oscillators and noise, so the audio is original and
royalty-free. Output: audio/soundtrack.wav (44.1 kHz stereo, 16-bit).

    python3 tools/make_audio.py
"""
import pathlib
import wave

import numpy as np

SR = 44100
DUR = 15.0
# Scene cuts - keep in sync with index.html (T2, T3, T4, T5, HIT)
T2, T3, T4, T5, HIT = 2.0, 4.5, 8.5, 10.5, 11.0
BPM = 120
BEAT = 60 / BPM  # 0.5 s, so every scene cut and the price hit land on a beat
N = int(SR * DUR)
rng = np.random.default_rng(850)  # fixed seed -> identical file on every run

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



def beep():
    d = 0.32
    t = t_(d)
    s = np.sin(2 * np.pi * 2093 * t) * ((t < 0.09) | ((t > 0.15) & (t < 0.24)))
    return s * np.exp(-t / 0.25) * 0.8


def esweep(d=0.7):  # premium electronic sweep: detuned saws through a rising filter
    t = t_(d)
    f = 110
    s = sum(2 * (t * f * k % 1) - 1 for k in (1, 1.007, 1.5, 2.003))
    cut = np.linspace(300, 7000, len(t))
    out = np.empty_like(s)
    acc = 0.0
    for i, v in enumerate(s):
        a = np.exp(-2 * np.pi * cut[i] / SR)
        acc = (1 - a) * v + a * acc
        out[i] = acc
    return out * np.sin(np.pi * t / d) ** 1.5 * 0.35


def shimmer(d=0.9):
    t = t_(d)
    s = np.zeros_like(t)
    for k, n in enumerate([88, 91, 95, 100, 103]):
        off = k * 0.045
        tt = np.clip(t - off, 0, None)
        s += (t >= off) * np.sin(2 * np.pi * note(n) * tt) * np.exp(-tt / 0.35)
    return s * 0.25


def scan(d=1.7):  # soft scanning tone: filtered sine glide with tremolo
    t = t_(d)
    f = 520 + 260 * np.sin(2 * np.pi * t / d * 1.0)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 14 * t))
    e = np.minimum(t / 0.1, 1) * np.minimum((d - t) / 0.25, 1)
    return s * e * 0.3


def bass_hit():  # cinematic bass hit for the price slam
    d = 2.2
    t = t_(d)
    sub = np.sin(2 * np.pi * np.cumsum(38 + 120 * np.exp(-t / 0.06)) / SR) * np.exp(-t / 0.9)
    boom = onepole_lp(rng.standard_normal(len(t)), 900) * np.exp(-t / 0.18)
    crack = hp(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.03)
    return 1.2 * sub + 0.7 * boom + 0.5 * crack


def suck(d=0.45):  # reverse swell into the collapse
    return whoosh(d, up=True)[::-1] * 0.8 + riser(d) * 0.8


# ---------------------------------------------------------------- music bed
# 120 BPM, C - G - Am - F, one chord per bar (2 s). A riser carries the hook, the groove
# drops on the scene-2 cut, breaks for the collapse (10.5 - 11.0) and drops again on the price.
prog = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
arp_pat = [0, 1, 2, 1, 2, 0, 1, 2]


def groove(start, end, chord_at):
    tb = start
    while tb < end - 1e-6:
        root, ch = prog[chord_at(tb) % 4]
        b = int(round(tb / BEAT))
        place(kick(), tb, 0.55)
        if b % 2 == 1:
            place(clap(), tb, 0.30)
        place(bass(root, 0.24), tb, 0.30)
        place(bass(root + 12 if b % 4 == 3 else root, 0.2), tb + BEAT / 2, 0.22)
        for h in range(2):
            place(hat(), tb + h * BEAT / 2 + BEAT / 4, 0.10, pan=0.3)
        for s in range(2):
            ts = tb + s * BEAT / 2
            place(pluck(ch[arp_pat[(b * 2 + s) % 8]] + 12), ts, 0.10, pan=-0.35 if s else 0.35)
        tb += BEAT


bar_of = lambda tb: int((tb - T2) // (4 * BEAT))
for k, (s, e) in enumerate([(2.0, 4.0), (4.0, 6.0), (6.0, 8.0), (8.0, 10.0), (10.0, T5), (HIT, 13.0), (13.0, 14.0)]):
    place(pad(prog[bar_of(s) % 4][1], e - s), s, 0.10)
groove(T2, T5, bar_of)
groove(HIT, 14.0, lambda tb: 3 if tb < 13.0 else 1)  # F ... G for the turnaround
# hook: kick on each slam + riser
for at in (0.5, 1.0, 1.5):
    place(kick(), at, 0.6)
place(riser(T2 - 0.05), 0.05, 0.5)
# final resolution: C major chord + chime on 14.0, ringing out to the end
place(pad([48, 60, 64, 67, 72], 1.0), 14.0, 0.22)
place(bass(36, 0.9), 14.0, 0.35)
place(kick(), 14.0, 0.5)

# ---------------------------------------------------------------- SFX cue sheet
# Times match the GSAP timeline in index.html.
cues = [
    (0.06, impact, 0.95, 0.0),          # scale slams in (lands 0.12)
    (0.20, beep, 0.35, 0.0),            # digital scale beep
    (0.30, lambda: whoosh(0.25), 0.40, -0.3),
    (0.50, slam, 0.70, 0.0),            # NAK TURUN
    (0.78, lambda: whoosh(0.25), 0.40, 0.3),
    (1.00, slam, 0.70, 0.0),            # BERAT BADAN?
    (1.50, impact, 0.80, 0.0),          # TENGOK NI!
    (T2 - 0.25, lambda: whoosh(0.35), 0.45, 0.0),
    (T2 + 0.20, lambda: esweep(0.9), 0.55, 0.0),   # premium medical reveal
    (T2 + 1.05, shimmer, 0.35, 0.3),
    (T3 - 0.40, lambda: whoosh(0.45), 0.50, 0.0),
    (T3, slam, 0.35, 0.0),
    (5.00, lambda: pop(520), 0.55, -0.2),  # three FREE cards
    (5.75, lambda: pop(620), 0.55, 0.2),
    (6.50, lambda: pop(740), 0.60, 0.0),
    (7.20, shimmer, 0.30, 0.0),
    (T4 - 0.32, lambda: whoosh(0.4), 0.45, 0.0),
    (T4 + 0.20, scan, 0.55, 0.0),
    (T4 + 0.75, shimmer, 0.22, -0.3),
    (T5 - 0.45, suck, 0.55, 0.0),        # everything collapses
    (T5 + 0.02, shimmer, 0.40, 0.0),    # golden light sweep
    (T5 + 0.12, lambda: whoosh(0.3), 0.35, 0.0),
    (HIT, bass_hit, 1.00, 0.0),         # RM850
    (11.45, lambda: whoosh(0.4), 0.35, 0.0),
    (12.00, chime, 0.60, 0.0),          # CTA settled
    (12.50, lambda: pop(880), 0.25, 0.0),  # WhatsApp pulse
    (14.00, chime, 0.45, 0.0),          # logo light sweep / resolution
]
for at, fn, g, pan in cues:
    place(fn(), at, g, pan)

# ---------------------------------------------------------------- master
t = np.arange(N) / SR
fade = np.clip((DUR - t) / 0.4, 0, 1)  # short tail fade over the final 0.4 s
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
