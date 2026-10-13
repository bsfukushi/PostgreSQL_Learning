# CLAUDE.md - Claude Code 固有設定

@AGENTS.md

> 全 AI 共通の規約は上の import で読み込まれる（グローバル設定が無い環境でも読まれるように import している。二重には読まれない）。Read し直さない。
> このファイルには Claude Code 固有の差分だけを書く。200 行未満を保つ。

---

## セッションの始め方・終わり方

- 始める: `/init-session`（HANDOFF・伝言・TODO・メモリ目次を読み、今日やることを提案する）
- 終える: `/handoff`（HANDOFF.md に追記・TODO 更新・メモリ保存の確認）
- 知見は auto memory（= `.agent/memory/`。`.claude/settings.local.json` の `autoMemoryDirectory`）に 1 件 1 ファイルで保存し、`tags` を付ける
- 方針・目次の経緯は `docs/2026-10-14_pg-learning-material-handoff-v1.md`（壁打ちの記録）。確定事項は `.spec/SPEC.md` に移してあるので、普段はそちらを見る

---

## Claude Code 固有のルール

### 基本姿勢

- 書く前に前提・用語・影響範囲を確認する
- ライブラリを使う場合はバージョンを必ず明記する

### 手元環境（Windows）

- Python は `py`。README の `python3` は `py` に読み替える
- `psql` は PATH に無い。`"C:/Program Files/PostgreSQL/<版>/bin/psql.exe"` をフルパスで呼ぶ
- 初期化SQLを流す前に、接続先（ホスト・DB名・ロール）を出力して1行で示してから実行する（`command-target-check.md`）

### Git 運用（グローバルの pr-flow の例外）

- リモートは `https://github.com/bsfukushi/PostgreSQL_Learning`（public。スマホの Claude Code から操作するため）
- **main 直接運用。pr-flow の対象外**（Issue・ブランチ・PR・Codex レビューは使わない）。コミット＆push は確認なしで行う
- 2026-10-14 ともさん決定。一人で作る資料で、CI も無いため
- public なので、コミットする前に、パスワード・接続情報・個人の環境パスが含まれていないことを確かめる

### バージョン管理ルール

セマンティックバージョニング（major.minor.patch）で資料の成長を可視化する。

- **バージョンの置き場所**: `.spec/TODO.md` 冒頭のバージョン表記（`build/package.json` は版を持たない）
- **バンプ判定**:
  - **major**: マイルストーン達成時に手動指定（TODO.md のマイルストーン表）
  - **minor**: 章の本文追加、画面機能の追加
  - **patch**: 誤り訂正、言い回し・体裁の微調整、ビルドスクリプトの修正
- **タグ**: 配布するビルドごとに `git tag vX.Y.Z` を打つ

---

> 環境パス・エスカレーション手順・AI担当領域はグローバル `~/.claude/CLAUDE.md` を参照。

---

## ECC エージェント

ステップ1.5 で `.claude/agents/` に登録したものだけを使う（起動の判断は各エージェントの `description`）。
登録していない ECC エージェントが必要になったら、`$ECC_DIR/agents/<name>.md` を `.claude/agents/` にコピーして登録し、
ウィンドウを再ロードする（troubleshoot: `ecc-agent-not-found`）。

| エージェント | 使う場面 |
|---|---|
| database-reviewer | 章内SQL・初期化SQL・設計事例のレビュー（Step の品質ゲート「SQL・設計のレビュー」） |

---

## サブエージェント自動委譲ルール

Opus（メインセッション）は以下のルールに従い、ユーザーに確認せず自律的にサブエージェントへ委譲する。

### 判断フロー

```
タスクを受け取る
  ↓
[1] Opus が構成・説明の筋・例題の設計を行う（章の執筆そのものは Opus）
  ↓
[2] 確定パターンを3ファイル以上に横展開するか？（記法の置換、全章の体裁統一など）
  → YES → batch-apply (Sonnet) を並列起動
  ↓
[3] 章の SQL を実DBで照合するか？
  → YES → sql-verifier (Sonnet)
  ↓
[4] 版固有の挙動など、事実の裏取りが要るか？
  → YES → fact-checker (Sonnet)。主張ごとに並列起動してよい
  ↓
[5] Opus が直接実行（説明の設計・ビルドのデバッグ・方針変更）
```

### 各エージェントの自動起動条件

| エージェント | model | 自動起動する条件 |
|---|---|---|
| **batch-apply** | sonnet | 確定パターンを3ファイル以上に適用するとき |
| **sql-verifier** | sonnet | 章の SQL を追加・変更したあと、または初期化SQLを変更したあと |
| **fact-checker** | sonnet | 版固有の挙動・Windows固有の挙動など、裏取りが要る記述を書く前後 |
| **database-reviewer** | sonnet | 章ごとの品質ゲート「SQL・設計のレビュー」 |
| **Explore** | sonnet | 3クエリ以上の探索が見込まれる調査 |

### Opus が自分でやるべき作業（委譲しない）

- 章の本文の執筆（説明の順序・例題・失敗例の選定）
- ユーザーとの仕様すり合わせ（目次・体裁・配布方法）
- ビルドスクリプトの設計変更・デバッグ
- 手本になる最初の1章（横展開の元）
- セッション管理（HANDOFF.md / MEMORY.md 更新）

### 委譲時のプロンプト設計

batch-apply に渡すプロンプトには必ず以下を含めること:
1. パターン定義 — 何をどう変更するか（具体例）
2. 対象ファイル一覧 — フルパスのリスト
3. マッピング表 — 変更前→変更後の対応
4. 手本ファイル — 完成形のファイルパス（あれば）
5. 触らない箇所 — 変更対象外の明示

sql-verifier には、対象の章MD・接続オプション・照合前に初期化するかを渡す。
fact-checker には、確かめたい主張を1文ずつ・対象バージョンを渡す。

### 並列化の方針

- 独立したファイルへの変更は最大限並列化する
- 1エージェントあたりの対象は 1〜3ファイル が最適
- SQL照合は同じ学習用DBを使うため**並列にしない**（初期化と照合が交錯する）

---

_最終更新：2026-10-14_
