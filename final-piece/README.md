# Klinik Nissa: Project Nemesis, Trial 03 "The Final Piece" briefing (101 s)

This is the instructional video for Mini Game 03 (real game: Geometric Puzzle Box Challenge), screened just before the game. It is 16:9, 1920 × 1080, 30 fps, MP4 (H.264 + AAC), with Malay narration and animated burned-in Malay captions. Its identity matches Operation Blackout, The Recall Protocol and Project Enigma.

**Final file:** `renders/final-piece-briefing.mp4`

## How it is made

| Layer | Tool | Notes |
| --- | --- | --- |
| Narration | **Higgsfield Text-to-Speech v2** (ElevenLabs engine), voice element "Dr-Azren", the same voice as the other briefings | 8 lines, `media/vo/l01–l08.mp3` |
| Stills | **Higgsfield GPT Image 2.6**, 2 new images, plus the red/blue arena re-used from The Recall Protocol | Two puzzle stations with empty trays, and a tunnel of floating geometric shapes |
| Demo puzzle | SVG in code | **Fictional** 4 × 3 tray tiled exactly by 5 pieces: 2 × 1 bar (2 units), two L-trominoes (3 + 3), two right triangles (2 + 2) = 12 unit squares. Geometrically valid and unrelated to the competition puzzle. |
| Music | Re-used original ElevenLabs score from the teaser | Re-cut per scene and ducked ~11 dB under the narration; quieter under the rules |
| SFX | Synthesised in `tools/build_audio.py` | Piece clicks, countdown beeps, ticks, buzzer, shatter, holo, victory sting, sub impact |
| Motion graphics and captions | **HyperFrames + GSAP**, `index.html` | Metallic shape breaking apart, split-screen race, rule demos, moderator check, scoreboard, timer, tunnel finale |

## Storyboard (actual timings)

| Time | Scene | Rules shown |
| --- | --- | --- |
| 0:00–0:13.4 | The Challenge Reveal | Metallic hexagon rotates and breaks into glowing fragments over the red/blue stations; KLINIK NISSA PRESENTS · PROJECT NEMESIS · TRIAL 03 · THE FINAL PIECE; "Everything has its place. Find yours." |
| 0:13.4–0:22 | The Competitors | Split red/blue arena, TEAM A (RED) vs TEAM B (BLUE), VS, 1 VS 1 SHOWDOWN, SPEED × PRECISION × STRATEGY; identical puzzle sets, tested complete and solvable by the moderator |
| 0:22–0:34 | Understanding the Puzzle | Tray rises, boundary highlighted; ONE BOX · MULTIPLE PIECES · ONE COMPLETE SOLUTION; close-up fitting, including one wrong rotation that is then corrected; CONTOH REKAAN |
| 0:34–0:48 | How to Play | Equivalent mirrored starting layouts, all pieces outside the box, no touching before START; 3 · 2 · 1 · START!; split-screen race with ROTATE / REPOSITION / TRY AGAIN |
| 0:48–1:01.6 | Important Rules | 01 All pieces must fit · 02 No overlapping · no protruding · 03 No forcing or breaking · 04 No outside assistance (shield blocks a teammate) · 05 Hands off when done, each with a demo |
| 1:01.6–1:16.4 | How to Win | A keeps trying; B completes, hands off, DONE!; the moderator inspects with a magnifier; ✓ PUZZLE VERIFIED; TEAM A — STILL PLAYING · TEAM B — 02:18 (CONTOH SAHAJA); gold glow; a wrong DONE! means the player continues |
| 1:16.4–1:26.4 | Points & Time Limit | +1 INDIVIDUAL POINT · +1 TEAM POINT; MAXIMUM 5 MINUTES (05:00 → 00:00); SUDDEN DEATH, NEW PUZZLE. FINAL CHANCE.; an easier new puzzle, the same for both; no winner by partial progress; loser 0 points |
| 1:26.4–1:41 | The Final Challenge | Tunnel fly-through, pieces orbit and converge into a glowing "?"; THINK FAST. / STAY FOCUSED. / FIND THE PERFECT FIT.; THE FINAL PIECE, ARE YOU READY?; final impact, fade |

**The real competition puzzle and its solution are never shown.** Only the fictional 4 × 3 demo set is used.

## Rebuild

```bash
python3 tools/prep_vo.py       # trim and normalise VO, time captions, inject into index.html
python3 tools/build_audio.py   # music re-cut + VO + SFX -> audio/mix.wav (-14 LUFS)
npx hyperframes render . -f 30 -q high -w 4 -o renders/final-piece-briefing-master.mp4
```

## Credits used

- **Higgsfield: 5.15 credits**, measured on the balance (2,958.86 → 2,953.71). That is 2 images (0.5) and 8 narration lines (~4.65). Prices were confirmed with free cost checks first, and there were no retries, variations or upscales.
- This is within the 30-credit cap, and also within the shared remainder (30 − 7.65 − 5.05 − 4.80 = 12.5).
- **ElevenLabs:** 0.
