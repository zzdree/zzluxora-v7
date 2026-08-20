"""Phase 18 verification: AST check all .py with BOM-safe encoding."""
import ast
import pathlib
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
files = [p for p in root.rglob("*.py") if "__pycache__" not in str(p)]
ok = 0
bad = []
for p in files:
    try:
        # utf-8-sig strips BOM if present, falls back to plain utf-8
        ast.parse(p.read_text(encoding="utf-8-sig"))
        ok += 1
    except SyntaxError as e:
        bad.append((p, str(e)))

print(f"AST: {ok}/{len(files)} files OK")
if bad:
    for p, e in bad:
        print(f"  FAIL: {p}: {e}")
    sys.exit(1)
print("PASS: all Python files parse cleanly")
