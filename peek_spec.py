import re
t = open("products/veterinary/vetus-8-veterinary-ultrasound-system.html", encoding="utf-8", newline="").read()
m = re.search(r'<table class="spec-table">(.{0,700})', t, re.S)
print("table found:", bool(m))
print(m.group(1) if m else "NO MATCH")
