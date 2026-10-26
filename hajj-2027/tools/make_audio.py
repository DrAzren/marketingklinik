"""Synthesise the 15 s soundtrack for the Hajj 1448H/2027M story ad.

Music: Middle Eastern-inspired instrumental in D Hijaz (D Eb F# G A Bb C) with warm
string pads, an oud-like plucked melody (Karplus-Strong), frame drum and darbuka
taps. It ends on a bright D major resolution. There are no vocals, recitation or
samples, so the audio is original and royalty-free by construction.

The SFX cue sheet (impact, shimmer, swooshes, UI clicks, heartbeat, logo chime) is
timed to the GSAP timeline in index.html.

    python3 tools/make_audio.py      # -> audio/soundtrack.wav (44.1 kHz stereo, 16-bit)
"""
import pathlib
import wave

import numpy as np

SR = 44100
DUR = 15.0
# Scene cuts - keep in sync with index.html (T1, T2, T3, D)
T1, T2, T3 = 3.0, 7.0, 10.5
BPM = 120  # 0.5 s beats: every scene cut (3.0 / 7.0 / 10.5 s) lands on a beat
BEAT = 60 / BPM
N = int(SR * DUR)
rng = np.random.default_rng(1448)  # fixed seed -> identical file on every run

L = np.zeros(N)
R = np.zeros(N)
# separate send bus for the reverb
RVB_L = np.zeros(N)
RVB_R = np.zeros(N)


def t_(d):
    return np.arange(int(SR * d)) / SR


def place(sig, at, gain=1.0, pan=0.0, rvb=0.25):
    i = int(round(at * SR))
    if i >= N:
        return
    sig = sig[: N - i] * gain
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    L[i : i + len(sig)] += sig * gl
    R[i : i + len(sig)] += sig * gr
    RVB_L[i : i + len(sig)] += sig * gl * rvb
    RVB_R[i : i + len(sig)] += sig * gr * rvb


def fft_filter(x, lo=None, hi=None):
    """Zero-phase band filter with smooth (raised-cosine) skirts."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if hi:
        g *= np.clip(1 - (f - hi) / (hi * 0.6), 0, 1) ** 2
    if lo:
        g *= np.clip((f - lo * 0.6) / (lo * 0.4), 0, 1) ** 2
    return np.fft.irfft(X * g, n)


def adsr(d, a=0.01, r=0.1, decay=None):
    t = t_(d)
    e = np.minimum(t / a, 1.0) if a > 0 else np.ones_like(t)
    if decay:
        e *= np.exp(-t / decay)
    rel = int(r * SR)
    if rel and rel < len(e):
        e[-rel:] *= np.linspace(1, 0, rel) ** 1.5
    return e


def hz(note):
    names = {"C": -9, "C#": -8, "Db": -8, "D": -7, "D#": -6, "Eb": -6, "E": -5, "F": -4, "F#": -3,
             "Gb": -3, "G": -2, "G#": -1, "Ab": -1, "A": 0, "A#": 1, "Bb": 1, "B": 2}
    name, octave = note[:-1], int(note[-1])
    return 440.0 * 2 ** ((names[name] + 12 * (octave - 4)) / 12)


# ---------------------------------------------------------------- instruments
def strings(notes, d, bright=7.0, a=0.45, r=0.6):
    """Warm ensemble pad: 3 detuned additive saw voices per note with slow vibrato."""
    t = t_(d)
    out = np.zeros(len(t))
    for note in notes:
        f0 = hz(note)
        for det in (-0.07, 0.0, 0.065):
            fv = f0 * 2 ** (det / 12)
            ph = rng.uniform(0, 2 * np.pi)
            vib = 0.0035 * np.sin(2 * np.pi * (5.1 + det * 4) * t + ph)
            phase = 2 * np.pi * fv * np.cumsum(1 + vib) / SR
            for k in range(1, 14):
                if fv * k > 9000:
                    break
                out += np.sin(k * phase + ph * k) / k * np.exp(-k / bright)
    out /= max(1, len(notes)) * 3
    return out * adsr(d, a=a, r=r)


def oud(note, d=1.4, gain=1.0, slide=0.0):
    """Karplus-Strong pluck with a bright plectrum attack (oud-like)."""
    f0 = hz(note)
    P = int(SR / f0)
    n = int(SR * d)
    buf = rng.uniform(-1, 1, P)
    buf = np.convolve(buf, [0.5, 0.5], mode="same")  # slightly soften the excitation
    out = np.zeros(n + P)
    out[:P] = buf
    decay = 0.996
    # Block-wise vectorised KS: each period depends only on the previous one.
    i = P
    while i < n:
        prev = out[i - P : i]
        nxt = decay * 0.5 * (prev + np.roll(prev, 1))
        m = min(P, n - i)
        out[i : i + m] = nxt[:m]
        i += P
    y = out[:n]
    if slide:
        tt = np.arange(n)
        idx = np.clip(tt * (1 + slide * np.minimum(tt / (0.08 * SR), 1)), 0, n - 1)
        y = np.interp(idx, tt, y)
    # body resonance + pick click
    y = y + 0.25 * fft_filter(y, lo=180, hi=900)
    y[: int(0.004 * SR)] += rng.uniform(-0.4, 0.4, int(0.004 * SR))
    return y * adsr(d, a=0.001, r=0.25) * gain


def frame_drum(gain=1.0):
    d = 0.6
    t = t_(d)
    f = 62 * np.exp(-t / 0.08) + 48
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
    slap = fft_filter(rng.uniform(-1, 1, len(t)), lo=200, hi=1800) * np.exp(-t / 0.03)
    return (body + 0.35 * slap) * gain


def tek(gain=1.0):
    d = 0.12
    t = t_(d)
    n = fft_filter(rng.uniform(-1, 1, len(t)), lo=2200, hi=7000) * np.exp(-t / 0.018)
    tone = np.sin(2 * np.pi * 820 * t) * np.exp(-t / 0.02)
    return (n + 0.5 * tone) * gain


def impact(gain=1.0, d=2.6):
    t = t_(d)
    f = 70 * np.exp(-t / 0.25) + 34
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.75)
    crack = fft_filter(rng.uniform(-1, 1, len(t)), lo=60, hi=2600) * np.exp(-t / 0.12)
    air = fft_filter(rng.uniform(-1, 1, len(t)), lo=5000, hi=14000) * np.exp(-t / 0.9) * 0.18
    return (boom + 0.55 * crack + air) * gain


def shimmer(d=1.0, density=26, lo=2600, hi=7800, gain=1.0):
    """Cluster of tiny bell pings: golden particle sparkle."""
    out = np.zeros(int(SR * d) + int(SR * 0.6))
    for _ in range(int(density * d)):
        f = rng.uniform(lo, hi)
        at = rng.uniform(0, d)
        tt = t_(0.5)
        s = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.09) * rng.uniform(0.3, 1)
        i = int(at * SR)
        out[i : i + len(s)] += s
    env = np.ones(len(out))
    fade = int(0.08 * SR)
    env[:fade] = np.linspace(0, 1, fade)
    return out * env * gain / 4


def whoosh(d=0.6, f_from=300, f_to=5000, gain=1.0):
    """Filtered-noise swoosh with a sweeping band (chunked FFT filtering)."""
    n = int(SR * d)
    noise = rng.uniform(-1, 1, n + 4096)
    out = np.zeros(n + 4096)
    hop = 1024
    win = np.hanning(2048)
    for i in range(0, n, hop):
        p = i / n
        fc = f_from * (f_to / f_from) ** p
        seg = noise[i : i + 2048]
        if len(seg) < 2048:
            break
        out[i : i + 2048] += fft_filter(seg, lo=fc * 0.5, hi=fc * 1.6) * win
    out = out[:n]
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * np.clip(t, 0, 1)) ** 1.6
    return out * env * gain


def click(f=2400, gain=1.0):
    t = t_(0.06)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.008)
    s[: int(0.002 * SR)] += rng.uniform(-0.5, 0.5, int(0.002 * SR))
    return s * gain


def pop(gain=1.0):
    t = t_(0.18)
    f = 380 + 900 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05) * gain


def heartbeat(gain=1.0):
    out = np.zeros(int(SR * 0.6))
    for at, g in ((0.0, 1.0), (0.17, 0.7)):
        t = t_(0.3)
        f = 58 * np.exp(-t / 0.05) + 42
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09) * g
        i = int(at * SR)
        out[i : i + len(s)] += s
    return out * gain


def bell(note, d=3.0, gain=1.0):
    f0 = hz(note)
    t = t_(d)
    out = np.zeros(len(t))
    for ratio, amp, dec in ((1, 1, 1.6), (2.0, 0.45, 1.0), (2.76, 0.35, 0.7), (5.4, 0.18, 0.35), (8.93, 0.08, 0.2)):
        out += amp * np.sin(2 * np.pi * f0 * ratio * t) * np.exp(-t / dec)
    return out * adsr(d, a=0.002, r=0.3) * gain


def riser(d=0.5, gain=1.0):
    t = t_(d)
    f = 400 * (6 ** (t / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.2
    n = fft_filter(rng.uniform(-1, 1, len(t)), lo=1500, hi=9000)
    return (tone + n) * (t / d) ** 2 * gain


def bass(note, d, gain=1.0):
    t = t_(d)
    f = hz(note)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t)
    return s * adsr(d, a=0.08, r=0.4) * gain


# ---------------------------------------------------------------- music bed
# Chord pads (start, end, notes)
chords = [
    (0.0, 3.0, ["G3", "Bb3", "D4"], "G1"),
    (3.0, 5.0, ["Eb3", "G3", "Bb3"], "Eb2"),
    (5.0, 7.0, ["C3", "Eb3", "G3"], "C2"),
    (7.0, 9.0, ["G3", "Bb3", "D4"], "G1"),
    (9.0, 10.5, ["D3", "F#3", "A3"], "D2"),
    (10.5, 12.0, ["C3", "Eb3", "G3"], "C2"),
    (12.0, 15.0, ["D3", "F#3", "A3", "D4"], "D2"),  # resolution: D major
]
for s, e, notes, b in chords:
    final = s >= 12.0
    d = e - s + (0.0 if final else 0.5)  # overlap into the next chord for legato
    gain = 0.30 if not final else 0.38
    place(strings(notes, d, bright=6.5 if not final else 8.5, a=0.35 if s else 0.05, r=0.5 if not final else 1.6), s, gain, pan=-0.15, rvb=0.6)
    place(strings([n[:-1] + str(int(n[-1]) + 1) for n in notes[:2]], d, bright=4.5, a=0.5, r=0.5), s, gain * 0.35, pan=0.25, rvb=0.7)
    place(bass(b, d, 0.32), s, 1.0, rvb=0.1)

# Drone fifth under scene 1
place(strings(["D2", "A2"], 3.4, bright=3.0, a=0.02, r=0.8), 0.0, 0.22, rvb=0.4)

# Oud melody: Hijaz descent in scene 1, sparse answers later, hopeful arpeggio at the end
oud_notes = [
    (0.50, "A4"), (0.75, "Bb4"), (1.00, "A4"), (1.25, "G4"), (1.50, "F#4"), (1.75, "Eb4"), (2.00, "D4"),
    (2.50, "F#4"), (2.62, "G4"),
    (3.00, "G4"), (3.50, "A4"), (4.25, "D5"), (4.50, "C5"), (5.25, "Bb4"), (5.50, "A4"), (6.00, "G4"),
    (7.00, "G4"), (7.25, "A4"), (7.50, "Bb4"), (8.25, "A4"), (8.50, "G4"), (9.00, "F#4"), (9.50, "A4"), (10.00, "Eb4"),
    (10.75, "D4"), (10.95, "F#4"), (11.15, "A4"), (11.35, "D5"),
    (12.00, "D5"), (12.25, "C5"), (12.50, "Bb4"), (12.75, "A4"), (13.25, "F#4"), (13.75, "D4"),
]
for i, (at, n) in enumerate(oud_notes):
    pan = 0.3 if i % 2 else 0.15
    d = 2.2 if at >= 13.7 else 1.3
    place(oud(n, d=d, slide=0.0), at, 0.42, pan=pan, rvb=0.35)
    # octave-down doubling for warmth on important notes
    if at in (2.0, 4.25, 11.35, 12.0, 13.75):
        place(oud(n[:-1] + str(int(n[-1]) - 1), d=d), at, 0.28, pan=-0.2, rvb=0.35)

# Percussion: elegant half-time frame drum + light darbuka taps from scene 2
for k in range(int(DUR / BEAT)):
    at = k * BEAT
    if at < T1 or at >= 14.0:
        continue
    bar_pos = k % 4
    if bar_pos in (0, 2):
        place(frame_drum(), at, 0.30 if bar_pos == 0 else 0.2, rvb=0.2)
    if T1 <= at < T3:
        place(tek(), at + BEAT * 0.5, 0.08, pan=0.4, rvb=0.15)
        if bar_pos == 3:
            place(tek(), at + BEAT * 0.75, 0.06, pan=-0.4, rvb=0.15)

# ---------------------------------------------------------------- SFX cue sheet
# Scene 1 - Makkah reveal
place(impact(1.0), 0.0, 0.85, rvb=0.5)
place(shimmer(0.7, density=30), 0.08, 0.5, pan=0.2, rvb=0.6)
for i in range(4):  # "2027" digits
    place(click(3200 + 300 * i), 0.32 + 0.07 * i, 0.12, pan=-0.3 + 0.2 * i)
place(impact(0.6, d=1.8), 0.90, 0.55, rvb=0.5)  # "HAJI?"
place(whoosh(0.45, 600, 6000), 1.38, 0.22, pan=0.3)
place(whoosh(0.7, 250, 7000), 2.62, 0.45, pan=-0.2, rvb=0.4)

# Scene 2 - official listing
place(impact(0.4, d=1.4), 3.0, 0.4, rvb=0.6)
place(click(1800), 3.30, 0.18)
place(shimmer(0.6, density=24, lo=3000, hi=9000), 3.25, 0.4, pan=-0.2)
place(shimmer(0.6, density=40), 3.55, 0.6, pan=0.2, rvb=0.6)  # particles flow into the name
place(pop(), 4.25, 0.35)
place(frame_drum(1.0), 4.25, 0.25)
place(click(2600), 4.27, 0.15)
place(whoosh(0.35, 1200, 6000), 4.70, 0.15, pan=0.3)
place(bell("D6", d=2.0), 5.25, 0.18, pan=0.1, rvb=0.6)
place(shimmer(0.7, density=22, lo=4000, hi=10000), 5.70, 0.35, pan=0.3, rvb=0.6)
place(whoosh(0.7, 250, 7000), 6.65, 0.42, pan=0.2, rvb=0.4)

# Scene 3 - healthcare experience
place(whoosh(0.5, 2000, 400), 7.0, 0.2, rvb=0.3)
place(heartbeat(1.0), 7.35, 0.55, rvb=0.15)
place(heartbeat(1.0), 8.05, 0.45, rvb=0.15)
place(click(2000), 7.85, 0.2)
place(click(2800), 7.95, 0.14)
for i, at in enumerate((8.35, 8.80, 9.25)):
    place(pop(), at, 0.32, pan=-0.2 + 0.2 * i)
    place(click(2400 + 200 * i), at + 0.28, 0.2, pan=-0.2 + 0.2 * i)  # check-mark tick
    place(shimmer(0.25, density=40, lo=5000, hi=9000), at + 0.28, 0.25, pan=0.2)
place(riser(0.55), 9.95, 0.3, rvb=0.4)

# Scene 4 - WhatsApp finale
place(whoosh(0.6, 7000, 300), 10.25, 0.4, rvb=0.4)
place(impact(0.5, d=2.2), 10.5, 0.45, rvb=0.7)
place(bell("D5", d=3.2), 10.75, 0.3, pan=-0.1, rvb=0.7)  # logo chime
place(bell("A5", d=3.0), 10.90, 0.2, pan=0.2, rvb=0.7)
place(bell("D6", d=2.8), 11.05, 0.16, pan=0.0, rvb=0.7)
place(shimmer(0.9, density=26, lo=3500, hi=9500), 11.0, 0.4, rvb=0.7)
for i in range(5):
    place(click(3000 + 150 * i), 11.15 + 0.12 * i, 0.07, pan=-0.3 + 0.15 * i)
place(frame_drum(1.0), 11.75, 0.32)
place(pop(), 11.75, 0.25)
place(bell("A5", d=1.6), 12.2, 0.12, rvb=0.6)  # WhatsApp pulse ping
place(impact(0.35, d=2.8), 12.0, 0.35, rvb=0.8)  # final resolution hit
place(shimmer(1.4, density=12, lo=4000, hi=9000), 12.1, 0.25, rvb=0.8)

# ---------------------------------------------------------------- reverb + master
def reverb(x, seconds=2.4, seed=0):
    r = np.random.default_rng(seed)
    n = int(SR * seconds)
    t = np.arange(n) / SR
    ir = r.uniform(-1, 1, n) * np.exp(-t / (seconds / 5.5))
    ir = fft_filter(ir, lo=180, hi=7000)
    ir[: int(0.02 * SR)] = 0  # pre-delay
    m = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[: len(x)]
    return y / np.sqrt(np.sum(ir ** 2))


L += 0.55 * reverb(RVB_L, seed=1)
R += 0.55 * reverb(RVB_R, seed=2)

mix = np.stack([L, R], axis=1)
mix -= mix.mean(axis=0)
# gentle tanh glue, then normalise to -1 dBFS peak
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))
# short fade-in click guard and a musical tail fade over the last 0.45 s
mix[:64] *= np.linspace(0, 1, 64)[:, None]
tail = int(0.45 * SR)
mix[-tail:] *= (np.linspace(1, 0, tail) ** 2)[:, None]

out = pathlib.Path(__file__).resolve().parent.parent / "audio" / "soundtrack.wav"
out.parent.mkdir(exist_ok=True)
with wave.open(str(out), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(f"wrote {out} ({DUR:.1f} s)")
