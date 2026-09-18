#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Submit URLs to IndexNow (Bing, Yandex and other participating engines).

Run this AFTER the site is deployed. It does nothing to the site itself.

    # see what would be sent, without sending
    python tools/indexnow-submit.py --dry-run

    # submit every URL in sitemap.xml
    python tools/indexnow-submit.py

    # submit only specific URLs (the normal case once set up)
    python tools/indexnow-submit.py --url https://icenmedical.com/about.html

Rules of thumb from Microsoft:
  * submit only URLs that were added, updated or deleted
  * do NOT submit unchanged URLs again, and never submit noindex pages
  * a submission is a discovery hint, not a guarantee of indexing

Requires: the key file must already be live at https://icenmedical.com/<KEY>.txt
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

HOST = "icenmedical.com"
KEY = "dcdae902ab0cd92247669e8df6eb42a3"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
SITEMAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "sitemap.xml")

# 200 ok | 400 bad request | 403 key not valid | 422 url/host mismatch | 429 rate limited
EXPLAIN = {
    200: "OK - URLs submitted",
    202: "Accepted - key validation pending",
    400: "Bad request - invalid format",
    403: "Forbidden - key not valid (key file missing, or the file does not contain the key)",
    422: "Unprocessable - URLs do not belong to this host, or the key does not match the schema",
    429: "Too many requests - potential spam; slow down",
}


def urls_from_sitemap(path):
    with open(path, encoding="utf-8") as fh:
        return re.findall(r"<loc>(.*?)</loc>", fh.read())


def submit(urls, timeout=30):
    payload = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:                                  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", default=[],
                    help="submit this URL (repeatable). Default: every URL in sitemap.xml")
    ap.add_argument("--dry-run", action="store_true", help="print the payload, send nothing")
    ap.add_argument("--limit", type=int, default=10000, help="max URLs (IndexNow cap is 10000)")
    args = ap.parse_args()

    urls = args.url or urls_from_sitemap(SITEMAP)
    urls = urls[:args.limit]

    print(f"host         : {HOST}")
    print(f"key          : {KEY}")
    print(f"keyLocation  : {KEY_LOCATION}")
    print(f"endpoint     : {ENDPOINT}")
    print(f"urls         : {len(urls)}")
    for u in urls[:8]:
        print(f"   {u}")
    if len(urls) > 8:
        print(f"   ... +{len(urls) - 8} more")

    if args.dry_run:
        print("\n[dry-run] nothing sent.")
        return 0

    print("\nsubmitting ...")
    status, body = submit(urls)
    print(f"  HTTP {status}: {EXPLAIN.get(status, 'unexpected status')}")
    if body.strip():
        print(f"  body: {body.strip()[:500]}")
    if status == 200:
        print("\nDone. Confirm receipt under Bing Webmaster Tools -> IndexNow.")
        return 0
    if status == 403:
        print(f"\nCheck that {KEY_LOCATION} is live and its body is exactly the key.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
