# TODO.md - タスク分解

> SPEC.md を元にAIが分解する。人間の承認後に確定。
> ステータス: [ ] 未着手 / [~] 作業中 / [x] 完了 / [-] スキップ

## バージョン

> **現在: v0.1.0**（体裁見本：第7章・第10章のみ本文あり）

| バージョン | マイルストーン |
|---|---|
| v1.0.0 | 第1冊（基礎＋設計）の必修章がすべて本文あり・SQL照合済み（v18）で、メンバーに配布できる |
| v2.0.0 | 第2冊（実践＋MCP）の必修章がすべて本文あり。MCP サーバーを選定・検証済み |

> マイルストーンの条件は仮置き。ともさんが確定する。

## ファイル構成

```
PostgreSQL_Learning/
├── AGENTS.md / CLAUDE.md / GEMINI.md / README.md
├── src/                 ← 正
│   ├── toc.yaml         目次（章ID・番号・必修/任意・本文ファイル）
│   ├── glossary.yaml    用語集
│   ├── about.md
│   ├── vol1/            第1冊の章MD（v1_07_join.md, v1_10_five-questions.md）
│   ├── vol2/            第2冊（空）
│   ├── bessatsu/        別冊（空）
│   ├── appendix/        付録（空）
│   └── sql/             初期化SQL（99_reset → 01_schema → 02_seed）
├── build/               build.py / template.html / render_mermaid.mjs / verify_sql.py / package.json
├── dist/                ← 派生物（直接編集しない）index.html / artifact.html
├── docs/                壁打ちハンドオフ
├── .spec/               PLAN / SPEC / TODO / KNOWLEDGE / archive/
├── .agent/              memory/ / handoff/
└── .claude/             agents/ / settings.local.json
```

## 未解決・要確認事項

### ともさんの判断待ち
1. **再開ポイントの選択**: A 見本の体裁レビュー ／ B 第4章・第5章の執筆
2. 見本の体裁（色、文字の大きさ、枠の種類、図の形、ER図の大きさ）
3. 1章30分の仮置きでよいか。学習期間の目安（週◯回×◯分）→「はじめに」に書く
4. 配布方法: アーティファクトのリンク共有／HTMLファイル配布／共有フォルダ
5. MCP サーバーの選定（リファレンス実装はアーカイブ済みとの報告あり・未確認。候補: bytebase/dbhub、crystaldba/postgres-mcp）。選定前に「UPDATE が拒否されること」を手元で検証
6. ニュース本文を保存する場合の著作権の扱い（事例の設計に影響）
7. `dist/` を git で追跡するか（配布物として残す／派生物として除外する）

### 環境
- 手元の PostgreSQL は **16**（`C:\Program Files\PostgreSQL\16`、PATH 未登録）。資料は 18 前提なので、v18 での照合環境を用意する
- `build/node_modules` 未インストール（`cd build && npm i`）

### 執筆前に裏取りが必要な事実
| 項目 | 確度 |
|---|---|
| COPY の `ON_ERROR ignore` は型変換エラーのみが対象（UNIQUE／NOT NULL違反はコマンド全体が失敗） | Fable は公式で確認と報告。Claude は未再確認 |
| `REJECT_LIMIT`、`LOG_VERBOSITY silent` は v18 で追加 | Fable は公式で確認と報告 |
| Windows：インストーラーが PostgreSQL の `bin` を PATH に追加しないことが多い | 中 |
| Windows：psql の文字化け対策（`chcp 65001`、`\encoding UTF8`、Windows Terminal） | 中（各PCで再現確認） |
| Windows：`pgpass.conf` の場所（`%APPDATA%\postgresql\`） | 高（場所は要確認） |
| Claude Code が使うシェル（Git Bash／PowerShell）での `psql -c "..."` の引用符の扱い | 中 |
| Windows のロケール名・照合順序の既定値、メンバー間で揃っているか | 低（第4章で全員に確認させる） |
| pg_bigm の Windows 向けバイナリの有無 | 低 |
| pgAdmin4 の PostgreSQL 18 対応バージョン、Query Tool の自動コミット設定の名称 | 低 |
| 見本の2章の SQL は PostgreSQL 16 で検証済み。v18 で再実行して確認 | — |

---

## Phase 1: 第1冊 基礎＋設計

> 各章の Step は AGENTS.md「標準ステップ構成」に従う（執筆 → ビルド → SQL照合 → 裏取り → レビュー → 表示確認）。

### Step 1-0: 作業環境
- [x] 記憶管理システム初期化（2026-10-14）
- [x] GitHub リモート登録（bsfukushi/PostgreSQL_Learning、public、main 直接運用）
- [ ] `pip install markdown pyyaml pymdown-extensions` / `cd build && npm i`
- [ ] v18 の学習用DBを用意し、初期化SQLを流す（PC で行う。クラウドは照合しない：SPEC「SQL照合の正」）
- [ ] `py build/build.py` でビルドが通ることを確認
- [ ] 見本2章を v18 で照合

### Step 1-1 以降: 章の執筆
- [x] 第7章 JOINを読む（見本。v16 で照合済み）
- [x] 第10章 設計の5つの問い（見本。v16 で照合済み）
- [ ] 残りの必修章（順序は再開ポイントの選択後に分解する）
