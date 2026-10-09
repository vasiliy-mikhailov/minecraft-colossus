#!/usr/bin/env python3
"""Colossus: box model + sampled texture + Java + bbmodel + previews.

Coordinates: parts are authored in "H-space": x = MC model x (entity's right = -x),
H = height above ground (up), z = MC model z (front = -z).  MC model y = 24 - H.
"""
import json, math, os, sys, uuid, base64, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)
REF = np.array(Image.open(os.path.join(HERE, 'ref.png')).convert('RGB')).astype(np.int32)
S = 7.0  # reference pixels per model unit

# view calibration: (image x of model x=0 / z=0, image y of ground, x sign)
VIEW = {
    'front': dict(cx=146.5, g=412.0, sx=+1),   # img_x = cx + 7*x
    'back':  dict(cx=626.5, g=414.0, sx=-1),   # img_x = cx - 7*x
    'side':  dict(cx=386.0, g=415.0, sx=+1),   # img_x = cx + 7*z  (left side, +x face)
}
BG = np.array([45, 44, 43])

# ----------------------------------------------------------------- geometry
# bones: name -> parent, pivot (x, H, z), rotation (rx, ry, rz) radians (MC convention)
BONES = {
    'root':      dict(parent=None,        pivot=(0, 0, 0),        rot=(0, 0, 0)),
    'body':      dict(parent='root',      pivot=(0, 21, 0),       rot=(0, 0, 0)),
    'head':      dict(parent='root',      pivot=(0, 38, -1),      rot=(0, 0, 0)),
    'right_arm': dict(parent='root',      pivot=(-11, 36, -0.5),  rot=(0, 0, 0)),
    'left_arm':  dict(parent='root',      pivot=(11, 36, -0.5),   rot=(0, 0, 0)),
    'sword':     dict(parent='right_arm', pivot=(-12, 18.5, -0.5), rot=(-0.7, 0, 0.18)),
    'right_leg': dict(parent='root',      pivot=(-4.5, 21, 0),    rot=(0, 0, 0)),
    'left_leg':  dict(parent='root',      pivot=(4.5, 21, 0),     rot=(0, 0, 0)),
}

PARTS = []
def part(name, bone, x0, x1, H0, H1, z0, z1, **opt):
    for a, b in ((x0, x1), (H0, H1), (z0, z1)):
        assert abs((b - a) - round(b - a)) < 1e-6 and b > a, (name, a, b)
    PARTS.append(dict(name=name, bone=bone, x0=x0, x1=x1, H0=H0, H1=H1, z0=z0, z1=z1, **opt))

def mirror_x(name, bone, x0, x1, *a, **k):
    part(name, bone, -x1, -x0, *a, **k)

# head: great helm + stepped crest
part('helm', 'head', -4, 4, 38, 47, -6.5, 1.5)
for k, (z0, z1, H0, H1) in enumerate([(-4.5, -2.5, 47, 52), (-2.5, -1.5, 46.5, 51.5), (-1.5, -0.5, 46, 51),
                                       (-0.5, 0.5, 45.5, 50.5), (0.5, 1.5, 45, 50), (1.5, 2.5, 44, 49),
                                       (2.5, 3.5, 43, 48), (3.5, 4.5, 42, 47), (4.5, 5.5, 41, 46)]):
    part('crest%d' % (k + 1), 'head', -1.5, 1.5, H0, H1, z0, z1)
# body
part('chest', 'body', -8, 8, 31, 39, -5.5, 4.5)
part('ribs', 'body', -7, 7, 28, 31, -5, 4)
part('waist', 'body', -6, 6, 25, 28, -4.5, 3.5)
part('belt', 'body', -7, 7, 21, 25, -5, 5, side_src='front')
part('buckle', 'body', -3, 3, 21.5, 24.5, -6, -5, side_src='front')
part('tabard', 'body', -3, 3, 10, 21, -5, -4, cutout=True)
part('back_plate', 'body', -7, 7, 29, 36, 4.5, 5.5)
part('back_tabard', 'body', -4, 4, 11, 25, 5, 6)
# arms
for side, sgn in (('right', -1), ('left', +1)):
    arm = side + '_arm'
    def P(n, x0, x1, *a, **k):
        if sgn < 0: part(n, arm, x0, x1, *a, **k)
        else: mirror_x(n, arm, x0, x1, *a, **k)
    P(side + '_pauldron', -14, -8, 31, 39, -5, 4)
    P(side + '_mail', -13.5, -8.5, 27, 31, -3, 2, side_src='front')
    P(side + '_bracer', -15, -8, 21, 27, -4, 3, side_src='front')
    P(side + '_hand', -14.5, -9.5, 16, 21, -3, 2, side_src='front')
# legs
for side, sgn in (('right', -1), ('left', +1)):
    leg = side + '_leg'
    def P(n, x0, x1, *a, **k):
        if sgn < 0: part(n, leg, x0, x1, *a, **k)
        else: mirror_x(n, leg, x0, x1, *a, **k)
    P(side + '_thigh', -7.5, -1.5, 10, 21, -3, 3)
    P(side + '_tasset', -8, -1, 14, 21, -4, 4, side_src='front')
    P(side + '_shin', -8, -1, 3, 10, -4, 4)
    P(side + '_boot', -9, -1, 0, 3, -5.5, 4.5)
# sword (authored hanging straight down from the fist; the bone tilts it)
part('grip', 'sword', -13, -11, 14, 22, -1.5, 0.5, tex='grip')
part('guard', 'sword', -15.5, -8.5, 12, 14, -2, 1, tex='guard')
part('blade', 'sword', -14, -10, -1, 12, -1.5, 0.5, tex='blade')

# ----------------------------------------------------------------- sampling
def classify(px):
    px = px.astype(float)
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    mx = px.max(-1); sat = (mx - px.min(-1)) / (mx + 1)
    bg = (np.abs(px - BG).sum(-1) < 13)
    eye = (r > 170) & (r - b > 110) & (g > 50)
    gold = (sat > 0.27) & (r > 95) & (r >= g) & (g > b) & ~eye
    green = (g - r > 4) & (g >= b) & ~gold & ~eye & ~bg
    return bg, eye, gold, green

def sample_rect(view, ix0, ix1, iy0, iy1, w, h, mirror=False):
    """Downsample image rect to w x h cells: majority material class, median colour. RGBA (a=0 invalid)."""
    out = np.zeros((h, w, 4), np.uint8)
    cw = (ix1 - ix0) / w; ch = (iy1 - iy0) / h
    for j in range(h):
        for i in range(w):
            cx0 = ix0 + i * cw; cy0 = iy0 + j * ch
            xs = np.arange(int(round(cx0 + 0.1 * cw)), int(round(cx0 + 0.9 * cw)))
            ys = np.arange(int(round(cy0 + 0.1 * ch)), int(round(cy0 + 0.9 * ch)))
            xs = xs[(xs >= 0) & (xs < REF.shape[1])]; ys = ys[(ys >= 41) & (ys < REF.shape[0])]
            if len(xs) == 0 or len(ys) == 0:
                continue
            blk = REF[np.ix_(ys, xs)].reshape(-1, 3)
            bg, eye, gold, green = classify(blk)
            n = len(blk)
            if eye.sum() >= 2:
                m = eye; c = blk[m].max(0)
            elif gold.sum() >= 0.3 * n:
                m = gold; c = np.median(blk[m], 0)
            elif bg.sum() > 0.5 * n:
                continue
            elif green.sum() >= 0.45 * n:
                m = green; c = np.median(blk[m], 0)
            else:
                m = ~bg & ~gold & ~eye
                if m.sum() == 0: m = ~bg
                c = np.median(blk[m], 0)
                c = np.array([c.mean() + 4, c.mean() + 1, c.mean() - 3])  # de-tint stone to neutral grey
            out[j, i, :3] = np.clip(c, 0, 255); out[j, i, 3] = 255
    if mirror:
        out = out[:, ::-1].copy()
    return out

def fill_invalid(t, fallback=(118, 116, 112)):
    t = t.copy()
    a = t[..., 3] > 0
    if not a.any():
        t[..., :3] = fallback; t[..., 3] = 255
        return t
    for _ in range(64):
        if a.all(): break
        na = a.copy()
        h, w = a.shape
        for j in range(h):
            for i in range(w):
                if a[j, i]: continue
                acc = []
                for dj, di in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    jj, ii = j + dj, i + di
                    if 0 <= jj < h and 0 <= ii < w and a[jj, ii]:
                        acc.append(t[jj, ii, :3].astype(int))
                if acc:
                    t[j, i, :3] = np.mean(acc, 0); na[j, i] = True
        a = na
    t[..., 3] = 255
    return t

def view_rect(view, x0, x1, H0, H1):
    v = VIEW[view]
    if v['sx'] > 0:
        ix0, ix1 = v['cx'] + S * x0, v['cx'] + S * x1
    else:
        ix0, ix1 = v['cx'] - S * x1, v['cx'] - S * x0
    return ix0, ix1, v['g'] - S * H1, v['g'] - S * H0

rng = np.random.default_rng(7)

def noise(t, amp=10):
    t = t.copy()
    n = rng.integers(-amp, amp + 1, t.shape[:2])[..., None]
    t[..., :3] = np.clip(t[..., :3].astype(int) + n, 0, 255)
    return t

def shade(t, f):
    t = t.copy(); t[..., :3] = np.clip(t[..., :3].astype(float) * f, 0, 255); return t

def resize_nn(t, w, h):
    return np.array(Image.fromarray(t, 'RGBA').resize((w, h), Image.NEAREST))

GOLD = np.array([176, 140, 74]); GOLD_D = np.array([120, 92, 44])
def solid(w, h, c, amp=8):
    t = np.zeros((h, w, 4), np.uint8); t[..., :3] = c; t[..., 3] = 255
    return noise(t, amp)

def blade_front(w=4, h=15):
    top = np.array([52.0, 300.0]); bot = np.array([36.0, 389.0])
    ax = bot - top; L = np.linalg.norm(ax); ax /= L
    pp = np.array([ax[1], -ax[0]])
    if pp[0] < 0: pp = -pp
    cellw = 30.0 / w
    out = np.zeros((h, w, 4), np.uint8)
    for j in range(h):
        for i in range(w):
            c = top + (j + 0.5) / h * L * ax + (i - (w - 1) / 2) * cellw * pp
            x, y = int(c[0]), int(c[1])
            blk = REF[y - 1:y + 2, x - 1:x + 2].reshape(-1, 3)
            px = blk[4]
            if np.abs(px - BG).sum() < 25:
                px = np.array([150, 150, 150])
            out[j, i, :3] = px; out[j, i, 3] = 255
    return out

def make_faces(p):
    """Return dict face-> RGBA array, faces: top,bottom,west(-x),north(front),east(+x),south(back)."""
    w = int(round(p['x1'] - p['x0'])); h = int(round(p['H1'] - p['H0'])); d = int(round(p['z1'] - p['z0']))
    tex = p.get('tex')
    if tex == 'blade':
        f = blade_front(w, h)
        edge = solid(d, h, (196, 196, 192), 10)
        return dict(north=f, south=f[:, ::-1].copy(), west=edge, east=edge,
                    top=solid(w, d, (150, 150, 146)), bottom=solid(w, d, (205, 205, 200)))
    if tex == 'guard':
        f = solid(w, h, GOLD, 10); f[-1, :, :3] = GOLD_D
        s = solid(d, h, GOLD, 10); s[-1, :, :3] = GOLD_D
        return dict(north=f, south=f.copy(), west=s, east=s.copy(), top=solid(w, d, GOLD + 20), bottom=solid(w, d, GOLD_D))
    if tex == 'grip':
        f = solid(w, h, (92, 70, 44), 6)
        f[::2, :, :3] = GOLD_D; f[0, :, :3] = GOLD; f[-1, :, :3] = GOLD
        s = f[:, :d].copy() if d <= w else resize_nn(f, d, h)
        return dict(north=f, south=f.copy(), west=s, east=s.copy(), top=solid(w, d, GOLD), bottom=solid(w, d, GOLD))

    return paint_part(p, w, h, d)

# palettes (albedo; sampled from the lit, front-facing areas of the reference, lightly cleaned)
STONE = np.array([(84, 81, 78), (100, 97, 93), (116, 113, 108), (130, 127, 122), (145, 142, 136), (162, 159, 152)])
GOLDS = {'g': (112, 88, 52), 'G': (156, 124, 72), 'H': (186, 154, 98)}
GREEN = np.array([(52, 66, 46), (66, 84, 58), (82, 102, 70), (98, 120, 84)])
FLAT = {'M': (60, 76, 52), 'D': (30, 32, 28), 'E': (255, 150, 40), 'W': (70, 72, 54)}
BASE = {'S': 2.1, 'L': 3.1, 'K': 0.9, 'P': 1.4}

def ref_shading(view, rect, n_w, n_h):
    """Per-cell luminance offset (in stone-ramp steps) sampled from the reference view."""
    ix0, ix1, iy0, iy1 = rect
    cw = (ix1 - ix0) / n_w; ch = (iy1 - iy0) / n_h
    off = np.zeros((n_h, n_w)); ok = np.zeros((n_h, n_w), bool)
    for j in range(n_h):
        for i in range(n_w):
            xs = np.arange(int(round(ix0 + (i + .15) * cw)), int(round(ix0 + (i + .85) * cw)))
            ys = np.arange(int(round(iy0 + (j + .15) * ch)), int(round(iy0 + (j + .85) * ch)))
            xs = xs[(xs >= 0) & (xs < REF.shape[1])]; ys = ys[(ys >= 41) & (ys < REF.shape[0])]
            if len(xs) == 0 or len(ys) == 0: continue
            blk = REF[np.ix_(ys, xs)].reshape(-1, 3)
            bg, eye, gold, green = classify(blk)
            m = ~bg & ~gold & ~eye
            if m.sum() < 0.4 * len(blk): continue
            off[j, i] = np.median(blk[m].mean(1)); ok[j, i] = True
    if ok.sum() < 2: return np.zeros((n_h, n_w))
    med = np.median(off[ok])
    return np.where(ok, np.clip((off - med) / 22.0, -1.0, 1.0), 0)

def paint(gridc, shading):
    h = len(gridc); w = len(gridc[0])
    out = np.zeros((h, w, 4), np.uint8)
    for j in range(h):
        for i in range(w):
            c = gridc[j][i]
            if c == '.': continue
            jit = rng.normal(0, 0.33)
            if c in BASE:
                lv = BASE[c] + shading[j, i] + jit
                if c == 'P': col = STONE[int(np.clip(round(lv), 0, 5))] * np.array([0.93, 0.95, 0.98])
                else: col = STONE[int(np.clip(round(lv), 0, 5))]
            elif c in GOLDS:
                base = np.array(GOLDS[c], float); col = base * (1 + rng.normal(0, 0.05))
            elif c in ('C', 'c'):
                lv = (2 if (i + (j % 2)) % 2 == 0 else 1) + (j == 0) * 0.5 - (c == 'c') * 1
                col = GREEN[int(np.clip(round(lv + jit * 0.6), 0, 3))]
            else:
                col = np.array(FLAT[c], float) + rng.normal(0, 3)
            out[j, i, :3] = np.clip(col, 0, 255); out[j, i, 3] = 255
    return out

def paint_part(p, w, h, d):
    from design import design
    G = design(p['name'], w, h, d)
    sh = {}
    sh['north'] = ref_shading('front', view_rect('front', p['x0'], p['x1'], p['H0'], p['H1']), w, h)
    sh['south'] = ref_shading('back', view_rect('back', p['x0'], p['x1'], p['H0'], p['H1']), w, h)
    se = ref_shading('side', (VIEW['side']['cx'] + S * p['z0'], VIEW['side']['cx'] + S * p['z1'],
                              VIEW['side']['g'] - S * p['H1'], VIEW['side']['g'] - S * p['H0']), d, h)
    if p.get('side_src') == 'front':
        se = np.zeros((h, d))
    sh['east'] = se; sh['west'] = se[:, ::-1]
    sh['top'] = np.zeros((d, w)); sh['bottom'] = np.zeros((d, w))
    return {k: paint(G[k], sh[k]) for k in G}

# ----------------------------------------------------------------- UV packing
def footprint(p):
    w = int(round(p['x1'] - p['x0'])); h = int(round(p['H1'] - p['H0'])); d = int(round(p['z1'] - p['z0']))
    return 2 * (w + d), d + h, w, h, d

def pack(TW, TH):
    order = sorted(range(len(PARTS)), key=lambda i: -footprint(PARTS[i])[1])
    x = y = rowh = 0
    pos = {}
    for i in order:
        fw, fh = footprint(PARTS[i])[:2]
        if x + fw > TW:
            x = 0; y += rowh; rowh = 0
        if y + fh > TH:
            return None
        pos[i] = (x, y); x += fw; rowh = max(rowh, fh)
    return pos

TW = TH = 128
pos = pack(TW, TH)
if pos is None:
    TW, TH = 256, 128
    pos = pack(TW, TH)
    if pos is None:
        TW = TH = 256; pos = pack(TW, TH)
print('texture', TW, TH)

tex = np.zeros((TH, TW, 4), np.uint8)
for i, p in enumerate(PARTS):
    u, v = pos[i]; p['u'], p['v'] = u, v
    _, _, w, h, d = footprint(p)
    f = make_faces(p)
    def put(arr, x, y):
        hh, ww = arr.shape[:2]
        assert (hh, ww) == arr.shape[:2]
        tex[y:y + hh, x:x + ww] = arr
    put(f['top'], u + d, v)
    put(f['bottom'], u + d + w, v)
    put(f['west'], u, v + d)
    put(f['north'], u + d, v + d)
    put(f['east'], u + d + w, v + d)
    put(f['south'], u + 2 * d + w, v + d)

# emissive eyes layer: orange eye texels on the helm front
eyes = np.zeros_like(tex)
r, g, b, a = [tex[..., k].astype(int) for k in range(4)]
eyemask = (r > 170) & (r - b > 110) & (a > 0)
hp = next(p for p in PARTS if p['name'] == 'helm')
hw, hh, hd = 8, 9, 8
region = np.zeros_like(eyemask); region[hp['v'] + hd:hp['v'] + hd + hh, hp['u'] + hd:hp['u'] + hd + hw] = True
eyemask &= region
print('eye texels', int(eyemask.sum()), np.argwhere(eyemask).tolist())
eyes[eyemask] = [255, 160, 50, 255]
tex[eyemask, :3] = [255, 150, 40]
Image.fromarray(tex, 'RGBA').save(os.path.join(OUT, 'colossus.png'))
Image.fromarray(eyes, 'RGBA').save(os.path.join(OUT, 'colossus_eyes.png'))

# ----------------------------------------------------------------- MC math / renderer
def mc_abs_pivot(bone):
    x, H, z = BONES[bone]['pivot']; return np.array([x, 24.0 - H, z])

def rot_zyx(rx, ry, rz):
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def bone_world(bone, pose):
    """4x4 transform from bone-local (relative to its pivot) to model space; pose: bone -> (dx,dy,dz,rx,ry,rz) extra."""
    b = BONES[bone]
    off = mc_abs_pivot(bone) - (mc_abs_pivot(b['parent']) if b['parent'] else np.zeros(3))
    if b['parent'] is None:
        off = np.array([0.0, 24.0, 0.0])
    extra = pose.get(bone, (0, 0, 0, 0, 0, 0))
    rx, ry, rz = b['rot']
    M = np.eye(4); M[:3, 3] = off + np.array(extra[:3]); M[:3, :3] = rot_zyx(rx + extra[3], ry + extra[4], rz + extra[5])
    if b['parent']:
        return bone_world(b['parent'], pose) @ M
    return M

def cube_polys(p, pose):
    """MC ModelPart.Cube polygons: list of (verts 4x3 model space, uv 4x2, normal)."""
    piv = mc_abs_pivot(p['bone'])
    x0, x1 = p['x0'] - piv[0], p['x1'] - piv[0]
    y0, y1 = (24 - p['H1']) - piv[1], (24 - p['H0']) - piv[1]
    z0, z1 = p['z0'] - piv[2], p['z1'] - piv[2]
    if p['bone'] == 'root':
        y0, y1 = (24 - p['H1']) - 24, (24 - p['H0']) - 24
    _, _, w, h, d = footprint(p)
    u, v = p['u'], p['v']
    V = [np.array(c, float) for c in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    f4, f5, f6, f7, f8, f9 = u, u + d, u + d + w, u + d + w + w, u + d + w + d, u + d + w + d + w
    f10, f11, f12 = v, v + d, v + d + h
    spec = [((5, 4, 0, 1), f5, f10, f6, f11, 'top'),
            ((2, 3, 7, 6), f6, f11, f7, f10, 'bottom'),
            ((0, 4, 7, 3), f4, f11, f5, f12, 'west'),
            ((1, 0, 3, 2), f5, f11, f6, f12, 'north'),
            ((5, 1, 2, 6), f6, f11, f8, f12, 'east'),
            ((4, 5, 6, 7), f8, f11, f9, f12, 'south')]
    M = bone_world(p['bone'], pose)
    out = []
    for idx, u1, v1, u2, v2, nm in spec:
        vs = np.array([(M @ np.append(V[k], 1))[:3] for k in idx])
        uv = np.array([(u2, v1), (u1, v1), (u1, v2), (u2, v2)], float)
        out.append((vs, uv, nm))
    return out

LIGHT = {'top': 1.0, 'bottom': 0.5, 'north': 0.9, 'south': 0.9, 'west': 0.75, 'east': 0.75}

def render(view_R, scale, pose=None, size=None, center=None, texture=None, bgc=(45, 44, 43), outline=False):
    pose = pose or {}
    texture = tex if texture is None else texture
    polys = []
    for p in PARTS:
        polys += cube_polys(p, pose)
    allv = np.concatenate([(view_R @ pv.T).T for pv, _, _ in polys])
    if center is None:
        center = np.array([0.0, (allv[:, 1].min() + allv[:, 1].max()) / 2])
    W, H = size
    img = np.zeros((H, W, 3)); img[:] = bgc
    zb = np.full((H, W), np.inf)
    for pv, uv, nm in polys:
        q = (view_R @ pv.T).T
        sp = np.stack([(q[:, 0] - center[0]) * scale + W / 2, (q[:, 1] - center[1]) * scale + H / 2], 1)
        o = sp[1]; eu = sp[0] - sp[1]; ev = sp[2] - sp[1]
        det = eu[0] * ev[1] - eu[1] * ev[0]
        if abs(det) < 1e-6: continue
        x0, x1 = int(max(0, math.floor(sp[:, 0].min()))), int(min(W - 1, math.ceil(sp[:, 0].max())))
        y0, y1 = int(max(0, math.floor(sp[:, 1].min()))), int(min(H - 1, math.ceil(sp[:, 1].max())))
        if x1 < x0 or y1 < y0: continue
        YY, XX = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        px = XX + 0.5 - o[0]; py = YY + 0.5 - o[1]
        a = (px * ev[1] - py * ev[0]) / det
        b = (eu[0] * py - eu[1] * px) / det
        ins = (a >= 0) & (a < 1) & (b >= 0) & (b < 1)
        if not ins.any(): continue
        dep = q[1, 2] + a * (q[0, 2] - q[1, 2]) + b * (q[2, 2] - q[1, 2])
        U = uv[1, 0] + a * (uv[0, 0] - uv[1, 0]); Vv = uv[1, 1] + b * (uv[2, 1] - uv[1, 1])
        ui = np.clip(np.floor(U).astype(int), 0, texture.shape[1] - 1)
        vi = np.clip(np.floor(Vv).astype(int), 0, texture.shape[0] - 1)
        col = texture[vi, ui]
        ok = ins & (col[..., 3] > 0) & (dep < zb[y0:y1 + 1, x0:x1 + 1])
        n = np.cross(q[0] - q[1], q[2] - q[1]); nz = abs(n[2]) / (np.linalg.norm(n) + 1e-9)
        lf = 0.55 + 0.45 * nz if nm not in ('top', 'bottom') else (1.0 if nm == 'top' else 0.5)
        sub = img[y0:y1 + 1, x0:x1 + 1]
        sub[ok] = col[..., :3][ok] * lf
        zb[y0:y1 + 1, x0:x1 + 1][ok] = dep[ok]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), zb

R_FRONT = np.eye(3)
R_BACK = np.diag([-1.0, 1.0, -1.0])
R_SIDE = np.array([[0, 0, 1.0], [0, 1, 0], [-1.0, 0, 0]])   # left side: screen x = z
def R_yaw_pitch(yaw, pitch):
    cy, sy = math.cos(yaw), math.sin(yaw); cp, sp_ = math.cos(pitch), math.sin(pitch)
    Ry = np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
    Rp = np.array([[1, 0, 0], [0, cp, -sp_], [0, sp_, cp]])
    return Rp @ Ry

if __name__ == '__main__':
    import preview  # noqa
