"""Synthesise the 15 s soundtrack for the "Fly to Klinik Nissa" navigation video.

Same oscillator-and-noise toolkit as tools/make_audio.py: original and royalty-free.
Cue times follow the GSAP / Three.js timeline in fly-to-clinic/. Output:
fly-to-clinic/audio/soundtrack.wav (44.1 kHz stereo, 16-bit).

    python3 tools/make_nav_audio.py
"""
import pathlib
import wave

import numpy as np

SR = 44100
DUR = 15.0
BPM = 120
BEAT = 60 / BPM
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




def flutter(d, rate=118.0):
    """Wing buzz: band-passed noise, amplitude-modulated at the wing-beat rate."""
    t = t_(d)
    n = hp(onepole_lp(rng.standard_normal(len(t)), 900), 120)
    am = 0.55 + 0.45 * np.sin(2 * np.pi * rate * t)
    e = np.minimum(t / 0.04, 1) * np.minimum((d - t) / 0.08, 1)
    return n * am * e * 2.2


def beep(f=1320, d=0.09):
    t = t_(d)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * env(d, 0.003, 0.035)


def nav(up=True):
    """Two-note navigation confirmation (rising = turn, falling = info)."""
    a, b = (76, 83) if up else (83, 79)
    s = np.zeros(int(SR * 0.4))
    for k, n in enumerate((a, b)):
        tone = beep(note(n), 0.22)
        i = int(k * 0.11 * SR)
        s[i : i + len(tone)] += tone
    return s


def pin_drop():
    d = 0.35
    t = t_(d)
    f = 1500 * np.exp(-t / 0.05) + 380
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, 0.001, 0.09)
    p = pop(700)
    body[: len(p)] += 0.4 * p
    return body


def success():
    """Arrival: bright major arpeggio + shimmer."""
    d = 2.0
    t = t_(d)
    s = np.zeros_like(t)
    for k, n in enumerate([72, 76, 79, 84, 88]):
        off = k * 0.07
        tt = np.clip(t - off, 0, None)
        s += (t >= off) * np.sin(2 * np.pi * note(n) * tt) * np.exp(-tt / 0.7) * 0.7
        s += (t >= off) * 0.2 * np.sin(2 * np.pi * note(n) * 3.0 * tt) * np.exp(-tt / 0.25)
    shimmer = hp(rng.standard_normal(len(t)), 7000) * np.exp(-t / 0.5) * 0.15
    return s * 0.55 + shimmer


# ---------------------------------------------------------------- music bed
# 120 BPM, C - G - Am - F, one chord per bar. Light intro under the hook, full groove on the route.
prog = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
arp_pat = [0, 1, 2, 1, 2, 0, 1, 2]
bar, i = 0.0, 0
while bar < DUR:
    root, ch = prog[i % 4]
    d = min(4 * BEAT, DUR - bar)
    place(pad(ch, d), bar, 0.10)
    full = bar >= 1.5
    for b in range(4):
        tb = bar + b * BEAT
        if tb >= DUR:
            break
        if full or b == 0:
            place(kick(), tb, 0.5)
        if full and b % 2 == 1:
            place(clap(), tb, 0.26)
        if full:
            place(bass(root, 0.24), tb, 0.28)
            place(bass(root + 12 if b == 3 else root, 0.2), tb + BEAT / 2, 0.2)
            for h in range(2):
                place(hat(), tb + h * BEAT / 2 + BEAT / 4, 0.09, pan=0.3)
    for s_ in range(8):
        ts = bar + s_ * BEAT / 2
        if ts < DUR:
            place(pluck(ch[arp_pat[s_]] + 12), ts, 0.09, pan=-0.35 if s_ % 2 else 0.35)
    bar += 4 * BEAT
    i += 1

# ---------------------------------------------------------------- SFX cue sheet (seconds)
cues = [
    # hook: fly zooms at the lens, headline slams, loop round the giant pin, dive
    (0.00, lambda: whoosh(0.45), 0.55, -0.3),
    (0.02, lambda: flutter(0.55, 124), 0.30, -0.2),
    (0.08, impact, 0.55, 0.0),
    (0.24, slam, 0.55, 0.0),
    (0.62, lambda: whoosh(0.4, up=False), 0.35, 0.4),
    (0.80, pop, 0.40, 0.0),
    (1.05, lambda: whoosh(0.7, up=False), 0.55, 0.0),
    # exit tol: pin, wing-powered acceleration
    (1.52, pin_drop, 0.40, 0.2),
    (1.95, lambda: whoosh(0.6), 0.45, -0.2),
    # first traffic light: beep beep, turn right
    (2.62, pin_drop, 0.35, 0.3),
    (2.90, lambda: beep(1320), 0.40, 0.0),
    (3.05, lambda: beep(1320), 0.40, 0.0),
    (2.97, lambda: nav(True), 0.50, 0.2),
    (3.40, lambda: whoosh(0.45), 0.40, 0.4),
    (3.45, lambda: flutter(0.45, 150), 0.30, 0.0),
    # McDonald's, KFC corner, turn left
    (4.15, pin_drop, 0.35, -0.3),
    (4.55, pin_drop, 0.35, 0.3),
    (4.87, lambda: nav(True), 0.50, -0.2),
    (5.30, lambda: whoosh(0.4), 0.35, -0.4),
    # Dataran Nilai and AEON on the right
    (5.87, pin_drop, 0.38, 0.4),
    (5.95, lambda: beep(1568, 0.07), 0.25, 0.4),
    (7.57, pin_drop, 0.38, 0.4),
    (7.65, lambda: beep(1568, 0.07), 0.25, 0.4),
    # turn left into Putra Point
    (8.72, lambda: nav(True), 0.50, -0.2),
    (9.30, lambda: whoosh(0.4), 0.35, -0.4),
    (9.80, lambda: nav(False), 0.40, 0.0),
    # arrival
    (10.40, lambda: whoosh(0.6), 0.35, 0.0),
    (10.62, success, 0.75, 0.0),
    (10.66, impact, 0.30, 0.0),
    # end card
    (11.30, lambda: whoosh(0.5), 0.45, 0.0),
    (11.62, slam, 0.40, 0.0),
    (11.90, pop, 0.30, 0.0),
    (12.15, click, 0.30, -0.2),
    (12.60, pop, 0.38, 0.0),
    (12.95, chime, 0.55, 0.0),
]
for at, fn, g, pan in cues:
    place(fn(), at, g, pan)
# soft wing buzz under the whole flight, swelling with speed
place(flutter(9.9, 118) * np.interp(t_(9.9), [0, 1.0, 1.5, 6, 9.4, 9.9], [0.3, 0.6, 1.0, 0.7, 0.8, 0.0]), 1.4, 0.10, 0.0)

# ---------------------------------------------------------------- master
t = np.arange(N) / SR
fade = np.clip((DUR - t) / 0.6, 0, 1)  # gentle tail fade over the final 0.6 s
mix = np.stack([L, R], axis=1) * fade[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)  # soft clip
mix *= 0.89 / np.max(np.abs(mix))

out = pathlib.Path(__file__).resolve().parent.parent / "fly-to-clinic" / "audio" / "soundtrack.wav"
out.parent.mkdir(exist_ok=True)
with wave.open(str(out), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(out)
