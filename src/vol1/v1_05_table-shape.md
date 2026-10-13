---
id: ch02
volume: 第1冊 基礎＋設計
part: 第2部 表と SQL を読む
number: 5
title: 表の形を読む（テーブル設計の基本）
required: true
minutes: 30
status: draft
prereq: 第2章（pgAdmin4とpsql）、第3章（サンプルデータ）、第4章（Claude Codeに頼む前の約束）
---

## この章で分かるようになること

- `CREATE TABLE` や `\d` を読んで、その表に「何が入り、何が入らないか」を説明できる
- 日時をタイムゾーン付きで保存する理由と、タイムゾーンを書かない日時で起きるズレを説明できる
- エラーが出たときに、「表の決まりごとが守ってくれた」のか「頼み方がおかしい」のかを見分けられる
- Claude Code に表の形を調べさせ、検証役の結果と `\d` の実物で確かめられる

## 1. 表の形は「決まりごとの集まり」

第3章で作った `articles`（記事）の表は、次の `CREATE TABLE` で作られています（`01_schema.sql` の一部）。

```sql show
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
```

1行が1つの列です。列の名前のあとに、「何の種類の値が入るか（**型**）」と「どんな値なら入れてよいか（**[[制約]]**）」が並んでいます。

| 列 | 型 | 制約 | 読み方 |
|---|---|---|---|
| `id` | `integer`（整数） | IDENTITY、PRIMARY KEY | 番号は PostgreSQL が振る。重複も NULL もない |
| `source_id` | `integer` | REFERENCES sources(id) | 配信元の番号。`sources` に無い番号は入らない。NULL は入る |
| `title` | `text`（文字） | NOT NULL | タイトルは必ずある |
| `url` | `text` | NOT NULL、UNIQUE | URL は必ずあり、同じ URL は2回入らない |
| `published_at` | `timestamptz`（タイムゾーン付きの日時） | なし | 公開日時。NULL は入る |
| `fetched_at` | `timestamptz` | NOT NULL、DEFAULT now() | 取得日時。書かなければ、入れた時刻が入る |
| `status` | `text` | NOT NULL、DEFAULT、CHECK | `active` か `hidden` のどちらかだけ |

`\d articles`（第2章）で見えるのも、この同じ決まりごとです。`CREATE TABLE` は「作るときの文」、`\d` は「いまの実物」なので、食い違ったときは `\d` が正しいと考えます。

> 🧭 **なぜ表の形を読めるようになる必要があるのか**：Claude Code が出す SQL の結果は、表の形に左右されます。たとえば「配信元ごとの記事数」が合わないとき、原因が SQL にあるのか、`source_id` に NULL が入りうるという表の形にあるのかは、表の形を読めないと切り分けられません。

この章では、決まりごとを4つに分けて読みます。

| 節 | 決まりごと | 守ってくれること |
|---|---|---|
| 2 | 型 | 数字として比べるか、文字として比べるか |
| 3 | 日時とタイムゾーン | 「いつ」がずれないこと |
| 4 | 主キーと IDENTITY | 1行を必ず1つに特定できること |
| 5 | NOT NULL・UNIQUE・外部キー | 欠けてはいけない値が欠けない、重複しない、存在しない相手を指さない |

## 2. 型：数字か、文字か

同じ「10」と「9」でも、型によって比べ方が変わります。

```sql
SELECT '10' < '9' AS text_compare, 10 < 9 AS integer_compare;
```

:::result 1
| text_compare | integer_compare |
|---|---|
| t | f |
:::

引用符で囲んだ `'10'` は文字なので、辞書の順番のように1文字目から比べます。`'1'` は `'9'` より前なので、「10 は 9 より小さい」（`t`）になります。引用符のない `10` は整数なので、ふつうに「10 は 9 より小さくない」（`f`）です。

> 🔍 **なぜ型が大事なのか**：番号や金額を `text` で持つと、並べ替えたときに「1, 10, 2, 3…」のような順番になり、`>` で絞ったときの結果も変わります。エラーにはならず、値の比べ方だけが静かに変わるので、第6章で扱う「値が変わる」ズレの原因になります。Claude Code が作った表で、数字のはずの列が `text` になっていないかは、`\d` の `Type` で確かめられます。

## 3. 日時とタイムゾーン：「いつ」をずらさない

### タイムゾーン付きで保存する

`published_at` の型 `timestamptz` は、「世界のどこで見ても同じ1つの瞬間」を保存します。表示するときは、接続している人の設定（第3章で確かめた `timezone`）の時刻に直して見せます。

```sql
SELECT id, published_at, published_at AT TIME ZONE 'UTC' AS utc_wall_clock
FROM articles
WHERE id IN (1, 2)
ORDER BY id;
```

:::result 2
| id | published_at | utc_wall_clock |
|---:|---|---|
| 1 | 2026-10-01 09:00:00+09 | 2026-10-01 00:00:00 |
| 2 | 2026-10-02 08:30:00+09 | 2026-10-01 23:30:00 |
:::

`published_at` の末尾の `+09` は、「日本時間（UTC より9時間進んでいる）で表示している」という印です。`AT TIME ZONE 'UTC'` は、同じ瞬間を UTC（世界の基準の時刻）の時計で読むとどうなるかを表示します。記事2は、日本では10月2日の朝ですが、UTC ではまだ10月1日です。

> 🧭 **なぜタイムゾーン付きで保存するのか**：ニュースの配信元には、海外のサービスや、UTC で時刻を返すシステムもあります。時刻だけを保存すると、「9時」が日本の9時なのか UTC の9時なのかが分からなくなります。タイムゾーン付きで保存しておけば、どこから来た時刻でも、同じ1本の時間の線の上に並べられます。

### タイムゾーンを書かない日時は、設定で意味が変わる

SQL の中で日時を書くときも、タイムゾーンを書かないと、接続している人の設定で解釈されます。psql で、自分の接続だけ設定を UTC に変えて試します（この設定は、psql を終えると元に戻ります）。

```text
SET TimeZone = 'UTC';
SELECT COUNT(*) FROM articles WHERE published_at >= '2026-10-02 00:00';
SELECT COUNT(*) FROM articles WHERE published_at >= '2026-10-02 00:00+09';
RESET TimeZone;
```

| 書き方 | 意味 | 件数 |
|---|---|---:|
| `'2026-10-02 00:00'` | **UTC の**10月2日0時（＝日本時間の10月2日9時）以降 | 2 |
| `'2026-10-02 00:00+09'` | 日本時間の10月2日0時以降 | 3 |

同じ「10月2日以降」のつもりでも、タイムゾーンを書かないと件数が変わります。記事2（日本時間の10月2日8時30分）が、片方では入り、片方では入りません。

> 🔍 **Claude Code の結果と自分の結果が9時間ずれる理由**：Claude Code も、あなたの PC の psql で接続するので、ふだんは同じ設定になります。ただし、環境変数や接続の設定が違う場面（第2冊の MCP サーバーなど）では、設定が UTC になっていることがあります。だから、この資料では日時を `'2026-10-02 00:00+09'` のように、いつもタイムゾーン付きで書きます（第7章の例もこの書き方です）。

## 4. 主キーと IDENTITY：1行を必ず1つに特定する

### 主キー

`id` の `PRIMARY KEY` は、[[主キー]]の印です。主キーの列は、重複も NULL も許されないので、`id` が分かれば行が必ず1つに決まります。

### 番号は PostgreSQL が振る

`GENERATED ALWAYS AS IDENTITY` は、「番号は PostgreSQL が順に振る。人が指定してはいけない」という決まりです。番号を指定して入れようとすると、エラーになります。

```sql copy=8
INSERT INTO tags (id, name) VALUES (10, 'テスト');
```

:::result error
```text
ERROR:  cannot insert a non-DEFAULT value into column "id"
DETAIL:  Column "id" is an identity column defined as GENERATED ALWAYS.
```
:::

「`id` は IDENTITY（GENERATED ALWAYS）の列なので、値を指定して入れられない」という意味です。番号を振っている部品が、第2章の `\d` で見えた `tags_id_seq` などの[[シーケンス]]です。

> 🔍 **番号は欠けることがある**：シーケンスは、INSERT のたびに次の番号を渡します。INSERT が途中でエラーになっても、渡した番号は返ってきません。そのため、失敗した INSERT のあとに成功した INSERT は、番号が1つ飛びます（例：`tags` の id が 4 の次に 6 になる）。番号に欠けがあっても、データが消えたとは限りません。「id が連続しているか」で件数を確かめず、`COUNT(*)` で数えます。

> 🔍 **リセットすると、番号は 1 から振り直される**：第3章の軽いリセットは、表ごと消して作り直します。シーケンスも作り直されるので、番号は 1 からになります。本文の SQL が「配信元の id が 1 ならテック日報」という前提で書けるのは、このためです。

## 5. NOT NULL・UNIQUE・外部キー：入れてはいけない値を止める

### NOT NULL：欠けてはいけない

`title` は `NOT NULL` なので、タイトルの無い記事は入りません。

```sql copy=8
INSERT INTO articles (source_id, title, url) VALUES (1, NULL, 'https://example.com/test/1');
```

:::result error
```text
ERROR:  null value in column "title" of relation "articles" violates not-null constraint
```
:::

### UNIQUE：重複してはいけない

`tags` の `name` は [[UNIQUE制約]]付きなので、同じ名前のタグは2つ作れません。

```sql copy=8
INSERT INTO tags (name) VALUES ('AI');
```

:::result error
```text
ERROR:  duplicate key value violates unique constraint "tags_name_key"
DETAIL:  Key (name)=(AI) already exists.
```
:::

### 外部キー：存在しない相手を指してはいけない

`articles.source_id` は、`sources.id` を指す[[外部キー]]です。`sources` に無い番号（99）を指す記事は入りません。

```sql copy=8
INSERT INTO articles (source_id, title, url) VALUES (99, 'テスト', 'https://example.com/test/2');
```

:::result error
```text
ERROR:  insert or update on table "articles" violates foreign key constraint "articles_source_id_fkey"
DETAIL:  Key (source_id)=(99) is not present in table "sources".
```
:::

逆に、記事から指されている配信元を消そうとしても、止まります。

```sql copy=8
DELETE FROM sources WHERE id = 1;
```

:::result error
```text
ERROR:  update or delete on table "sources" violates foreign key constraint "articles_source_id_fkey" on table "articles"
DETAIL:  Key (id)=(1) is still referenced from table "articles".
```
:::

「配信元1は、まだ articles から参照されている」という意味です。第3章のリセットで、参照している側（`article_tags`）から順に消していたのは、このエラーを避けるためです。

> 🧭 **なぜ配信元を別の表に分けたのか**：記事ごとに配信元の名前を書くと、「経済ウィークリー」と「経済ウイークリー」のような表記ゆれが起き、配信元ごとに数えたときに別々に数えられてしまいます。名前は `sources` に1回だけ書き、記事には番号（`source_id`）だけを持たせれば、表記ゆれは起きません。外部キーは、その番号が実在する配信元を指していることを保証します。この考え方を、生データから自分で導く手順は第10章で扱います。

### 親を消したら、子はどうなるか（ON DELETE）

外部キーには、「指されている行（親）を消そうとしたとき、指している行（子）をどうするか」を決める設定があります。

| 設定 | 親を消すと | この資料のサンプル |
|---|---|---|
| 書かない（NO ACTION） | 子がいれば、エラーで止まる | **これ**（上のエラー） |
| `ON DELETE CASCADE` | 子も**一緒に消える** | 使っていない |
| `ON DELETE SET NULL` | 子の外部キーの列が NULL になる | 使っていない |

> 🧭 **なぜ CASCADE を使わないのか**：`CASCADE` だと、配信元を1つ消しただけで、その配信元の記事が何本も、エラーも出ずに消えます。1行消すつもりが、何行も減る ― 第6章で扱う「行が減る」ズレが、データそのものに起きる形です。止まってくれる設定のほうが、何が消えるかを人が確かめてから進められます。

### エラーは「表が守ってくれた」印

この節のエラーは、どれも、決まりに合わないデータを PostgreSQL が止めてくれたものです。エラーになったとき、データは何も変わっていません。

困るのは、エラーを消すために決まりごとのほうを外してしまうことです。UNIQUE を外せば重複したタグが入り、外部キーを外せば存在しない配信元を指す記事が入ります。どちらも、あとで数えたときに、エラーにならずに結果がずれる原因になります。

## 6. 手を動かす

### psql で

1. `learner` で `pglearn` に接続し、`\d sources` を実行します。一番下の `Referenced by:` に、「`articles` の `source_id` から指されている」ことが書かれているのを確かめます。
2. 第2節〜第5節の SQL を順に実行し、結果やエラーの文章を読みます。エラーの SQL は、何度実行してもデータを変えません。
3. 次の2行を実行し、`tags` の id が 4 の次が 5 ではなく 6 になることを確かめます（1行目は UNIQUE のエラーになり、番号を1つ使います）。

    ```text copy=8
    INSERT INTO tags (name) VALUES ('AI');
    INSERT INTO tags (name) VALUES ('テスト') RETURNING id;
    ```

4. 手順3でデータを変えたので、第3章の軽いリセットで元に戻します。

PC の設定によっては、エラーの文章が日本語で表示されます。意味は同じです。

### Claude Code で（書く役 → 検証役 → あなた）

`C:\pglearn\` で Claude Code を起動し、次のとおりに頼みます。第4章で決めた流れを、初めて通しで使います。

```text
PostgreSQL 18 の学習用DBで、articles 表の決まりごとを一覧にしてください。
① 目的: articles の列ごとに、型・NULL を許すか・制約（主キー、UNIQUE、外部キー、CHECK）を知りたい
③ 使う表: articles
- b として、psql の \d articles の結果を加工せずに並べる
- 表の形は変えない（ALTER TABLE はしない）
```

返ってきたら、次の順に確かめます。

1. **`/tasks`**：`sql-checker` が Sonnet で動いたか
2. **一覧と `\d` の実物**：書く役の一覧が、b の `\d articles` と1列ずつ一致しているか。特に `source_id` と `published_at` が「NULL を許す」になっているか
3. **検証役の報告**：c（検証役が別の方法で調べた結果）が「一致」か
4. **e（前提）**：「制約」の意味を、頼んだとおりに解釈しているか

## 💡 Claude Codeで使うなら

:::claude 頼み方の例
第4章の作業フォルダ（`C:\pglearn\`）で頼むときの形です。接続先・してはいけないこと・検証材料 a・b・d・e・検証役（`sql-checker`）は `CLAUDE.md` に書いてあるので、依頼に書くのは①目的と③使う表、それにこの章で足すことだけです。

```text
PostgreSQL 18 の学習用DBで、10月2日以降（日本時間）に公開された記事を一覧にしてください。
① 目的: 10月2日 0時（日本時間）以降に公開された記事の id・タイトル・公開日時を知りたい
③ 使う表: articles
- 日時は、タイムゾーン付き（+09）で書く
- d として、公開日時が NULL の記事が結果に入らないことと、その記事の id を示す
```

**この章で足す検証材料**

| 記号 | 足すもの | 理由 |
|---|---|---|
| b | 表の形を説明させたら、`\d` の結果を加工せずに並べさせる | 説明と実物を、あなたが見比べられる |
| d | NULL を許す列（`source_id`・`published_at`）が絡むときは、NULL の行がどう扱われたか | NULL の行は、条件によって静かに消える |
| e | 日時を書いた SQL では、どのタイムゾーンで解釈したか | 書かないと、設定によって9時間ずれる |

**出てきたものの検証ポイント**

1. SQL の中の日時に `+09` などのタイムゾーンが付いているか
2. 結果の件数（3）が、自分で数えた件数と合うか。公開日時が NULL の記事4が入っていないか
3. 表の形を変える SQL（`ALTER TABLE`）が実行されていないか

**起きがちな失敗と、その理由**

- **「UNIQUE 制約のエラーが出たので、制約を外して登録しました」と報告される**：Claude Code は、頼まれた目的（登録する）を果たすために、障害になっている決まりごとを外そうとすることがあります。決まりごとを外すと、重複や存在しない相手を指すデータが入り、あとの集計がずれます。`ALTER TABLE` で制約を外す提案が出たら、許可せずに、「どのデータが決まりに合わなかったか」を報告させます。
- **件数が自分の結果と1件違う**：日時のタイムゾーンが書かれていないことがあります。境目の時刻の近くにある記事（記事2など）が、入ったり入らなかったりします。
- **id の欠けを見て「データが消えています」と報告される**：失敗した INSERT でも番号は進むので、欠けは消えた証拠になりません。`COUNT(*)` と a（基準の件数）で確かめます。
:::

## 確認問題

:::quiz Q1. Claude Code が「記事の登録で、URL の UNIQUE 制約のエラーが出たため、制約を外してから登録しました」と報告しました。どこを疑いますか？
制約を外したことを疑います。エラーは「同じ URL の記事がもう入っている」という知らせで、データは変わっていませんでした。制約を外して登録すると、同じ記事が2行になり、記事数を数えたときに増えます。まず、すでに入っている同じ URL の記事を見せてもらい、本当に別の記事なのかを確かめます。
:::

:::quiz Q2. Claude Code の結果では、記事1の公開日時が `2026-10-01 00:00:00+00` と表示されました。あなたの psql では `2026-10-01 09:00:00+09` です。データが違うのでしょうか？
データは同じです。どちらも同じ瞬間を、違うタイムゾーンで表示しているだけです（`+00` は UTC、`+09` は日本時間）。ただし、Claude Code の接続が UTC になっているので、タイムゾーンを書かない日時で絞ると、件数がずれます。SQL の日時に `+09` が付いているかを確かめます。
:::

:::quiz Q3. 「配信元を1つ消して」と頼んだら、Claude Code が「外部キーのエラーで消せなかったので、ON DELETE CASCADE に変更してから消しました」と報告しました。どこを疑いますか？
外部キーの設定を CASCADE に変えたことを疑います。CASCADE では、その配信元の記事も一緒に、エラーも出ずに消えます。記事の件数（a）が減っていないかを確かめ、減っていれば第3章のリセットで戻します。本当は、消す前に「この配信元を指している記事が何本あるか」を確かめて、記事をどうするかを決める必要があります。
:::

:::why 📚 なぜ？豆知識（読み飛ばしてもかまいません）

### 🔍 `timestamptz` は、タイムゾーンの名前を保存していない

名前から「タイムゾーンも一緒に保存している」と思われがちですが、実際に保存しているのは「1つの瞬間」だけです。入れるときに、書かれたタイムゾーン（無ければ接続の設定）を使って瞬間に直し、表示するときに、接続の設定の時刻に直します。「どの国の記事か」を残したいときは、タイムゾーンの名前を別の列に持たせます。

タイムゾーンの無い `timestamp` という型もあります。こちらは「時計の針の位置」だけを保存するので、どこの時刻なのかが分かりません。この資料では使いません。

### 🧭 `serial` と書かれていたら

古い書き方では、番号を振る列を `id serial` と書きます。動きはほぼ同じですが、番号を人が指定して入れることもできてしまいます。Claude Code が `serial` で表を作ってきたら、`GENERATED ALWAYS AS IDENTITY` で書き直すように頼んでかまいません。

### 🔍 CHECK 制約

`status` の `CHECK (status IN ('active', 'hidden'))` は、「この2つの値しか入れてはいけない」という決まりです。`'Active'`（大文字）や `'非表示'` のような表記ゆれを入口で止められます。

さらに知りたい人は、公式ドキュメント（PostgreSQL 18）の [制約](https://www.postgresql.org/docs/18/ddl-constraints.html)、[日付／時刻データ型](https://www.postgresql.org/docs/18/datatype-datetime.html)、[識別列](https://www.postgresql.org/docs/18/ddl-identity-columns.html) を参照してください。
:::

:::check
エラーが出たとき、決まりごと（制約）を外すのではなく、どのデータが決まりに合わなかったかを確かめたか
:::
