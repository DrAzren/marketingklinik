# Klinik Nissa: Game 2.5 "Psychology Betrayal" briefing (117 s)

This is the instructional video for Game 2.5, Psychology Betrayal. Teammates duel against each other as Deceiver and Detective, with a dry bean in a closed fist or an empty fist.

It is 16:9, 1920 × 1080, 30 fps, MP4 (H.264 + AAC), with Malay narration and animated burned-in Malay captions. The visual identity matches the other Final Showdown briefings: the same HUD, fonts, grain and caption style, with purple added as the accent for "betrayal".

**Final file:** `renders/psychology-betrayal-briefing.mp4`, 117.0 s, 1920 × 1080, 30 fps, H.264 High 4.5 Mbps two-pass with AAC 160 kbps.

## How it is made

| Layer | Tool | Notes |
| --- | --- | --- |
| Narration | **ElevenLabs v4** (`eleven_v4`), Dr Azren voice clone, with audio tags (`[deep voice]`, `[dramatically]`, `[whispers]` …) | 8 lines, one take each, the user's script verbatim, `media/vo/l01–l08.mp3` |
| Stills | **Higgsfield GPT Image 2.6**, 2 new images, plus the red/blue arena re-used from The Recall Protocol | Purple-spotlit duel room with two empty chairs (`duel_1080.jpg`); a close-up of a closed fist (`fist_1080.jpg`) |
| Hands and bean | SVG in code | Stylised open hand, fist and bean, used for the fictional demonstrations |
| Music | Re-used original ElevenLabs score from the teaser | Re-cut per scene on its 2 s bar grid and ducked ~10 dB under the narration |
| SFX | Synthesised in `tools/build_audio.py` | Glitch, shatter, ticks, heartbeats, hand grab, bean pop, ding, buzzer, impacts, sub drops |
| Motion graphics and captions | **HyperFrames + GSAP**, `index.html` | |

## Storyboard (actual timings)

| Time | Scene | What is shown |
| --- | --- | --- |
| 0:00–0:16.5 | Alliance shatters | Four gold teammates linked: TEAM ALLIANCE. It glitches and turns red/blue, then shatters. In the duel room: KLINIK NISSA PRESENTS · GAME 2.5 · PSYCHOLOGY BETRAYAL; "Your greatest enemy might be your closest ally." |
| 0:16.5–0:26.5 | Teammate vs teammate | TEAM A VS TEAM B is struck out (BUKAN LAGI TEAM VS TEAM). Then "your own team": two teammates step out, turn red and blue, and face each other with VS. TEAMMATE VS TEAMMATE, then TRUST NO ONE. |
| 0:26.5–0:38.5 | The roles | Two cards. THE DECEIVER, HIDE THE TRUTH (mask). THE DETECTIVE, FIND THE TRUTH (magnifier). |
| 0:38.5–0:51.5 | The choice | Option A: a bean in the palm, then a fist. Option B: an empty hand, then a fist, with the bean kept in a concealed container. Both become one identical fist: ADA KACANG? / ATAU TIADA KACANG?. Choice locked once shown (CONTOH SAHAJA). |
| 0:51.5–1:06 | Ten seconds | Real-time 10 → 0 ring timer over the fist close-up. WAJAH · GERAK-GERI · REAKSI, then ⚠ LAWAN DIBENARKAN MENIPU!. MAKE YOUR FINAL GUESS! with ADA KACANG / TIADA KACANG. One final answer, no spectator signals, no touching. |
| 1:06–1:20 | Scoring examples | Example 1: "ADA KACANG!", bean revealed, ✓ CORRECT, DETECTIVE +1 POINT. Example 2: "TIADA KACANG!", bean revealed, ✕ WRONG, DECEIVER +1 POINT. ONE DUEL. ONE POINT. ONE WINNER. |
| 1:20–1:35 | Individual points and rotation | Team boards hit by NO TEAM POINTS. An individual leaderboard rises: INDIVIDUAL POINTS ONLY · EVERY POINT COUNTS. Role swap: 4 players = 4 duels in 2 rounds (roles swap); 3 players = 3 duels in rotation. Everyone plays both roles, the moderator announces matchups, and the moderator's decision is final. |
| 1:35–1:57 | Finale | TRUST cracks; CAN YOU READ THE TRUTH? / OR WILL YOU BELIEVE THE LIE?; PSYCHOLOGY BETRAYAL; ARE YOU READY? with a bass impact; fade. |

All hands, beans, names and scores are fictional demonstrations. No real game content is revealed.

## Rebuild

```bash
python3 tools/prep_vo.py       # trim and normalise VO, time captions, inject into index.html
python3 tools/build_audio.py   # music re-cut + VO + SFX -> audio/mix.wav (-14 LUFS)
npx hyperframes render . -f 30 -q high -w 4 -o renders/psychology-betrayal-briefing-master.mp4
```

## Credits used (shared 30-credit Higgsfield project budget)

| Video | Higgsfield credits |
| --- | --- |
| Operation Blackout | 7.65 |
| The Recall Protocol | 5.05 |
| Project Enigma | 4.80 |
| The Final Piece | 5.15 |
| Unknown Substance | 4.70 |
| **Psychology Betrayal** | **0.50** (2 images at 0.25 each, confirmed with a free cost check; balance 2,949.01 → 2,948.51) |
| **Total** | **27.85 / 30** (2.15 left) |

- The narration was not made on Higgsfield, because the ~4–5 credits needed would have exceeded the 2.65 left.
- It was made directly on ElevenLabs instead: **~1,566 ElevenLabs credits**, from that account's own balance, for 8 lines with one take each and no retries.
- There were no retries, variations or upscales on either service.
