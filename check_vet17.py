import re, html as htm
p = "products/veterinary/index.html"
t = open(p, encoding="utf-8", newline="").read()
clean = lambda s: re.sub(r"\s+", " ", htm.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
body = re.search(r"<main>(.*?)</main>", t, re.S).group(1)
txt = clean(body)
for m in re.finditer(r"17|18", txt):
    a = max(0, m.start()-90); b = m.end()+90
    print("...", txt[a:b], "...")
    print("-")
print("HEADLINE cards:", len(re.findall(r"prod-card", t)))
