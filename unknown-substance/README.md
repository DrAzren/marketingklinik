# Klinik Nissa: Project Nemesis, Trial 04 "Unknown Substance" briefing (100.5 s)

This is the instructional video for Mini Game 04 (real game: Mystery Drink Taste Test), screened just before the game. It is 16:9, 1920 × 1080, 30 fps, MP4 (H.264 + AAC), with Malay narration and animated burned-in Malay captions. Its identity matches the other Project Nemesis briefings.

**Final file:** `renders/unknown-substance-briefing.mp4`: 100.5 s, 1920 × 1080, 30 fps, H.264 High 4.5 Mbps two-pass with AAC 160 kbps, 58 MB, SSIM 0.992 against the HyperFrames master.

## How it is made

| Layer | Tool | Notes |
| --- | --- | --- |
| Narration | **Higgsfield Text-to-Speech v2** (ElevenLabs engine), voice element "Dr-Azren", the same voice as the other briefings | 8 lines, `media/vo/l01–l08.mp3` |
| Stills | **Higgsfield GPT Image 2.6**, 2 new images, plus the red/blue arena re-used | Five plain opaque cups on a holo platform, and two tables with five cups each. No bottles, brands or contents are visible. |
| Music | Re-used original ElevenLabs score from the teaser | Re-cut per scene; quiet heartbeat section for sudden death; ducked ~11 dB under the narration |
| SFX | Synthesised in `tools/build_audio.py` | Droplet, pouring, ticks, beeps, correct dings and wrong buzzes, heartbeat, victory sting, sub impact |
| Motion graphics and captions | **HyperFrames + GSAP**, `index.html` | Droplet and ripple, numbered cups, rule demos, timer montage, answer sheets, scoreboards, confetti, sixth cup, particle "?" |

## Storyboard (actual timings)

| Time | Scene | Rules shown |
| --- | --- | --- |
| 0:00–0:11.6 | The Mystery Unveiled | Droplet falls and ripples; five cups rise; red/blue sweeps; KLINIK NISSA PRESENTS · PROJECT NEMESIS · TRIAL 04 · UNKNOWN SUBSTANCE; "Trust your senses. Question your instincts." |
| 0:11.6–0:20.8 | The Final Duel | TEAM A (RED) vs TEAM B (BLUE), VS, 1 VS 1 SHOWDOWN; overhead view of both numbered sets 1–5; FIVE MYSTERY SAMPLES |
| 0:20.8–0:31.4 | The Objective | Cups 01–05 with "?" holograms; TASTE → IDENTIFY → WRITE YOUR ANSWER; symbolic sip from cup 01; answer sheet; safety note: ordinary safe drinks only, allergies checked, separate cups, packaging and brands hidden, opt-out allowed |
| 0:31.4–0:45 | The Rules | 01 Taste in order · 02 Write your answers · 03 No discussion · 04 No copying · 05 No phones / no outside help, each with a demo; same samples and order for both; re-tasting your own samples is allowed |
| 0:45–1:01 | The Countdown | TASTING TIME · 90 SECONDS (90 → 60 → 30 → 10 → 05 → 00); montage of tasting (A goes back to cup 2), thinking, writing; TIME'S UP! PENS DOWN!; the moderator collects the sheets and then reveals the drinks |
| 1:01–1:15 | The Reveal | Scoreboards with masked answers and ✓/✕: A 4/5, B 3/5 (CONTOH SAHAJA); TEAM A WINS!; +1 INDIVIDUAL POINT · +1 TEAM POINT; confetti; judging rule: the moderator sets brand vs. general category beforehand, the same standard for both, spelling variations accepted, no extra points per drink, loser 0 |
| 1:15–1:27.6 | Sudden Death | Scores become 4/5 – 4/5; IT'S A TIE! SUDDEN DEATH ACTIVATED; sixth cup "06" under a gold spotlight; NEW SAMPLE, ONE FINAL CHALLENGE; only one correct wins, otherwise repeat with a new drink |
| 1:27.6–1:40.5 | The Final Warning | Five glowing cups, light particles form a "?", rush to the centre cup; TRUST YOUR SENSES. / STAY FOCUSED. / EVERY TASTE COUNTS.; UNKNOWN SUBSTANCE, ARE YOU READY?; final impact, fade |

**The real competition drinks are never shown or named.** No brands or bottles appear, and the scoreboards show masked answer bars instead of drink names. There are no hazard symbols or chemicals.

## Rebuild

```bash
python3 tools/prep_vo.py       # trim and normalise VO, time captions, inject into index.html
python3 tools/build_audio.py   # music re-cut + VO + SFX -> audio/mix.wav (-14 LUFS)
npx hyperframes render . -f 30 -q high -w 4 -o renders/unknown-substance-briefing-master.mp4
```

## Credits used (shared 30-credit project budget)

| Video | Higgsfield credits |
| --- | --- |
| Operation Blackout | 7.65 |
| The Recall Protocol | 5.05 |
| Project Enigma | 4.80 |
| The Final Piece | 5.15 |
| **Unknown Substance** | **4.70** (2 images 0.5 + 8 narration lines ~4.2; balance 2,953.71 → 2,949.01) |
| **Total** | **27.35 / 30** |

Prices were confirmed with free cost checks first, and there were no retries, variations or upscales. ElevenLabs: 0.
