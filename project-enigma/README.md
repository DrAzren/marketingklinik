# Klinik Nissa: Project Nemesis, Trial 02 "Project Enigma" briefing (101.5 s)

This is the instructional video for Mini Game 02 (real game: Guess the Beans), screened to the contestants just before it starts. It is 16:9, 1920 × 1080, 30 fps, MP4 (H.264 + AAC), with Malay narration and burned-in Malay captions. Its visual identity matches Operation Blackout and The Recall Protocol.

**Final file:** `renders/project-enigma-briefing.mp4`: 101.5 s, 1920 × 1080, 30 fps, H.264 High 4.5 Mbps two-pass with AAC 160 kbps, 59 MB, SSIM 0.992 against the HyperFrames master.

## How it is made

| Layer | Tool | Notes |
| --- | --- | --- |
| Narration | **Higgsfield Text-to-Speech v2** (ElevenLabs engine), voice element "Dr-Azren", the same voice as the other briefings | 8 lines, `media/vo/l01–l08.mp3` |
| Stills | **Higgsfield GPT Image 2.6**, 3 new images, plus 2 re-used from The Recall Protocol | Jar on an arena pedestal, close-up demo jar, jar under a gold spotlight; the arena with the red/blue contestants and the two writing desks are re-used |
| Jars in code | SVG | Fictional demo jars (~340 random beans, uncountable, not the competition jar) for Scene 2 and the tie-breaker |
| Music | Re-used original ElevenLabs score from the teaser | Re-cut per scene and ducked ~11 dB under the narration; quieter under the maths |
| SFX | Synthesised in `tools/build_audio.py` | Ticks, beeps, buzzer, holo screen, pen scribbles, number reveals, victory sting, sub impact |
| Motion graphics and captions | **HyperFrames + GSAP**, `index.html` | Timers, rule badges, answer sheets, scoreboard, number line, rewards |

## Storyboard (actual timings)

| Time | Scene | Rules shown |
| --- | --- | --- |
| 0:00–0:11 | The Mystery Begins | Black and ticking, red/blue sweeps, jar rises, gold "?"; KLINIK NISSA PRESENTS · PROJECT NEMESIS · TRIAL 02 · PROJECT ENIGMA; "The answer is right in front of you." |
| 0:11–0:19 | The Competitors | TEAM A vs TEAM B, VS emblem, 1 VS 1 SHOWDOWN, small demo jar |
| 0:19–0:33 | The Secret Jar | HOW MANY BEANS? ONE JAR. ONE SECRET NUMBER.; the moderator counts and records the real number in secret; "this demo jar is fictional" |
| 0:33–0:48 | Observation Phase | 45 SECONDS (45 → 30 → 15 → 05 → 00); LOOK CAREFULLY · DO NOT TOUCH · DO NOT SHAKE · DO NOT OPEN · DO NOT MOVE; no phones, calculators, measuring tools or outside help; zoom into the jar at 00 |
| 0:48–1:00 | Make Your Guess | Alarm; jar hidden behind a holo screen; private sheets with a divider; 15 SECONDS (15 → 00); ONE FINAL ANSWER · NO DISCUSSION · NO CHANGES AFTER SUBMISSION; sheets stamped SUBMITTED |
| 1:00–1:19 | How To Win | CLOSEST ANSWER WINS; BEZA = \|TEKAAN − JUMLAH SEBENAR\|; fictional example: actual 200, A 180 → \|180 − 200\| = 20, B 205 → \|205 − 200\| = 5; number line; TEAM B WINS (CONTOH SAHAJA); "not the highest or lowest guess, the most accurate one" |
| 1:19–1:31 | Rewards & Tie-breaker | +1 INDIVIDUAL POINT · +1 TEAM POINT; TIE? SUDDEN DEATH!; NEW JAR. NEW GUESS.; a second jar with a different secret count, repeated if still tied; a tie is never decided by the higher or lower guess; no extra points |
| 1:31–1:41.5 | Final Challenge | Jar under a gold spotlight, floating symbols; TRUST YOUR INSTINCTS. / THINK ANALYTICALLY. / MAKE EVERY GUESS COUNT.; PROJECT ENIGMA, ARE YOU READY?; final impact, fade to black |

**The real bean count is never revealed or hinted at.** The only numbers shown are the fictional example (200 / 180 / 205), labelled CONTOH SAHAJA. The maths is correct: \|180 − 200\| = 20 and \|205 − 200\| = 5, so B is closer.

## Rebuild

```bash
python3 tools/prep_vo.py       # trim and normalise VO, time captions, inject into index.html
python3 tools/build_audio.py   # music re-cut + VO + SFX -> audio/mix.wav (-14 LUFS)
npx hyperframes render . -f 30 -q high -w 4 -o renders/project-enigma-briefing-master.mp4
```

## Credits used

- **Higgsfield: 4.80 credits**, measured on the balance (2,963.66 → 2,958.86). That is 3 images (0.75) and 8 narration lines (~4.05). Prices were confirmed with free cost checks first, and there were no retries, variations or upscales.
- This is within every reading of the budget: 30 for this production, 20 in the final checklist, or the shared 30 minus earlier use (30 − 7.65 − 5.05 = 17.3).
- **ElevenLabs:** 0.
