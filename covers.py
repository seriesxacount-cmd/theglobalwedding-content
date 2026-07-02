# -*- coding: utf-8 -*-
"""Брендовая обложка статьи The Global Wedding. Фон/акцент — из config.json.
Авто-режим: светлый фон → тёмный заголовок и чёрный логотип; тёмный фон → белый текст и белый логотип."""
import os
from PIL import Image, ImageDraw, ImageFont
from factory_config import CFG, HERE

ASSETS = os.path.join(HERE, "assets")
FONT_DIR = os.path.join(ASSETS, "fonts")
MARK_LIGHT = os.path.join(HERE, CFG.get("cover_mark", "assets/mark_white.png"))       # белый лого (для тёмного фона)
MARK_DARK = os.path.join(HERE, CFG.get("cover_mark_dark", "assets/mark_black.png"))    # чёрный лого (для светлого фона)
W, H, PAD = 1536, 864, 96
_c = CFG.get("colors", {})
TOP = tuple(_c.get("top", [255, 255, 255]))
BOTTOM = tuple(_c.get("bottom", [244, 244, 244]))
ACCENT = tuple(_c.get("accent", [190, 150, 78]))
BRAND = CFG.get("brand_display", "БРЕНД")
BRAND_LINE = CFG.get("brand_line", "")

# яркость фона → выбор цвета текста и логотипа
_lum = (0.299*TOP[0] + 0.587*TOP[1] + 0.114*TOP[2] + 0.299*BOTTOM[0] + 0.587*BOTTOM[1] + 0.114*BOTTOM[2]) / 2
LIGHT_BG = _lum > 140
TEXT = (26, 26, 26) if LIGHT_BG else (245, 245, 245)
MARK = MARK_DARK if LIGHT_BG else MARK_LIGHT

def font(sz, bold=True):
    fn = "Font-Bold.ttf" if bold else "Font-Regular.ttf"
    cands = [os.path.join(FONT_DIR, fn)]
    if bold:
        cands += [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    else:
        cands += [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in cands:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

def _grad():
    g = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / H
        g.putpixel((0, y), tuple(int(TOP[i]*(1-t)+BOTTOM[i]*t) for i in range(3)))
    return g.resize((W, H)).convert("RGBA")

def _wrap(d, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur+" "+w).strip()
        if d.textlength(test, font=fnt) <= maxw:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def render_cover(title, out):
    img = _grad()
    d = ImageDraw.Draw(img)
    # заголовок — подбираем размер, чтобы влез в 4 строки
    fsz = 84
    while fsz > 44:
        fnt = font(fsz); lines = _wrap(d, title, fnt, W-2*PAD)
        if len(lines) <= 4: break
        fsz -= 6
    lh = int(fsz*1.2); block = lh*len(lines)
    y = (H-block)//2 - 60
    # золотая полоска-акцент над заголовком
    d.rectangle((PAD, y-42, PAD+96, y-32), fill=ACCENT)
    for ln in lines:
        d.text((PAD, y), ln, font=fnt, fill=TEXT); y += lh
    # нижний бренд-блок: логотип-леттеринг слева
    mh = 66; ly = H-mh-58
    if os.path.exists(MARK):
        m = Image.open(MARK).convert("RGBA")
        mw = int(m.width*mh/m.height); m = m.resize((mw, mh))
        img.alpha_composite(m, (PAD, ly))
    else:
        d.text((PAD, ly+4), BRAND, font=font(54), fill=TEXT)
    # подпись справа — золотым
    if BRAND_LINE:
        blf = font(28, bold=False); blw = d.textlength(BRAND_LINE, font=blf)
        d.text((W-PAD-blw, ly+20), BRAND_LINE, font=blf, fill=ACCENT)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.convert("RGB").save(out, "PNG")