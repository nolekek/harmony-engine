import os
import re
from collections import defaultdict

modules = ["core", "rules", "solver", "syntax", "export", "ml"]
graph = defaultdict(set)

root_src = "D:/aitraining/src/harmony"
for mod in modules:
    mod_dir = os.path.join(root_src, mod)
    if not os.path.isdir(mod_dir): continue
    for f in os.listdir(mod_dir):
        if not f.endswith(".py"): continue
        with open(os.path.join(mod_dir, f), "r", encoding="utf-8") as fp:
            content = fp.read()
            for target in modules:
                if f"src.harmony.{target}" in content or f"harmony.{target}" in content:
                    if target != mod:
                        graph[mod].add(target)

print("Layer Dependency Graph (src/harmony):")
for k, v in sorted(graph.items()):
    print(f"  {k} -> {sorted(list(v))}")

# Check backend imports
backend_dir = "D:/aitraining/backend"
backend_deps = defaultdict(set)
for f in os.listdir(backend_dir):
    if not f.endswith(".py"): continue
    with open(os.path.join(backend_dir, f), "r", encoding="utf-8") as fp:
        content = fp.read()
        for target in modules:
            if f"src.harmony.{target}" in content:
                backend_deps[f].add(target)
        for b in os.listdir(backend_dir):
            if b.endswith(".py") and b != f and b[:-3] in content:
                backend_deps[f].add(f"backend.{b[:-3]}")

print("\nBackend Dependencies:")
for k, v in sorted(backend_deps.items()):
    print(f"  {k} -> {sorted(list(v))}")
