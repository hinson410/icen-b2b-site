#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Refresh the <lastmod> values in sitemap.xml from real git history.

WHY THIS MATTERS
Google uses <lastmod> to decide which known URLs are worth re-crawling. A URL
whose lastmod is older than its real change date tells Google "nothing new
here", so a genuinely updated page can sit un-crawled. This script sets each
<lastmod> to the date the file was actually last committed.

Run after any content change, before committing:
    python tools/update-sitemap-lastmod.py            # dry run, shows the diff
    python tools/update-sitemap-lastmod.py --apply

Options:
    --date YYYY-MM-DD   force every entry to this date (rarely wanted)
    --check             exit 1 if anything is stale (for CI / pre-commit)
"""
import os
import re
import subprocess
import sys
from collections import defaultdict

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://icenmedical.com'
SITEMAP = os.path.join(R, 'sitemap.xml')

APPLY = '--apply' in sys.argv
CHECK = '--check' in sys.argv
FORCE = None
if '--date' in sys.argv:
    FORCE = sys.argv[sys.argv.index('--date') + 1]


def git_last_change(paths):
    """Map repo-relative path -> last commit date (YYYY-MM-DD)."""
    out = subprocess.run(
        ['git', 'log', '--since=2020-01-01', '--name-only', '--pretty=format:@@%ad',
         '--date=short', '--'] + list(paths),
        capture_output=True, text=True, cwd=R).stdout
    cur, res = None, {}
    for line in out.splitlines():
        if line.startswith('@@'):
            cur = line[2:].strip()
        elif line.strip():
            res.setdefault(line.strip().replace('\\', '/'), cur)   # newest first wins
    return res


def loc_to_path(loc):
    rel = loc.replace(SITE + '/', '')
    if rel == '' or rel.endswith('/'):
        rel = rel + 'index.html'
    return rel


def main():
    if not os.path.exists(SITEMAP):
        print(f"!! no sitemap at {SITEMAP}")
        return 1
    raw = open(SITEMAP, encoding='utf-8', newline='').read()
    entries = re.findall(r'<url>\s*<loc>(.*?)</loc>\s*<lastmod>(.*?)</lastmod>', raw)
    if not entries:
        print("!! no <loc>/<lastmod> pairs found")
        return 1

    paths = [loc_to_path(l) for l, _ in entries]
    changed = git_last_change(paths)

    stale, missing, new_raw = [], [], raw
    for loc, lm in entries:
        p = loc_to_path(loc)
        real = FORCE or changed.get(p)
        if not real:
            missing.append(p)
            continue
        if real > lm:
            stale.append((p, lm, real))
            # the file writes <loc>...</loc><lastmod>...</lastmod> with no
            # whitespace in between, so match with \s* rather than a literal newline
            pat = (r'(<loc>' + re.escape(loc) + r'</loc>\s*<lastmod>)'
                   + re.escape(lm) + r'(</lastmod>)')
            new_raw, n = re.subn(pat, lambda m: m.group(1) + real + m.group(2),
                                 new_raw, count=1)
            if n == 0:
                print(f"   !! could not rewrite lastmod for {loc}")

    print(f"sitemap entries : {len(entries)}")
    print(f"stale lastmods  : {len(stale)}")
    print(f"no git date     : {len(missing)} {missing if missing else ''}")
    print()
    for p, lm, real in stale:
        print(f"   {p:68s} {lm} -> {real}")

    if CHECK:
        return 1 if stale else 0

    if not APPLY:
        print("\n(dry run - re-run with --apply to write sitemap.xml)")
        return 0

    if stale:
        open(SITEMAP, 'w', encoding='utf-8', newline='').write(new_raw)
        print(f"\nupdated {len(stale)} lastmod value(s) in sitemap.xml")
    else:
        print("\nnothing to update")
    return 0


if __name__ == '__main__':
    sys.exit(main())
