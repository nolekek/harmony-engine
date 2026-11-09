import pymupdf, pathlib
doc = pymupdf.open(r"D:\aitraining\.research\brigade.pdf")
outdir = pathlib.Path(r"D:\aitraining\.research\pages"); outdir.mkdir(exist_ok=True)
for n in (5, 6, 60, 61):
    pix = doc[n-1].get_pixmap(dpi=170)
    p = outdir / f"p{n:03d}.png"; pix.save(p)
    print(p, pix.width, pix.height, pix.n)
