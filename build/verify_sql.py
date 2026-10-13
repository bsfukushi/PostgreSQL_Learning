#!/usr/bin/env python3
"""章の Markdown にある ```sql ブロックを実際に実行し、直後の :::result N の行数と一致するかを確かめる。
使い方: python3 build/verify_sql.py <章のMarkdown> -- <psql の接続オプション…>
学習用DBは、事前に 99_reset → 01_schema → 02_seed の順で初期化しておくこと。"""
import re, subprocess, sys
md = open(sys.argv[1], encoding="utf-8").read()
psql = sys.argv[sys.argv.index("--") + 1:]
blocks = list(re.finditer(r"```sql\n(.*?)```", md, flags=re.S))
ng = 0
for i, m in enumerate(blocks, 1):
    sql = m.group(1)
    after = md[m.end():m.end() + 400]
    exp = re.match(r"\s*:::result (\d+)", after)
    r = subprocess.run(psql + ["-X", "-A", "-t", "-c", sql], capture_output=True, text=True)
    if r.returncode != 0 or "ERROR" in r.stderr:
        ng += 1; print(f"[{i}] ERROR: {r.stderr.strip()}"); continue
    rows = [l for l in r.stdout.splitlines() if l.strip() != ""]
    if exp:
        ok = int(exp.group(1)) == len(rows)
        ng += 0 if ok else 1
        print(f"[{i}] rows={len(rows)} expected={exp.group(1)} {'OK' if ok else 'MISMATCH'}")
        for l in rows: print("     ", l)
    else:
        print(f"[{i}] rows={len(rows)} (結果表なし) {rows[:3]}")
sys.exit(1 if ng else 0)
