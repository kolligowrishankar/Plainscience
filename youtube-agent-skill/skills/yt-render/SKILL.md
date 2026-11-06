---
name: yt-render
description: >-
  Render and voice a Plain Science Short so it does not read as flat,
  robotic or static. Use for "render the short", "make the video", "add
  the voice", or any step after the script is gated and before upload.
---

# yt-render

The 2026-11-06 render was rated 4.5/10: plain diagrams, no animation, nothing
attention-grabbing, no music with any energy, a robotic AI voice. This skill
is the fix. It is not optional polish - a render that skips any of the four
checks below is not ready to upload.

## 1. Motion: every beat is a cut, not a dissolve

Use `../yt-shorts/kinetic.py` (`beat_camera`, `hook_punch`) in every
render.py. `beat_camera(im, t, beat_start, beat_end)` gives a punch-zoom plus
a short decaying shake right at the start of each beat, so a scene change
*reads* as a cut. Call `hook_punch` for the first beat only - the hook needs
to hit harder than the rest of the video. A beat longer than 3 seconds with
no motion inside it (no shake, no zoom, no element entering/leaving) fails
review; split it.

## 2. Captions: word-by-word, not static blocks

Use `kinetic_caption(...)` from the same module. It needs `(word, start,
end)` timestamps. Get real ones with Speko `audio_transcribe` on the
rendered voiceover (word_timestamps: true) - this is one extra API call and
is worth it; the fallback `even_word_times()` (even split per beat) is only
for a quick preview render, never for the version that gets uploaded, since
evenly-spaced words drift visibly out of sync with real speech.

## 3. Voice: expressive, not a monotone narrator

Synthesize with Speko `audio_synthesize` using an instruction-capable model
so delivery can actually be directed:

```
voice: "fable"
model: "gpt-4o-mini-tts"
instructions: "Speak like an excited, warm older sibling sharing a mind-
  blowing secret with a curious 14-year-old. Energetic and quick-paced on
  the hook, then conversational and a little playful. Vary pitch and pace
  naturally, add a short dramatic pause before any question, emphasize
  surprising words. Never flat, never a news-anchor monotone."
constraints: {allowedProviders: {tts: ["openai"]}}
```

Tested 2026-11-06: this reads noticeably more alive than the flat ElevenLabs
default used before. Rewrite the `instructions` text per script if the hook
formula calls for a different energy (e.g. a calm "here's the weird part"
beat vs. an urgent cold open), but keep the core: vary pace, never monotone.

If the user is recording their own voice instead (ask once per batch, not
every run), skip this step and splice their audio in directly - do not run
it through TTS.

## 4. Music: real royalty-free tracks, ducked under the voice

No synthesized pads or generated tones - they are what makes a render sound
cheap. Pull an actual track from the YouTube Audio Library (Studio > Audio
Library > filter "no attribution required"), download it once per batch of
videos (ask the user before the first download: name the track, source URL,
file size), and reuse it across several Shorts rather than fetching a new
one per video. Duck it under the voice (roughly -20 to -24 dB under the
narration, lower during any spoken line, allowed to come up slightly in
silent gaps) rather than mixing at a fixed low volume throughout - a fixed
low mix is part of why the old renders felt lifeless.

## Gate

Before saving to the queue folder, confirm: every beat has a cut-feeling
motion, captions are word-by-word with real timestamps, the voice used
`gpt-4o-mini-tts` + instructions (or the user's own recording), and the
music is a real track, ducked, not a synthesized pad. If any of these is
missing, the render is not ready - do not save it to the queue as final.
