"""Prepare the narration lines and time the burned-in captions.

1. Each Higgsfield TTS line (media/vo/lNN.mp3) is trimmed of leading/trailing
   silence and loudness-normalised to -16 LUFS -> media/vo_prep/lNN.wav.
2. Caption chunks (timeline.json "lines") are timed inside each line. Line 5 uses
   the word timestamps from the ElevenLabs Scribe transcript (media/vo/l05_words.json).
   The others are allocated by spoken-character weight and each boundary is
   snapped to the quietest point of the speech envelope within +-0.35 s.
3. Writes captions.json and injects the CAPTIONS array into index.html.

    python3 tools/prep_vo.py
"""
import json, pathlib, re, subprocess, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
T = json.loads((ROOT / "timeline.json").read_text())
SR = 48000
OUT = ROOT / "media" / "vo_prep"
OUT.mkdir(exist_ok=True)


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def env(x, win=0.02):
    n = int(SR * win)
    k = len(x) // n
    return np.sqrt(np.mean(x[: k * n].reshape(k, n) ** 2, axis=1) + 1e-12), n


def write(path, x):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def weight(text):
    spoken = T["spoken_overrides"].get(text, text)
    w = len(re.sub(r"[^A-Za-z]", "", spoken))
    w += 4 * spoken.count(",") + 7 * spoken.count(".") + 7 * spoken.count("!") + 7 * spoken.count("?")
    return max(w, 1)


captions, meta = [], {}
for k in sorted(T["lines"], key=int):
    x = load(ROOT / f"media/vo/l{int(k):02d}.mp3")
    e, n = env(x)
    db = 20 * np.log10(e)
    thr = max(db.max() - 38, -55)
    voiced = np.where(db > thr)[0]
    s0 = max(0, voiced[0] * n - int(0.05 * SR)); s1 = min(len(x), (voiced[-1] + 1) * n + int(0.12 * SR))
    lead = s0 / SR
    y = x[s0:s1]
    tmp = OUT / f"_l{int(k):02d}.wav"; write(tmp, y)
    dst = OUT / f"l{int(k):02d}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af", "loudnorm=I=-16:TP=-2:LRA=7", "-ar", str(SR), "-ac", "1", str(dst)], check=True)
    tmp.unlink()
    dur = len(y) / SR
    at = T["vo_at"][k]
    chunks = T["lines"][k]
    words_file = ROOT / f"media/vo/l{int(k):02d}_words.json"
    if words_file.exists():
        words = [w for w in json.loads(words_file.read_text()) if w.get("type", "word") == "word"]
        idx, times = 0, []
        for c in chunks:
            cnt = len(c.split())
            ws = words[idx: idx + cnt]; idx += cnt
            times.append((ws[0]["start"] - lead, ws[-1]["end"] - lead))
    else:
        ye, yn = env(y)
        ydb = 20 * np.log10(ye)
        act = np.where(ydb > thr)[0]
        a, b = act[0] * yn / SR, (act[-1] + 1) * yn / SR
        ws = np.array([weight(c) for c in chunks], float)
        cuts = a + (b - a) * np.cumsum(ws)[:-1] / ws.sum()
        # real pauses: >= 0.18 s more than 30 dB below the loudest frame
        quiet = ydb < ydb.max() - 30
        pauses, run = [], None
        for i, q in enumerate(quiet):
            if q and run is None: run = i
            if not q and run is not None:
                if (i - run) * yn / SR >= 0.18 and run * yn / SR > a and i * yn / SR < b:
                    pauses.append(((run + i) / 2) * yn / SR)
                run = None
        snapped, used = [], set()
        for c in cuts:
            near = [p for p in pauses if abs(p - c) < 0.6 and p not in used]
            if near:
                p = min(near, key=lambda p: abs(p - c)); used.add(p); snapped.append(p); continue
            i0, i1 = int((c - 0.35) * SR / yn), int((c + 0.35) * SR / yn)
            i0 = max(i0, 0); i1 = min(i1, len(ye) - 1)
            seg = np.convolve(ye[i0:i1], np.ones(5) / 5, mode="same")
            snapped.append((i0 + int(np.argmin(seg))) * yn / SR)
        bounds = [a] + snapped + [b]
        for ci, tval in T.get("caption_bounds", {}).get(k, {}).items():
            bounds[int(ci)] = tval  # hand-checked pause position (seconds into the trimmed line)
        times = [(bounds[i], bounds[i + 1]) for i in range(len(chunks))]
    for (ta, tb), c in zip(times, chunks):
        captions.append([round(at + max(ta, 0) - 0.05, 2), round(at + tb + 0.2, 2), c])
    meta[k] = {"duration": round(dur, 3), "start": at, "end": round(at + dur, 3)}
    print(k, f"{dur:.2f}s", f"{at:.2f}-{at + dur:.2f}", [f"{t[0]:.2f}" for t in times])

# make consecutive captions never overlap
for i in range(len(captions) - 1):
    if captions[i][1] > captions[i + 1][0] - 0.04:
        captions[i][1] = round(captions[i + 1][0] - 0.04, 2)
(ROOT / "captions.json").write_text(json.dumps(captions, indent=1, ensure_ascii=False))
(OUT / "vo_meta.json").write_text(json.dumps(meta, indent=1))

html = ROOT / "index.html"
if html.exists():
    s = html.read_text()
    block = "const CAPTIONS = " + json.dumps(captions, ensure_ascii=False) + ";"
    s = re.sub(r"/\*CAPTIONS\*/.*?/\*END\*/", "/*CAPTIONS*/" + block + "/*END*/", s, flags=re.S)
    html.write_text(s)
print(len(captions), "captions")
