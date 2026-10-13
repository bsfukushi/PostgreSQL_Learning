# PostgreSQL学習資料（見本 v0.1）

正は `src/`。`dist/` はビルドで毎回作り直す派生物なので、直接編集しない。

## フォルダ
- src/toc.yaml        目次（章ID・番号・必修/任意・本文ファイル）
- src/glossary.yaml   用語集（本文の [[用語]] と付録Aの元）
- src/vol1/ vol2/ bessatsu/ appendix/   章ごとの Markdown
- src/sql/            初期化SQL（99_reset → 01_schema → 02_seed）
- build/build.py      Markdown → HTML
- build/verify_sql.py 章内のSQLを実DBで実行し、結果表の行数と照合
- dist/index.html     単体で開ける完全版（配布用）／ dist/artifact.html（Claudeのアーティファクト用）

## ビルド
    pip install markdown pyyaml pymdown-extensions
    cd build && npm i && cd ..
    python3 build/build.py

## 注意（YAMLの落とし穴）
- キー名 `no` は真偽値（false）として読まれるため、章番号は `num` を使う
- 用語 `NULL` はキーとして書くと空値になるため、`"NULL"` と引用符で囲む
