import sys, fitz, re
doc = fitz.open(sys.argv[1])
t = "\n".join(p.get_text() for p in doc)
open(sys.argv[1][:-4] + ".txt", "w", encoding="utf-8").write(t)
for pat in sys.argv[2:]:
    for m in re.finditer(pat, t):
        print(repr(t[max(0, m.start()-80): m.end()+120]))
        print("--")
