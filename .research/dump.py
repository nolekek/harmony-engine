import pypdf, re, pathlib
r = pypdf.PdfReader(r"D:\aitraining\.research\brigade.pdf")
out = []
for i, p in enumerate(r.pages):
    try:
        t = p.extract_text() or ""
    except Exception as e:
        t = f"[EXTRACT ERROR {e}]"
    out.append(f"\n<<<PAGE {i+1}>>>\n" + t)
txt = "".join(out)
pathlib.Path(r"D:\aitraining\.research\brigade.txt").write_text(txt, encoding="utf-8")
print("chars", len(txt))
# оглавление: первые страницы с перечнем глав
head = txt[:20000]
print(head[:6000])
