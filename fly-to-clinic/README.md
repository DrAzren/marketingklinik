# Klinik Nissa: "Terbang ke Klinik" 3D navigation video (20 s)

A 20-second, 9:16 (1080 × 1920, 30 fps) animated navigation ad in Bahasa Melayu. The clinic's navy-and-gold fly mascot guides the viewer from
**Exit Tol Nilai** to **Klinik Nissa, Jalan BBN 1/3C, Pusat Bandar Putra Point**, over a miniature 3D model of Bandar Baru Nilai.

Built with **HyperFrames + GSAP + Three.js**. The city, pins, arrows and soundtrack are generated in code. The mascot and the
shopfront photo are the clinic's own images.

**Higgsfield credits used: 0 / 50.** There is no AI video, image or audio generation and no paid stock.

Final render: `renders/klinik-nissa-terbang-ke-klinik-20s.mp4`. It is exactly 20.0 s: 1080 × 1920, 30 fps (600 frames),
H.264 High at about 5.8 Mbps (two-pass) with AAC 128 kbps audio, and under WhatsApp Status's 16 MB limit. The same file also suits
Instagram Stories/Reels and TikTok.

## Map accuracy

The map is not hand-drawn. `tools/build_nav_map.py` builds `assets/map-data.js` from two sources:

- **OpenStreetMap** (© OpenStreetMap contributors, ODbL) supplies every road, building footprint, park, lake, land-use plate,
  traffic signal and landmark position.
- **OSRM** (the open-source router running on OpenStreetMap) supplies the driving route from Plaza Tol Nilai to Jalan BBN 1/3C.

The script prints the route steps and where each landmark sits relative to the route:

| Along route | Landmark (OSM) | Side | Owner's directions |
| --- | --- | --- | --- |
| 0 m | Plaza Tol Nilai (toll booth node, interchange 215) | start | ✅ Exit Tol Nilai |
| 1,663 m | First traffic signal (T-junction, OSM ref NL01) → **turn RIGHT** onto Persiaran Pusat Bandar | — | ✅ first traffic light, right |
| 2,635 m | McDonald's (building, Persiaran Pusat Bandar) | left | ✅ pass McDonald's |
| 2,953 m | **Turn LEFT** onto Jalan BBN 1/3 at the KFC (Jalan Nilai Square) corner | KFC ahead-right | ⚠️ see note 1 |
| 3,070 m | Dataran Nilai | **right** | ✅ Dataran Nilai on the right |
| 3,348 m | AEON Mall Nilai | **right** | ✅ AEON on the right |
| 3,351 m | **Turn LEFT** into Pusat Bandar Putra Point, then Jalan BBN 1/3A → Jalan BBN 1/3C | — | ✅ left towards the clinic |
| 3,462 m | Jalan BBN 1/3C | arrive | ✅ |

The 3D camera is heading-up: it always looks along the direction of travel. So a landmark on the driver's right always appears on
the right of the screen. While the fly passes Dataran Nilai and AEON, the camera leans towards them so they are visibly on the right.
The camera never flips or reverses.

### Things to confirm with the clinic before posting

1. **KFC and McDonald's order.** Driving from the toll, you pass McDonald's first. The KFC is at the corner where you turn left
   onto Jalan BBN 1/3. The video says *"LEPAS MCD, DI SIMPANG KFC — BELOK KIRI"* instead of *"LEPAS KFC & MCD"*.
2. **Kolej Kediaman USIM.** It is left out. The only USIM residential college in OpenStreetMap is Kolej Kediaman 1, on the USIM campus
   about 3.5 km north of Jalan BBN 1/3C, so it is not near Putra Point. The arrival uses the verified *"PUSAT BANDAR PUTRA POINT"*
   instead. If the clinic means another building (for example a hostel USIM rents in Putra Point), send its name or a map link and
   it can be added as a pin.
3. **Exact shop lot.** The pin is on Jalan BBN 1/3C. No. 9697 is not in OpenStreetMap or any public listing, so the pin marks the
   street, not one lot. On arrival the pin shows the clinic's own photo of its front signage (`assets/klinik-nissa-signage.jpg`,
   supplied by the clinic). No shopfront is modelled or invented.
4. **Building heights.** Footprints come from OpenStreetMap. Heights are estimated (×1.3 for the miniature look) because OSM has no
   height data here. Trees are a stylised, deterministic scatter and do not mark real trees.

## Storyboard

The choreography is written on a 15 s story clock and played over 20 s through one smooth time warp (`WARP_KEYS` in
`assets/world.js` and `tools/make_nav_audio.py`). The Exit Tol Nilai hold and the arrival get the most extra time. Wing beats,
bobbing and pulses run on real time, so nothing looks slow-motion.

| Time | Scene | What happens |
| --- | --- | --- |
| 0.0–2.7 | Hook | Aerial view of Nilai. The fly zooms up to the lens, then loops round a giant floating pin. "NAK KE KLINIK NISSA?" and "IKUT LALUAN INI!" appear. The camera swoops down to the toll. |
| 2.7–4.6 | Exit Tol Nilai (starting point) | The fly hovers just past the toll plaza canopy. A big yellow pin carries the "EXIT TOL NILAI · MULA DI SINI" label, held for about 2.2 s with the toll in view. |
| 4.6–6.9 | First traffic light | The fly speeds down the link road with a glowing trail and hovers at the first traffic light, which turns green. It looks back at the viewer, then banks right. A 3D arrow rises from the road and the banner reads "BELOK KANAN". |
| 6.9–9.6 | McD and KFC | Wing-powered burst. McDonald's (red/gold block) on the left and KFC at the corner, each with a pin and label. A left-turn arrow and the banner "BELOK KIRI". |
| 9.6–11.8 | Dataran Nilai | The plaza, with a pin and "SEBELAH KANAN" label, sits on the right. |
| 11.8–13.7 | AEON Nilai | The AEON mall (magenta roof) with "SEBELAH KANAN". Banner "SELEPAS AEON NILAI — BELOK KIRI" and a left-turn arrow. |
| 13.7–17.0 | Arrival | Banner "PUSAT BANDAR PUTRA POINT — JALAN BBN 1/3C". The camera tilts down. The destination pin opens a photo card of the real Klinik Nissa shopfront. The fly loops round the pin and hovers beside it. "ANDA DAH SAMPAI!" appears. |
| 17.0–20.0 | Destination card | A circular reveal grows out of the destination pin. The Klinik Nissa logo sits inside a map pin, followed by the full address and the WhatsApp number. The fly hovers beside the pin, waving. The card holds until the end. |

All text sits between y ≈ 260 and y ≈ 1510, inside the Instagram Story safe zone.

## How it is built

- `index.html` is the HyperFrames composition: HTML layers plus one GSAP master timeline.
- `assets/world.js` holds the Three.js world. Every visual is a pure function of time: no clock and no `Math.random`. HyperFrames
  seeks frame by frame and the page renders on its `hf-seek` event, so renders are deterministic.
  - Two WebGL canvases: the city layer below the labels, and the fly layer above everything, so the mascot stays sharp over the end card.
  - The city layer holds extruded buildings, ribbon roads with dashed centre lines, parks, water, instanced trees, soft shadows,
    the toll plaza canopy, traffic lights, holographic pins and 3D turn arrows that follow the real turn geometry.
  - The fly is the clinic's own mascot illustration, used as a 2.5D puppet. `tools/cutout_mascot.py` keys out the black background
    (a flood fill from the border, so dark navy shading is never touched), removes the dark edge fringe, and splits the wings into
    their own layer (`assets/mascot-body.png`, `assets/mascot-wings.png`). In the scene the layers sit on camera-facing planes, so
    the art is shown exactly as drawn and is not tone-mapped. The wings beat around the shoulder with foreshortening (a 4-frame
    cycle at 30 fps, plus a motion-blur ghost). The mascot leans into turns, and turns round to point the way: right by default,
    left for each left turn, with its motion while it loops round the pins, and at the clinic pin on the end card. It leaves a
    glowing air trail and sparkles, with a soft shadow on the map.
- `audio/soundtrack.wav` comes from `tools/make_nav_audio.py`. The music is deliberately different from the clinic's other video
  (C–G–Am–F at 120 BPM with saw plucks): a warm marimba and electric-piano groove at 116 BPM in E♭ (Fm9 – B♭13 – E♭maj9 – Cm9),
  with a syncopated sub bass, rimshot and shaker, and a whistled hook on the opening and on the end card. On top sit the wing
  flutter, navigation beeps, pin drops, turn chimes, an arrival chime and an outro. The video still works without sound, because
  every instruction is on screen.

## Rebuild

```bash
npm ci
npm run nav:map        # re-download OSM + OSRM (cached in tools/.osm-cache/) and rebuild assets/map-data.js
python3 tools/cutout_mascot.py <mascot.webp>   # only when the mascot artwork changes
npm run nav:audio      # regenerate audio/soundtrack.wav (deterministic)
npm run nav:lint
npm run nav:snapshot   # key frames as PNGs
npm run nav:render     # master render, then two-pass encode -> fly-to-clinic/renders/klinik-nissa-terbang-ke-klinik-20s.mp4
```

In a sandbox without a GPU, point HyperFrames at a local Chromium, for example
`HYPERFRAMES_BROWSER_PATH=/path/to/chrome npm run nav:render`. WebGL then runs in SwiftShader on the CPU, so expect a render of about 25–30 minutes. `chrome-headless-shell` is the fastest option because it enables BeginFrame capture.
