---
name: yt-style
description: >-
  Approved editing style for Plain Science Shorts (captions, badge, pacing,
  visuals, sound). Use for every render: "make the video", "edit the short",
  "style", "captions", "B-roll". Read STYLE_SHEET.md here before rendering.
---

# yt-style

Owner-approved on 2026-11-12. Derived from three reference Shorts (fast "N facts" lists with
word-by-word captions, countdown badge, red-arrow callouts, constant cuts). The owner said:
"Always follow this style sheet."

## What to do
1. Read `STYLE_SHEET.md` in this folder. It is the source of truth for look and feel.
2. Prefer the ranked "N facts" format (countdown badge 3-2-1) when the topic splits into 2-3 facts;
   otherwise a single-topic Short in the same caption/pace style.
3. Captions: Montserrat ExtraBold from `fonts/Montserrat.ttf` (SIL OFL), UPPERCASE, white with thick black
   outline, 2-3 words at a time, key word yellow, lower third (about 77% down), pop-in.
4. Pace: cut or move every 1.5-3 s, punch-zoom at each cut (`../yt-shorts/kinetic.py`: beat_camera,
   hook_punch). Compress voice pauses to about 0.25 s (the voice is fast: about 160-180 wpm).
5. Visuals: real photos/footage of the actual subject under a free licence, or an animated Pillow diagram in
   the same palette. Red arrows/circles on diagrams, short 1-2 word labels. Never film/TV clips, never the
   reference creators' footage or wording.
6. Sound: voice on top, music very low and ducked, whoosh on cuts, soft ding on the badge, subtle hits.
7. Credits: every CC BY / CC BY-SA photo must be credited in the description (title, author, licence).
8. Ending: close on the last fact, no "follow/subscribe" line.

## Reference implementation
`reference/sample1_build.py` is the renderer used for sample 1 ("3 octopus facts that sound made up",
uploaded private 2026-11-12). It shows beat mapping from Whisper word times, pause compression, kinetic captions,
the badge, hearts diagram, counter, 2/3 donut, SFX and music ducking. It has Windows paths (music file, assets) and
needs adapting per video; copy the ideas, not the topic.

## Cloud runs
The cloud sandbox may not reach Wikimedia or other photo sites. If footage cannot be fetched, build the visuals
as animated diagrams in the same palette and say so in the push notification. Do not substitute unlicensed images.
