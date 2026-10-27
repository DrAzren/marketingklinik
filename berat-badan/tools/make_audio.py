"""Synthesise the 15 s soundtrack (music bed + beat-synced SFX) for the weight-loss ad.

Concept: half-time future bass / trap in F minor, a different world from the clinic's
earlier four-on-the-floor major-key spot. It uses sidechained supersaw chords, a gliding
808, rolling trap hats, a pitched "chop" lead, a filtered breakdown under the body scan
and a second drop on the RM850 slam.

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
BEAT = 60 / BPM  # 0.5 s; every scene cut and the price hit land on a beat
BAR = 4 * BEAT
N = int(SR * DUR)
rng = np.random.default_rng(1411)  # fixed seed -> identical file on every run


def bus():
    return np.zeros((N, 2))


drums, bassbus, chords, lead, fx = bus(), bus(), bus(), bus(), bus()


def t_(d):
    return np.arange(int(SR * d)) / SR


def note(n):  # MIDI -> Hz
    return 440 * 2 ** ((n - 69) / 12)


def place(b, sig, at, gain=1.0, pan=0.0):
    i = int(round(at * SR))
    if i >= N or i < 0:
        return
    sig = sig[: N - i] * gain
    b[i : i + len(sig), 0] += sig * np.sqrt(0.5 * (1 - pan))
    b[i : i + len(sig), 1] += sig * np.sqrt(0.5 * (1 + pan))


def lp(x, cutoff):
    """One-pole low-pass; cutoff may be a scalar or a per-sample array."""
    c = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape[:1])
    a = np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = np.zeros(x.shape[1:]) if x.ndim > 1 else 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def hp(x, cutoff):
    return x - lp(x, cutoff)


def adsr(d, a=0.005, r=0.05):
    t = t_(d)
    return np.minimum(t / max(a, 1e-4), 1) * np.clip((d - t) / max(r, 1e-4), 0, 1)


def saw(f, t, phase=0.0):
    return 2 * ((t * f + phase) % 1) - 1


# ---------------------------------------------------------------- instruments
def k808(n=29, d=0.9, glide_to=None):
    """Long 808: pitch-dropped sine with slight drive; optional glide to another note."""
    t = t_(d)
    f0, f1 = note(n), note(glide_to if glide_to is not None else n)
    f = f0 + (f1 - f0) * np.clip((t - 0.12) / 0.12, 0, 1) if glide_to is not None else np.full_like(t, f0)
    f = f * (1 + 1.6 * np.exp(-t / 0.018))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return np.tanh(2.2 * s) / np.tanh(2.2) * np.exp(-t / (d * 0.55)) * adsr(d, 0.002, 0.05)


def punch():  # short kick transient layered on the 808
    t = t_(0.12)
    return np.sin(2 * np.pi * np.cumsum(60 + 240 * np.exp(-t / 0.01)) / SR) * np.exp(-t / 0.04)


def snare():
    t = t_(0.35)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05)
    noise = hp(rng.standard_normal(len(t)), 1800) * np.exp(-t / 0.11)
    return 0.6 * tone + 0.9 * noise


def clap():
    t = t_(0.3)
    n = hp(rng.standard_normal(len(t)), 1200)
    e = np.zeros_like(t)
    for o in (0, 0.009, 0.018, 0.028):
        i = int(o * SR)
        e[i:] += np.exp(-np.arange(len(t) - i) / SR / 0.06)
    return n * e * 0.45


def hat(open_=False):
    d = 0.22 if open_ else 0.045
    t = t_(d)
    metal = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (5600, 7130, 8410, 9950))
    s = hp(0.5 * metal + rng.standard_normal(len(t)), 7000)
    return s * np.exp(-t / (0.07 if open_ else 0.012)) * 0.5


def supersaw_chord(notes, d, cutoff):
    """7-voice detuned saws per note, stereo-spread, through a (possibly moving) low-pass."""
    t = t_(d)
    st = np.zeros((len(t), 2))
    det = [-0.11, -0.06, -0.025, 0, 0.025, 0.06, 0.11]
    for n in notes:
        f = note(n)
        for k, dv in enumerate(det):
            v = saw(f * 2 ** (dv / 12), t, phase=(k * 0.137 + n * 0.071) % 1)
            p = (k - 3) / 3
            st[:, 0] += v * np.sqrt(0.5 * (1 - p))
            st[:, 1] += v * np.sqrt(0.5 * (1 + p))
    st /= len(notes) * 4
    st = lp(st, cutoff)
    return st * adsr(d, 0.02, 0.08)[:, None]


def chop(n, d=0.22, bend=0.0):
    """Pitched 'vocal-chop' style lead (no vocals): pulse + formant-ish band, pitch scoop."""
    t = t_(d)
    f = note(n) * 2 ** ((bend * np.exp(-t / 0.04)) / 12)
    ph = np.cumsum(f) / SR
    s = np.where((ph % 1) < 0.32, 1.0, -1.0) * 0.6 + np.sin(2 * np.pi * ph * 3) * 0.4
    s = lp(s, 3200) - 0.6 * lp(s, 700)
    return s * adsr(d, 0.004, 0.06) * np.exp(-t / 0.35)


def place_st(b, st, at, gain=1.0):
    i = int(round(at * SR))
    st = st[: N - i] * gain
    b[i : i + len(st)] += st


# ---------------------------------------------------------------- SFX
def impact(d=1.4):
    t = t_(d)
    sub = np.sin(2 * np.pi * np.cumsum(32 + 110 * np.exp(-t / 0.07)) / SR) * np.exp(-t / 0.5)
    crack = lp(rng.standard_normal(len(t)), 4000) * np.exp(-t / 0.04)
    tail = lp(rng.standard_normal(len(t)), 600) * np.exp(-t / 0.35) * 0.4
    return 1.1 * sub + 0.6 * crack + tail


def whoosh(d=0.4, up=True):
    t = t_(d)
    sweep = np.geomspace(300, 6000, len(t)) if up else np.geomspace(6000, 300, len(t))
    s = hp(lp(rng.standard_normal(len(t)), sweep), 200)
    return s * np.sin(np.pi * t / d) ** 2 * 1.5


def beep():
    t = t_(0.3)
    s = np.sin(2 * np.pi * 1760 * t) * ((t < 0.08) | ((t > 0.14) & (t < 0.22)))
    return s * 0.7


def fm_bell(n, d=1.6, idx=3.0):  # glassy FM bell, distinct from the earlier sine chime
    t = t_(d)
    f = note(n)
    mod = idx * np.exp(-t / 0.4) * np.sin(2 * np.pi * f * 3.5 * t)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 0.7) * adsr(d, 0.002, 0.1)


def bubble(f0):  # liquid "bloop" for the three free cards
    t = t_(0.2)
    f = f0 * (1 + 1.2 * (t / 0.2) ** 0.6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05) * adsr(0.2, 0.002, 0.03)


def scan(d=1.7):
    t = t_(d)
    f = 900 + 500 * np.sin(2 * np.pi * t / d)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 16 * t)))
    return lp(s, 2500) * adsr(d, 0.08, 0.3) * 0.25


def riser(d):
    t = t_(d)
    s = hp(lp(rng.standard_normal(len(t)), np.geomspace(400, 9000, len(t))), 300)
    tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(200, 1600, len(t))) / SR) * 0.3
    return (s + tone) * (t / d) ** 2


def bass_drop():  # cinematic sub hit for RM850
    t = t_(2.4)
    sub = np.sin(2 * np.pi * np.cumsum(30 + 140 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 1.0)
    boom = lp(rng.standard_normal(len(t)), 800) * np.exp(-t / 0.2)
    crack = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.025)
    return 1.3 * np.tanh(1.5 * sub) + 0.7 * boom + 0.5 * crack


# ---------------------------------------------------------------- arrangement
# F minor: Fm - Db - Ab - Eb (i - VI - III - VII), one chord per 2 s bar from 2.0 s.
CH = [[53, 56, 60, 65], [53, 56, 61, 65], [51, 56, 60, 63], [51, 55, 58, 63]]
ROOT = [29, 25, 32, 27]  # 808 roots (F1, Db1, Ab1, Eb1)


def chord_idx(tb):
    return int((tb - T2) // BAR) % 4


kicks = []  # sidechain trigger times


def drop(start, end):
    """Half-time trap groove: 808 on 1 and the 'and' of 2, snare on 3, rolling hats."""
    bar = start
    while bar < end - 1e-6:
        ci = chord_idx(bar)
        nxt = ROOT[(ci + 1) % 4]
        for off, n, d, g in ((0.0, ROOT[ci], 0.7, None), (0.75, ROOT[ci], 0.5, None), (1.5, ROOT[ci] + 12, 0.45, nxt + 12)):
            at = bar + off
            if at < end - 1e-6:
                place(bassbus, k808(n, d, g), at, 0.9)
                place(drums, punch(), at, 0.75)
                kicks.append(at)
        if bar + 1.0 < end:
            place(drums, snare(), bar + 1.0, 0.55)
            place(drums, clap(), bar + 1.0, 0.45)
        # hats: 8ths, with a 16th/triplet roll in the last beat of each bar
        for h in range(8):
            at = bar + h * BEAT / 2
            if at < end - 1e-6 and h < 6:
                place(drums, hat(h == 3), at, 0.32 if h % 2 else 0.22, pan=0.25)
        roll = np.linspace(0, BEAT, 7 if chord_idx(bar) % 2 else 9, endpoint=False)
        for k, r in enumerate(roll):
            at = bar + 3 * BEAT + r
            if at < end - 1e-6:
                place(drums, hat(), at, 0.12 + 0.02 * k, pan=-0.25)
        bar += BAR


# 0 - 2.0 hook: 808 booms on every slam, snare roll build, filtered chord stabs
for at, n in ((0.12, 29), (0.5, 29), (1.0, 25), (1.5, 27)):
    place(bassbus, k808(n, 0.45), at, 0.85)
    place(drums, punch(), at, 0.8)
    place_st(chords, supersaw_chord(CH[0], 0.22, 2600), at, 0.55)
for at in np.concatenate([np.arange(1.0, 1.5, BEAT / 4), np.arange(1.5, 2.0, BEAT / 8)]):
    place(drums, snare(), at, 0.08 + 0.3 * (at - 1.0))
place(fx, riser(1.4), 0.6, 0.35)

# 2.0 - 8.5 drop A (chords pump under the kick)
drop(T2, T4)
bar = T2
while bar < T4 - 1e-6:
    d = min(BAR, T4 - bar)
    place_st(chords, supersaw_chord(CH[chord_idx(bar)], d, 3800), bar, 0.9)
    bar += BAR
# chop-lead hook over the cards (4.5 - 8.5)
motif = [(0, 72, 0.0), (0.5, 75, -2), (0.75, 77, 0.0), (1.25, 75, 0.0), (1.5, 72, -1), (1.75, 70, 0.0)]
for bar0 in (4.0, 6.0):
    for off, n, bend in motif:
        at = bar0 + off
        if T3 - 0.01 <= at < T4:
            ci = chord_idx(at)
            place(lead, chop(n - (1 if ci == 1 and n == 72 else 0), 0.22, bend), at, 0.42, pan=-0.2 if int(off * 4) % 2 else 0.2)

# 8.5 - 10.5 breakdown: filtered chords swell under the scan, no kick, riser into the collapse
place_st(chords, supersaw_chord(CH[1], 2.0, np.geomspace(500, 2200, int(SR * 2.0))), T4, 0.85)
for h in range(8):
    place(drums, hat(), T4 + 0.25 + h * BEAT / 2, 0.12, pan=0.3 if h % 2 else -0.3)
place(fx, riser(1.6), T4 + 0.4, 0.45)

# 10.5 - 11.0: silence (the collapse), then drop B on the price slam
drop(HIT, 14.0)
for at, ci in ((HIT, 0), (12.0, 3), (13.0, 2)):
    place_st(chords, supersaw_chord(CH[ci], 1.0, 5000), at, 1.0)
for off, n, bend in [(0.0, 77, -2), (0.25, 75, 0), (0.5, 72, 0), (1.0, 75, -1), (1.25, 77, 0), (1.75, 80, -2)]:
    place(lead, chop(n, 0.22, bend), 12.0 + off, 0.38, pan=0.15)

# 14.0 resolution: open Db major (VI) ringing out, last 808
place_st(chords, supersaw_chord([49, 56, 61, 65, 68], 1.0, np.geomspace(5000, 900, int(SR * 1.0))), 14.0, 1.0)
place(bassbus, k808(25, 1.0), 14.0, 0.9)
place(drums, punch(), 14.0, 0.8)
kicks.append(14.0)

# ---------------------------------------------------------------- sidechain pump
t = np.arange(N) / SR
duck = np.ones(N)
for k in kicks:
    i = int(k * SR)
    seg = np.arange(N - i) / SR
    duck[i:] = np.minimum(duck[i:], 1 - 0.75 * np.exp(-seg / 0.13))
chords *= duck[:, None]
lead *= (0.5 + 0.5 * duck)[:, None]
# ping-pong echo on the lead (dotted eighth = 0.375 s)
echo = np.zeros_like(lead)
for k, g in enumerate((0.45, 0.3, 0.18, 0.1), start=1):
    i = int(0.375 * k * SR)
    ch = k % 2
    echo[i:, ch] += lead[: N - i].mean(axis=1) * g
lead += lp(echo, 2500)

# ---------------------------------------------------------------- SFX cue sheet
# Times match the GSAP timeline in index.html.
cues = [
    (0.06, impact, 0.85, 0.0),         # scale slams in (lands 0.12)
    (0.20, beep, 0.30, 0.0),           # digital scale beep
    (0.30, lambda: whoosh(0.25), 0.35, -0.3),
    (0.78, lambda: whoosh(0.25), 0.35, 0.3),
    (1.50, impact, 0.70, 0.0),         # TENGOK NI!
    (T2 - 0.30, lambda: whoosh(0.35, up=True), 0.40, 0.0),
    (T2 + 1.05, lambda: fm_bell(96, 0.9, 2.0), 0.18, 0.3),   # metallic sweep glint
    (T3 - 0.40, lambda: whoosh(0.45), 0.45, 0.0),
    (5.00, lambda: bubble(420), 0.60, -0.2),  # three FREE cards
    (5.75, lambda: bubble(520), 0.60, 0.2),
    (6.50, lambda: bubble(640), 0.65, 0.0),
    (7.20, lambda: fm_bell(91, 0.9, 1.5), 0.16, 0.0),
    (T4 - 0.32, lambda: whoosh(0.4), 0.40, 0.0),
    (T4 + 0.20, scan, 0.55, 0.0),
    (T5 - 0.45, lambda: whoosh(0.45, up=True)[::-1], 0.55, 0.0),  # everything collapses
    (T5 + 0.02, lambda: fm_bell(101, 0.8, 1.2), 0.20, 0.0),       # golden light sweep
    (HIT, bass_drop, 1.00, 0.0),       # RM850
    (11.40, lambda: whoosh(0.4, up=False), 0.30, 0.0),
    (12.00, lambda: fm_bell(84, 1.6, 2.5) + 0.6 * fm_bell(91, 1.6, 2.0), 0.30, 0.0),  # CTA settled
    (12.50, lambda: bubble(760), 0.28, 0.0),  # WhatsApp pulse
    (14.00, lambda: fm_bell(89, 1.0, 2.0) + 0.6 * fm_bell(96, 1.0, 1.5), 0.30, 0.0),  # logo sweep / resolution
]
for at, fn, g, pan in cues:
    place(fx, fn(), at, g, pan)

# ---------------------------------------------------------------- master
mix = 0.95 * drums + 0.85 * bassbus + 0.42 * chords + 0.6 * lead + 0.9 * fx
fade = np.clip((DUR - t) / 0.4, 0, 1)  # short tail fade over the final 0.4 s
mix *= fade[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)  # soft clip / glue
mix *= 0.66 / np.max(np.abs(mix))  # about -13 LUFS, close to IG/TikTok playback loudness

out = pathlib.Path(__file__).resolve().parent.parent / "audio" / "soundtrack.wav"
out.parent.mkdir(exist_ok=True)
with wave.open(str(out), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(out)
