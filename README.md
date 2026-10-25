# Klinik Nissa: Instagram Story motion infographic (20 s)

> **New ad:** `ads/100-tabs/` holds the 15 s "100 Tabs Dalam Kepala" mental-health ad (1080×1920, 30 fps, 0 Higgsfield credits). See `ads/100-tabs/README.md`.

A 20-second vertical motion infographic, rendered at **2160 × 3840 (4K), 60 fps** from a 1080 × 1920 composition in Bahasa Melayu, built with
**HyperFrames + GSAP**. All visuals are code-driven: CSS, SVG, MorphSVG and DrawSVG. The soundtrack is synthesised locally.

**Higgsfield credits used: 4 / 50.** That is two 4K image upscales at 2 credits each: one for the panel logos and one for the
original Klinik Nissa logo. There is no AI video, image or audio generation and no paid stock.

Final render: `renders/klinik-nissa-ig-story-20s-4k60.mp4`

WhatsApp Status version: `renders/klinik-nissa-whatsapp-status-20s.mp4`. It is 1080 × 1920 at 30 fps, H.264 High, 5.6 Mbps, two-pass, 14.5 MB, under WhatsApp's 16 MB limit. It is downscaled from the 4K master and measures 51.5 dB PSNR against it (visually lossless). Rebuild it with `npm run whatsapp`.

## Storyboard

| Time | Scene | What happens |
| --- | --- | --- |
| 0:00–2.0 | Hook | Turquoise cross spins in and morphs into a clock. "NAK DATANG KLINIK?" and "CHECK WAKTU DULU! ⏰" slam in with camera shake, then a yellow flash. |
| 2.0–6.5 | Waktu operasi | A floating 3D calendar and magnetic sliding glass cards on a timeline. All three rows are held on screen together (about 2 s). Paper-cut transition out. |
| 6.5–12.5 | Perkhidmatan kami | Service 01 (mental health) appears as a hero card with an animated brain icon. Services 02–17 then fold in as a numbered two-column grid. The full list holds for about 3 s. |
| 12.5–16.0 | Senarai panel kami | The 12 panel logos flip in on white cards (3 × 4) and hold for about 1.5 s. |
| 16.0–20.0 | CTA | The logo rises on a clean gradient (the decorative "+" elements fade out). Name, operating hours and the WhatsApp number with a pulsing icon stay readable until the end. |

Scene cut times live in one place: `const D, T2, T3, TP, T4` in `index.html` and the matching line in `tools/make_audio.py`.

All content stays between y ≈ 250 and y ≈ 1545, inside the Instagram Story safe zone.

## Content (from the clinic's services poster; verify before posting)

**Waktu operasi:** Isnin – Jumaat 9.00 pagi – 6.00 petang · Sabtu 9.00 pagi – 2.00 petang · Ahad tutup
**WhatsApp:** 012-608 1411

**Perkhidmatan kesihatan dan rawatan**
1. Konsultasi, saringan dan rawatan kesihatan mental
2. Pemeriksaan kesihatan Haji
3. Program penurunan berat badan
4. Kesihatan am
5. Cuci atau jahit luka
6. Masalah kulit
7. Rawatan asma (Nebulizer)
8. ECG (Pemeriksaan jantung)
9. Pap Smear
10. Sedut Kahak
11. Check Kuning Bayi
12. Sunat Bayi Perempuan
13. Pemeriksaan kesihatan
14. Ibu mengandung
15. Kesihatan wanita dan kanak-kanak
16. Vaksinasi
17. Dan lain-lain lagi

**Senarai panel:** PMCare, AIA, Etiqa+, ASP, eMAS, Perodua, FOMEMA, MAINS, Great Eastern, RedAlert Online, HealthMetrics, MedKad.

## Assets

- **Logo.** `assets/klinik-nissa-emblem.svg` (used in the video) and `assets/klinik-nissa-logo.png` / `tools/klinik-nissa-logo.svg` (full logo with wordmark).
  They are vectors rebuilt from the clinic's own poster by `tools/trace_logo.py`:
  1. The logo crop was first upscaled to 4K with Higgsfield (bytedance upscaler).
  2. The ring is a fitted circle.
  3. The leaves and figure are traced from the upscale.
  4. The brain is redrawn from its centre line.
  5. The wordmark is set in Poppins Bold.

  Because the logo is a vector, it stays sharp at any render resolution.
- **Panel logos.** `assets/panels/*.png` were cut from a 4K Higgsfield upscale of the poster's panel card by `tools/extract_panels.py`, with the turquoise card keyed out.
  `tools/fix_panel_text.py` then fixes the letters the upscaler invented:
  - ASP's band is repainted as "Electronic Health Care Cards".
  - RedAlert's tagline is repainted as "Realtime Electronic Data".
  - eMAS's tagline is removed, because it is illegible in the source.
  - On the MAINS crest, the curved fine print and calligraphy come from the original pixels.

  If official high-resolution panel logos are available, drop them into `assets/panels/` with the same file names.

## Rebuild

```bash
npm ci
npm run audio      # regenerate audio/soundtrack.wav (deterministic)
npm run lint
npm run render:preview   # quick 1080p30 draft
npm run render           # -> renders/klinik-nissa-ig-story-20s-4k60.mp4 (2160x3840, 60 fps; local, free)
```

To render in a sandbox without Chrome downloads, point HyperFrames at a local headless Chromium:
`HYPERFRAMES_BROWSER_PATH=/path/to/headless_shell npm run render`.

Regenerating the logo or panel crops needs the poster frame, the two upscales and `pip install potracer numpy pillow`:

```bash
python3 tools/trace_logo.py <poster_frame.png> 420 25 240 230 <logo_crop_upscaled.png>
python3 tools/extract_panels.py <panel_region_upscaled.png> 560 750 360
python3 tools/fix_panel_text.py <poster_frame.png> <panel_region_upscaled.png> 560 750 360
```

## Audio

`tools/make_audio.py` synthesises a 120 BPM upbeat bed (C–G–Am–F) and the SFX cue sheet from oscillators and noise:
impact, whoosh, slam, tick, UI click, pop cascade and outro chime.
The SFX cues are timed to the GSAP timeline. It is original and royalty-free by construction.
The video works without sound because every piece of information is on screen.
