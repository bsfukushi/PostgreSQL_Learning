---
name: psql-null-only-row-blank
description: psql -A -t の出力で NULL だけの行は空行になり、空行を捨てて数えると行数がずれる。-P null=(null) で回避
type: troubleshoot
tags: [postgresql, psql, null, verify, silent-failure, row-count]
---

## 症状
`psql -X -A -t -c "SELECT DISTINCT source_id FROM articles ORDER BY source_id;"` の出力を行に分け、空行を除いて数えたら、
期待の3行（1・2・NULL）が2行と数えられた（build/verify_sql.py が MISMATCH を出した）。

## 原因
`-A -t`（区切りなし・見出しなし）では、NULL は空文字で表示される。列が1つでその値が NULL の行は、丸ごと空行になる。
「空行は捨てる」処理と組み合わさると、NULL の行だけが数えられない。
複数列の行（`5|配信元不明の転載記事|`）は空行にならないので、気づきにくい。

## 対処
psql に `-P null=(null)` を付け、NULL を目に見える文字で出させる。
誤りの方向は「合っているのに不一致」で、誤った結果を「一致」と見逃すことはなかった。

## 教訓
出力の行数で照合するときは、「空の値」と「空行」を区別できる表示にしてから数える。
