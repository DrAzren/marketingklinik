# Klinik Nissa: Operation Blackout, official Game 01 briefing (147 s)

An instructional briefing video for the team captains, screened just before the game. It is 16:9, 1920 × 1080, 30 fps, MP4 (H.264 + AAC), with Malay narration and burned-in Malay captions.

**Final file:** `renders/operation-blackout-briefing.mp4`: 147.0 s, 1920 × 1080, 30 fps, H.264 High 4.5 Mbps two-pass with AAC 160 kbps, 86 MB, SSIM 0.996 against the HyperFrames master. The master is not committed.

## How it is made

| Layer | Tool | Notes |
| --- | --- | --- |
| Narration | **Higgsfield Text-to-Speech v2** (ElevenLabs engine), voice element "Dr-Azren", used at the user's request | 10 lines, `media/vo/l01–l10.mp3` |
| Footage | Re-used Higgsfield clips from the teaser (`../showdown-2026/media/clips`) | Door, sealed vault with four silhouettes, red vs blue teams. No new video generations. |
| Music | Re-used original ElevenLabs score from the teaser | Re-cut to the scenes; ducked ~11 dB under narration and lowered further during the rules |
| SFX | Synthesised in `tools/build_audio.py` | Ticks, UI beeps, holo sweeps, mechanical opening, impacts, error buzzer, victory sting, sub drop |
| Motion graphics and captions | **HyperFrames + GSAP**, `index.html` | Envelopes, code slots, mission cards, timer, hint tokens, penalty equation, scoreboards, rewards |

## Storyboard (actual timings)

| Time | Scene | On screen |
| --- | --- | --- |
| 0:00–0:13.5 | Mission Activated | Black, then vault door, red sweep, command monitor: KLINIK NISSA PRESENTS / GAME 01 / OPERATION BLACKOUT / tagline |
| 0:13.5–0:24 | Team Formation | TEAM A (RED) vs TEAM B (BLUE), 3–4 players each, 25:00 clock, 3 sealed envelopes per team, TWO TEAMS / THREE MISSIONS / ONE SECRET CODE |
| 0:24–0:36.4 | Your Objective | Security panel with 3 hidden slots; Mission 01→Digit 1, 02→2, 03→3; "3 MISSIONS = 3 DIGITS = 1 CODE" |
| 0:36.4–0:48.6 | Mission 01: Signal Intercept | Abstract symbol layers and a signal wave collapse into "?"; Kebijaksanaan · Pemikiran Kritikal · Penyelesaian Masalah |
| 0:48.6–1:01.6 | Mission 02: Seating Conspiracy | Investigation board: 4 anonymous icons and blank cards, an arrangement that shuffles and is then hidden by "?"; Penaakulan Logik · Ketelitian · Pemikiran Analitikal |
| 1:01.6–1:12.2 | Mission 03: Grid Override | Blank 6×6 grid with non-numeric placeholders, tilting into a 3D security interface; Logik Matematik · Daya Tumpuan · Ketepatan |
| 1:12.2–1:26.4 | The Countdown | Live 25:00 timer; Time limit 25 min · Open envelopes in order · Work together · No outside assistance (pen, paper and supplied materials only, other tools only with moderator approval) |
| 1:26.4–1:49.8 | Hints & Penalties | HELP button; max 2 hints per team, each +2 MINIT; incorrect code → WAIT 45 SECONDS; RAW TIME + HINT PENALTY = OFFICIAL TIME; 15 + 2 = 17 MINIT (CONTOH SAHAJA) |
| 1:49.8–2:05.6 | The Winning Team | A 16:00 + 04:00 = 20:00, B 18:00 + 00:00 = 18:00, TEAM B WINS (EXAMPLE ONLY); +1 point for every member; Special advantage: choose your opponents in Game 02 |
| 2:05.6–2:27 | Final Briefing | Vault and teams: THINK FAST. / WORK TOGETHER. / TRUST YOUR TEAM.; 3 mission seals; 25:00; ARE YOU READY?; OPERATION BLACKOUT BEGINS NOW; final impact; fade to black |

**No puzzle content is revealed.** There are no real messages, ciphers, clues, names, badges, seating arrangements, grids, numbers or codes. The glyph rows, seating icons and 6×6 placeholders are abstract and invented. The only times shown are the clearly labelled fictional examples from the brief.

## Rebuild

From this folder:

```bash
python3 tools/prep_vo.py       # trim and normalise VO, time captions, inject into index.html
python3 tools/build_audio.py   # music re-cut + VO + SFX -> audio/mix.wav (-14 LUFS)
npx hyperframes render . -f 30 -q high -w 4 -o renders/operation-blackout-briefing-master.mp4
```

## Credits used

| Service | Used | Detail |
| --- | --- | --- |
| Higgsfield | **7.65 of the 30-credit cap** | 3 voice tests (~1.3) and 10 narration lines (~6.3). Cost checks (free) showed that one Seedance clip (720p, 5 s) costs 35 credits, which is over the cap, so no video was generated. |
| ElevenLabs | ~67 | One Scribe transcript (line 5) to check the narration and time its captions. Its estimate said ~7 credits but it charged 67; three further transcripts and one speech attempt failed for lack of credits and were not charged. The ElevenLabs balance is now about 3 credits. |
