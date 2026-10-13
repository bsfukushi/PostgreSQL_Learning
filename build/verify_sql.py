#!/usr/bin/env python3
"""章の Markdown にある ```sql ブロックを実際に実行し、直後の :::result N の行数と一致するかを確かめる。
使い方: python3 build/verify_sql.py <章のMarkdown> -- <psql の接続オプション…>
```sql show は実行しない。直後が :::result error のブロックは、エラーになれば OK。
学習用DBは、事前に 99_reset → 01_schema → 02_seed の順で初期化しておくこと。"""
import re, subprocess, sys
md = open(sys.argv[1], encoding="utf-8").read()
psql = sys.argv[sys.argv.index("--") + 1:]
blocks = [m for m in re.finditer(r"```sql([^\n]*)\n(.*?)```", md, flags=re.S)
          if "show" not in m.group(1).split()]  # ```sql copy=6 は対象、```sql show は表示だけなので対象外
ng = 0
for i, m in enumerate(blocks, 1):
    sql = m.group(2)
    after = md[m.end():m.end() + 400]
    exp = re.match(r"\s*:::result (\d+)", after)
    r = subprocess.run(psql + ["-X", "-A", "-t", "-c", sql], capture_output=True, text=True)
    failed = r.returncode != 0 or "ERROR" in r.stderr
    if re.match(r"\s*:::result error", after):  # エラーになるのが正しい例
        ng += 0 if failed else 1
        print(f"[{i}] expected=error {'OK' if failed else 'MISMATCH（エラーにならなかった）'}: {r.stderr.strip()[:200]}")
        continue
    if failed:
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
