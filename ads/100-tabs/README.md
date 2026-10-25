# Klinik Nissa: "100 Tabs Dalam Kepala" (15 s, 9:16)

This is a 15-second Instagram Story / Reels / TikTok / WhatsApp Status ad for **Konsultasi & Saringan Kesihatan Mental**.
It is 1080 × 1920 at 30 fps, in Bahasa Melayu, and built with **HyperFrames + GSAP**.
All motion is deterministic code: CSS 3D, SVG, MorphSVG, DrawSVG and procedural particles. The soundtrack is synthesised locally.

**Higgsfield credits used: 0 / 50.** No AI video, image, audio or upscale was needed.
The logo is the clinic's own file, "Klinik Nissa Logo Clean.png" from Google Drive, with the navy background keyed out locally.

| File | Use |
| --- | --- |
| `renders/klinik-nissa-100-tabs-15s.mp4` | Master: H.264 1080×1920 30 fps, AAC, 19.7 MB |
| `renders/klinik-nissa-100-tabs-15s-whatsapp.mp4` | WhatsApp Status: 6.5 Mbps two-pass, 12.6 MB (under the 16 MB limit) |

## Storyboard

| Time | Beat | What happens |
| --- | --- | --- |
| 0.0–2.0 | Pattern interrupt | Frame 0 already shows a browser window mid-pop with tabs flying. The tab strip multiplies and about 60 tabs fly at the camera while the perspective collapses (a dolly zoom). "KEPALA / MACAM ADA" punches in letter by letter. A giant extruded 3D **"100"** rushes in from deep space and lands on the bass hit with a 4-frame RGB-split glitch, a spark burst and camera shake. Then "TABS?!" lands. The camera pushes through the "0". |
| 2.0–4.5 | Controlled chaos | About 120 tabs stream through a 3D tunnel. Six foreground tabs pop open with a ping each: KERJA, DUIT, TIDUR, OVERTHINKING, MASA DEPAN, EMOSI. They drift at different depths, bounce on the beat, and their favicons spin like loading icons. The "OTAK ASYIK BERFIKIR?" notification snaps down with squash and overshoot, then buzzes. |
| 4.5–6.5 | Emotional reset | The music cuts to silence and every tab freezes. A turquoise pulse radiates out. The browser outline **morphs** (MorphSVG) into a brain while the camera orbits, and every frozen tab is pulled onto the brain outline as a spark. The neural network draws in and data flows along it. "MINDA PUN / PERLUKAN / PERHATIAN." |
| 6.5–10.5 | Services | The brain outline morphs into two card outlines (cyan and yellow). The cards swing in with a perspective entry and a magnetic snap. Card 1 is a glossy 3D speech bubble with a brain: **KONSULTASI / KESIHATAN MENTAL**. Card 2 is an assessment checklist with a glowing medical indicator: **SARINGAN / KESIHATAN MENTAL**. Light sweeps run across both, and both cards hold together for about 2 s. |
| 10.5–15.0 | Brand + CTA | Both cards converge into a light burst and the official logo lands, followed by a masked light sweep. Then KLINIK NISSA, "KONSULTASI & SARINGAN / KESIHATAN MENTAL" and "TAK PERLU TUNGGU SAMPAI TERUK." appear. The yellow WhatsApp panel ("WHATSAPP SEKARANG", **012-608 1411**, the largest type in the frame) has a pulsing icon. It is stable from about 13.4 s to the end. |

Colour story: coral, violet and sky accents exist only while the head is overloaded. From the brain reveal onwards, the palette is only the brand colours: navy `#102849`, cyan `#26D6D2`, yellow `#FFE100` and white.

Essential text stays between y ≈ 262 and y ≈ 1512, inside the Instagram Story and TikTok safe zones.
There are no flashes above about 75 % opacity, and the only strobe-like effect is the 4-frame glitch.

## Copy (verify before posting)

KEPALA MACAM ADA 100 TABS?! · KERJA · DUIT · TIDUR · OVERTHINKING · MASA DEPAN · EMOSI · OTAK ASYIK BERFIKIR? ·
MINDA PUN PERLUKAN PERHATIAN. · KONSULTASI / SARINGAN KESIHATAN MENTAL · KLINIK NISSA ·
TAK PERLU TUNGGU SAMPAI TERUK. · WHATSAPP SEKARANG · 012-608 1411

The ad makes no health promises or diagnosis claims.

## Sound

`tools/make_audio.py` writes `audio/soundtrack.wav`. It is an original 120 BPM electronic bed, so every scene cut lands on a beat:

- **0–4.5 s:** Am–F–C driving arp.
- **4.50–4.62 s:** hard silence.
- **4.62–6.5 s:** Fmaj7 pad with plucks and a riser.
- **6.5–10.5 s:** C–G–Am–F groove.
- **10.5–15 s:** F–G–C, ending in a chime with a short fade (no abrupt cut).

The SFX are cued to the GSAP timeline:

- Pops as the tab strip multiplies.
- A bass impact and glitch on "100".
- A digital ping and UI click for each labelled tab.
- A notification ding and phone buzz.
- A pulse swell with shimmer at the brain reveal.
- A click, snap and tick for each card and checklist item.
- The logo impact, the CTA chime and a final impact.

The mix is about −15 LUFS with peaks under −1 dBTP. Every message is on screen, so the ad still works on mute.

## Rebuild

From the repo root, after `npm ci`:

```bash
cd ads/100-tabs
python3 tools/make_audio.py                 # deterministic soundtrack
npx hyperframes lint .
npx hyperframes render . -f 30 -q high --resolution portrait -o renders/klinik-nissa-100-tabs-15s.mp4
```

In a sandbox without a Chrome download, set `HYPERFRAMES_BROWSER_PATH` to a local `chrome-headless-shell` first.

Rebuild the WhatsApp encode from the master:

```bash
O="-c:v libx264 -preset slow -profile:v high -level 4.1 -pix_fmt yuv420p -b:v 6500k -maxrate 9000k -bufsize 13000k"
ffmpeg -y -i renders/klinik-nissa-100-tabs-15s.mp4 $O -pass 1 -an -f null /dev/null
ffmpeg -y -i renders/klinik-nissa-100-tabs-15s.mp4 $O -pass 2 -c:a aac -b:a 128k -movflags +faststart renders/klinik-nissa-100-tabs-15s-whatsapp.mp4
```

The scene cut times live in `const D, T1, T2, T3, T4` in `index.html` and must match the same constants in `tools/make_audio.py`.

## Assets

- `assets/klinik-nissa-emblem.png` and `assets/klinik-nissa-logo.png`: the official logo, keyed from Drive (1024 px source).
- Fonts: Unbounded 700–900 (SIL OFL, `assets/fonts/UNBOUNDED-OFL.txt`) for headlines. Poppins 600–900 for the wordmark and service names, to match the logo.
- `assets/vendor/`: GSAP 3.13 with MorphSVG and DrawSVG, the same files as the main project.
