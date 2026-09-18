#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Write one consistent set of social / share meta tags into every indexable page.

What it writes, per page:
  robots            index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1
  og:site_name      ICEN Medical Equipment Limited
  og:type           website (article on /resources/)
  og:url            the page's canonical
  og:title          existing hand-written og:title if present, else the <title>
  og:description    existing og:description if present, else the meta description
  og:image          1200x630 card from assets/og/
  og:image:width / :height / :alt
  twitter:card      summary_large_image     (+ twitter:title / :description / :image)

The tag order and the `content="..." property="og:x"` attribute order match the
convention already used in this project.

    python tools/add-social-meta.py            # preview
    python tools/add-social-meta.py --apply    # write

Cards are produced by tools/make-og-images.py. Run that first if a page has no card.
404.html and thank-you.html are skipped on purpose: they are noindex.
"""
import argparse
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://icenmedical.com"
BLOG = "ICEN Medical Equipment Limited"
SKIP = {"404.html", "thank-you.html"}

ROBOTS = ("index,follow,max-image-preview:large,"
          "max-snippet:-1,max-video-preview:-1")


def pages():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in (".git", "node_modules", "tools",
                                            "assets", "css", "js", "videos")]
        for f in fn:
            if f.endswith(".html"):
                rel = os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/")
                if rel not in SKIP:
                    out.append(rel)
    return sorted(out)


def read(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)


def meta(pattern, text, group=1):
    m = re.search(pattern, text, re.I | re.S)
    return html.unescape(m.group(group)) if m else None


def existing_og(text, prop):
    return meta(rf'<meta[^>]*property="{prop}"[^>]*content="([^"]*)"', text) or \
           meta(rf'<meta[^>]*content="([^"]*)"[^>]*property="{prop}"', text)


def meta_name(text, name):
    return meta(rf'<meta[^>]*name="{name}"[^>]*content="([^"]*)"', text) or \
           meta(rf'<meta[^>]*content="([^"]*)"[^>]*name="{name}"', text)


def slug_for(rel):
    return rel.replace("/", "-").replace(".html", "") or "home"


def canonical_for(rel, text):
    c = meta(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"', text) or \
        meta(r'<link[^>]*href="([^"]+)"[^>]*rel="canonical"', text)
    if c:
        return c
    if rel.endswith("/index.html"):
        return f"{SITE}/{rel[:-len('index.html')]}"
    if rel == "index.html":
        return SITE + "/"
    return f"{SITE}/{rel}"


def esc(v):
    return html.escape(v or "", quote=True)


def build_block(rel, text):
    slug = slug_for(rel)
    card = f"{SITE}/assets/og/{slug}.jpg"
    ctype = "article" if rel.startswith("resources/") else "website"

    title = (existing_og(text, "og:title")
             or meta(r"<title>(.*?)</title>", text)
             or BLOG)
    title = re.sub(r"\s+", " ", title).strip()
    desc = (existing_og(text, "og:description")
            or meta_name(text, "description")
            or "")
    desc = re.sub(r"\s+", " ", desc).strip()
    url = canonical_for(rel, text)

    alt = title
    parts = [
        f'<meta content="{esc(ROBOTS)}" name="robots"/>',
        f'<meta content="{esc(BLOG)}" property="og:site_name"/>',
        f'<meta content="{ctype}" property="og:type"/>',
        f'<meta content="{esc(url)}" property="og:url"/>',
        f'<meta content="{esc(title)}" property="og:title"/>',
    ]
    if desc:
        parts.append(f'<meta content="{esc(desc)}" property="og:description"/>')
    parts += [
        f'<meta content="{card}" property="og:image"/>',
        f'<meta content="1200" property="og:image:width"/>',
        f'<meta content="630" property="og:image:height"/>',
        f'<meta content="{esc(alt)}" property="og:image:alt"/>',
        f'<meta content="summary_large_image" name="twitter:card"/>',
        f'<meta content="{esc(title)}" name="twitter:title"/>',
    ]
    if desc:
        parts.append(f'<meta content="{esc(desc)}" name="twitter:description"/>')
    parts.append(f'<meta content="{card}" name="twitter:image"/>')
    return "".join(parts), slug, os.path.exists(
        os.path.join(ROOT, "assets", "og", slug + ".jpg"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    todo = pages()
    print(f"indexable pages: {len(todo)}\n")
    missing_cards, changed, unchanged = [], 0, 0

    for rel in todo:
        path = os.path.join(ROOT, rel)
        t = read(path)
        block, slug, has_card = build_block(rel, t)
        if not has_card:
            missing_cards.append((rel, slug))

        # drop every existing og:/twitter: tag, then insert the block once
        t2 = re.sub(r'<meta[^>]*(?:property|name)="(?:og|twitter):[^"]*"[^>]*/?>', "", t)
        m = re.search(r'<meta charset="utf-8"\s*/?>', t2, re.I)
        if not m:
            print(f"   !! no charset anchor: {rel}")
            continue
        t2 = t2[:m.end()] + block + t2[m.end():]

        if t2 == t:
            unchanged += 1
        else:
            changed += 1
            if args.apply:
                write(path, t2)

    print(f"  would change / changed : {changed}")
    print(f"  already correct        : {unchanged}")
    print(f"  pages with no card     : {len(missing_cards)}")
    for rel, slug in missing_cards:
        print(f"     !! {rel}  (expected assets/og/{slug}.jpg)")
    print("APPLY =", args.apply)
    if not args.apply:
        print("\n(dry run - nothing written. Re-run with --apply.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
