"""Pixel-art face designs for the Colossus, traced from the ortho reference.

Each design returns char grids per face (north=front, south=back, east=+x, west=-x, top, bottom),
authored for the RIGHT-side (-x) variant of paired parts; left parts are mirrored by the caller.
Legend: S stone, L light stone, K dark stone, P dark panel stone, G gold, g dark gold, H gold highlight,
C chainmail, M mossy face, D void, E eye, W leather, . transparent.
North/south/east/west grids are h rows x (w or d) cols in MC texture order:
  north col0 = -x ; south col0 = +x ; east col0 = front(-z) ; west col0 = back(+z).
"""

def grid(w, h, ch='S'):
    return [[ch] * w for _ in range(h)]

def rows(strs):
    return [list(s) for s in strs]

def fill_row(g, r, ch, c0=0, c1=None):
    c1 = len(g[0]) - 1 if c1 is None else c1
    for c in range(c0, c1 + 1): g[r][c] = ch

def fill_col(g, c, ch, r0=0, r1=None):
    r1 = len(g) - 1 if r1 is None else r1
    for r in range(r0, r1 + 1): g[r][c] = ch

def mirror(g):
    return [list(reversed(r)) for r in g]

def banded(w, h, spec):
    """spec: dict row->char (negative rows from bottom)."""
    g = grid(w, h)
    for r, ch in spec.items():
        fill_row(g, r % h, ch)
    return g

def design(name, w, h, d):
    n = name.replace('right_', '').replace('left_', '')
    F = {}
    if n == 'helm':
        F['north'] = rows(["SSSLLSSS", "SSSLLSSS", "SGGGGGGS", "SGDLLDGS", "SGELLEGS",
                           "SGGMMGGS", "SSGMMGSS", "SSGMMGSS", "KKGMMGKK"])
        e = rows(["SSSSSSSS", "SSSGGGGS", "SSSSSSGS", "DGSSSSGS", "DGSSSSGS",
                  "DGSSSSGS", "SSSSSSGS", "SSSSSSGS", "KKKKKKGK"])
        F['east'] = e; F['west'] = mirror(e)
        s = grid(w, h); fill_row(s, h - 1, 'G'); F['south'] = s
        F['top'] = grid(w, d, 'L'); F['bottom'] = grid(w, d, 'K')
    elif n.startswith('crest'):
        f = grid(w, h, 'L'); fill_col(f, 0, 'S'); fill_col(f, w - 1, 'S'); F['north'] = f
        shade_ = 'L' if int(n[5:]) % 2 else 'P'
        e = grid(d, h, shade_); fill_row(e, h - 1, 'K')
        if n == 'crest1': fill_col(e, 0, 'S'); fill_row(e, 0, 'L')
        F['east'] = e; F['west'] = mirror(e)
        s = grid(w, h); fill_row(s, 0, 'L'); F['south'] = s
        F['top'] = grid(w, d, 'L')
    elif n == 'chest':
        f = grid(w, h)
        fill_col(f, 0, 'G'); fill_col(f, w - 1, 'G')
        fill_row(f, 1, 'G', 5, 10)
        fill_col(f, 4, 'K', 1, 5); fill_col(f, 11, 'K', 1, 5)
        f[4][7] = 'H'; f[4][8] = 'G'; f[5][7] = 'G'; f[5][8] = 'g'
        fill_row(f, 7, 'G', 1, 5); fill_row(f, 7, 'G', 10, 14); fill_row(f, 6, 'G', 5, 10)
        F['north'] = f
        s = grid(w, h); fill_col(s, 0, 'G'); fill_col(s, w - 1, 'G'); fill_row(s, 0, 'G', 4, 11); fill_row(s, 7, 'G')
        F['south'] = s
        e = banded(d, h, {7: 'G'}); F['east'] = e; F['west'] = mirror(e)
        F['top'] = grid(w, d, 'L')
    elif n == 'ribs':
        f = rows(["S" * w, "K" + "S" * (w - 2) + "K", "KK" + "G" * (w - 4) + "KK"])
        F['north'] = f; F['south'] = f
        e = banded(d, h, {2: 'K'}); F['east'] = e; F['west'] = e
    elif n == 'waist':
        def stripes(n_):
            return [['K' if c % 2 == 0 else 'P' for c in range(n_)] for _ in range(h)]
        F['north'] = stripes(w); F['south'] = stripes(w); F['east'] = stripes(d); F['west'] = stripes(d)
        F['top'] = grid(w, d, 'P'); F['bottom'] = grid(w, d, 'P')
    elif n == 'belt':
        def b(n_):
            g = banded(n_, h, {0: 'G', 1: 'W', 2: 'W', 3: 'g'})
            g[1][1] = g[1][n_ - 2] = 'S'
            return g
        F['north'] = b(w); F['south'] = b(w); F['east'] = b(d); F['west'] = b(d)
        F['top'] = grid(w, d, 'W')
    elif n == 'buckle':
        F['north'] = rows(["GGGGGG", "GKGGKG", "GGGGGG"])
        F['south'] = grid(w, h, 'g'); F['east'] = grid(d, h, 'G'); F['west'] = grid(d, h, 'G')
        F['top'] = grid(w, d, 'H'); F['bottom'] = grid(w, d, 'g')
    elif n == 'tabard':
        f = rows(["GGGGGG", "GPPPPG", "GPGGPG", "GPKGPG", "GPGGPG", "GPPPPG", "GPPPPG", "GPPPPG",
                  ".GPPG.", ".GPPG.", "..GG.."])
        F['north'] = f; F['south'] = mirror(f)
        F['east'] = [['g' if r[w - 1] == 'G' else r[w - 1]] for r in f]; F['west'] = [['g' if r[0] == 'G' else r[0]] for r in f]
        F['top'] = grid(w, d, 'G'); F['bottom'] = grid(w, d, '.')
    elif n == 'back_plate':
        F['south'] = rows(["GGGGGGGGGGGGGG", "GSSSSSSSSSSSSG", "GSGGSGGGGSGGSG", "GSSSSGKKGSSSSG",
                           "GSSSSGGGGSSSSG", "GSSSSSSSSSSSSG", "GGGGGGGGGGGGGG"])
        F['north'] = grid(w, h)
        F['east'] = grid(d, h, 'G'); F['west'] = grid(d, h, 'G')
        F['top'] = grid(w, d, 'G'); F['bottom'] = grid(w, d, 'G')
    elif n == 'back_tabard':
        F['south'] = rows(["GGGGGGGG", "GSSSSSSG", "GSSSSSSG", "GGGGGGGG", "GPPPPPPG", "GPPPPPPG",
                           "GPPPPPPG", "GPPPPPPG", "GPPPPPPG", "GPGGGGPG", "GPGKKGPG", "GPGGGGPG",
                           "GPPPPPPG", "GGGGGGGG"])
        F['north'] = grid(w, h, 'P')
        F['east'] = grid(d, h, 'g'); F['west'] = grid(d, h, 'g')
        F['top'] = grid(w, d, 'G'); F['bottom'] = grid(w, d, 'g')
    elif n == 'pauldron':
        f = rows(["LLLLLL", "SSSSSS", "SSSSSS", "SSSSSS", "GSSSSS", "GGGGGG", "KSSSSK", "KSSSSK"])
        F['north'] = f; F['south'] = mirror(f)
        e = rows(["LLLLLLLLL", "SKSSSSSKS", "SKSSSSSKS", "SKSSSSSKS", "SKSSSSSKS", "SGGGGGGGS",
                  "SSSSSSSSS", "KKKKKKKKK"])
        F['east'] = e; F['west'] = mirror(e)
        F['top'] = grid(w, d, 'L'); F['bottom'] = grid(w, d, 'K')
    elif n in ('mail', 'hand'):
        for k, ww in (('north', w), ('south', w), ('east', d), ('west', d)):
            F[k] = grid(ww, h, 'C')
        F['top'] = grid(w, d, 'C'); F['bottom'] = grid(w, d, 'C')
        if n == 'hand':
            for k in ('north', 'south', 'east', 'west'):
                fill_row(F[k], h - 1, 'c')
    elif n == 'bracer':
        def b(n_):
            g = banded(n_, h, {0: 'G', 5: 'G'})
            for r in (2, 3): fill_row(g, r, 'L', 1, n_ - 2)
            return g
        F['north'] = b(w); F['south'] = b(w); F['east'] = b(d); F['west'] = b(d)
        F['top'] = grid(w, d, 'S'); F['bottom'] = grid(w, d, 'C')
    elif n == 'thigh':
        def t(n_):
            g = grid(n_, h); fill_col(g, 0, 'K'); fill_col(g, n_ - 1, 'K'); return g
        F['north'] = t(w); F['south'] = t(w); F['east'] = t(d); F['west'] = t(d)
    elif n == 'tasset':
        f = grid(w, h); fill_row(f, 0, 'L'); fill_col(f, w - 1, 'G'); fill_row(f, h - 1, 'G')
        F['north'] = f; F['south'] = mirror(f)
        e = banded(d, h, {0: 'L', h - 1: 'G'}); F['east'] = e; F['west'] = mirror(e)
        F['top'] = grid(w, d, 'L'); F['bottom'] = grid(w, d, 'K')
    elif n == 'shin':
        F['north'] = rows(["GGGGGGG", "SSSKSSS", "SSSKSSS", "SSSSSSS", "SSGGGSS", "SSGKGSS", "SSGGGSS"])
        F['south'] = banded(w, h, {0: 'G', 5: 'G'})
        e = banded(d, h, {0: 'G', 5: 'G'}); fill_col(e, 3, 'K', 1, 4); F['east'] = e; F['west'] = mirror(e)
        F['top'] = grid(w, d, 'S'); F['bottom'] = grid(w, d, 'K')
    elif n == 'boot':
        for k, ww in (('north', w), ('south', w), ('east', d), ('west', d)):
            F[k] = banded(ww, h, {0: 'K', 1: 'S', 2: 'G'})
        F['top'] = grid(w, d, 'S'); F['bottom'] = grid(w, d, 'K')
    else:
        raise KeyError(name)
    # defaults
    F.setdefault('north', grid(w, h)); F.setdefault('south', grid(w, h))
    F.setdefault('east', grid(d, h)); F.setdefault('west', grid(d, h))
    F.setdefault('top', grid(w, d, 'L')); F.setdefault('bottom', grid(w, d, 'K'))
    if name.startswith('left_'):
        F = dict(north=mirror(F['north']), south=mirror(F['south']), top=mirror(F['top']),
                 bottom=mirror(F['bottom']), east=mirror(F['west']), west=mirror(F['east']))
    for k, (ww, hh) in dict(north=(w, h), south=(w, h), east=(d, h), west=(d, h), top=(w, d), bottom=(w, d)).items():
        assert len(F[k]) == hh and all(len(r) == ww for r in F[k]), (name, k, len(F[k]), len(F[k][0]), ww, hh)
    return F
