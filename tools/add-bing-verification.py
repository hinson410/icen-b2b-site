#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add the Bing Webmaster Tools ownership tag to every page.

The verification code is issued by Bing - it CANNOT be generated here.
Get it from: https://www.bing.com/webmasters  ->  Add site  ->  HTML Meta Tag

    # preview, change nothing
    python tools/add-bing-verification.py 1A2B3C4D5E6F...

    # write it into every page
    python tools/add-bing-verification.py 1A2B3C4D5E6F... --apply

    # remove it again
    python tools/add-bing-verification.py --remove --apply

Alternative methods Bing accepts, if you prefer not to use this script:
  * import the site from Google Search Console (no code needed at all)
  * host a BingSiteAuth.xml at the site root:  --xml --apply
  * add a CNAME record in Cloudflare DNS
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG_NAME = "msvalidate.01"
XML_FILE = "BingSiteAuth.xml"


def pages():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in (".git", "node_modules", "tools")]
        for f in fn:
            if f.endswith(".html"):
                out.append(os.path.join(dp, f))
    return sorted(out)


def read(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)


def meta_bits(code):
    return (f'<meta content="{code}" name="{TAG_NAME}"/>',
            f'<meta name="{TAG_NAME}" content="{code}"/>')


def apply_meta(code, do_write):
    tag_a, tag_b = meta_bits(code)
    added = updated = already = anchor_missing = 0
    for p in pages():
        t = read(p)
        # drop any previous tag for this property
        existing = re.findall(rf'<meta[^>]*{re.escape(TAG_NAME)}[^>]*>', t)
        if existing:
            if all(code in e for e in existing):
                already += 1
                continue
            t2 = t
            for e in existing:
                t2 = t2.replace(e, "")
            updated += 1
            t = t2
        else:
            added += 1
        m = re.search(r'<meta charset="utf-8"\s*/?>', t, re.I)
        if not m:
            anchor_missing += 1
            continue
        t = t[:m.end()] + tag_a + t[m.end():]
        if do_write:
            write(p, t)
    return added, updated, already, anchor_missing


def remove_meta(do_write):
    n = 0
    for p in pages():
        t = read(p)
        t2 = re.sub(rf'<meta[^>]*{re.escape(TAG_NAME)}[^>]*>', "", t)
        if t2 != t:
            n += 1
            if do_write:
                write(p, t2)
    return n


def apply_xml(code, do_write):
    path = os.path.join(ROOT, XML_FILE)
    body = ('<?xml version="1.0"?>\n'
            '<users>\n'
            f'  <user>{code}</user>\n'
            '</users>\n')
    if do_write:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
    return path, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code", nargs="?", help="the msvalidate.01 value from Bing")
    ap.add_argument("--apply", action="store_true", help="write the files")
    ap.add_argument("--remove", action="store_true", help="strip the tag from every page")
    ap.add_argument("--xml", action="store_true", help="write BingSiteAuth.xml instead")
    args = ap.parse_args()

    if args.remove:
        n = remove_meta(args.apply)
        print(f"pages that had the tag: {n}")
        print("APPLY =", args.apply)
        return 0

    if not args.code:
        ap.error("a verification code is required (or use --remove). "
                 "Get one from https://www.bing.com/webmasters")

    code = args.code.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", code):
        print("warning: that does not look like a Bing verification code "
              "(expected 8-128 letters/digits). Continuing anyway.")

    if args.xml:
        path, body = apply_xml(code, args.apply)
        print(body)
        print("wrote:", path, "(APPLY =", args.apply, ")")
        return 0

    added, updated, already, anchor_missing = apply_meta(code, args.apply)
    total = len(pages())
    print(f"pages scanned              : {total}")
    print(f"  tag added                : {added}")
    print(f"  tag updated (old code)   : {updated}")
    print(f"  already correct          : {already}")
    print(f"  no <meta charset> anchor : {anchor_missing}")
    print("APPLY =", args.apply)
    if not args.apply:
        print("\n(dry run - nothing written. Re-run with --apply to write.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
