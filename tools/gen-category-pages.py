# -*- coding: utf-8 -*-
"""Build the 10 category landing pages from products.html.

SOURCE OF TRUTH: the product cards in products.html. Add a product card there,
then re-run this script, and the per-category model counts, the ItemList schema
and the FAQ answers all update together. Do NOT hand-edit the counts on the
category pages - they are derived from products.html and would drift.

Run from anywhere:  python tools/gen-category-pages.py

Design:
 - Shell (header / footer / whatsapp float / scripts) reused verbatim from an existing page
 - Product cards reused VERBATIM from products.html (only relative -> root-absolute URLs)
 - Only existing CSS classes are used; no new CSS
 - JSON-LD: Organization + BreadcrumbList + ItemList + FAQPage (real characters, no entities)
"""
import os, re, json, html, shutil

# repo root = the parent of tools/
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = "\r\n"

def load(p):
    return open(p, encoding="utf-8", newline="").read()

def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()

def txt(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def jdump(o):
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

# ---------- shell source ----------
SHELL_SRC = "products/anesthesia/a5-anesthesia-system.html"
shell = load(os.path.join(R, SHELL_SRC))
HEADER = re.search(r"<header.*?</header>", shell, re.S).group(0)
FOOTER = re.search(r"<footer.*?</footer>", shell, re.S).group(0)
TAIL = shell[shell.find("</footer>") + len("</footer>"):]          # scripts + whatsapp float
ORG_LD = re.search(r'<script type="application/ld\+json">(\{"@context":"https://schema\.org","@type":"Organization".*?\})</script>',
                   shell, re.S).group(1)

idx = load(os.path.join(R, "index.html"))
CTA = re.search(r'<section class="cta-band">.*?</section>', idx, re.S).group(0)

# ---------- categories ----------
ph = load(os.path.join(R, "products.html"))
CATS = [
    # id, slug, display name, title(<=60), meta description(<=160)
    ("ultrasound", "ultrasound", "Ultrasound Imaging",
     "Ultrasound Imaging Systems | Mindray Ultrasound | ICEN",
     "Mindray diagnostic ultrasound systems for general imaging, obstetrics, cardiology and point-of-care use. ICEN supplies hospitals, clinics and distributors."),
    ("veterinary", "veterinary", "Veterinary Diagnostics",
     "Veterinary Ultrasound & Lab Equipment | ICEN Medical",
     "Mindray and Edan veterinary ultrasound, hematology, chemistry and blood gas systems for companion animal and mixed veterinary practices."),
    ("hematology", "hematology-laboratory", "Hematology &amp; Laboratory",
     "Hematology Analyzers | Mindray CBC Analyzers | ICEN",
     "Mindray automated hematology analyzers for routine CBC, 5-part differential and CRP testing, for laboratories of every size."),
    ("icu-ventilation", "ventilators", "ICU &amp; Ventilation",
     "ICU Ventilators | Mindray SV &amp; TV Series | ICEN",
     "Mindray ICU, non-invasive and transport ventilators for intensive care, emergency and respiratory care departments."),
    ("patient-monitors", "patient-monitors", "Patient Monitors",
     "Patient Monitors | Mindray BeneVision &amp; ePM | ICEN",
     "Mindray bedside and transport patient monitors from the BeneVision, ePM, VS and uMEC families for continuous multiparameter monitoring."),
    ("monitoring", "monitoring", "Patient Monitoring &amp; Cardiac Care",
     "ECG &amp; Defibrillators | Mindray BeneHeart | ICEN",
     "Mindray ECG, vital signs and cardiac emergency devices supporting clinicians from the bedside to the emergency scene."),
    ("anesthesia", "anesthesia", "Anesthesia Systems",
     "Anesthesia Systems | Mindray A-Series &amp; WATO | ICEN",
     "Mindray anesthesia systems for precise, safer inhaled anesthesia in modern operating rooms, from the WATO EX-35 to the A9."),
    ("clinical-lab", "clinical-laboratory", "Clinical Chemistry &amp; Laboratory",
     "Clinical Chemistry Analyzers | Mindray BS Series | ICEN",
     "Mindray chemistry analyzers, coagulation and immunoassay systems, plus cellular analysis lines for clinical laboratories."),
    ("radiology", "radiology", "Digital Radiography (DR)",
     "Digital Radiography Systems | Mindray DR | ICEN",
     "Mindray fixed, ceiling-mounted and mobile digital radiography systems for sharp imaging at lower dose."),
    ("infusion", "infusion", "Infusion Systems",
     "Infusion &amp; Syringe Pumps | Mindray BeneFusion | ICEN",
     "Mindray BeneFusion infusion pumps, syringe pumps and infusion supervision systems for accurate fluid and drug delivery."),
]

def cat_block(cid):
    m = re.search(r'<div class="cat-block" id="' + re.escape(cid) + r'">(.*?)(?=<div class="cat-block"|</main>)', ph, re.S)
    assert m, "category block not found: " + cid
    return m.group(1)

def rewrite_urls(s):
    """relative -> root-absolute, so the page works from /products/<slug>/"""
    def fix(m):
        attr, val = m.group(1), m.group(2)
        if re.match(r"^(?:https?:|mailto:|tel:|#|/)", val):
            return m.group(0)
        return '%s="/%s"' % (attr, val)
    return re.sub(r'\b(src|href)="([^"]*)"', fix, s)

print("=" * 78)
print("BUILDING 10 CATEGORY PAGES")
print("=" * 78)
built = []
for cid, slug, name, title, desc in CATS:
    blk = cat_block(cid)
    cards = re.findall(r'<article class="prod-card[^"]*">.*?</article>', blk, re.S)
    names = [txt(x) for x in re.findall(r"<h3>(.*?)</h3>", blk, re.S)]
    catdesc = txt(re.search(r'<p class="cat-desc">(.*?)</p>', blk, re.S).group(1))
    n = len(cards)
    assert n == len(names) and n > 0, "%s: %d cards / %d names" % (cid, n, len(names))

    # intro copy - built only from text already on the site
    p1 = catdesc
    p2 = ("ICEN lists %d models in this category, including %s, %s and %s. ICEN provides sourcing and "
          "project support for distributors, hospitals and healthcare programs, and can confirm "
          "configuration, documentation and destination-market requirements before quotation."
          % (n, names[0], names[1] if n > 1 else names[0], names[2] if n > 2 else names[-1]))

    faq = [
        ("Which %s models can ICEN supply?" % txt(name),
         "ICEN currently lists %d models in this category: %s." % (n, "; ".join(names) + ".")),
        ("Can ICEN provide a quotation for %s?" % txt(name),
         "Yes. Use the Request a Quote button to send the product model, quantity, target market and "
         "requirements to our export team."),
        ("Can you support international shipment?",
         "ICEN provides export coordination and can discuss shipping arrangements, documentation and "
         "delivery terms for your project."),
        ("Is availability the same in every country?",
         "No. Product availability, configuration, registration and market authorization can vary by "
         "country. Confirm the applicable market requirements with ICEN before purchase."),
    ]

    # ---- JSON-LD ----
    BASE = "https://icenmedical.com/products/%s/" % slug
    bl = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://icenmedical.com/"},
        {"@type": "ListItem", "position": 2, "name": "Products", "item": "https://icenmedical.com/products.html"},
        {"@type": "ListItem", "position": 3, "name": html.unescape(txt(name)), "item": BASE}]}
    il = {"@context": "https://schema.org", "@type": "ItemList", "name": html.unescape(txt(name)),
          "numberOfItems": n, "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "name": nm, "url": BASE + h}
              for i, (nm, h) in enumerate([
                  (names[j], re.search(r'href="products/[^"]*?/([^"/]+\.html)"', cards[j]).group(1)
                   if re.search(r'href="products/[^"]*?/([^"/]+\.html)"', cards[j]) else "")
                  for j in range(n)])]}
    fq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

    OG_IMG = "https://icenmedical.com/assets/og/products-" + slug + "-index.jpg"
    head = (
        "<!DOCTYPE html>" + NL + '<html lang="en"><head>' + NL +
        '<!-- Google tag (gtag.js) -->' + NL +
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-40F0LVQR2G"></script>' + NL +
        "<script>" + NL + "  window.dataLayer = window.dataLayer || [];" + NL +
        "  function gtag(){dataLayer.push(arguments);}" + NL +
        "  gtag('js', new Date());" + NL + NL + "  gtag('config', 'G-40F0LVQR2G');" + NL + "</script>" + NL +
        '<meta charset="utf-8"/><meta content="width=device-width, initial-scale=1" name="viewport"/>'
        "<title>" + title + "</title>"
        '<meta content="' + desc + '" name="description"/>'
        '<link href="/assets/icen-logo.png" rel="icon" type="image/png"/>'
        '<link href="https://fonts.googleapis.com" rel="preconnect"/>'
        '<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;display=swap" rel="stylesheet"/>'
        '<link href="/css/style.css" rel="stylesheet"/>'
        '<link href="/css/seo.css" rel="stylesheet"/>'
        '<link href="' + BASE + '" rel="canonical"/>'
        '<meta content="index,follow,max-image-preview:large,max-snippet:-1,'
        'max-video-preview:-1" name="robots"/>'
        '<meta content="ICEN Medical Equipment Limited" property="og:site_name"/>'
        '<meta content="website" property="og:type"/>'
        '<meta content="' + BASE + '" property="og:url"/>'
        '<meta content="' + title.replace('&amp;', '&') + '" property="og:title"/>'
        '<meta content="' + desc + '" property="og:description"/>'
        '<meta content="' + OG_IMG + '" property="og:image"/>'
        '<meta content="1200" property="og:image:width"/>'
        '<meta content="630" property="og:image:height"/>'
        '<meta content="' + title.replace('&amp;', '&') + '" property="og:image:alt"/>'
        '<meta content="summary_large_image" name="twitter:card"/>'
        '<meta content="' + title.replace('&amp;', '&') + '" name="twitter:title"/>'
        '<meta content="' + desc + '" name="twitter:description"/>'
        '<meta content="' + OG_IMG + '" name="twitter:image"/>' + NL +
        '<script type="application/ld+json">' + ORG_LD + "</script>" + NL +
        '<script type="application/ld+json">' + jdump(bl) + "</script>" + NL +
        '<script type="application/ld+json">' + jdump(il) + "</script>" + NL +
        '<script type="application/ld+json">' + jdump(fq) + "</script>" + NL +
        "</head>" + NL)

    grid_cards = (NL + NL).join(rewrite_urls(c) for c in cards)
    faq_html = (NL).join(
        "<details><summary>" + q + "</summary><p>" + a + "</p></details>" for q, a in faq)

    siblings = [(s2, n2) for (i2, s2, n2, t2, d2) in CATS if s2 != slug][:4]
    rel = "".join('<a href="/products/%s/">%s</a>' % (s2, n2) for s2, n2 in siblings)

    main = (
        "<main>" + NL +
        '<section class="page-hero">' + NL + '<div class="container">' + NL +
        "<h1>" + name + "</h1>" + NL + "<p>" + p1 + "</p>" + NL +
        '<nav aria-label="Breadcrumb" class="crumb"><a href="/">Home</a><span>/</span>'
        '<a href="/products.html">Products</a><span>/</span>' + name + "</nav>" + NL +
        "</div>" + NL + "</section>" + NL + NL +
        '<section class="section soft">' + NL + '<div class="container narrow-content">' + NL +
        '<span class="eyebrow">Category Overview</span>' + NL +
        "<h2>" + name + " supplied by ICEN</h2>" + NL +
        "<p>" + p1 + "</p>" + NL + "<p>" + p2 + "</p>" + NL +
        "</div>" + NL + "</section>" + NL + NL +
        '<section class="section">' + NL + '<div class="container">' + NL +
        '<div class="section-title"><span class="eyebrow">Products</span>' + NL +
        "<h2>" + name + " available from ICEN</h2>" + NL +
        "<p>" + str(n) + " models currently listed in this category. Contact our team for configuration, "
        "documentation and pricing.</p></div>" + NL +
        '<div class="prod-grid prod-grid-3">' + NL + grid_cards + NL + "</div>" + NL +
        "</div>" + NL + "</section>" + NL + NL +
        '<section class="section soft">' + NL + '<div class="container faq-wrap">' + NL +
        '<div class="section-title"><span class="eyebrow">FAQ</span>' + NL +
        "<h2>" + name + " - common questions</h2></div>" + NL +
        '<div class="faq-grid">' + NL + faq_html + NL + "</div>" + NL +
        "</div>" + NL + "</section>" + NL + NL +
        '<section class="section">' + NL + '<div class="container narrow-content">' + NL +
        '<span class="eyebrow">Related</span>' + NL +
        "<h2>Related categories and solutions</h2>" + NL +
        '<div class="seo-links"><a href="/products.html">All Products</a>' + rel +
        '<a href="/solutions/hospital-setup.html">Hospital Setup</a>'
        '<a href="/solutions/icu-critical-care.html">ICU &amp; Critical Care</a>'
        '<a href="/resources.html">Buying Guides</a></div>' + NL +
        "</div>" + NL + "</section>" + NL + NL + CTA + NL + "</main>")

    out = head + HEADER + NL + main + NL + FOOTER + TAIL
    dest_dir = os.path.join(R, "products", slug)
    os.makedirs(dest_dir, exist_ok=True)
    open(os.path.join(dest_dir, "index.html"), "w", encoding="utf-8", newline="").write(out)
    built.append((slug, name, n, len(title), len(desc)))
    print("   %-24s %-38s cards=%-3d title=%-3d desc=%d" % (slug, txt(name)[:36], n, len(title), len(desc)))

print("\nbuilt:", len(built))
print("title lengths <=60:", all(t <= 60 for _, _, _, t, _ in built))
print("\nslug map:")
print(json.dumps([{"id": c[0], "slug": c[1], "name": html.unescape(txt(c[2]))}
                  for c in CATS], ensure_ascii=False, indent=1))

