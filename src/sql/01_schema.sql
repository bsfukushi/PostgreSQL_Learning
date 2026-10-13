SET client_encoding = 'UTF8';  -- このファイルは UTF-8。PC の設定に関係なく正しく読ませる（第4章）
-- =============================================================
-- 01_schema.sql  学習用サンプル：ニュース情報（第4章で実行）
-- 対象: PostgreSQL 18（構文はPostgreSQL 16以降で共通）
-- この環境は「壊してよい学習用」です。本番DBでは実行しないこと。
-- =============================================================

-- 配信元（1行 = 1つの配信元）
CREATE TABLE sources (
    id          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        text        NOT NULL UNIQUE,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- 記事（1行 = 1本の記事）
CREATE TABLE articles (
    id            integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id     integer REFERENCES sources(id),   -- 配信元が分からない記事は NULL
    title         text        NOT NULL,
    url           text        NOT NULL UNIQUE,
    published_at  timestamptz,                       -- 公開日時が取れないことがある
    fetched_at    timestamptz NOT NULL DEFAULT now(),
    status        text        NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'hidden'))
);

-- タグ（1行 = 1つのタグ）
CREATE TABLE tags (
    id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name  text NOT NULL UNIQUE
);

-- 記事とタグの対応（1行 = 「この記事にこのタグが付いている」という事実）
CREATE TABLE article_tags (
    article_id  integer NOT NULL REFERENCES articles(id),
    tag_id      integer NOT NULL REFERENCES tags(id),
    PRIMARY KEY (article_id, tag_id)
);
