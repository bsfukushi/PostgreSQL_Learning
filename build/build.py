#!/usr/bin/env python3
"""
PostgreSQL 学習資料のビルドスクリプト（章ごとの Markdown → 1枚の HTML）

使い方:
    python3 build/build.py            # dist/index.html（単体で開ける完全版）と dist/artifact.html を出力

正（Source of Truth）は src/ 配下の Markdown と YAML。dist/ は毎回作り直す派生物なので、直接編集しない。

Markdown の独自記法（章テンプレート v2 に対応）:
    :::result 4 [wrong]   … psql の実行結果（4 行）。wrong を付けると「誤った結果」の印
    :::claude 見出し       … 💡 Claude Codeで使うなら の枠
    :::quiz 問題文         … 確認問題（クリックで答えを表示）
    :::why 見出し          … 📚 なぜ？豆知識（折りたたみ）
    :::check               … チェックリストに追加する1行（付録C に自動で集約）
    :::                    … 枠の終わり（入れ子にできる）
    [[用語]]               … glossary.yaml の説明をホバー／タップで表示
    > 🔍 / > 🧭            … 本文中の一言理由
    ```mermaid             … ビルド時に SVG へ変換（オフラインでも表示できる）
    ```sql copy=6          … 「写して実行する SQL（読み方は第6章）」の帯を付ける。=N を省くと第6章。
                             sql 以外（```text copy=8 など）にも付けられる。
                             第5章より前の章で、copy の付いていない ```sql ブロックは警告になる（付け忘れ防止）
    ```sql show            … 表示するだけの SQL（verify_sql.py は実行しない）。CREATE TABLE を読ませる場面など
    :::result error        … 直前の SQL がエラーになるのが正しい結果。中にエラーの文章を書く。verify_sql.py はエラーなら OK
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
BUILD = ROOT / "build"

MD_EXTENSIONS = ["tables", "pymdownx.highlight", "pymdownx.superfences", "sane_lists", "attr_list"]
MD_CONFIGS = {"pymdownx.highlight": {"use_pygments": False}}

warnings: list[str] = []


# ---------------------------------------------------------------- 読み込み
def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def split_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---\n"):
        end = text.index("\n---\n", 4)
        return yaml.safe_load(text[4:end]) or {}, text[end + 5:]
    return {}, text


# ---------------------------------------------------------------- Markdown 変換
SQL_KEYWORDS = (
    "SELECT FROM WHERE AND OR NOT AS ON JOIN INNER LEFT RIGHT FULL OUTER CROSS GROUP BY ORDER "
    "HAVING LIMIT OFFSET COUNT DISTINCT SUM INSERT INTO VALUES UPDATE SET DELETE CREATE TABLE "
    "PRIMARY KEY REFERENCES UNIQUE CHECK DEFAULT NULL IS IN GENERATED ALWAYS IDENTITY DROP IF EXISTS "
    "BEGIN COMMIT ROLLBACK RETURNING WITH TRUNCATE ALTER"
).split()
SQL_KW_RE = re.compile(r"\b(" + "|".join(SQL_KEYWORDS) + r")\b")


def highlight_sql(code_html: str) -> str:
    """SQL のキーワードとコメントだけを色分けする（読む練習の邪魔をしない最小限）。"""
    out_lines = []
    for line in code_html.split("\n"):
        comment = ""
        idx = line.find("--")
        if idx >= 0:
            line, comment = line[:idx], line[idx:]
        # 文字列リテラル（'...'）の中はキーワード扱いしない
        parts = re.split(r"('(?:[^']|'')*')", line)
        for i, p in enumerate(parts):
            if i % 2 == 1:
                parts[i] = f'<span class="st">{p}</span>'
            else:
                parts[i] = SQL_KW_RE.sub(r'<span class="kw">\1</span>', p)
        line = "".join(parts)
        if comment:
            line += f'<span class="cm">{comment}</span>'
        out_lines.append(line)
    return "\n".join(out_lines)


class Renderer:
    def __init__(self, glossary: dict, mermaid_store: dict):
        self.glossary = glossary
        self.mermaid_store = mermaid_store  # key -> code
        self.blocks: dict[str, str] = {}
        self.checks: list[tuple[str, str]] = []  # (chapter_id, text)
        self.chapter_id = ""
        self.chapter_num: int | None = None  # 章番号（整数の章だけ。copy の付け忘れ検出に使う）

    # Markdown → HTML（独自記法を含む）
    def render(self, text: str, chapter_id: str = "") -> str:
        if chapter_id:
            self.chapter_id = chapter_id
        text = self._copy_fences(text)
        text = self._containers(text)
        text = self._mermaid(text)
        out = markdown.markdown(text, extensions=MD_EXTENSIONS, extension_configs=MD_CONFIGS)
        out = self._post(out)
        return out

    COPY_DEFAULT_CHAPTER = 6   # copy の =N を省いたときの「読み方は第N章」
    READ_START_CHAPTER = 5     # 「読む SQL」が初めて出てくる章。これより前の章の ```sql には copy が必要
    COPY_SENTINEL = "@@COPY:{}@@"

    def _copy_fences(self, text: str) -> str:
        """コードブロックの指定（```lang copy[=N] / ```sql show）を処理する。
        copy: ```lang に戻し、コードの1行目に目印を入れる（_post で帯に置き換える）。
        show: 表示だけ（verify_sql.py が実行しない）。見た目は通常のコードブロック。
        「読む SQL」が始まる章（READ_START_CHAPTER）より前の章で、copy も show も無い ```sql は警告する。"""
        out = []
        in_fence = False
        for line in text.split("\n"):
            m = re.match(r"^(\s*)```(\w+)(.*)$", line)
            if not in_fence and m:
                in_fence = True
                indent, lang, rest = m.group(1), m.group(2), m.group(3).split()
                copy_ch = None
                marked = False
                for tok in rest:
                    cm = re.fullmatch(r"copy(?:=(\d+))?", tok)
                    if cm:
                        copy_ch = cm.group(1) or str(self.COPY_DEFAULT_CHAPTER)
                        marked = True
                    elif tok == "show" and lang == "sql":
                        marked = True
                    else:
                        warnings.append(f"{self.chapter_id}: 不明なコードブロックの指定 ```{lang} {tok}")
                if (lang == "sql" and not marked and self.chapter_num is not None
                        and self.chapter_num < self.READ_START_CHAPTER):
                    warnings.append(f"{self.chapter_id}: 第{self.READ_START_CHAPTER}章より前の章の ```sql に copy がありません")
                out.append(f"{indent}```{lang}")
                if copy_ch:
                    out.append(indent + self.COPY_SENTINEL.format(copy_ch))
                continue
            if in_fence and line.strip().startswith("```"):
                in_fence = False
            out.append(line)
        return "\n".join(out)

    def _placeholder(self, html_text: str) -> str:
        key = f"XBLOCKX{len(self.blocks)}XBLOCKX"
        self.blocks[key] = html_text
        return f"\n\n{key}\n\n"

    def _containers(self, text: str) -> str:
        """::: で囲まれた枠を、内側から順に HTML に変換してプレースホルダに置き換える。"""
        lines = text.split("\n")
        stack: list[tuple[str, str, list[str]]] = []  # (kind, arg, lines)
        root: list[str] = []
        in_fence = False
        for line in lines:
            target = stack[-1][2] if stack else root
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                target.append(line)
                continue
            if not in_fence and stripped.startswith(":::"):
                rest = stripped[3:].strip()
                if rest:  # 開始
                    kind, _, arg = rest.partition(" ")
                    stack.append((kind, arg.strip(), []))
                else:  # 終了
                    if not stack:
                        warnings.append(f"{self.chapter_id}: 対応する開始のない ::: があります")
                        continue
                    kind, arg, inner = stack.pop()
                    rendered = self._render_container(kind, arg, "\n".join(inner))
                    (stack[-1][2] if stack else root).append(self._placeholder(rendered))
                continue
            target.append(line)
        if stack:
            warnings.append(f"{self.chapter_id}: 閉じていない ::: があります（{stack[-1][0]}）")
        return "\n".join(root)

    def _render_container(self, kind: str, arg: str, inner: str) -> str:
        inner_html = self.render(inner)
        if kind == "result" and arg.split()[:1] == ["error"]:
            return (f'<div class="result error"><div class="result-head"><span class="badge-error">エラーになる</span>'
                    f'<span>実行結果</span></div>{inner_html}'
                    f'<div class="result-foot">（エラー。データは変わらない）</div></div>')
        if kind == "result":
            parts = arg.split()
            rows = parts[0] if parts else "?"
            wrong = "wrong" in parts
            badge = '<span class="badge-wrong">誤った結果</span>' if wrong else ""
            cls = "result wrong" if wrong else "result"
            return (f'<div class="{cls}"><div class="result-head">{badge}<span>実行結果</span></div>'
                    f'{inner_html}'
                    f'<div class="result-foot">({rows} 行)</div></div>')
        if kind == "claude":
            return (f'<section class="box claude"><h3 class="box-title">{html.escape(arg)}</h3>'
                    f"{inner_html}</section>")
        if kind == "quiz":
            return (f'<details class="quiz"><summary><span class="q">{self._inline(arg)}</span>'
                    f'<span class="reveal">答えを見る</span></summary>'
                    f'<div class="ans">{inner_html}</div></details>')
        if kind == "why":
            return (f'<details class="why"><summary>{html.escape(arg)}</summary>'
                    f'<div class="why-body">{inner_html}</div></details>')
        if kind == "check":
            plain = inner.strip()
            self.checks.append((self.chapter_id, plain))
            return (f'<div class="check"><div class="check-label">チェックリストに追加する1行</div>'
                    f'<p>□ {self._inline(plain)}</p></div>')
        warnings.append(f"{self.chapter_id}: 不明な枠の種類 :::{kind}")
        return inner_html

    def _inline(self, text: str) -> str:
        out = markdown.markdown(text, extensions=MD_EXTENSIONS, extension_configs=MD_CONFIGS)
        out = re.sub(r"^<p>(.*)</p>$", r"\1", out.strip(), flags=re.S)
        return self._terms(out)

    def _mermaid(self, text: str) -> str:
        def repl(m):
            key = f"d{len(self.mermaid_store)}"
            self.mermaid_store[key] = m.group(1)
            return self._placeholder(f'<figure class="diagram" data-mermaid="{key}"></figure>')
        return re.sub(r"```mermaid\n(.*?)```", repl, text, flags=re.S)

    def _terms(self, out: str) -> str:
        def repl(m):
            term = m.group(1)
            if term not in self.glossary:
                warnings.append(f"{self.chapter_id}: 用語集にない用語 [[{term}]]")
                return term
            return (f'<button type="button" class="term" data-def="{html.escape(self.glossary[term])}">'
                    f"{term}</button>")
        return re.sub(r"\[\[(.+?)\]\]", repl, out)

    def _post(self, out: str) -> str:
        # 写して実行する SQL の帯（_copy_fences の目印を置き換える）
        def copy_note(m):
            return (f'<div class="copy-note">📋 写して実行する SQL（いまは中身を読まなくてかまいません。'
                    f'読み方は第{m.group(2)}章）</div>{m.group(1)}')
        out = re.sub(r'(<pre class="highlight"><code[^>]*>)@@COPY:(\d+)@@\n', copy_note, out)
        # SQL の色分け
        def sql(m):
            return f'<pre class="code sql"><code>{highlight_sql(m.group(1))}</code></pre>'
        out = re.sub(r'<pre class="highlight"><code class="language-sql">(.*?)</code></pre>', sql, out, flags=re.S)
        out = re.sub(r'<pre class="highlight"><code class="language-text">', '<pre class="code text"><code>', out)
        out = re.sub(r'<pre class="highlight"><code>', '<pre class="code"><code>', out)
        # 一言理由（🔍 仕組み / 🧭 設計理由）
        def aside(m):
            body = m.group(1)
            cls = "aside mech" if "🔍" in body[:40] else ("aside design" if "🧭" in body[:40] else "aside")
            return f'<aside class="{cls}">{body}</aside>'
        out = re.sub(r"<blockquote>\s*(.*?)\s*</blockquote>", aside, out, flags=re.S)
        # 表は横スクロール枠に入れる（結果表は枠側で処理済み）
        out = re.sub(r"(<table>.*?</table>)", r'<div class="scroll">\1</div>', out, flags=re.S)
        out = self._terms(out)
        # プレースホルダを戻す（入れ子があるので、なくなるまで繰り返す）
        for _ in range(10):
            changed = False
            for key, val in list(self.blocks.items()):
                if key in out:
                    out = out.replace(f"<p>{key}</p>", val).replace(key, val)
                    changed = True
            if not changed:
                break
        return out


# ---------------------------------------------------------------- ページ組み立て
def chapter_header(ch: dict, meta: dict, book: str, part: str) -> str:
    req = ch.get("required", False)
    badges = [f'<span class="pill {"req" if req else "opt"}">{"必修" if req else "任意"}</span>']
    if meta.get("minutes"):
        badges.append(f'<span class="pill time">約{meta["minutes"]}分</span>')
    if meta.get("status") == "draft":
        badges.append('<span class="pill draft">下書き</span>')
    prereq = (f'<p class="prereq">前提：{html.escape(meta["prereq"])}</p>' if meta.get("prereq") else "")
    no = ch["num"]
    label = f"第{no}章" if no.isdigit() else (f"付録{no}" if len(no) == 1 else no)
    return (f'<header class="ch-head"><p class="crumb">{html.escape(book)} ／ {html.escape(part)}</p>'
            f'<h1><span class="ch-no">{label}</span>{html.escape(ch["title"])}</h1>'
            f'<div class="pills">{"".join(badges)}</div>{prereq}</header>')


def build():
    toc = load_yaml(SRC / "toc.yaml")
    glossary = load_yaml(SRC / "glossary.yaml")
    mermaid_store: dict[str, str] = {}
    r = Renderer(glossary, mermaid_store)

    flat: list[dict] = []
    for book in toc["books"]:
        for part in book["parts"]:
            for ch in part["chapters"]:
                flat.append({**ch, "_book": book["title"], "_part": part["title"]})

    # 本文を持つ章を先に描画（付録C がチェック項目を集めるため）
    bodies: dict[str, str] = {}
    for ch in flat:
        if ch.get("file"):
            meta, body = split_frontmatter((SRC / ch["file"]).read_text(encoding="utf-8"))
            r.chapter_num = meta.get("number") if isinstance(meta.get("number"), int) else None
            bodies[ch["id"]] = chapter_header(ch, meta, ch["_book"], ch["_part"]) + \
                f'<div class="prose">{r.render(body, ch["id"])}</div>'
    about_meta, about_body = split_frontmatter((SRC / "about.md").read_text(encoding="utf-8"))
    about_html = (f'<header class="ch-head"><p class="crumb">見本</p><h1>{html.escape(about_meta["title"])}</h1></header>'
                  f'<div class="prose">{r.render(about_body, "about")}</div>')

    titles = {c["id"]: c for c in flat}
    for ch in flat:
        if ch["id"] in bodies:
            continue
        gen = ch.get("generated")
        head = chapter_header(ch, {}, ch["_book"], ch["_part"])
        if gen == "glossary":
            rows = "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>"
                           for k, v in glossary.items())
            bodies[ch["id"]] = head + ('<div class="prose"><p>本文中の点線の用語は、この表から説明を表示しています。'
                                       '元データは <code>src/glossary.yaml</code> です。</p>'
                                       f'<div class="scroll"><table class="gloss">{rows}</table></div></div>')
        elif gen == "checklist":
            items = "".join(
                f'<li><span class="from">{titles[c]["num"]}章</span>{r._inline(t)}</li>' for c, t in r.checks)
            bodies[ch["id"]] = head + ('<div class="prose"><p>各章の最後にある「チェックリストに追加する1行」を、'
                                       'ビルドのときに自動で集めた一覧です。章を書き足すと、ここも増えます。</p>'
                                       f'<ul class="checklist">{items}</ul></div>')
        elif gen == "sql":
            parts = []
            for f in sorted((SRC / "sql").glob("*.sql")):
                code = html.escape(f.read_text(encoding="utf-8"), quote=False)
                parts.append(f'<h2>{f.name}</h2><pre class="code sql"><code>{highlight_sql(code)}</code></pre>')
            bodies[ch["id"]] = head + ('<div class="prose"><p>第3章で実行する初期化 SQL です。'
                                       '<code>99_reset.sql</code> → <code>01_schema.sql</code> → '
                                       '<code>02_seed.sql</code> の順に流すと、学習用データが初期状態に戻ります。</p>'
                                       + "".join(parts) + "</div>")
        else:
            bodies[ch["id"]] = head + ('<div class="prose stub"><p>この章は準備中です。</p>'
                                       '<p>見本として本文があるのは、第7章「JOINを読む」と第10章「設計の5つの問い」です。'
                                       '付録A・C・D は、本文と SQL から自動で作られています。</p></div>')

    # Mermaid → SVG
    svgs = {}
    if mermaid_store:
        with tempfile.TemporaryDirectory() as td:
            inp, outp = Path(td) / "in.json", Path(td) / "out.json"
            inp.write_text(json.dumps(mermaid_store, ensure_ascii=False), encoding="utf-8")
            subprocess.run(["node", str(BUILD / "render_mermaid.mjs"), str(inp), str(outp)], check=True)
            svgs = json.loads(outp.read_text(encoding="utf-8"))

    def inject(s: str) -> str:
        return re.sub(r'<figure class="diagram" data-mermaid="(d\d+)"></figure>',
                      lambda m: f'<figure class="diagram">{svgs.get(m.group(1), "")}</figure>', s)

    # 左メニュー
    nav = []
    for book in toc["books"]:
        nav.append(f'<div class="nav-book">{html.escape(book["title"])}</div>')
        for part in book["parts"]:
            show_part = part["title"] not in (book["title"].split(" ")[0], "別冊", "付録")
            if show_part:
                nav.append(f'<div class="nav-part">{html.escape(part["title"])}</div>')
            nav.append("<ul>")
            for ch in part["chapters"]:
                ready = "ready" if (ch.get("file") or ch.get("generated")) else "todo"
                req = "true" if ch.get("required") else "false"
                nav.append(
                    f'<li data-required="{req}" class="{ready}"><a href="#{ch["id"]}" data-id="{ch["id"]}">'
                    f'<span class="n">{html.escape(ch["num"])}</span><span class="t">{html.escape(ch["title"])}</span>'
                    f'<span class="done" aria-label="読了">✓</span></a></li>')
            nav.append("</ul>")

    order = ["about"] + [c["id"] for c in flat]
    names = {"about": "この見本について", **{c["id"]: c["title"] for c in flat}}
    articles = [f'<article id="page-about" data-id="about">{inject(about_html)}</article>']
    for ch in flat:
        articles.append(f'<article id="page-{ch["id"]}" data-id="{ch["id"]}" hidden>{inject(bodies[ch["id"]])}</article>')

    template = (BUILD / "template.html").read_text(encoding="utf-8")
    page = (template
            .replace("{{NAV}}", "\n".join(nav))
            .replace("{{ARTICLES}}", "\n".join(articles))
            .replace("{{ORDER}}", json.dumps(order))
            .replace("{{NAMES}}", json.dumps(names, ensure_ascii=False)))

    DIST.mkdir(exist_ok=True)
    # artifact.html：Claude のアーティファクト用（<html><head><body> は公開時に付く）
    (DIST / "artifact.html").write_text(page, encoding="utf-8")
    # index.html：ファイルとして配って、そのままブラウザで開ける完全版
    full = ('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            '</head><body>\n' + page + "\n</body></html>\n")
    (DIST / "index.html").write_text(full, encoding="utf-8")

    for w in warnings:
        print("WARN:", w, file=sys.stderr)
    print(f"built: {len(flat)} 章（本文あり {sum(1 for c in flat if c.get('file'))}）, 図 {len(svgs)}, "
          f"チェック項目 {len(r.checks)} → {DIST}")
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(build())
