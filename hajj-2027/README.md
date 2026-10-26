# Klinik Nissa Nilai: Hajj 1448H / 2027M health screening (Instagram Story, 15 s)

**"The Golden Journey."** A 15-second vertical Instagram Story ad (1080 × 1920, 30 fps, H.264 + AAC) for
**Pemeriksaan Kesihatan Bakal Haji 1448H/2027M at Klinik Nissa Nilai**. It is built with **HyperFrames + GSAP**:
CSS 3D, SVG, DrawSVG and MorphSVG, procedural particles, and a synthesised soundtrack.

Final render: `renders/klinik-nissa-haji-2027-15s.mp4` (15.000 s, 450 frames, 25 MB).

**Higgsfield credits used: 0 / 50**, checked against the account balance: 154.87 before and 154.87 after.
- No AI video, image or audio generation and no upscaling.
- The MP4 is rendered locally with the HyperFrames CLI (headless Chromium + ffmpeg).

The copy contains no dates, countdowns, prices or availability claims, so the ad can be reposted daily.

## Storyboard

A single gold line runs through the whole ad and morphs from shape to shape: Islamic arch → glass listing panel → medical dashboard → ring → final card.

| Time | Scene | What happens |
| --- | --- | --- |
| 0:00–3.0 | Makkah reveal | Frame 0 already shows the gold arch with the Kaabah inside. A 2.5D dolly-in on the photo moves against the arch, sky rays and particles. A gold ring forms around a large "2027". "BAKAL JEMAAH / HAJI?" lands with an impact, then "DAH BUAT PEMERIKSAAN / KESIHATAN?" follows. |
| 3.0–7.0 | Official listing | The arch morphs into a glass panel. A 3D extruded turquoise cross rotates in inside an 8-point star, which later morphs into a 16-point rosette. Gold particles flow into "KLINIK NISSA NILAI". The letters of "KLINIK BERDAFTAR" snap together. Then "TERSENARAI UNTUK PEMERIKSAAN / KESIHATAN BAKAL HAJI" and a "1448H / 2027M" gold badge appear. The full message holds for about 1.5 s. |
| 7.0–10.5 | Healthcare experience | The panel morphs into a dashboard ("SEBELUM KE TANAH SUCI / PERSIAPAN KESIHATAN"). A stethoscope draws itself in and morphs into a checklist. Three glossy icon rows spring in, each with a check mark: TEKANAN DARAH, PEMERIKSAAN KESIHATAN, PENILAIAN DOKTOR. |
| 10.5–15.0 | WhatsApp finale | The graphics merge into the logo with a gold flare and shockwave, then the logo reveal and light sweep play. The background switches to the navy-and-gold geometric environment, and the ring opens into the final card. **All final copy is in place by 12.0 s and holds still until 15.0 s (3 s), with no fade-out.** The WhatsApp icon pulses once. |

On-screen copy (Bahasa Melayu):
- **Scene 4 card:** KLINIK NISSA NILAI · PEMERIKSAAN KESIHATAN · BAKAL HAJI 2027 · TERSENARAI SEBAGAI FASILITI PEMERIKSAAN KESIHATAN BAKAL HAJI · WHATSAPP UNTUK TEMU JANJI · **012-608 1411**.
- **No claims of:** guaranteed clearance, Hajj approval, Tabung Haji endorsement, prices, packages or availability.
- **No official marks:** there are no seals, stamps or certificates.

Essential copy sits between y ≈ 300 and y ≈ 1580, inside the Instagram Story safe area. The scene cut times are defined in one place, `const D, T1, T2, T3` in `index.html`, with a matching line in `tools/make_audio.py`.

## Assets and licensing

- **Logo:** `assets/klinik-nissa-logo-original.png` is the clinic's own file, "Klinik Nissa Logo Clean.png" from Google Drive. It is used **unaltered**. A soft radial mask blends its navy background (#062750) into a background of the same colour.
- **Kaabah photo:** `assets/masjidil-haram.jpg`, from [Wikimedia Commons: "Mosquée Masjid el Haram à la Mecque.jpg"](https://commons.wikimedia.org/wiki/File:Mosqu%C3%A9e_Masjid_el_Haram_%C3%A0_la_Mecque.jpg).
  - **Licence:** public domain, released by the photographer (Flickr user "Tab59", 2010). No attribution is required.
  - **Treatment:** the photo is only resized, cropped by the arch window and zoomed or panned. The Kaabah itself is not edited or distorted.
  - **Rejected alternative:** a Commons file tagged CC0 ("Masjid al-Haram 2022.jpg") was not used, because its source credit points to a news-agency gallery.
- **Fonts:** Poppins (SIL Open Font License).
- **Code:** GSAP 3.13 with the DrawSVG and MorphSVG plugins.
- **Audio:** `tools/make_audio.py` synthesises everything from oscillators, Karplus-Strong plucks and noise, so it is original and royalty-free. There are no vocals, recitation or samples.
  - **Music:** an instrumental in D Hijaz (warm strings, oud-like melody, frame drum and darbuka taps) that resolves to D major.
  - **SFX:** opening impact, particle shimmer, swooshes, UI clicks, heartbeat and the logo chime, timed to the timeline.
  - **Without sound:** every message is on screen, so the ad still works muted.

## Rebuild (local, no credits)

```bash
npm ci                                  # in the repository root
npm run hajj:audio                      # regenerate audio/soundtrack.wav (deterministic)
npm run hajj:lint
npm run hajj:render                     # -> hajj-2027/renders/klinik-nissa-haji-2027-15s.mp4
```

In a sandbox without a Chrome download, add `HYPERFRAMES_BROWSER_PATH=/path/to/chrome-headless-shell` before the render command.
