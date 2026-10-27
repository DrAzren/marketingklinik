# Klinik Nissa: "Terbang ke Klinik" 3D navigation video (15 s)

A 15-second, 9:16 (1080 × 1920, 30 fps) animated navigation ad in Bahasa Melayu. A turquoise 3D fly mascot guides the viewer from
**Exit Tol Nilai** to **Klinik Nissa, Jalan BBN 1/3C, Pusat Bandar Putra Point**, over a miniature 3D model of Bandar Baru Nilai.

Built with **HyperFrames + GSAP + Three.js**. Everything is generated in code: the city, the fly, the pins, the arrows and the soundtrack.

**Higgsfield credits used: 0 / 50.** There is no AI video, image or audio generation and no paid stock.

Final render: `renders/klinik-nissa-terbang-ke-klinik-15s.mp4`

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
3. **Exact shop lot.** The pin is on Jalan BBN 1/3C. No. 9697 is not in OpenStreetMap or any public listing, so the video does not
   point at a specific shopfront, and no shopfront is invented.
4. **Building heights.** Footprints come from OpenStreetMap. Heights are estimated (×1.3 for the miniature look) because OSM has no
   height data here. Trees are a stylised, deterministic scatter and do not mark real trees.

## Storyboard

| Time | Scene | What happens |
| --- | --- | --- |
| 0.0–1.5 | Hook | Aerial view of Nilai. The fly zooms up to the lens, then loops round a giant floating pin. "NAK KE KLINIK NISSA?" and "IKUT LALUAN INI!" appear. The camera swoops down to the toll. |
| 1.5–3.5 | Exit Tol Nilai | Toll plaza canopy and pin with the "EXIT TOL NILAI" label. The fly speeds down the link road with a glowing trail and hovers at the first traffic light, which turns green. It looks back at the viewer, then banks right. A 3D arrow rises from the road and the banner reads "BELOK KANAN". |
| 3.5–5.5 | McD and KFC | Wing-powered burst. McDonald's (red/gold block) on the left and KFC at the corner, each with a pin and label. A left-turn arrow and the banner "BELOK KIRI". |
| 5.5–7.5 | Dataran Nilai | The plaza, with a pin and "SEBELAH KANAN" label, sits on the right. |
| 7.5–9.5 | AEON Nilai | The AEON mall (magenta roof) with "SEBELAH KANAN". Banner "SELEPAS AEON NILAI — BELOK KIRI" and a left-turn arrow. |
| 9.5–11.5 | Arrival | Banner "PUSAT BANDAR PUTRA POINT — JALAN BBN 1/3C". The camera tilts down. The fly loops round the pulsing turquoise and gold destination pin and hovers beside it. "ANDA DAH SAMPAI!" and the "KLINIK NISSA" label appear. |
| 11.5–15.0 | Destination card | A circular reveal grows out of the destination pin. The Klinik Nissa logo sits inside a map pin, followed by the full address and the WhatsApp number. The fly hovers beside the pin, waving. The card holds until the end. |

All text sits between y ≈ 260 and y ≈ 1510, inside the Instagram Story safe zone.

## How it is built

- `index.html` is the HyperFrames composition: HTML layers plus one GSAP master timeline.
- `assets/world.js` holds the Three.js world. Every visual is a pure function of time: no clock and no `Math.random`. HyperFrames
  seeks frame by frame and the page renders on its `hf-seek` event, so renders are deterministic.
  - Two WebGL canvases: the city layer below the labels, and the fly layer above everything, so the mascot stays sharp over the end card.
  - The city layer holds extruded buildings, ribbon roads with dashed centre lines, parks, water, instanced trees, soft shadows,
    the toll plaza canopy, traffic lights, holographic pins and 3D turn arrows that follow the real turn geometry.
  - The fly is one reusable model built from primitives: a metallic turquoise body with gold rings, big glossy eyes, translucent
    iridescent wings (4-frame flap cycle at 30 fps), antennae and waving arms. It banks through turns, looks back at hovers, and
    leaves a glowing air trail and sparkles.
- `audio/soundtrack.wav` comes from `tools/make_nav_audio.py`: a 120 BPM bed plus wing flutter, navigation beeps, pin drops,
  turn chimes, an arrival chime and an outro. The video still works without sound, because every instruction is on screen.

## Rebuild

```bash
npm ci
npm run nav:map        # re-download OSM + OSRM (cached in tools/.osm-cache/) and rebuild assets/map-data.js
npm run nav:audio      # regenerate audio/soundtrack.wav (deterministic)
npm run nav:lint
npm run nav:snapshot   # key frames as PNGs
npm run nav:render     # -> fly-to-clinic/renders/klinik-nissa-terbang-ke-klinik-15s.mp4
```

In a sandbox without a GPU, point HyperFrames at a local Chromium, for example
`HYPERFRAMES_BROWSER_PATH=/path/to/chrome npm run nav:render`. WebGL then runs in SwiftShader, so expect a render of about 15 minutes.
