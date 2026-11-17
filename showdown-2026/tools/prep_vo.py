"""Tighten the ElevenLabs voiceover takes and write their speech segments.

For each chosen take: decode to 48 kHz mono, shorten internal pauses longer than
MAX_GAP, speed up by TEMPO (ffmpeg atempo, pitch preserved), then detect the
speech segments again so captions can follow the real phrasing.

    python3 showdown-2026/tools/prep_vo.py
"""
import json, pathlib, subprocess, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "media" / "vo"
OUT = ROOT / "media" / "vo_prep"
OUT.mkdir(exist_ok=True)
SR = 48000
TEMPO = 1.10
MAX_GAP = 0.55
TAKES = {1: "s1b", 2: "s2a", 3: "s3b", 4: "s4a", 5: "s5a", 6: "s6a", 7: "s7b"}


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def speech_mask(x, thr_db=-40, win=0.02):
    n = int(SR * win)
    frames = len(x) // n
    rms = np.sqrt(np.mean(x[: frames * n].reshape(frames, n) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    return db > thr_db, n


def segments(x, min_gap=0.25):
    m, n = speech_mask(x)
    segs, start, last = [], None, None
    for i, s in enumerate(m):
        t = i * n / SR
        if s:
            if start is None:
                start = t
            elif t - last > min_gap:
                segs.append([start, last + n / SR]); start = t
            last = t
    if start is not None:
        segs.append([start, last + n / SR])
    return segs


def write(path, x):
    y = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


meta = {}
for scene, take in TAKES.items():
    x = load(SRC / f"{take}.mp3")
    segs = segments(x)
    # rebuild with pauses capped; keep 40 ms lead-in and 120 ms tail
    pieces, pad = [], int(0.04 * SR)
    for i, (a, b) in enumerate(segs):
        ia, ib = max(0, int(a * SR) - pad), min(len(x), int(b * SR) + pad)
        pieces.append(x[ia:ib])
        if i < len(segs) - 1:
            gap = segs[i + 1][0] - b
            pieces.append(np.zeros(int(min(gap, MAX_GAP) * SR)))
    y = np.concatenate(pieces + [np.zeros(int(0.12 * SR))])
    tmp = OUT / f"_tmp{scene}.wav"
    write(tmp, y)
    dst = OUT / f"vo{scene}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af", f"atempo={TEMPO}", "-ar", str(SR), str(dst)], check=True)
    tmp.unlink()
    z = load(dst)
    meta[scene] = {"take": take, "duration": round(len(z) / SR, 3),
                   "segments": [[round(a, 3), round(b, 3)] for a, b in segments(z)]}
    print(scene, take, meta[scene]["duration"], meta[scene]["segments"])

(OUT / "vo_meta.json").write_text(json.dumps(meta, indent=1))
