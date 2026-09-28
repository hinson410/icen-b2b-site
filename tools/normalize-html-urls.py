#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Align canonical / og:url / sitemap URLs with the URL form the host actually serves.

THE PROBLEM
The host (Cloudflare Pages pretty URLs) answers the EXTENSIONLESS form with 200
and 308-redirects the `.html` form to it:

    /products/ventilators/sv300-ventilator        -> 200
    /products/ventilators/sv300-ventilator.html   -> 308 -> the above

But every page declared `rel=canonical` (and og:url) pointing at the `.html`
form, and sitemap.xml listed the `.html` form too. So each canonical pointed at
a redirect target - a self-contradicting loop - and the sitemap fed Google 52
URLs that all redirect. Search Console reported 25 of them as
"Page with redirect" and the same page was being split across two URL forms.

WHAT THIS DOES
Rewrites canonical + og:url in every page, and the <loc> entries in sitemap.xml,
to the extensionless form - the one that returns 200.

    python tools/normalize-html-urls.py            # dry run
    python tools/normalize-html-urls.py --apply
    python tools/normalize-html-urls.py --check     # exit 1 if anything stale

It does NOT touch /index.html directory URLs (those are already correct),
does NOT add a canonical where none exists (404 / thank-you), and does NOT
rewrite internal <a href> links - those still redirect harmlessly.
"""
import os
import re
import sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://icenmedical.com'
APPLY = '--apply' in sys.argv
CHECK = '--check' in sys.argv

rd = lambda p: open(p, encoding='utf-8', newline='').read()
wr = lambda p, s: open(p, 'w', encoding='utf-8', newline='').write(s)


def strip_html(u):
    """https://site/a/b.html -> https://site/a/b   (leaves /index.html alone)"""
    if not u or not u.startswith(SITE):
        return u
    path = u[len(SITE):]
    if path.endswith('/index.html') or path in ('/index.html', ''):
        return u
    if path.endswith('.html'):
        return SITE + path[:-5]
    return u


def targets():
    for dp, dn, fn in os.walk(R):
        dn[:] = [d for d in dn if d not in ('.git', 'node_modules', 'tools',
                                           'assets', 'css', 'js', 'videos')]
        for f in fn:
            if f.endswith('.html'):
                yield os.path.join(dp, f)


# ---------- pages: rel=canonical + og:url -------------------------------------
page_changes = []
for path in targets():
    t = rd(path)
    orig = t

    def fix_tag(m):
        tag = m.group(0)
        is_canon = re.search(r'rel\s*=\s*["\']?canonical', tag, re.I)
        is_ogurl = re.search(r'property\s*=\s*["\']og:url["\']', tag, re.I)
        if not (is_canon or is_ogurl):
            return tag
        m2 = re.search(r'(href|content)\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if not m2:
            return tag
        new = strip_html(m2.group(2))
        if new == m2.group(2):
            return tag
        return tag[:m2.start(2)] + new + tag[m2.end(2):]

    t = re.sub(r'<(?:link|meta)\b[^>]*>', fix_tag, t, flags=re.I)
    if t != orig:
        page_changes.append(path)
        if APPLY:
            wr(path, t)

# ---------- sitemap ------------------------------------------------------------
sm_path = os.path.join(R, 'sitemap.xml')
sm_changes = []
if os.path.exists(sm_path):
    sm = rd(sm_path)
    locs = re.findall(r'<loc>(.*?)</loc>', sm)
    new_sm = sm
    for loc in locs:
        new = strip_html(loc)
        if new != loc:
            sm_changes.append((loc, new))
            new_sm = re.sub(r'<loc>' + re.escape(loc) + r'</loc>',
                            '<loc>' + new + '</loc>', new_sm, count=1)
    if APPLY and sm_changes:
        wr(sm_path, new_sm)

# ---------- report -------------------------------------------------------------
print(f"pages needing a canonical/og:url fix : {len(page_changes)}")
for p in page_changes:
    print("   " + os.path.relpath(p, R).replace('\\', '/'))
print()
print(f"sitemap <loc> entries to rewrite      : {len(sm_changes)}")
for a, b in sm_changes[:4]:
    print(f"   {a}\n   -> {b}")
if len(sm_changes) > 4:
    print(f"   ... and {len(sm_changes) - 4} more")

if CHECK:
    sys.exit(1 if (page_changes or sm_changes) else 0)
if not APPLY:
    print("\n(dry run - re-run with --apply to write)")
elif page_changes or sm_changes:
    print(f"\nwritten: {len(page_changes)} page(s), sitemap {len(sm_changes)} loc(s)")
