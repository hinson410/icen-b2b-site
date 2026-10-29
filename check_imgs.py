import glob, os
pats = ["n22", "pm60", "pm-60", "nb350", "bc20s", "bc-20s", "bc30s", "bc-30s", "mr96", "mr-96", "veled", "vetina"]
files = [os.path.basename(p) for p in glob.glob("assets/img/*")]
print("assets/img total:", len(files))
for pat in pats:
    hits = [f for f in files if pat in f.lower()]
    print(f"  {pat:8s} -> {hits if hits else 'NONE'}")
