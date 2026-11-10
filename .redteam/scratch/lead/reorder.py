from pathlib import Path
p = Path(r"D:\aitraining\.redteam\REPORT.md")
t = p.read_text(encoding="utf-8")
start = t.index("## 2. Карта багов")
end = t.index("### 1.11. Что произошло")
block = t[start:end]
rest = t[:start] + t[end:]
insert_at = rest.index("## 3. Теория")
new = rest[:insert_at] + block + rest[insert_at:]
p.write_text(new, encoding="utf-8")
print("moved", len(block), "chars")
