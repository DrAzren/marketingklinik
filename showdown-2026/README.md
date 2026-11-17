# Klinik Nissa: The Final Showdown 2026 (teaser, 75 s)

A cinematic teaser for the staff retreat competition, in 16:9 at 1920 × 1080 and 30 fps. It is built to be shared in the staff WhatsApp group.

**Final file:** `renders/final-showdown-2026-whatsapp.mp4`. It is H.264 High with AAC audio and `+faststart`, and is sized for WhatsApp.

## How it is made

| Layer | Tool | Files |
| --- | --- | --- |
| Cinematic footage | **Higgsfield**: Seedance 2.5, 1080p, text-to-video, 8 clips | `media/clips/c1…c8_*.mp4` |
| Narration | **ElevenLabs v4** (`eleven_v4`), voice "Zain – Powerful Game Character" (library voice, not the Dr Azren clone) | `media/vo/s*.mp3` (raw takes), `media/vo_prep/` (tightened) |
| Music | **ElevenLabs Music v2.5**, original 75 s trailer score | `media/music/score.mp3` |
| Sound effects | Synthesised in code: ticks, heartbeat, impacts, whooshes, beeps, riser, sub drop | `tools/build_audio.py` |
| Motion graphics, captions, compositing | **HyperFrames + GSAP** (HTML composition) | `index.html` |

Fonts are Big Shoulders Display (titles), Chakra Petch (HUD) and Barlow Semi Condensed (captions). All are OFL, from Fontsource.

## Storyboard (actual timings)

| Time | Scene | Footage | Graphics |
| --- | --- | --- | --- |
| 0:00–0:09.4 | The Invitation | Blast door opens on the crimson/blue arena | Red countdown 00:03 → 00:00, metallic "THE FINAL SHOWDOWN 2026", "KLINIK NISSA" |
| 0:09.4–0:19.4 | Game 01: Operation Blackout | Four silhouettes before a sealed chamber, holographic glyphs | Mission clock, glitch title, tagline, 3 attributes, red flash |
| 0:19.4–0:33.4 | Game 02: Project Nemesis | Red vs blue teams, the floor turns into a versus stage, neural network | Title, then 4 trials (Recall Protocol, Project Enigma, The Final Piece, Unknown Substance), each with 3 attributes and an abstract HUD visual; "STRATEGIC ADVANTAGE / UNLOCKED BY GAME 01 WINNER" |
| 0:33.4–0:42.4 | Game 02.5: Psychology Betrayal | Two figures back to back; the trust emblem shatters into particles | Cracked title, tagline, 3 attributes, music cuts to a heartbeat |
| 0:42.4–0:54.2 | Game 03: The Nightfall Protocol | Red moon over a foggy forest, circle of silhouettes | Title, tagline, 3 attributes, flashes of eyes and an abstract vote ring |
| 0:54.2–1:02.2 | The Rewards | Gold, silver and bronze trophies rise, confetti | JUARA RM150 (largest), NAIB JUARA RM100, TEMPAT KETIGA RM50 |
| 1:02.2–1:15 | The Final Warning | Arena lights switch off one by one | "YOU KNOW THE SKILLS." / "YOU DON'T KNOW THE GAME." / title / COMING SOON / TRUST NO ONE. EXPECT THE UNEXPECTED. |

The Malay captions are burned in and timed to the voice. The last line ("The Final Showdown 2026... coming soon") has no caption, because the same words fill the screen.

No game mechanics are shown. There are no bombs, codes, memory objects, beans, puzzle pieces, drinks, role cards or solutions; every trial visual is abstract.

## Rebuild

From this folder (`showdown-2026/`):

```bash
python3 tools/prep_vo.py       # tighten VO pauses, +10 % tempo  -> media/vo_prep/
python3 tools/build_audio.py   # music re-cut + VO + SFX, -14 LUFS -> audio/mix.wav
tools/build_plate.sh           # conform clips -> media/plate.mp4 (2250 frames)
npx hyperframes render . -f 30 -q high -w 4 -o renders/final-showdown-2026-master.mp4
```

All timing lives in `timeline.json`: scene cuts, voice start times, music re-cut map, sound effects and captions. `index.html` mirrors the scene and caption times.

## Credits used

**Renders:** `renders/final-showdown-2026-whatsapp.mp4` (15.2 MB, 1480 kbps two-pass, SSIM 0.986 against the master) and `renders/final-showdown-2026-whatsapp-HD.mp4` (46 MB, 4.8 Mbps, SSIM 0.991, for "HD" sending or as a document). The 126 MB master is not committed; rebuild it with the render command above.

- **Higgsfield:** 960 credits (8 × 120).
- **ElevenLabs:** about 3,122 credits (7 lines × 2 takes, plus one 75 s music track; a second music take failed for insufficient credits and was not charged).
