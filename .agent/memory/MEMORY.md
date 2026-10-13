# MEMORY.md - 蓄積された経験・知見

> 1 行 1 件の索引: `- [タイトル](ファイル.md) — 一言`。本文は個別ファイルに書く。
> AGENTS.md / CLAUDE.md / コードから分かることは書かない。

---

- [psql の NULL だけの行が空行になる](psql-null-only-row-blank.md) — -A -t で数えると行数がずれる。-P null=(null) で回避
- [別モデルによる検証の設計](separate-model-verification.md) — 別モデル＋履歴を渡さない＋読み取り専用ロール。一致は証明ではない。抜け道は /tasks で目視
