# Klinik Nissa: Project Nemesis, Trial 01 "The Recall Protocol" briefing (106 s)

This is the instructional video for Mini Game 01, screened to staff just before it starts. It is 16:9, 1920 × 1080, 30 fps, MP4 (H.264 + AAC), with Malay narration and burned-in Malay captions. Its visual identity matches the Operation Blackout briefing: the same HUD, fonts, red/blue/gold palette, glass panels and grid floor.

**Final file:** `renders/recall-protocol-briefing.mp4`

## How it is made

| Layer | Tool | Notes |
| --- | --- | --- |
| Narration | **Higgsfield Text-to-Speech v2** (ElevenLabs engine), voice element "Dr-Azren", the same voice as the Operation Blackout briefing | 8 lines, `media/vo/l01–l08.mp3` |
| Stills | **Higgsfield GPT Image 2.6**, 4 images | Holographic brain, arena with red/blue contestants, empty glass table, two writing desks. Animated in code with push-ins, hologram sway and overlays. |
| Music | Re-used original ElevenLabs score from the teaser | Re-cut per scene (dramatic intro, suspenseful observation, intense turn, fast recall, triumphant win, finale) and ducked ~11 dB under the narration |
| SFX | Synthesised in `tools/build_audio.py` | Heartbeat, ticks, beeps, buzzer, cloth drop, pen scribbles, victory sting, sub impact |
| Motion graphics and captions | **HyperFrames + GSAP**, `index.html` | 20 abstract placeholder shapes in a 4 × 5 grid, timers, cloth, answer sheets, scoreboards, tie-breaker |

## Storyboard (actual timings)

| Time | Scene | Rules shown |
| --- | --- | --- |
| 0:00–0:11 | The Challenge Begins | KLINIK NISSA PRESENTS, PROJECT NEMESIS, TRIAL 01: THE RECALL PROTOCOL, "Every detail matters." |
| 0:11–0:20 | The Competitors | TEAM A (RED CHAMPION) vs TEAM B (BLUE CHAMPION), 1 VS 1 SHOWDOWN |
| 0:20–0:32 | The Object Challenge | **20 OBJECTS** (counter 0→20; 4 × 5 abstract placeholders); the moderator sets them out and both players view from equal positions |
| 0:32–0:45 | Observation Phase | **45 SECONDS**; countdown 45 → 30 → 15 → 05 → 00; OBSERVATION TIME IS OVER |
| 0:45–0:57 | Turn Around | TIME'S UP!; both players turn away; TURN AROUND; objects covered with a black cloth; NO PEEKING |
| 0:57–1:13 | Recall Phase | RECALL TIME: **60 SECONDS** (60 → 00); NO TALKING / NO COPYING / NO PHONES; paper and pen supplied; work alone; STOP WRITING the moment time ends |
| 1:13–1:30 | Scoring & Winner | A 16/20, B 18/20 (CONTOH SAHAJA); WINNER: TEAM B CHAMPION; **+1 INDIVIDUAL POINT, +1 TEAM POINT**; 1 correct object = 1 mark, repeats count once, spelling variations accepted if clear, no partial marks, loser 0 points, checked by the moderator against the official list |
| 1:30–1:46 | Tie-breaker & Final | TIE!, SUDDEN DEATH: 5 NEW OBJECTS · 10 SECONDS TO MEMORIZE · 20 SECONDS TO WRITE; repeat with a new set if still tied; LOOK CLOSELY. / REMEMBER EVERYTHING. / EVERY DETAIL MATTERS.; THE RECALL PROTOCOL, ARE YOU READY? |

**The real competition objects are not shown.** The grid uses 20 invented abstract shapes (circle, star, hexagon, bolt and so on), and the answer sheets show unreadable scribble bars, not object names.

## Rebuild

```bash
python3 tools/prep_vo.py       # trim and normalise VO, time captions, inject into index.html
python3 tools/build_audio.py   # music re-cut + VO + SFX -> audio/mix.wav (-14 LUFS)
npx hyperframes render . -f 30 -q high -w 4 -o renders/recall-protocol-briefing-master.mp4
```

## Credits used

- **Higgsfield: 5.05 of the 20-credit cap**, measured on the balance (2,968.71 → 2,963.66). That is 4 images (~1.0) and 8 narration lines (~4.05). Prices were confirmed with free cost checks first. There were no retries, variations or upscales.
- **ElevenLabs:** 0 (the balance is ~3 credits). The music is re-used from the teaser.
