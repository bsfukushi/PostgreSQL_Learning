# TODO.md - タスク分解

> SPEC.md を元にAIが分解する。人間の承認後に確定。
> ステータス: [ ] 未着手 / [~] 作業中 / [x] 完了 / [-] スキップ

## バージョン

> **現在: v0.7.0**（本文あり：第2・3・4・5・7・10章）

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
1. ~~再開ポイントの選択~~ → 執筆を優先（2026-10-14 決定）。第3章・第4章を執筆済み
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
| Windows のロケール名・照合順序の既定値、メンバー間で揃っているか | 低（第3章で全員に確認させる） |
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

### Step 1-2: 第2章 pgAdmin4とpsql
- [x] 執筆（クラウド。2026-10-14）
- [x] ビルド確認（警告0件）
- [ ] SQL照合（PC の v18。クラウドの v16 では下見のみ通過。`\d` の出力は v16 の英語表示を載せた）
- [ ] 事実の裏取り（下の「第2章で残った裏取り」）
- [ ] SQL・設計のレビュー
- [ ] 表示確認
- [ ] PC で手順を実地確認（where psql、Path 登録、chcp 65001 と \encoding UTF8、\copy、Excel の取り込み、pgAdmin4 のメニュー名）

#### 第2章で決めたこと（ともさん確認待ち）
- コマンドを打つ画面はコマンドプロンプトに統一（PowerShell は使わない）。第3章の記述も合わせた
- 文字化け対策は「画面と psql を両方 UTF-8 に揃える」（chcp 65001 ＋ \encoding UTF8）を標準にした
- CSV の出力先は `C:\pglearn\out\`
- 第3章より前で pglearn が無いため、「手を動かす」を「今すぐ試す」と「第3章のあとで試す」に分けた

#### 第2章で残った裏取り
| 項目 | 確度 |
|---|---|
| EDB インストーラーが bin を Path に追加しない | 中（ともさんの PC では未登録） |
| `where` の「見つからない」ときの日本語メッセージ | 中 |
| chcp 65001 で psql がコードページの警告を出す | 中 |
| Windows 版 psql の画面が日本語で表示されるか（NLS） | 低（本文は英語表示で説明） |
| Excel「テキストまたは CSV から」の「元のファイル」で UTF-8 を選べる | 中〜高 |
| pgAdmin4 の「View/Edit Data → All Rows」、NULL の `[null]` 表示、Query Tool の自動コミット既定オン | 中 |
| psql の \copy で、引用符内の `\` がエスケープとして読まれうる | 中 |

### Step 1-5: 第5章 表の形を読む（テーブル設計の基本）
- [x] 執筆（クラウド。2026-10-14）
- [x] ビルド確認（警告0件）
- [ ] SQL照合（PC の v18。クラウドの v16 で下見済み：7ブロック OK、エラーの例のあともデータは 3・5・4・8 のまま）
- [ ] 事実の裏取り（エラー文の v18 での文言、日本語表示になるか、serial と IDENTITY の違い）
- [ ] SQL・設計のレビュー
- [ ] 表示確認
- [ ] PC で Claude Code の通し練習（§6 の依頼で、書く役 → sql-checker → 人 の流れが回るか）

### Step 1-W: 作業フォルダのひな形（src/workspace/）
- [x] 作成（CLAUDE.md / .claude/settings.json / .claude/agents/sql-checker.md）（2026-10-14）
- [ ] 配り方を決める（zip で配る／リポジトリから取る／付録に全文を載せる）
- [ ] PC で実地確認：C:\pglearn で起動して Opus になるか、sql-checker が Sonnet・reviewer で動くか（/tasks の表示）、CLAUDE.md の流れどおりに報告されるか
- [ ] Windows でサブエージェントの Bash から pgpass.conf が読めるか（裏取りでは推測止まり）

### Step 1-3: 第3章 サンプルデータを入れる・元に戻す
- [x] 執筆（クラウド。2026-10-14）
- [x] ビルド確認（警告0件）
- [ ] SQL照合（PC の v18。クラウドの v16 では構文の下見のみ通過）
- [~] 事実の裏取り（fact-checker 済み。残りは下の「第3・4章で残った裏取り」）
- [ ] SQL・設計のレビュー
- [ ] 表示確認
- [ ] PC で手順を実地確認（learner / pglearn の作成、C:\pglearn\sql\、軽いリセット・完全リセット、設定確認の SQL）

### Step 1-4: 第4章 Claude Codeに頼む前の約束
- [x] 執筆（クラウド。2026-10-14）
- [x] ビルド確認（警告0件）
- [ ] SQL照合（PC の v18。クラウドの v16 では構文の下見のみ通過）
- [~] 事実の裏取り（同上）
- [ ] SQL・設計のレビュー
- [ ] 表示確認
- [ ] PC で手順を実地確認（pgpass.conf、`-w` の挙動、Claude Code の許可画面の選択肢の文言）

#### 第3・4章で決めたこと（ともさん確認待ち）
- 学習用ロール名 `learner`、DB名 `pglearn`（DB の持ち主を learner にし、初期化SQLは learner で流す）
- 初期化SQLの置き場所 `C:\pglearn\sql\`
- 初期化SQL 3本の1行目に `SET client_encoding = 'UTF8';` を追加
- リセットは2段階（軽い＝3ファイル再実行／完全＝DROP DATABASE して作り直し）
- 「指示の最小型」= ①目的 ②接続先 ③使う表 ④してよいこと・いけないこと ⑤実行前に見せるもの ⑥実行後に見せるもの

#### 第3・4章で残った裏取り
| 項目 | 確度 |
|---|---|
| 日本語 Windows の psql は client_encoding が UTF-8 以外になり、UTF-8 の SQL ファイルが化ける（`SET client_encoding` で防げる） | 中〜低（PC で再現確認） |
| EDB インストーラーの既定（エンコーディング UTF8、タイムゾーン、ロケール Japanese_Japan.932） | 低（ロケール＝OS のみ中）。第3章は「表示の一例」として書いた |
| pgpass.conf が無いとき、Claude Code から実行した psql は入力待ちで止まる | 中（PC で確認） |
| Claude Code の許可画面に「今後は確認しない」系の選択肢がある | 中（PC で文言確認） |
| datlocprovider の値 c / i / b（b は v17 以降） | 中 |
- [x] 第7章 JOINを読む（見本。v16 で照合済み）
- [x] 第10章 設計の5つの問い（見本。v16 で照合済み）
- [ ] 残りの必修章（順序は再開ポイントの選択後に分解する）
