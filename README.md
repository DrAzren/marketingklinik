# Klinik Nissa: Instagram Story motion infographic (15 s)

A 15-second vertical (1080 × 1920, 30 fps) motion infographic in Bahasa Melayu, built with
**HyperFrames + GSAP**. All visuals are code-driven: CSS, SVG, MorphSVG and DrawSVG. The soundtrack is synthesised locally.

**Higgsfield credits used: 0 / 50.** No AI video, image or audio generation, no paid stock and no upscaling.

Final render: `renders/klinik-nissa-ig-story-15s.mp4`

## Storyboard

| Time | Scene | What happens |
| --- | --- | --- |
| 0:00–1.5 | Hook | Turquoise cross spins in and morphs into a clock. "NAK DATANG KLINIK?" and "CHECK WAKTU DULU! ⏰" slam in with camera shake, then a yellow flash. |
| 1.5–4.6 | Waktu operasi | A floating 3D calendar and magnetic sliding glass cards on a timeline. All three rows are held on screen together. Paper-cut transition out. |
| 4.6–9.0 | Perkhidmatan kami | Service 01 (mental health) appears as a hero card with an animated brain icon. Services 02–17 then fold in as a numbered two-column grid. |
| 9.0–11.6 | Senarai panel kami | The 12 panel logos flip in on white cards (3 × 4). |
| 11.6–15 | CTA | The logo rises from a rotating medical cross. Name, operating hours and the WhatsApp number with a pulsing icon stay readable until the end. |

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

- `assets/klinik-nissa-logo.png`: the original Klinik Nissa logo, rebuilt as a clean vector
  (`tools/klinik-nissa-logo.svg`) from the clinic's own poster by `tools/trace_logo.py`.
  - The ring is a fitted circle.
  - The leaves and figure are traced.
  - The brain is redrawn from its centre line.
  - The wordmark is set in Poppins Bold.

  If a high-resolution original logo file is available, save it as `assets/klinik-nissa-logo.png`
  (1024 × 1024, emblem centred) and adjust the crop numbers on `#s4-logo img` / `#s4-shine` in `index.html`.
- `assets/panels/*.png`: panel logos cut from the same poster by `tools/extract_panels.py`, with the turquoise card keyed out.

## Rebuild

```bash
npm ci
npm run audio      # regenerate audio/soundtrack.wav (deterministic)
npm run lint
npm run render     # -> renders/klinik-nissa-ig-story-15s.mp4 (~1 min, local, free)
```

To render in a sandbox without Chrome downloads, point HyperFrames at a local headless Chromium:
`HYPERFRAMES_BROWSER_PATH=/path/to/headless_shell npm run render`.

Regenerating the logo or panel crops needs the poster frame and `pip install potracer numpy pillow`:

```bash
python3 tools/trace_logo.py <poster_frame.png> 420 25 240 230
python3 tools/extract_panels.py <poster_frame.png>
```

## Audio

`tools/make_audio.py` synthesises a 120 BPM upbeat bed (C–G–Am–F) and the SFX cue sheet from oscillators and noise:
impact, whoosh, slam, tick, UI click, pop cascade and outro chime.
The SFX cues are timed to the GSAP timeline. It is original and royalty-free by construction.
The video works without sound because every piece of information is on screen.
