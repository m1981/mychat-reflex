#!/usr/bin/env python3
# gen_diagram.py
import ast
import os
from pathlib import Path

classes = {}  # name → {bases, methods, attrs, file}

for root, _, files in os.walk("."):
    if any(p in root for p in [".venv", ".git", "__pycache__"]):
        continue
    for f in files:
        if not f.endswith(".py"):
            continue
        path = os.path.join(root, f)
        try:
            tree = ast.parse(Path(path).read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = [ast.unparse(b) for b in node.bases]
            methods, attrs = [], []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(child.name)
                elif isinstance(child, ast.Assign):
                    for t in child.targets:
                        if isinstance(t, ast.Name):
                            attrs.append(t.id)
            classes[node.name] = {
                "bases": bases,
                "methods": methods,
                "attrs": attrs,
                "file": os.path.relpath(path),
            }

# Emit dot
print("digraph Architecture {")
print("  rankdir=TB;")
print("  node [shape=record fontname=Helvetica];")
print()

for name, info in classes.items():
    methods_str = r"\l".join(
        f"+ {m}()" for m in info["methods"] if not m.startswith("__")
    )
    attrs_str = r"\l".join(f"- {a}" for a in info["attrs"])
    module = info["file"].replace("/", ".").replace(".py", "")
    label = f"{name}|{attrs_str + r'\\l' if attrs_str else ''}{methods_str + r'\\l' if methods_str else ''}"
    print(f'  {name} [label="{{{label}}}" tooltip="{module}"];')

print()
for name, info in classes.items():
    for base in info["bases"]:
        base_clean = base.split(".")[-1]  # strip module prefix
        if base_clean in classes:
            print(f"  {base_clean} -> {name} [arrowhead=onormal];")  # inheritance
print()
print("}")
