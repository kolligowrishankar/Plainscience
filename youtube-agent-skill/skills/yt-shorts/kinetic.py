"""
Reusable motion/caption primitives for Plain Science Shorts renderers.

Why this exists: the 2026-11-06 render was rated 4.5/10 for being visually
flat - static per-beat caption blocks, a slow uniform zoom, no reaction to
beat changes, no impact on the hook. This module gives any render.py three
drop-in pieces that fix that, without forcing a particular visual style:

    - kinetic_caption(...)  word-by-word pop-in captions with the active
      word highlighted, built from real (word, start, end) timestamps.
    - beat_camera(...)      per-beat punch-zoom + a short decaying shake
      impulse, so every cut *reads* as a cut instead of a slow dissolve.
    - hook_punch(...)       an extra-aggressive zoom/shake for the first
      beat only, since the hook is the part that has to grab attention.

Usage sketch inside a render.py's frame(t) function:

    from kinetic import kinetic_caption, beat_camera, hook_punch

    def frame(t):
        im = Image.new('RGB', (W, H), BG)
        d = ImageDraw.Draw(im)
        ... draw scene content for this beat ...
        kinetic_caption(d, FONT_BOLD, words_for_current_beat, t, W, H)
        im = beat_camera(im, t, beat_start, beat_end)
        if beat_start == 0:
            im = hook_punch(im, t, beat_end)
        return im

`words_for_current_beat` is a list of (word, start, end) tuples in seconds,
covering only the words spoken during the current beat. If you only have
even per-beat timing (no real ASR), use `even_word_times(text, start, end)`
to approximate it - still far better than a static block, since each word
still pops in on roughly the right syllable.
"""
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WHITE = (245, 247, 255)
BLACK = (0, 0, 0)
HILITE = (255, 214, 64)


def even_word_times(text, start, end):
    """Fallback word timing: split the beat's duration evenly across words.
    Prefer real ASR word timestamps (e.g. Speko audio_transcribe) when available -
    pass those in directly as (word, start, end) instead of calling this."""
    words = text.split()
    if not words:
        return []
    dur = (end - start) / len(words)
    return [(w, start + i * dur, start + (i + 1) * dur) for i, w in enumerate(words)]


def kinetic_caption(d, font_path, words, t, W, H, base_size=78, y=300,
                     pop_in=0.12, fill=WHITE, hilite=HILITE, max_width=920):
    """
    Draw word-by-word captions: each word pops in (scale 0.4->1.0) over
    `pop_in` seconds starting at its own timestamp, and the currently-
    speaking word is drawn larger and in `hilite`. Wraps to multiple lines.
    `words` is a list of (word, start, end) in seconds, already filtered to
    the words relevant "around now" (pass ~1 beat's worth at a time).
    """
    if not words:
        return

    def font(sz):
        return ImageFont.truetype(font_path, max(1, int(sz)))

    # wrap into lines that fit max_width at base_size
    f0 = font(base_size)
    lines, cur, cur_w = [], [], 0
    space_w = d.textlength(" ", font=f0)
    for w, ws, we in words:
        ww = d.textlength(w, font=f0)
        if cur and cur_w + space_w + ww > max_width:
            lines.append(cur)
            cur, cur_w = [], 0
        cur.append((w, ws, we))
        cur_w += (space_w if cur_w else 0) + ww
    if cur:
        lines.append(cur)

    line_h = int(base_size * 1.28)
    total_h = line_h * len(lines)
    ly = y - total_h // 2

    for line in lines:
        widths = []
        for w, ws, we in line:
            active = ws <= t < we
            sz = base_size * (1.18 if active else 1.0)
            widths.append(d.textlength(w + " ", font=font(sz)))
        line_w = sum(widths)
        lx = (W - line_w) / 2

        for (w, ws, we), ww in zip(line, widths):
            since = t - ws
            if since < 0:
                continue  # not spoken yet: invisible
            scale = min(1.0, since / pop_in) if since < pop_in else 1.0
            # slight overshoot pop (ease-out-back feel)
            if since < pop_in:
                scale = 1.0 - (1.0 - scale) ** 2
                scale *= 1.0 + 0.15 * math.sin(scale * math.pi)
            active = ws <= t < we
            sz = base_size * (1.18 if active else 1.0) * scale
            f = font(max(1, sz))
            col = hilite if active else fill
            tw = d.textlength(w, font=f)
            tx = lx + (ww - d.textlength(w + " ", font=f)) / 2 + (ww - tw) / 2 - (ww - tw)
            tx = lx
            ty = ly + (base_size - sz) / 2
            for dx, dy in ((-3, -3), (3, 3), (-3, 3), (3, -3)):
                d.text((tx + dx, ty + dy), w, font=f, fill=BLACK)
            d.text((tx, ty), w, font=f, fill=col)
            lx += ww
        ly += line_h


def beat_camera(im, t, beat_start, beat_end, punch=0.10, shake_amp=5,
                 shake_freq=26, shake_decay=0.18):
    """
    Apply a punch-zoom (strong right at the cut, decaying across the beat)
    plus a short, decaying shake impulse right at beat_start. Call once per
    frame with the current beat's boundaries; cheap enough for per-frame use.
    """
    W, H = im.size
    since = max(0.0, t - beat_start)
    beat_dur = max(0.05, beat_end - beat_start)

    # punch-in zoom: starts at 1+punch, eases to 1.0 over ~0.35s, then a
    # slow continued push for the rest of the beat
    punch_t = min(1.0, since / 0.35)
    z_punch = punch * (1 - punch_t) ** 2
    z_drift = 0.04 * (since / beat_dur)
    z = 1.0 + z_punch + z_drift

    # shake impulse: decays to ~0 within shake_decay seconds
    if since < shake_decay:
        decay = (1 - since / shake_decay)
        dx = shake_amp * decay * math.sin(since * shake_freq)
        dy = shake_amp * decay * math.cos(since * shake_freq * 1.3)
    else:
        dx = dy = 0.0

    cw, ch = W / z, H / z
    cx, cy = W / 2 - dx, H / 2 - dy
    box = (
        max(0, cx - cw / 2), max(0, cy - ch / 2),
        min(W, cx + cw / 2), min(H, cy + ch / 2),
    )
    return im.resize((W, H), Image.BICUBIC, box=box)


def hook_punch(im, t, hook_end, flash_dur=0.08):
    """Extra punch for the hook's first frame: a quick white flash-fade,
    since the very first frame is what stops the scroll."""
    if t > flash_dur:
        return im
    amt = 1.0 - (t / flash_dur)
    overlay = Image.new('RGB', im.size, WHITE)
    return Image.blend(im, overlay, amt * 0.6)


def whip_cut_alpha(t, cut_at, dur=0.10):
    """Returns 0..1: how much of a quick directional blur-streak overlay to
    draw at a scene cut. Use with ImageFilter.GaussianBlur + a horizontal
    stretch, or simply crossfade two frames; kept as a scalar so render.py
    can implement the visual with whatever's cheapest for its pipeline."""
    d = t - cut_at
    if 0 <= d < dur:
        return 1.0 - (d / dur)
    return 0.0
