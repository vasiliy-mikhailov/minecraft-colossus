import math, os
import numpy as np
from PIL import Image, ImageDraw
from build import *  # noqa

CROPS = {'front': (10, 40, 262, 420), 'side': (262, 40, 470, 420), 'back': (505, 40, 775, 420)}
RS = {'front': R_FRONT, 'side': R_SIDE, 'back': R_BACK}

def aligned(view, Z=2, pose=None):
    a, t, b, bt = CROPS[view]
    W, H = b - a, bt - t
    v = VIEW[view]
    cx = (W / 2 - v['cx'] + a) / S
    cy = (H / 2 - v['g'] + 168 + t) / S
    im, zb = render(RS[view], S * Z, pose=pose, size=(W * Z, H * Z), center=np.array([cx, cy]) * 1.0)
    return im, zb

def sheet():
    Z = 2
    tiles = []
    for view in ('front', 'side', 'back'):
        a, t, b, bt = CROPS[view]
        ref = Image.open(os.path.join(HERE, 'ref.png')).convert('RGB').crop((a, t, b, bt)).resize(((b - a) * Z, (bt - t) * Z), Image.NEAREST)
        # aligned render needs center in model units relative to scale S*Z; recompute properly
        W, H = (b - a) * Z, (bt - t) * Z
        vv = VIEW[view]
        cx = ((b - a) / 2 - vv['cx'] + a) / S
        cy = ((bt - t) / 2 - vv['g'] + 168 + t) / S
        im, zb = render(RS[view], S * Z, size=(W, H), center=np.array([cx, cy]))
        mask = np.isfinite(zb)
        ov = np.array(ref).copy()
        edge = mask ^ np.roll(mask, 1, 0) | mask ^ np.roll(mask, 1, 1)
        ov[edge] = [255, 40, 40]
        tiles.append((view, ref, im, Image.fromarray(ov)))
    Wt = sum(r.width * 3 + 20 for _, r, _, _ in tiles)
    Ht = tiles[0][1].height + 30
    out = Image.new('RGB', (Wt, Ht), (20, 20, 24))
    d = ImageDraw.Draw(out)
    x = 0
    for view, ref, im, ov in tiles:
        for k, (lab, img) in enumerate((('ref ' + view, ref), ('model ' + view, im), ('overlay', ov))):
            out.paste(img, (x, 30)); d.text((x + 6, 8), lab, fill=(230, 200, 120)); x += img.width
        x += 20
    out.save(os.path.join(OUT, 'preview_compare.png'))
    for view, ref, im, ov in tiles:
        o = Image.new('RGB', (ref.width * 2 + 10, ref.height), (20, 20, 24)); o.paste(ref, (0, 0)); o.paste(im, (ref.width + 10, 0))
        o.save(os.path.join(OUT, 'cmp_' + view + '.png'))

def walk():
    frames = []
    for k in range(6):
        ls = k / 6 * (2 * math.pi / 0.6662)
        amt = 0.7
        c = math.cos(ls * 0.6662); c2 = math.cos(ls * 0.6662 + math.pi)
        bob = abs(c) * 1.2 * amt
        pose = {'right_leg': (0, 0, 0, c * 1.4 * amt * 0.5, 0, 0), 'left_leg': (0, 0, 0, c2 * 1.4 * amt * 0.5, 0, 0),
                'right_arm': (0, bob, 0, c2 * 0.8 * amt * 0.35, 0, 0), 'left_arm': (0, bob, 0, c * 0.8 * amt * 0.6, 0, 0),
                'body': (0, bob, 0, 0, 0, 0), 'head': (0, bob, 0, 0, 0, 0)}
        im, _ = render(R_yaw_pitch(math.radians(-50), math.radians(12)), 6, pose=pose, size=(260, 420), center=np.array([0, -2.0]))
        frames.append(im)
    out = Image.new('RGB', (260 * 6, 420))
    for k, f in enumerate(frames): out.paste(f, (260 * k, 0))
    out.save(os.path.join(OUT, 'preview_walk.png'))
    hero = []
    for yaw in (30, 150, -40):
        im, _ = render(R_yaw_pitch(math.radians(yaw), math.radians(15)), 9, size=(420, 560), center=np.array([0, -2.0]))
        hero.append(im)
    out = Image.new('RGB', (420 * 3, 560))
    for k, f in enumerate(hero): out.paste(f, (420 * k, 0))
    out.save(os.path.join(OUT, 'preview_3q.png'))
    tx = Image.open(os.path.join(OUT, 'colossus.png')).resize((TW * 4, TH * 4), Image.NEAREST)
    bgi = Image.new('RGBA', tx.size, (255, 0, 255, 255)); bgi.alpha_composite(tx); bgi.save(os.path.join(OUT, 'preview_texture.png'))

sheet()
walk()
print('ok')

def stacked():
    Z = 2
    ref = Image.open(os.path.join(HERE, 'ref.png')).convert('RGB')
    top = ref.crop((0, 40, 794, 420)).resize((794 * Z, 380 * Z), Image.NEAREST)
    bot = Image.new('RGB', top.size, (45, 44, 43))
    for view in ('front', 'side', 'back'):
        a, t, b, bt = CROPS[view]
        vv = VIEW[view]
        cx = ((b - a) / 2 - vv['cx'] + a) / S
        cy = ((bt - t) / 2 - vv['g'] + 168 + t) / S
        im, _ = render(RS[view], S * Z, size=((b - a) * Z, (bt - t) * Z), center=np.array([cx, cy]))
        bot.paste(im, (a * Z, 0))
    out = Image.new('RGB', (top.width, top.height * 2 + 4), (230, 200, 120))
    out.paste(top, (0, 0)); out.paste(bot, (0, top.height + 4))
    d = ImageDraw.Draw(out)
    d.text((10, top.height + 12), 'MODEL (box model render, same scale: 7 ref px = 1 unit)', fill=(230, 200, 120))
    out.save(os.path.join(OUT, 'preview_front_side_back.png'))

stacked()
