import pypdf, collections
r = pypdf.PdfReader(r"D:\aitraining\.research\brigade.pdf")
c = collections.Counter()
imgs = 0
for i,p in enumerate(r.pages):
    try: xo = p.get("/XObject")
    except Exception: xo = None
    if xo is not None:
        try:
            for k,v in xo.items():
                o = v.get_object()
                c[o.get("/Subtype")] += 1
                if o.get("/Subtype")=="/Image": imgs += 1
        except Exception as e:
            c[("err",str(e)[:30])] += 1
print("xobject subtypes:", dict(c))
print("total images:", imgs)
# размеры страниц и есть ли текст вообще на большинстве страниц
nonempty = sum(1 for p in r.pages if (p.extract_text() or "").strip())
print("pages with text:", nonempty, "of", len(r.pages))
