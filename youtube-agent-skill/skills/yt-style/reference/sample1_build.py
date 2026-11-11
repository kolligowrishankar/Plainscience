import json, math, subprocess, sys, random, re, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, r'D:\Plainscience\youtube-agent-skill\skills\yt-shorts')
from kinetic import beat_camera, hook_punch
W, H, FPS = 1080, 1920, 30
SR = 24000
FONT = 'fonts/Montserrat.ttf'
MUSIC = r'D:\Plainscience\music\Jumpy Pants - Freedom Trail Studio.mp3'
BLACK = (0, 0, 0); WHITE = (255, 255, 255); YEL = (255, 212, 0); RED = (255, 59, 48); BLUE = (80, 170, 255); PINK = (232, 111, 216)

# ---------- audio: load, trim, compress pauses ----------
def load(p, extra=()):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, *extra, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)
voice = load('voice.wav')[:int(34.95 * SR)]
k = int(0.02 * SR); env = np.sqrt(np.convolve(voice ** 2, np.ones(k) / k, 'same')); sil = env < 0.03 * env.max()
runs = []; i = 0
while i < len(sil):
    if sil[i]:
        j = i
        while j < len(sil) and sil[j]: j += 1
        if (j - i) >= 0.28 * SR: runs.append((i / SR, j / SR))
        i = j
    else: i += 1
dur_in = len(voice) / SR
segs = []; cur = 0.0
first = runs[0][1] if runs and runs[0][0] < 0.05 else 0.0
cur = max(0, first - 0.05)
for a, b in runs:
    if a <= 0.05 or b <= cur: continue
    segs.append((cur, a + 0.06)); cur = b - 0.06
segs.append((cur, dur_in))
GAP = 0.14
parts = []; mp = []; pos = 0.0
for n, (a, b) in enumerate(segs):
    parts.append(voice[int(a * SR):int(b * SR)]); mp.append((a, b, pos)); pos += b - a
    if n < len(segs) - 1: parts.append(np.zeros(int(GAP * SR))); pos += GAP
def f(t):
    for a, b, p in mp:
        if t <= b: return p + max(0, t - a)
    return pos
vo = np.concatenate(parts)
D = round(len(vo) / SR + 0.45, 2); n_s = int(D * SR); vo = np.pad(vo, (0, n_s - len(vo)))
rms = np.sqrt(np.mean(vo[np.abs(vo) > 0.01] ** 2)); vo = vo * (0.12 / rms)

# ---------- words (local whisper timings) ----------
J = json.load(open('voice.json', encoding='utf-8'))
raw = [(w['word'].strip(), w['start'], w['end']) for s in J['segments'] for w in s['words']]
raw = [(w, s, e) for w, s, e in raw if s < 34.9]
words = []
for w, s, e in raw:
    ws = f(s); we = max(ws + 0.09, f(e)); words.append((w, ws, we))
norm = lambda w: re.sub(r'[^a-z0-9]', '', w.lower())
def find(pred, start=0):
    for idx in range(start, len(words)):
        if pred(norm(words[idx][0])): return idx
    raise SystemExit('beat word not found after %d' % start)
ix = {}
ix['hook'] = 0
ix['why'] = find(lambda w: w == 'why')
ix['here'] = find(lambda w: w == 'here', ix['why'])
ix['n3'] = find(lambda w: w == 'number', ix['here'])
ix['yes'] = find(lambda w: w == 'yes', ix['n3'])
ix['two'] = find(lambda w: w == 'two', ix['yes'])
ix['one'] = find(lambda w: w == 'one', ix['two'])
ix['n2'] = find(lambda w: w == 'number', ix['one'])
ix['blood'] = find(lambda w: w == 'its', ix['n2'])
ix['cu'] = find(lambda w: 'copper' in w, ix['blood'])
ix['n1'] = find(lambda w: w == 'number', ix['cu'])
ix['neur'] = find(lambda w: w == 'octopus', ix['n1'])
ix['dog'] = find(lambda w: w == 'about', ix['neur'])
ix['third'] = find(lambda w: 'third' in w or w in ('23', 'twothirds'), ix['dog'])
ix['recap'] = find(lambda w: w == 'three', ix['third'])
order = ['hook', 'why', 'here', 'n3', 'yes', 'two', 'one', 'n2', 'blood', 'cu', 'n1', 'neur', 'dog', 'third', 'recap']
assert [ix[o] for o in order] == sorted(ix[o] for o in order), ix
beats = []
for n, o in enumerate(order):
    a = 0.0 if n == 0 else max(0, words[ix[o]][1] - 0.05)
    b = D if n == len(order) - 1 else max(0, words[ix[order[n + 1]]][1] - 0.05)
    beats.append((a, b, o))
CUTS = [a for a, b, o in beats[1:]]
BADGES = [(beats[3][0], 3), (beats[7][0], 2), (beats[10][0], 1)]

# ---------- images ----------
_fc = {}
def font(sz):
    sz = int(sz)
    if sz not in _fc:
        fo = ImageFont.truetype(FONT, sz)
        try: fo.set_variation_by_axes([800])
        except Exception: pass
        _fc[sz] = fo
    return _fc[sz]
def cover(path, fx=0.5, fy=0.5):
    im = Image.open(path).convert('RGB'); w, h = im.size
    s = max(W / w, H / h); im = im.resize((int(w * s) + 1, int(h * s) + 1), Image.LANCZOS)
    x = int((im.width - W) * fx); y = int((im.height - H) * fy)
    return im.crop((x, y, x + W, y + H))
BG = {'swim': cover('assets/swim.jpg', 0.30), 'eye': cover('assets/eye.jpg', 0.55), 'arms': cover('assets/arms.jpg', 0.5, 0.4),
      'rock': cover('assets/rock.jpg', 0.55), 'dog': cover('assets/dog.jpg', 0.5, 0.3)}
def dim(im, a): return Image.blend(im, Image.new('RGB', (W, H), (0, 0, 0)), a)

def txt(d, s, cx, cy, size, fill=WHITE, stroke=True, anchor='mm'):
    fo = font(size)
    d.text((cx, cy), s, font=fo, fill=fill, anchor=anchor, stroke_width=int(size * 0.09) if stroke else 0, stroke_fill=BLACK)
def pop(lt, dur=0.18):
    if lt >= dur: return 1.0
    x = max(0, lt) / dur; return (1 - (1 - x) ** 2) * (1 + 0.18 * math.sin(x * math.pi))
def heart_pts(cx, cy, size):
    pts = []
    for k2 in range(60):
        tt = k2 / 60 * 2 * math.pi
        x = 16 * math.sin(tt) ** 3; y = 13 * math.cos(tt) - 5 * math.cos(2 * tt) - 2 * math.cos(3 * tt) - math.cos(4 * tt)
        pts.append((cx + x * size / 34, cy - y * size / 34))
    return pts
def heart(d, cx, cy, size, col=(235, 60, 70), ring=None):
    if ring: d.polygon(heart_pts(cx, cy, size * 1.22), fill=ring)
    d.polygon(heart_pts(cx, cy, size), fill=col, outline=WHITE, width=5)
def arrow(d, x0, y0, x1, y1, col=RED, w=12):
    d.line([(x0, y0), (x1, y1)], fill=col, width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    for s in (-0.5, 0.5):
        d.line([(x1, y1), (x1 - 46 * math.cos(ang + s), y1 - 46 * math.sin(ang + s))], fill=col, width=w)
def panel(im, box, alpha=0.62, col=(8, 16, 34)):
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).rounded_rectangle(box, 40, fill=col + (int(255 * alpha),))
    return Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
rng = random.Random(7)
NODES = [(rng.randint(90, 990), rng.randint(650, 1300)) for _ in range(70)]
EDGES = [(a, b) for a in range(70) for b in range(a + 1, 70) if math.dist(NODES[a], NODES[b]) < 210]

# ---------- scenes ----------
def scene(name, lt, t):
    if name == 'hook':
        im = dim(BG['swim'], 0.15).copy(); d = ImageDraw.Draw(im)
        txt(d, 'HOW MANY', 540, 330, 150, WHITE); txt(d, 'HEARTS?', 540, 500, 190, YEL)
        return im
    if name == 'why':
        im = dim(BG['eye'], 0.25).copy(); d = ImageDraw.Draw(im); s = 1 + 0.1 * math.sin(lt * 10)
        txt(d, 'WHY', 540, 480, 150, WHITE); txt(d, '3?', 540, 780, int(420 * s), YEL)
        return im
    if name == 'here':
        im = dim(BG['rock'], 0.35).copy(); d = ImageDraw.Draw(im); p = pop(lt)
        txt(d, '3 FACTS', 540, 640, int(200 * p), YEL); txt(d, 'THAT SOUND', 540, 880, int(116 * p)); txt(d, 'MADE UP', 540, 1020, int(116 * p))
        return im
    if name in ('n3', 'n2', 'n1'):
        base = {'n3': dim(BG['swim'], 0.45), 'n2': dim(BG['arms'], 0.4), 'n1': None}[name]
        if base is None: base = Image.new('RGB', (W, H), (10, 14, 30))
        return base.copy()
    if name in ('yes', 'two', 'one'):
        im = dim(BG['swim'], 0.6); im = panel(im, (110, 470, 970, 1290)); d = ImageDraw.Draw(im)
        pulse = 1 + 0.07 * math.sin(lt * 12)
        txt(d, 'OCTOPUS HEARTS', 540, 540, 54, WHITE, stroke=False)
        main = (540, 840, 170); gl = (310, 1050, 105); gr = (770, 1050, 105)
        dimc = (120, 40, 50)
        for kx, (cx, cy, sz) in enumerate((main, gl, gr)):
            t0 = [0.15, 0.40, 0.60][kx] if name == 'yes' else 0
            sc = pop(lt - t0) if name == 'yes' else 1.0
            if sc <= 0: continue
            on = (name == 'yes') or (name == 'two' and kx > 0) or (name == 'one' and kx == 0)
            heart(d, cx, cy, sz * sc * (pulse if on else 1.0), (235, 60, 70) if on else dimc, ring=(255, 255, 255) if (on and name != 'yes') else None)
        for (cx, cy, sz) in (gl, gr): d.line([(540, 900), (cx, cy - 60)], fill=BLUE, width=9)
        if name == 'two':
            txt(d, '2 GILL HEARTS', 540, 1200, 78, YEL)
            arrow(d, 400, 1160, 330, 1115); arrow(d, 680, 1160, 750, 1115)
        if name == 'one':
            txt(d, '1 BODY HEART', 540, 650, 78, YEL); arrow(d, 540, 700, 540, 755)
        txt(d, 'simplified diagram', 540, 1262, 30, (190, 200, 220), stroke=False)
        return im
    if name == 'blood':
        im = dim(BG['arms'], 0.3).copy(); d = ImageDraw.Draw(im)
        txt(d, 'BLUE', 540, 560, 270, BLUE); txt(d, 'BLOOD', 540, 830, 190, WHITE)
        for n2 in range(7):
            x = 120 + n2 * 140; y = (lt * 700 + n2 * 230) % 1500 + 150
            d.ellipse([x - 28, y - 28 + 20, x + 28, y + 28 + 20], fill=(70, 150, 255), outline=WHITE, width=4)
            d.polygon([(x - 26, y + 8), (x + 26, y + 8), (x, y - 42)], fill=(70, 150, 255))
        return im
    if name == 'cu':
        im = dim(BG['arms'], 0.55).copy(); d = ImageDraw.Draw(im); p = pop(lt)
        txt(d, 'COPPER-RICH', 540, 360, 84); txt(d, 'PROTEIN', 540, 470, 84)
        cx, cy, hw, hh = 540, 930, int(230 * p), int(270 * p)
        d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], 36, fill=(205, 127, 50), outline=WHITE, width=8)
        if p > 0.9:
            txt(d, '29', cx - 150, cy - 190, 70, WHITE, stroke=False); txt(d, 'Cu', cx, cy, 230, WHITE); txt(d, 'COPPER', cx, cy + 190, 62, WHITE, stroke=False)
        return im
    if name == 'neur':
        im = Image.new('RGB', (W, H), (8, 12, 30)); d = ImageDraw.Draw(im)
        for a, b in EDGES: d.line([NODES[a], NODES[b]], fill=(40, 90, 170), width=3)
        for kx, (x, y) in enumerate(NODES):
            r = 9 + 5 * (0.5 + 0.5 * math.sin(t * 4 + kx)); d.ellipse([x - r, y - r, x + r, y + r], fill=(110, 200, 255))
        val = int(500_000_000 * min(1, lt / 1.2) ** 0.7)
        txt(d, f'{val:,}+', 540, 360, 118, YEL); txt(d, 'NEURONS', 540, 500, 100, WHITE)
        return im
    if name == 'dog':
        im = dim(BG['dog'], 0.15).copy(); d = ImageDraw.Draw(im)
        txt(d, 'ABOUT AS MANY', 540, 300, 100, WHITE); txt(d, 'AS A DOG', 540, 430, 140, YEL)
        return im
    if name == 'third':
        im = dim(BG['arms'], 0.5).copy(); d = ImageDraw.Draw(im); sweep = 240 * min(1, lt / 0.7)
        box = [240, 440, 840, 1040]
        d.arc(box, 0, 360, fill=(90, 90, 100), width=90)
        d.arc(box, -90, -90 + sweep, fill=YEL, width=90)
        txt(d, '2/3', 540, 740, 190, WHITE); txt(d, 'IN ITS ARMS', 540, 1180, 96, YEL)
        return im
    if name == 'recap':
        third = D - beats[-1][0]
        if lt < third / 3: im = dim(BG['swim'], 0.25).copy(); d = ImageDraw.Draw(im); txt(d, '3 HEARTS', 540, 520, 170, YEL)
        elif lt < 2 * third / 3: im = dim(BG['arms'], 0.25).copy(); d = ImageDraw.Draw(im); txt(d, 'BLUE', 540, 480, 230, BLUE); txt(d, 'BLOOD', 540, 700, 160)
        else: im = dim(BG['rock'], 0.3).copy(); d = ImageDraw.Draw(im); txt(d, 'NEURONS', 540, 480, 140); txt(d, 'IN THE ARMS', 540, 660, 110, YEL)
        return im
def badge(im, t):
    cur = None
    for st, n in BADGES:
        if t >= st: cur = (st, n)
    if not cur: return im
    st, n = cur; lt = t - st; e = min(1, lt / 0.45); e = 1 - (1 - e) ** 3
    x = 540 + (130 - 540) * e; y = 760 + (150 - 760) * e; s = (2.8 + (1 - 2.8) * e) * (0.4 + 0.6 * min(1, lt / 0.12))
    r = int(78 * s); d = ImageDraw.Draw(im)
    d.ellipse([x - r - 8, y - r - 8, x + r + 8, y + r + 8], fill=WHITE); d.ellipse([x - r, y - r, x + r, y + r], fill=PINK)
    d.text((x, y), str(n), font=font(int(105 * s)), fill=WHITE, anchor='mm')
    return im

# ---------- captions ----------
KEY = {'hearts', 'heart', 'three', 'blue', 'blood', 'neurons', 'arms', 'copper', 'copperrich', 'dog', 'gills', 'million', 'twothirds', '500', 'octopus'}
groups = []; cur = []
for kx, (w, s, e) in enumerate(words):
    cur.append(kx)
    if re.search(r'[.?!,]$', w) or len(cur) >= 3: groups.append(cur); cur = []
if cur: groups.append(cur)
def captions(im, t):
    g = None
    for gi, gr in enumerate(groups):
        s0 = words[gr[0]][1]; e0 = words[groups[gi + 1][0]][1] if gi + 1 < len(groups) else D
        if s0 - 0.02 <= t < min(e0, words[gr[-1]][2] + 0.35): g = gr; break
    if not g: return im
    ov = Image.new('RGBA', (W, H - 1240), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for yy in range(H - 1240): od.line([(0, yy), (W, yy)], fill=(0, 0, 0, int(165 * min(1, yy / 360) ** 1.4)))
    im = im.convert('RGBA'); im.alpha_composite(ov, (0, 1240)); im = im.convert('RGB')
    d = ImageDraw.Draw(im)
    labels = [re.sub(r'[.,]+$', '', words[k][0]).upper() for k in g]
    size = 70
    while sum(d.textlength(l, font=font(size)) + 26 for l in labels) > 940 and size > 40: size -= 4
    total = sum(d.textlength(l, font=font(size)) + 26 for l in labels) - 26; x = (W - total) / 2; y = 1480
    for k, l in zip(g, labels):
        w, s, e = words[k]; since = t - s
        wd = d.textlength(l, font=font(size))
        if since >= 0:
            sc = pop(since, 0.12); active = s <= t < e
            sz = size * sc * (1.1 if active else 1.0)
            key = norm(w) in KEY
            col = YEL if key else WHITE
            d.text((x + wd / 2, y), l, font=font(max(8, sz)), fill=col, anchor='mm', stroke_width=max(3, int(size * 0.11)), stroke_fill=BLACK)
        x += wd + 26
    return im

def beat_of(t):
    for n, (a, b, o) in enumerate(beats):
        if a <= t < b: return n
    return len(beats) - 1
def frame(t):
    n = beat_of(t); a, b, o = beats[n]; lt = t - a
    im = scene(o, lt, t)
    im = beat_camera(im, t, a, b, punch=0.08 if n else 0.14)
    im = badge(im, t)
    if n == 0: im = hook_punch(im, t, b)
    if n and lt < 0.1:
        bl = im.filter(ImageFilter.GaussianBlur(16)); im = Image.blend(im, bl, 0.7 * (1 - lt / 0.1))
    return captions(im, t)

# ---------- audio mix ----------
def build_audio():
    mu = load(MUSIC, ('-ss', '12', '-t', str(D + 1), '-af', 'loudnorm=I=-30:TP=-3'))
    mu = np.pad(mu, (0, max(0, n_s - len(mu))))[:n_s]
    fd = int(0.8 * SR); mu[:fd] *= np.linspace(0, 1, fd); mu[-fd:] *= np.linspace(1, 0, fd)
    e2 = np.convolve(np.abs(vo), np.ones(int(0.12 * SR)) / int(0.12 * SR), 'same')
    sp = np.clip((e2 - 0.01) / 0.04, 0, 1); sp = np.convolve(sp, np.ones(int(0.25 * SR)) / int(0.25 * SR), 'same')
    mu = mu * (10 ** ((-2 + 7 * (1 - sp)) / 20) * 0.5)
    sfx = np.zeros(n_s)
    def add(at, sig):
        i2 = int(at * SR); sfx[i2:i2 + len(sig)] += sig[:max(0, n_s - i2)]
    def tone(f0, dur, a, decay=12, f1=None):
        tt = np.arange(int(dur * SR)) / SR; fr = f0 if f1 is None else f0 + (f1 - f0) * tt / dur
        return a * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt * decay)
    def whoosh(dur=0.2, a=0.05):
        tt = np.arange(int(dur * SR)) / SR; x = np.random.RandomState(1).randn(len(tt)); x = np.convolve(x, np.ones(40) / 40, 'same'); return a * x * np.sin(np.pi * tt / dur)
    for c in CUTS: add(c - 0.03, whoosh()); add(c, tone(900, 0.08, 0.05, 40))
    for st, n in BADGES: add(st + 0.05, tone(1318, 0.5, 0.10, 6) + tone(1760, 0.5, 0.06, 6))
    h0 = beats[4][0]
    for off in (0.15, 0.40, 0.60): add(h0 + off, tone(150, 0.3, 0.14, 9, 90))
    b0 = beats[8][0]
    for off in (0.1, 0.5, 0.9): add(b0 + off, tone(1500, 0.15, 0.07, 30, 700))
    add(beats[0][0] + 0.0, tone(110, 0.4, 0.10, 8, 60))
    mix = vo + mu + sfx * 0.8; mix = mix * min(1, 0.89 / np.abs(mix).max())
    x = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
    with wave.open('audio.wav', 'wb') as w2: w2.setnchannels(2); w2.setsampwidth(2); w2.setframerate(SR); w2.writeframes(x.tobytes())

if __name__ == '__main__':
    print('duration', D, 'beats', [(round(a, 2), o) for a, b, o in beats])
    if len(sys.argv) > 1 and sys.argv[1] == 'snap':
        import os; os.makedirs('snaps', exist_ok=True)
        for a, b, o in beats: frame(a + min(0.9, (b - a) * 0.6)).save(f'snaps/{o}.png')
        sheet = Image.new('RGB', (5 * 270, 3 * 480))
        for kx, (a, b, o) in enumerate(beats): sheet.paste(Image.open(f'snaps/{o}.png').resize((270, 480)), ((kx % 5) * 270, (kx // 5) * 480))
        sheet.save('snaps/sheet.png'); sys.exit(0)
    build_audio()
    nf = int(D * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'audio.wav',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', 'plain-science-sample1-octopus.mp4'], stdin=subprocess.PIPE)
    for k3 in range(nf): p.stdin.write(frame(k3 / FPS).tobytes())
    p.stdin.close(); p.wait(); print('done', nf, 'frames')

