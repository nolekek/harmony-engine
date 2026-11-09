import pypdf, re
r = pypdf.PdfReader(r"D:\aitraining\.research\brigade.pdf")
for idx in (3, 60, 200):
    p = r.pages[idx]
    print("="*20, "page", idx+1)
    data = p.get_contents().get_data()
    print("len", len(data))
    s = data.decode("latin-1", "replace")
    print(s[:700].replace("\n"," | ")[:700])
    print("--- ops histogram:")
    toks = re.findall(r"/[A-Za-z][A-Za-z0-9]*|\bTj\b|\bTJ\b|\bDo\b|\bf\b|\bg\b|\bm\b", s)
    from collections import Counter
    print(Counter(toks).most_common(15))
