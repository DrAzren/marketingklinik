"""Synthesise the 15 s soundtrack (music bed + timeline-synced SFX) for "100 Tabs".

Everything comes from oscillators and seeded noise, so the audio is original,
royalty-free and identical on every run. Output: audio/soundtrack.wav (44.1 kHz stereo).

    python3 tools/make_audio.py
"""
import pathlib
import wave

import numpy as np

SR = 44100
DUR = 15.0
# Scene cuts - keep in sync with index.html (T1, T2, T3, T4). 120 BPM, so every cut is on a beat.
T1, T2, T3, T4 = 2.0, 4.5, 6.5, 10.5
BPM = 120
BEAT = 60 / BPM
DROP_END = T2 + 0.12  # the music drops out for a moment before the brain pulse
N = int(SR * DUR)
rng = np.random.default_rng(1411)

L = np.zeros(N)
R = np.zeros(N)


def t_(d):
    return np.arange(int(SR * d)) / SR


def place(sig, at, gain=1.0, pan=0.0):
    i = int(round(at * SR))
    if i >= N or i < 0:
        return
    sig = sig[: N - i] * gain
    L[i : i + len(sig)] += sig * np.sqrt(0.5 * (1 - pan))
    R[i : i + len(sig)] += sig * np.sqrt(0.5 * (1 + pan))


def lp(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def hp(x, cutoff):
    return x - lp(x, cutoff)


def env(d, a=0.005, decay=None):
    t = t_(d)
    e = np.minimum(t / a, 1.0) if a > 0 else np.ones_like(t)
    if decay:
        e *= np.exp(-t / decay)
    return e


def note(n):
    return 440 * 2 ** ((n - 69) / 12)


def saw(f, t):
    return 2 * (t * f % 1) - 1


# ---------------------------------------------------------------- instruments
def kick(d=0.32, punch=1.0):
    t = t_(d)
    f = 48 + 130 * np.exp(-t / 0.028)
    click = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.003) * 0.25
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11) + click) * punch


def clap(d=0.22):
    n = hp(rng.standard_normal(int(SR * d)), 1000)
    e = np.zeros_like(n)
    for o in (0, 0.011, 0.022):
        i = int(o * SR)
        e[i:] += np.exp(-np.arange(len(n) - i) / SR / 0.045)
    return n * e * 0.45


def hat(d=0.05, open_=False):
    d = 0.16 if open_ else d
    return hp(rng.standard_normal(int(SR * d)), 7000) * env(d, 0.001, 0.05 if open_ else 0.012)


def bass(n, d):
    t = t_(d)
    f = note(n)
    s = 0.6 * np.sin(2 * np.pi * f * t) + 0.4 * saw(f, t)
    return lp(s, 520) * env(d, 0.003, 0.16)


def arp(n, d=0.11):
    t = t_(d)
    f = note(n)
    s = saw(f, t) + 0.5 * saw(f * 1.006, t)
    return lp(s, 3400) * env(d, 0.001, 0.05)


def pluck(n, d=0.5):
    t = t_(d)
    f = note(n)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.08)
    return s * env(d, 0.002, 0.22)


def pad(ns, d, bright=0.0):
    t = t_(d)
    s = sum(np.sin(2 * np.pi * note(n) * t + 0.25 * np.sin(2 * np.pi * 0.35 * t + k)) for k, n in enumerate(ns))
    s += bright * sum(saw(note(n + 12), t) for n in ns) * 0.15
    e = np.minimum(t / 0.2, 1) * np.minimum((d - t) / 0.25, 1)
    return lp(s / len(ns), 2600) * np.clip(e, 0, 1)


# ---------------------------------------------------------------- SFX
def impact(big=1.0):
    d = 1.3
    t = t_(d)
    sub = np.sin(2 * np.pi * np.cumsum(32 + 110 * np.exp(-t / 0.07)) / SR) * np.exp(-t / 0.5)
    crack = lp(rng.standard_normal(len(t)), 3500) * np.exp(-t / 0.04)
    return (1.15 * sub + 0.55 * crack) * big


def slam(f0=80):
    d = 0.42
    t = t_(d)
    body = np.sin(2 * np.pi * np.cumsum(f0 + 170 * np.exp(-t / 0.018)) / SR) * np.exp(-t / 0.1)
    snap = hp(rng.standard_normal(len(t)), 1800) * np.exp(-t / 0.025)
    return 0.9 * body + 0.45 * snap


def whoosh(d=0.4, up=True, lo=350, hi=5200):
    t = t_(d)
    n = rng.standard_normal(len(t))
    sweep = np.geomspace(lo, hi, len(t)) if up else np.geomspace(hi, lo, len(t))
    out = np.empty_like(n)
    acc = 0.0
    for i, v in enumerate(n):
        a = np.exp(-2 * np.pi * sweep[i] / SR)
        acc = (1 - a) * v + a * acc
        out[i] = acc
    shape = np.sin(np.pi * t / d) ** 2
    return hp(out, 180) * shape * 1.7


def glitch():
    d = 0.14
    t = t_(d)
    sq = np.sign(np.sin(2 * np.pi * 220 * t)) * (np.floor(t / 0.012) % 2)
    crush = np.round(rng.standard_normal(len(t)) * 3) / 3
    return (0.35 * sq + 0.3 * hp(crush, 2000)) * env(d, 0.001, 0.06)


def ping(n=88):
    d = 0.45
    t = t_(d)
    f = note(n)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / 0.05)) * env(d, 0.002, 0.11)


def ding():
    d = 0.9
    t = t_(d)
    a = np.sin(2 * np.pi * note(84) * t) * np.exp(-t / 0.25)
    t2 = np.clip(t - 0.09, 0, None)
    b = (t >= 0.09) * np.sin(2 * np.pi * note(91) * t2) * np.exp(-t2 / 0.35)
    return (a + b) * 0.7


def click():
    d = 0.04
    t = t_(d)
    return hp(rng.standard_normal(len(t)), 2600) * np.exp(-t / 0.004) + 0.5 * np.sin(2 * np.pi * 1900 * t) * np.exp(-t / 0.007)


def pop(f0=520):
    d = 0.16
    t = t_(d)
    f = f0 + 1000 * np.exp(-t / 0.012)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, 0.001, 0.045)


def buzz():
    d = 0.16
    t = t_(d)
    return lp(np.sign(np.sin(2 * np.pi * 140 * t)), 900) * np.sin(np.pi * t / d) * 0.6


def swell(d=1.1):
    t = t_(d)
    sub = np.sin(2 * np.pi * np.cumsum(40 + 25 * np.exp(-t / 0.3)) / SR)
    air = lp(rng.standard_normal(len(t)), 1800)
    e = np.minimum(t / 0.03, 1) * np.exp(-t / 0.45)
    return (sub * 0.9 + air * 0.35) * e


def shimmer(ns, d=1.6, rate=0.07):
    t = t_(d)
    s = np.zeros_like(t)
    for k, n in enumerate(ns):
        off = k * rate
        tt = np.clip(t - off, 0, None)
        s += (t >= off) * np.sin(2 * np.pi * note(n) * tt) * np.exp(-tt / 0.7)
        s += (t >= off) * 0.2 * np.sin(2 * np.pi * note(n) * 2.01 * tt) * np.exp(-tt / 0.3)
    return s / len(ns) * 1.4


def air(d=0.7):
    t = t_(d)
    return hp(rng.standard_normal(len(t)), 6000) * np.sin(np.pi * t / d) ** 2 * 0.5


def riser(d):
    t = t_(d)
    f = np.geomspace(250, 2200, len(t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2 * 0.22 + hp(rng.standard_normal(len(t)), 3000) * (t / d) ** 3 * 0.25


# ---------------------------------------------------------------- music
def groove(start, end, chords, chord_len, kick_gain=0.6, arp_gain=0.0, pluck_gain=0.0, pad_gain=0.08, clap_on=True):
    """chords: list of (bass_root, [pad notes]); one chord every chord_len seconds."""
    t = start
    i = 0
    while t < end - 1e-6:
        root, ch = chords[i % len(chords)]
        d = min(chord_len, end - t)
        place(pad(ch, d, bright=0.3), t, pad_gain)
        nb = int(round(d / BEAT))
        for b in range(nb):
            tb = t + b * BEAT
            place(kick(), tb, kick_gain)
            if clap_on and int(round((tb - start) / BEAT)) % 2 == 1:
                place(clap(), tb, 0.3)
            place(bass(root, 0.22), tb, 0.32)
            place(bass(root + 12 if b % 2 else root, 0.18), tb + BEAT / 2, 0.24)
            for h in range(4):
                place(hat(open_=(h == 2)), tb + h * BEAT / 4, 0.07 if h != 2 else 0.06, pan=0.3 if h % 2 else -0.3)
        for s in range(int(round(d / (BEAT / 4)))):
            ts = t + s * BEAT / 4
            if arp_gain:
                place(arp(ch[s % len(ch)] + 12 + (12 if s % 8 >= 6 else 0)), ts, arp_gain, pan=-0.4 if s % 2 else 0.4)
            if pluck_gain and s % 2 == 0:
                place(pluck(ch[(s // 2) % len(ch)] + 12, 0.35), ts, pluck_gain, pan=-0.25 if s % 4 else 0.25)
        t += chord_len
        i += 1


Am = (45, [57, 60, 64])
F = (41, [57, 60, 65])
C = (48, [60, 64, 67])
G = (43, [59, 62, 67])

# 0 - 4.5: overload. Driving 16th arp, four on the floor.
groove(0.0, T2, [Am, F, C], 2.0, kick_gain=0.62, arp_gain=0.085, pad_gain=0.06)
# 4.5 - DROP_END: silence. Then the emotional reset: no drums, warm pad + plucks.
place(pad([53, 57, 60, 64], T3 - DROP_END), DROP_END, 0.16)  # Fmaj7
place(pad([41], T3 - DROP_END), DROP_END, 0.18)
for k, n in enumerate([72, 76, 79, 77, 76, 72, 74, 76]):
    place(pluck(n, 0.6), DROP_END + 0.2 + k * BEAT / 2, 0.12, pan=-0.3 if k % 2 else 0.3)
place(riser(0.6), T3 - 0.6, 0.55)
# 6.5 - 10.5: confident, crisp groove.
groove(T3, T4, [C, G, Am, F], 1.0, kick_gain=0.5, pluck_gain=0.11, pad_gain=0.07)
# 10.5 - 14.5: brand and CTA, full and bright, then the music resolves and the chime rings out.
groove(T4, 14.5, [F, G, C, C], 1.0, kick_gain=0.58, arp_gain=0.05, pad_gain=0.09)
place(pad([60, 64, 67, 72], 0.9), 14.5, 0.12)

# ---------------------------------------------------------------- SFX cue sheet (times match index.html)
cues = [
    (0.00, slam, 0.75, 0.0),
    (0.00, lambda: impact(0.6), 0.6, 0.0),
    (0.10, lambda: whoosh(0.5), 0.35, -0.3),
    (0.24, lambda: slam(95), 0.45, -0.1),
    (0.44, lambda: slam(110), 0.5, 0.1),
    (0.62, lambda: whoosh(0.32, lo=500, hi=7000), 0.5, 0.0),
    (0.94, lambda: impact(1.0), 1.0, 0.0),  # "100 TABS?!" bass hit
    (0.94, glitch, 0.55, 0.0),
    (1.04, lambda: whoosh(0.22), 0.3, 0.3),
    (1.22, lambda: pop(600), 0.35, -0.2),
    (1.28, lambda: pop(760), 0.35, 0.2),
    (T1 - 0.22, lambda: whoosh(0.4, lo=300, hi=8000), 0.6, 0.0),
    (T1 + 0.05, lambda: impact(0.4), 0.45, 0.0),
    (T2 - 0.98, lambda: whoosh(0.22, up=False), 0.35, 0.0),
    (T2 - 0.78, lambda: slam(70), 0.55, 0.0),
    (T2 - 0.76, ding, 0.45, 0.0),
    (T2 - 0.64, lambda: pop(700), 0.35, 0.3),
    (T2 - 0.45, buzz, 0.35, 0.0),
    (T2 - 0.2, buzz, 0.35, 0.0),
    # drop: 4.50 - 4.62 is silent
    (T2 + 0.12, swell, 0.95, 0.0),
    (T2 + 0.14, lambda: shimmer([69, 72, 76, 81, 84], 1.8, 0.05), 0.5, 0.0),
    (T2 + 0.2, lambda: whoosh(0.6, up=False, lo=300, hi=6000), 0.45, 0.0),
    (T2 + 0.8, lambda: slam(60), 0.25, 0.0),
    (T2 + 1.05, lambda: slam(70), 0.28, 0.0),
    (T2 + 1.3, lambda: slam(80), 0.32, 0.0),
    (T3 - 0.15, lambda: whoosh(0.45), 0.45, 0.0),
    (T3 + 0.3, lambda: whoosh(0.3), 0.35, 0.4),
    (T3 + 0.55, click, 0.55, 0.2),
    (T3 + 0.72, lambda: pop(420), 0.4, 0.2),
    (T3 + 1.1, lambda: whoosh(0.3), 0.35, -0.4),
    (T3 + 1.35, click, 0.55, -0.2),
    (T3 + 1.52, lambda: pop(420), 0.4, -0.2),
    (T3 + 1.6, click, 0.45, 0.0),
    (T3 + 1.85, click, 0.45, 0.0),
    (T3 + 2.1, click, 0.45, 0.0),
    (T3 + 2.1, air, 0.4, 0.3),
    (T3 + 3.1, air, 0.35, -0.3),
    (T4 - 0.32, lambda: whoosh(0.4, lo=400, hi=8000), 0.55, 0.0),
    (T4 + 0.2, lambda: impact(0.9), 0.85, 0.0),  # logo impact
    (T4 + 0.22, lambda: shimmer([72, 76, 79, 84, 88], 1.6, 0.06), 0.45, 0.0),
    (T4 + 0.65, air, 0.35, 0.0),
    (T4 + 1.6, lambda: slam(90), 0.3, 0.0),
    (T4 + 1.95, lambda: slam(100), 0.3, 0.0),
    (T4 + 2.3, lambda: whoosh(0.35), 0.4, 0.0),
    (T4 + 2.6, lambda: pop(520), 0.4, -0.2),
    (T4 + 2.85, lambda: slam(70), 0.6, 0.0),
    (T4 + 2.9, lambda: shimmer([84, 88, 91, 96], 1.4, 0.07), 0.5, 0.0),  # CTA chime
    (T4 + 3.2, lambda: ping(91), 0.12, 0.2),
    (T4 + 3.75, lambda: ping(91), 0.12, -0.2),
    (T4 + 3.9, lambda: impact(0.55), 0.55, 0.0),  # final impact, rings out under the chime
    (T4 + 3.92, lambda: shimmer([72, 79, 84, 88, 91, 96], 1.2, 0.05), 0.55, 0.0),
    (T4 + 4.3, lambda: ping(91), 0.1, 0.0),
]
# window tab strip duplicating
for k in range(26):
    cues.append((0.02 + k * 0.022, (lambda f: lambda: pop(f))(480 + 28 * k), 0.12, (k % 5 - 2) * 0.2))
# labeled tabs: one digital ping + UI click each
for k in range(6):
    cues.append((T1 + 0.12 + k * 0.25, (lambda n: lambda: ping(n))([84, 88, 91, 86, 89, 93][k]), 0.28, (k % 3 - 1) * 0.5))
    cues.append((T1 + 0.2 + k * 0.25, click, 0.35, (k % 3 - 1) * 0.5))
for at, fn, g, pan in cues:
    place(fn(), at, g, pan)

# ---------------------------------------------------------------- master
t = np.arange(N) / SR
# hard silence for the drop, then the pulse lands
drop = np.ones(N)
i0, i1 = int(T2 * SR), int(DROP_END * SR)
drop[i0:i1] = 0
ramp = int(0.006 * SR)
drop[i0 - ramp : i0] = np.linspace(1, 0, ramp)
L *= drop
R *= drop
fade = np.clip((DUR - t) / 0.45, 0, 1)  # the final chime decays into a short fade, no abrupt cut
mix = np.stack([L, R], axis=1) * fade[:, None]
mix = np.tanh(mix * 1.15) / np.tanh(1.15)
mix *= 0.89 / np.max(np.abs(mix))

out = pathlib.Path(__file__).resolve().parent.parent / "audio" / "soundtrack.wav"
out.parent.mkdir(exist_ok=True)
with wave.open(str(out), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(out)
