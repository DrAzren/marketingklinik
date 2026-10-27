# Klinik Nissa: Program Penurunan Berat Badan (15 s ad)

A 15-second vertical ad for Instagram Story, Reels, TikTok and WhatsApp Status. It is 1080 × 1920 at 30 fps, all on-screen text is in Bahasa Melayu, and it is built with **HyperFrames + GSAP**.
Every visual is code-driven: HTML, CSS 3D transforms, SVG, DrawSVG, and deterministic particles. The soundtrack is synthesised locally.

**Higgsfield credits used: 0 / 50.** There is no AI video, image or audio generation, no upscaling and no paid stock.

Final render: `renders/klinik-nissa-berat-badan-15s.mp4`. It is H.264 High + AAC, 15.0 s and 12.7 MB, which is under WhatsApp Status's 16 MB limit.

## Storyboard

| Time | Scene | What happens |
| --- | --- | --- |
| 0:00–2.0 | Hook | A glowing digital scale slams in and the camera dolly-zooms against the grid floor. Measurement rings, sparks and shards burst out. "NAK TURUN" / "BERAT BADAN?" / "TENGOK NI!" slam in on the beats, then fly apart. |
| 2.0–4.5 | Medical reveal | The scale plate stands up and becomes a glossy medical hub with a stethoscope that draws itself and an ECG pulse. Metabolic-health icons (apple, water, heart, leaf) orbit it. "PROGRAM / PENURUNAN BERAT BADAN / DI KLINIK NISSA" has a metallic light sweep. The hub then pushes through the lens. |
| 4.5–8.5 | Three free benefits | Three glass cards fly in from depth with turquoise particle trails and snap magnetically into a stack (5.0 / 5.75 / 6.5 s): PERCUMA KONSULTASI, PERCUMA UJIAN DARAH and PERCUMA ANALISIS KOMPOSISI BADAN. All three are held together for about 1.8 s. |
| 8.5–10.5 | Body composition | The camera pushes through the body-scan icon into a dashboard. A hologram body is scanned by a beam, with LEMAK BADAN and JISIM OTOT gauges and symbolic bars. No values or patient results are shown. |
| 10.5–15.0 | RM850 + CTA | Everything collapses to the centre and a golden light sweeps across. "SERENDAH" appears, then a giant 3D "RM850" slams in with shockwaves. The price docks into the final card: logo, programme, the three free items, WHATSAPP SEKARANG 012-608 1411 and the terms line. It is settled by 12.0 s and holds still for the last 3 s, with one WhatsApp pulse and a logo light sweep. |

Scene cuts live in one place: `const D, T2, T3, T4, T5, HIT` in `index.html`, matched by the same line in `tools/make_audio.py`.
All essential content stays between y ≈ 250 and y ≈ 1500, inside the Instagram Story safe zone.

## Compliance choices (verify before posting)

- **No injection pens.** Showing pen injectors in consumer advertising implies prescription weight-loss medication, which Malaysian medicine-advertising rules restrict. The brief's fallback is used instead: a medical consultation and metabolic-health illustration (stethoscope, ECG, healthy-lifestyle icons). No drug names, brands or packaging appear.
- **Bahasa Melayu only.** "FREE" is shown as **PERCUMA** and "Body Composition Analysis" as **ANALISIS KOMPOSISI BADAN**, with fat and muscle named in the scan scene (LEMAK BADAN, JISIM OTOT).
- **No outcomes.** There are no weight-loss claims, numbers, before/after images or testimonials. The scale display shows dashes, not a weight.
- **Terms line.** The final card shows "Tertakluk kepada syarat program & penilaian doktor."
- **Still to confirm.** The clinic should check the price, the free items and the overall ad against current KKM and Medical Advertisement Board / private-healthcare-facility advertising requirements before publishing.

## Rebuild

```bash
npm ci                       # from the repo root
npm run bb:audio             # regenerate audio/soundtrack.wav (deterministic)
npm run bb:lint
npm run bb:render            # -> berat-badan/renders/klinik-nissa-berat-badan-15s.mp4 (local, free)
```

In a sandbox without Chrome downloads, set `HYPERFRAMES_BROWSER_PATH=/path/to/chrome-headless-shell`.

## Audio

The music is a different concept from the clinic's earlier videos: **half-time future bass / trap in F minor** (Fm – Db – Ab – Eb), still on a 120 BPM grid so every cut lands on a beat. `tools/make_audio.py` synthesises it from oscillators and noise. It is original and royalty-free by construction.

| Time | Music |
| --- | --- |
| 0–2.0 s | An 808 boom and a supersaw stab on every slam, and a snare roll that builds into the cut |
| 2.0–8.5 s | Drop: gliding 808, snare on beat 3, rolling trap hats, supersaw chords that pump with the kick, and a pitched "chop" lead hook (no vocals) over the cards |
| 8.5–10.5 s | Filtered breakdown under the body scan, with a riser |
| 10.5–11.0 s | Near-silence while everything collapses |
| 11.0 s | Second drop with a cinematic sub hit on RM850 |
| 14.0 s | Ends on an open Db-major chord |

The sound effects use their own palette too: FM glass bells instead of sine chimes, liquid "bloops" for the three free cards, a pulsing scan tone, impacts and whooshes.
The master is about −14 LUFS, which matches Instagram and TikTok playback. `npm run bb:render` muxes the WAV into the MP4 unchanged, because the HyperFrames mix lowers it by about 3 dB.
The ad is fully understandable without sound.
