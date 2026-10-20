# Klinik Nissa: Instagram Story motion infographic (15 s)

A 15-second vertical (1080 × 1920, 30 fps) motion infographic in Bahasa Melayu, built with
**HyperFrames + GSAP**. All visuals are code-driven: CSS, SVG, MorphSVG and DrawSVG. The soundtrack is synthesised locally.

**Higgsfield credits used: 0 / 50.** No AI video, image or audio generation, no paid stock and no upscaling.

Final render: `renders/klinik-nissa-ig-story-15s.mp4`

## Storyboard

| Time | Scene | What happens |
| --- | --- | --- |
| 0:00–1.5 | Hook | Turquoise cross spins in and morphs into a clock. "NAK DATANG KLINIK?" and "CHECK WAKTU DULU! ⏰" slam in with camera shake, then a yellow flash. |
| 1.5–6.5 | Waktu operasi | A floating 3D calendar, then magnetic sliding glass cards on a timeline. At the end all three rows are held on screen together. |
| 6.5–11.5 | Perkhidmatan kami | Four glossy service cards fold in, each with an animated SVG icon (brain, stethoscope + ECG, shield + family, scale + checklist). |
| 11.5–15 | CTA | The logo rises from a rotating medical cross. Name, operating hours and the WhatsApp number with a pulsing icon stay readable until the end. |

All content stays between y ≈ 250 and y ≈ 1530, inside the Instagram Story safe zone.

## Content (verify before posting)

- Isnin – Jumaat: 9.00 pagi – 6.00 petang
- Sabtu: 9.00 pagi – 2.00 petang
- Ahad: tutup
- WhatsApp: 012-608 1411
- Services: Kesihatan Mental · Rawatan Am & ECG · Vaksinasi & Kesihatan Keluarga · Program Penurunan Berat Badan & Saringan Haji

## Logo

`assets/klinik-nissa-logo.png` is currently an **interim vector redraw** of the Klinik Nissa logo
(made by `tools/make_logo_placeholder.py`), because the original file wasn't available in the repo.
To use the original:

1. Save the original logo as `assets/klinik-nissa-logo.png`. Use the square 1024 × 1024 version with the emblem centred.
2. Run `npm run render`.

The CTA scene crops the circular emblem out of that square layout (`#s4-logo img` in `index.html`).
If the original file has a different size or framing, adjust those four numbers.

## Rebuild

```bash
npm ci
npm run audio      # regenerate audio/soundtrack.wav (deterministic)
npm run lint
npm run render     # -> renders/klinik-nissa-ig-story-15s.mp4 (~1 min, local, free)
```

To render in a sandbox without Chrome downloads, point HyperFrames at a local headless Chromium:
`HYPERFRAMES_BROWSER_PATH=/path/to/headless_shell npm run render`.

## Audio

`tools/make_audio.py` synthesises a 120 BPM upbeat bed (C–G–Am–F) and the SFX cue sheet from oscillators and noise:
impact, whoosh, slam, tick, UI click, pop and outro chime.
The SFX cues are timed to the GSAP timeline. It is original and royalty-free by construction.
The video works without sound because every piece of information is on screen.
