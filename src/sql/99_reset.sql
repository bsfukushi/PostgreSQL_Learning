-- =============================================================
-- 99_reset.sql  学習用テーブルをすべて消す（元に戻すときに使う）
-- 実行後に 01_schema.sql → 02_seed.sql の順で流すと初期状態に戻ります。
-- 消える順番に注意：参照している側（子）から先に消す。
-- =============================================================
DROP TABLE IF EXISTS article_tags;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS articles;
DROP TABLE IF EXISTS sources;
