#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the 1200x630 Open Graph share cards into assets/og/.

Deterministic composition from the site's own material: the real logo, the real
product photograph, the page's real title and the real domain. Nothing is invented.

    python tools/make-og-images.py                  # regenerate every card
    python tools/make-og-images.py index.html about.html   # only these pages

Then run:  python tools/add-social-meta.py --apply

IMPORTANT - source images
    Only clean studio product photographs are used. The company photographs
    (company-video-poster.jpg, office-factory.jpg, customer-visits-2025-poster.jpg)
    all show "ICEN Technology ..." signage, so they are deliberately never used on
    a share card, which is the most visible surface the site has.

Requires Pillow. Fonts come from the Windows font directory (Segoe UI, which is the
second entry in the site's own font stack).
"""
import os
import re
import sys
import html as htm          # NOT "as H" - H is the canvas height constant below
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, 'assets', 'og')
os.chdir(ROOT)
os.makedirs(DEST, exist_ok=True)

W, H = 1200, 630
NAVY = (16, 42, 86)
NAVY2 = (11, 31, 66)
CYAN = (31, 182, 228)
WHITE = (255, 255, 255)
MUTED = (168, 190, 218)
PANEL = (255, 255, 255)

FONT_DIR = os.environ.get('WINDIR', r'C:\Windows') + r'\Fonts'
F_REG = os.path.join(FONT_DIR, 'segoeui.ttf')
F_SB = os.path.join(FONT_DIR, 'seguisb.ttf')
F_BOLD = os.path.join(FONT_DIR, 'segoeuib.ttf')

SKIP = {'404.html', 'thank-you.html'}

CATEGORY = {
    'ultrasound': 'Ultrasound Imaging',
    'veterinary': 'Veterinary Equipment',
    'patient-monitors': 'Patient Monitoring',
    'ventilators': 'ICU & Ventilation',
    'anesthesia': 'Anesthesia',
    'clinical-laboratory': 'Clinical Laboratory',
    'hematology-laboratory': 'Hematology',
    'radiology': 'Radiology',
    'infusion': 'Infusion Therapy',
    'monitoring': 'Cardiac Care',
}

# pages with no product image of their own, or whose natural image is unsuitable
SRC_OVERRIDE = {
    'index.html': 'assets/img/mindray-resonai8.jpg',
    'about.html': 'assets/img/mindray-resonai8.jpg',
    'oem-odm.html': 'assets/img/mindray-sv800.webp',
    'quality-compliance.html': 'assets/img/mindray-bc6800.jpg',
    'contact.html': 'assets/img/mindray-a8.jpg',
    'resources.html': 'assets/img/mindray-resonai8.jpg',
    'video-center.html': 'assets/img/mindray-a9.jpg',
    'resources/how-to-choose-ultrasound-system.html': 'assets/img/mindray-resonai8.jpg',
    'resources/how-to-choose-patient-monitor.html': 'assets/img/mindray-n12.jpg',
    'resources/how-to-choose-hematology-analyzer.html': 'assets/img/mindray-bc6800.jpg',
    'resources/how-to-choose-5-part-hematology-analyzer.html': 'assets/img/mindray-bc7600.jpg',
    'resources/benevision-n1-vs-n12-vs-n17.html': 'assets/img/mindray-n12.jpg',
    'resources/how-to-buy-medical-equipment-from-china.html': 'assets/img/mindray-dc80.jpg',
    'resources/hospital-equipment-checklist.html': 'assets/img/mindray-epm12.jpg',
    'solutions/icu-critical-care.html': 'assets/img/mindray-sv800.webp',
    'solutions/diagnostic-imaging.html': 'assets/img/mindray-resonai8.jpg',
    'solutions/clinical-laboratory.html': 'assets/img/mindray-bc6800.jpg',
    'solutions/operating-room.html': 'assets/img/mindray-a9.jpg',
    'solutions/hospital-setup.html': 'assets/img/mindray-digieye680.jpg',
}
TITLE_OVERRIDE = {
    'index.html': 'ICEN Medical Equipment',
    'resources.html': 'Medical Equipment Buying Guides',
    'video-center.html': 'ICEN Video Centre',
}


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', htm.unescape(s)).strip()


def meta_one(text, prop):
    m = (re.search(rf'<meta[^>]*property="{prop}"[^>]*content="([^"]*)"', text, re.S)
         or re.search(rf'<meta[^>]*content="([^"]*)"[^>]*property="{prop}"', text, re.S))
    return htm.unescape(m.group(1)) if m else None


def meta_name(text, name):
    m = (re.search(rf'<meta[^>]*name="{name}"[^>]*content="([^"]*)"', text, re.S)
         or re.search(rf'<meta[^>]*content="([^"]*)"[^>]*name="{name}"', text, re.S))
    return htm.unescape(m.group(1)) if m else None


def eyebrow_for(rel):
    if rel.startswith('products/') and rel.endswith('/index.html'):
        return CATEGORY.get(rel.split('/')[1], 'Product category')
    if rel.startswith('products/'):
        return CATEGORY.get(rel.split('/')[1], 'Product')
    if rel.startswith('resources/'):
        return 'Buying guide'
    if rel.startswith('solutions/'):
        return 'Solution'
    return {
        'index.html': 'One-stop medical equipment',
        'products.html': 'Product catalogue',
        'about.html': 'About ICEN',
        'contact.html': 'Contact',
        'resources.html': 'Resources',
        'video-center.html': 'Video centre',
        'oem-odm.html': 'OEM / ODM',
        'quality-compliance.html': 'Quality & compliance',
    }.get(rel, 'ICEN Medical Equipment')


def card_title(rel, text):
    if rel in TITLE_OVERRIDE:
        return TITLE_OVERRIDE[rel]
    base = (meta_one(text, 'og:title')
            or strip_tags(re.search(r'<h1[^>]*>(.*?)</h1>', text, re.S).group(1)
                          if re.search(r'<h1[^>]*>(.*?)</h1>', text, re.S) else '')
            or strip_tags(re.search(r'<title>(.*?)</title>', text, re.S).group(1)
                          if re.search(r'<title>(.*?)</title>', text, re.S) else '')
            or 'ICEN Medical Equipment')
    for sep in (' | ', ' — ', ' – ', ' - '):
        parts = base.split(sep)
        while len(parts) > 1 and re.search(r'ICEN|Medical Equipment', parts[-1], re.I):
            parts.pop()
        base = sep.join(parts)
    return re.sub(r'\s+', ' ', base).strip(' -|—–') or 'ICEN Medical Equipment'


def source_image(rel, text):
    p = SRC_OVERRIDE.get(rel)
    if not p:
        imgs = [c for c in re.findall(r'<img[^>]*src="([^"]+)"', text)
                if c.startswith(('assets/', '/assets/'))
                and '/img/' in c and 'logo' not in c.lower()]
        p = imgs[0].lstrip('/') if imgs else None
    if not p:
        return None
    p = p.lstrip('/')
    if os.path.exists(p):
        return p
    base = os.path.splitext(p)[0]
    for alt in ('.jpg', '.webp', '.png'):
        if os.path.exists(base + alt):
            return base + alt
    return None


def gradient_bg():
    base = Image.new('RGB', (W, H), NAVY2)
    px = base.load()
    for y in range(H):
        for x in range(0, W, 2):
            t = (x / W * 0.45) + (y / H * 0.55)
            c = (int(NAVY2[0] + (NAVY[0] - NAVY2[0]) * t),
                 int(NAVY2[1] + (NAVY[1] - NAVY2[1]) * t),
                 int(NAVY2[2] + (NAVY[2] - NAVY2[2]) * t))
            px[x, y] = c
            if x + 1 < W:
                px[x + 1, y] = c
    glow = Image.new('RGB', (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse([W - 620, -320, W + 260, 420], fill=(10, 60, 90))
    return Image.blend(base, glow.filter(ImageFilter.GaussianBlur(110)), 0.30)


def fit_cover(im, bw, bh):
    sw, sh = im.size
    s = max(bw / sw, bh / sh)
    im = im.resize((max(1, int(sw * s + .5)), max(1, int(sh * s + .5))), Image.LANCZOS)
    nw, nh = im.size
    return im.crop(((nw - bw) // 2, (nh - bh) // 2,
                    (nw - bw) // 2 + bw, (nh - bh) // 2 + bh))


def wrap(draw, text, font, max_w):
    lines, cur = [], ''
    for w in text.split():
        trial = (cur + ' ' + w).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_spaced(draw, xy, text, font, fill, sp=3):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + sp


def build(rel, text):
    title = card_title(rel, text)
    eyebrow = eyebrow_for(rel).upper()
    src = source_image(rel, text)
    slug = rel.replace('/', '-').replace('.html', '') or 'home'

    img = gradient_bg()
    d = ImageDraw.Draw(img)
    pad = 64

    try:
        logo = Image.open('assets/icen-logo.png').convert('RGBA')
        logo.thumbnail((46, 46), Image.LANCZOS)
        img.paste(logo, (pad, pad - 6), logo)
    except Exception:
        pass
    d.text((pad + 58, pad + 6), 'ICEN MEDICAL EQUIPMENT',
           font=ImageFont.truetype(F_BOLD, 21), fill=WHITE)

    pw, ph = 430, 420
    px0, py0 = W - pad - pw, (H - ph) // 2 - 10
    text_max_w = px0 - pad - 56

    if src:
        try:
            base = Image.open(src).convert('RGB')
            card = Image.new('RGB', (pw, ph), PANEL)
            card.paste(fit_cover(base, pw - 44, ph - 44), (22, 22))
            mask = Image.new('L', (pw, ph), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1],
                                                   radius=22, fill=255)
            img.paste(card, (px0, py0), mask)
        except Exception as e:                                   # noqa: BLE001
            print(f"   ! image failed for {rel}: {e}")

    ey = py0 + 26
    if eyebrow:
        draw_spaced(d, (pad, ey), eyebrow[:42], ImageFont.truetype(F_SB, 20), CYAN)
        d.rectangle([pad, ey + 34, pad + 52, ey + 37], fill=CYAN)
        ty = ey + 58
    else:
        ty = ey

    size = 54
    while size >= 32:
        f_title = ImageFont.truetype(F_BOLD, size)
        lines = wrap(d, title, f_title, text_max_w)
        if len(lines) <= 3:
            break
        size -= 3
    for i, ln in enumerate(lines[:3]):
        d.text((pad, ty + i * int(size * 1.22)), ln, font=f_title, fill=WHITE)
    d.text((pad, H - pad - 26), 'icenmedical.com',
           font=ImageFont.truetype(F_REG, 22), fill=MUTED)

    out = os.path.join(DEST, slug + '.jpg')
    img.save(out, 'JPEG', quality=86, optimize=True, progressive=True)
    return out, slug, title, src


def main():
    only = set(sys.argv[1:])
    pages = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in ('.git', 'node_modules', 'tools',
                                            'assets', 'css', 'js', 'videos')]
        for f in fn:
            if f.endswith('.html'):
                rel = os.path.relpath(os.path.join(dp, f), ROOT).replace('\\', '/')
                if rel not in SKIP and (not only or rel in only):
                    pages.append(rel)
    pages.sort()
    print(f"generating {len(pages)} card(s)\n")
    total = 0
    warn = []
    for rel in pages:
        out, slug, title, src = build(rel, open(rel, encoding='utf-8', newline='').read())
        sz = os.path.getsize(out)
        total += sz
        if src and src.startswith(('assets/company/', 'assets/og/')):
            warn.append((rel, src))
        print(f"  {slug:50s} {sz/1024:6.1f} KB  {(src or '(none)')[:28]:28s} {title[:36]}")
    print(f"\n{len(pages)} cards, {total/1024/1024:.2f} MB")
    print(f"cards using a company photograph (must be 0): {len(warn)}")
    for rel, src in warn:
        print("   !!", rel, "->", src)
    return 0


if __name__ == '__main__':
    sys.exit(main())
