# md2imscp Specification

Status: Normative  
Version: v0.1  
Last Updated: 2026-04-20  
References: [README.md](./README.md), `examples/sample_assessment.md`, `examples/exportAssessment.zip`, `examples/imscp_v1p1.xsd`

## 1. 位置付け

この文書は `md2imscp` の正本仕様である。`README.md` および `docs/` 配下の文書は参考情報であり、この文書と矛盾する場合はこの文書を優先する。

付録および例は、明示しない限り参考情報である。

## 2. 適用範囲

本仕様は、Markdown で記述されたテスト原稿を IMS Content Packaging 形式の zip package に変換する CLI ツール `md2imscp` の v0.1 を定義する。

本仕様の対象は次とする。

- 入力 Markdown 文書の構造
- assessment レベルの front matter
- item 見出し属性
- サポートする問題形式
- Markdown から HTML / XML への変換規則
- asset 同梱規則
- 出力 package の構造
- CLI と検証条件
- build 時の item 順シャッフルと件数制限

本仕様の対象外は次とする。

- 手動採点を前提とする自由記述問題
- 埋め込み JavaScript
- 外部 URL asset のダウンロード
- 部分点や高度な採点ロジックの一般化
- 特定プラットフォーム固有 UI 設定の全面的な網羅

## 3. 用語と規範語

### 3.1 用語

- assessment: 1 つのテスト全体を表す論理単位
- section: assessment 配下の設問グループ
- item: 1 問分の設問
- asset: package に同梱される画像その他の相対参照ファイル
- package: `imsmanifest.xml` と QTI XML と asset を含む zip
- stem: 出力される QTI XML ファイル名のベース名

### 3.2 規範語

本仕様では次の語を RFC 的な意味で用いる。

- MUST: 必須要件
- MUST NOT: 禁止要件
- SHOULD: 強く推奨される要件
- MAY: 任意要件

## 4. 入力文書仕様

### 4.1 基本要件

- 入力文書は UTF-8 でなければならない。
- 入力 Markdown は `pandoc markdown` と等価な意味で解釈されなければならない。
- 文書は少なくとも 1 つの item を含まなければならない。

### 4.2 文書構造

- 文書先頭には YAML front matter を置いてよい。
- `##` 見出しは section を表す。
- `###` 見出しは item を表す。
- `#` および `####` 以降の見出しは section / item を開始せず、本文ブロックとして扱わなければならない。
- `##` が存在しない場合、実装は title が `Default` の section を 1 つ自動生成しなければならない。
- 各 section は少なくとも 1 つの item を持たなければならない。
- 最初の `##` または `###` より前にある本文ブロックは、最初の section の説明として扱わなければならない。

### 4.3 識別子

- assessment の識別子は front matter の `ident` を優先し、未指定時は `assessment-<stem>` から決定的に生成しなければならない。
- section 見出しに Pandoc の heading identifier がある場合、section 識別子として使用しなければならない。
- item 見出しに Pandoc の heading identifier がある場合、item 識別子として使用しなければならない。
- 自動生成される section / item 識別子は、同一入力から同一値になるよう決定的でなければならない。

### 4.4 Front Matter

front matter は assessment レベルの設定を与える。実装は少なくとも次のキーを解釈しなければならない。

| Key | Required | Type / format | Default | Meaning |
| --- | --- | --- | --- | --- |
| `title` | Yes | string | なし | assessment の表示名 |
| `author` | No | string | empty | assessment metadata `AUTHORS` |
| `creator` | No | string | `author` | assessment metadata `CREATOR` |
| `ident` | No | string | `assessment-<stem>` | assessment 識別子 |
| `open_at` | No | ISO 8601 datetime | empty | 公開日時 |
| `due_at` | No | ISO 8601 datetime | empty | 締切日時 |
| `time_limit` | No | ISO 8601 duration | empty | 制限時間 |
| `timezone` | No | IANA timezone name | `UTC` | 日時にタイムゾーンがない場合の補完規則 |
| `released_to` | No | string | empty | assessment metadata `ASSESSMENT_RELEASED_TO` |
| `navigation` | No | string | `RANDOM` | assessment metadata `NAVIGATION` |
| `question_layout` | No | string | `I` | assessment metadata `QUESTION_LAYOUT` |
| `question_numbering` | No | string | `CONTINUOUS` | assessment metadata `QUESTION_NUMBERING` |
| `max_attempts` | No | scalar | `1` | assessment metadata `MAX_ATTEMPTS` |
| `allow_raw_html` | No | boolean | `false` | raw HTML 通過可否 |
| `stem` | No | string | 出力 zip 名から決定 | QTI XML ファイル名のベース名 |

追加の front matter キーは存在してよい。定義されていないキーは無視してよい。

### 4.5 Item 見出し属性

item 見出しは Pandoc の属性構文を使ってよい。

```md
### 問題 1 {#q1 type="single-choice" shuffle="false"}
```

実装は少なくとも次の属性を解釈しなければならない。

| Attribute | Required | Type | Default | Meaning |
| --- | --- | --- | --- | --- |
| heading identifier (`#...`) | No | string | 自動生成 | item 識別子 |
| `type` | Yes | enum | なし | 問題形式 |
| `shuffle` | No | boolean | `false` | 選択肢の順序シャッフル |
| `answer` | Conditional | string | empty | 単一の正答値 |
| `answers` | Conditional | comma-separated string | empty | 複数の正答値 |

- `type` は `single-choice`, `multiple-choice`, `true-false`, `numeric`, `cloze`, `matching` のいずれかでなければならない。
- `shuffle` は `single-choice` および `multiple-choice` でのみ意味を持つ。他の問題形式では無視しなければならない。
- 定義されていない属性は無視してよい。

## 5. Assessment メタデータ仕様

### 5.1 基本規則

- `title` は必須であり、空文字であってはならない。
- `creator` が未指定の場合、実装は `author` の値を `CREATOR` として使用しなければならない。
- `stem` の決定順序は `CLI --stem`、front matter `stem`、出力 zip 名の順としなければならない。
- `stem` は XML ファイル名として安全な形に正規化されなければならない。

### 5.2 日時の正規化

- `open_at` および `due_at` は ISO 8601 extended format として解釈されなければならない。
- 日時にタイムゾーンオフセットが含まれない場合、`timezone` を補って解釈しなければならない。
- `timezone` が未指定の場合は `UTC` を用いなければならない。
- XML へ出力する日時は正規化済み ISO 8601 文字列でなければならない。
- `open_at` が存在する場合、`CONSIDER_START_DATE` は `True` でなければならない。
- `due_at` が存在する場合、`CONSIDER_END_DATE` は `True` でなければならない。
- `time_limit` が存在する場合、assessment `duration` 要素は空であってはならず、`CONSIDER_DURATION` は `True` でなければならない。

### 5.3 出力先対応

| Input | Output |
| --- | --- |
| `title` | `assessment@title` |
| `author` | `qtimetadata/AUTHORS` |
| `creator` | `qtimetadata/CREATOR` |
| `open_at` | `qtimetadata/START_DATE` |
| `due_at` | `qtimetadata/END_DATE` |
| `time_limit` | `assessment/duration`, `qtimetadata/CONSIDER_DURATION` |
| `released_to` | `qtimetadata/ASSESSMENT_RELEASED_TO` |
| `navigation` | `qtimetadata/NAVIGATION` |
| `question_layout` | `qtimetadata/QUESTION_LAYOUT` |
| `question_numbering` | `qtimetadata/QUESTION_NUMBERING` |
| `max_attempts` | `qtimetadata/MAX_ATTEMPTS` |

## 6. 問題形式仕様

### 6.1 共通規則

- item 見出しテキストは item の表示タイトルとして使用しなければならない。
- item 見出しテキストが空の場合、実装は問題形式に応じた既定タイトルを使ってよい。
- item 本文は、本文ブロック、選択肢または表、フィードバックブロックから構成されてよい。
- 各 item は、その問題形式に対応する正答情報を出力 XML に保持しなければならない。

### 6.2 `single-choice`

- item 本文中の最初の task-list bullet list が選択肢集合を定義しなければならない。
- 各選択肢は `- [ ]` または `- [x]` 記法で表されなければならない。
- 正解の選択肢はちょうど 1 個でなければならない。
- task list 以外の本文ブロックは問題文として扱わなければならない。
- `shuffle=true` の場合、出力 XML は選択肢シャッフル可能でなければならない。
- `--shuffle-multiple-choice-options` が指定された場合、実装は `multiple-choice` の選択肢出力順を並べ替えてよい。

例:

```md
### 問題 1 {type="single-choice"}
`cout` で改行するマニピュレータはどれか。

- [ ] `<<`
- [x] `endl`
- [ ] `::`
```

### 6.3 `multiple-choice`

- item 本文中の最初の task-list bullet list が選択肢集合を定義しなければならない。
- 各選択肢は `- [ ]` または `- [x]` 記法で表されなければならない。
- 正解の選択肢は 1 個以上でなければならない。
- task list 以外の本文ブロックは問題文として扱わなければならない。
- `shuffle=true` の場合、出力 XML は選択肢シャッフル可能でなければならない。

### 6.4 `true-false`

- `true-false` item は次のいずれか 1 つの形式を満たさなければならない。
  - task-list 形式
  - `answer="true"` または `answer="false"` を使う属性形式
- task-list 形式を使う場合、選択肢はちょうど 2 個で、正解はちょうど 1 個でなければならない。
- task-list 形式と `answer` 属性が同時に存在する場合、実装は task-list 形式を優先しなければならない。
- 属性形式を使う場合、実装は選択肢文言として `True` と `False` を出力しなければならない。
- `shuffle` は無視しなければならない。

例:

```md
### 問題 2 {type="true-false"}
- [x] True
- [ ] False
```

または:

```md
### 問題 2 {type="true-false" answer="true"}
`int` は整数型である。
```

### 6.5 `numeric`

- `numeric` item は `answer` または `answers` により 1 個以上の受理値を定義しなければならない。
- `answer` は 1 個の受理値として扱わなければならない。
- `answers` はカンマ区切りの複数受理値として扱わなければならない。
- 空文字の受理値は無視しなければならない。
- 正規化後に受理値が 0 個となる入力はエラーでなければならない。
- item 本文は問題文として扱わなければならない。

例:

```md
### 問題 3 {type="numeric" answers="1,1.0,01"}
`true` を整数として表した値を入力せよ。
```

### 6.6 `cloze`

- item 本文は HTML 断片へ変換された後、その中の `[[...]]` を空欄として解釈しなければならない。
- `[[answer]]` は単一受理値の空欄でなければならない。
- `[[a|b|c]]` は複数受理値の空欄でなければならない。
- 各空欄は 1 個以上の受理値を持たなければならない。
- item は少なくとも 1 個の空欄を持たなければならない。

例:

```md
### 問題 4 {type="cloze"}
`cout` で `"Hello"` を出力した後に改行するには `[[<<]] "Hello" [[endl]];` と書く。
```

### 6.7 `matching`

- item 本文中の最初の table が整合問題の対応表を定義しなければならない。
- 対応表は少なくとも 1 行の本文行を持たなければならない。
- 各本文行はちょうど 2 列でなければならない。
- 左列は prompt、右列は対応先ラベルとして扱わなければならない。
- 右列値の一意集合を選択肢群として生成しなければならない。
- table 以外の本文ブロックは問題文として扱わなければならない。

例:

```md
### 問題 5 {type="matching"}
左と右を対応づけよ。

| 項目 | 対応 |
| --- | --- |
| `int` | 整数 |
| `double` | 実数 |
```

## 7. フィードバック仕様

- item 本文中の fenced div で class `feedback` を持つものはフィードバックブロックとして解釈しなければならない。
- `kind="correct"` は正解時フィードバックでなければならない。
- `kind="incorrect"` は不正解時フィードバックでなければならない。
- 同一 kind のフィードバックブロックが複数存在する場合、実装は出現順に連結してよい。
- `feedback` class を持たない `Div` は通常本文として扱わなければならない。
- `feedback` class を持っていても `kind` が未定義または未知である場合、通常本文として扱ってよい。

例:

```md
::: {.feedback kind="correct"}
**正解**です。
:::

::: {.feedback kind="incorrect"}
`endl` は改行を出力する。
:::
```

## 8. 変換規則

### 8.1 基本規則

- 実装は Markdown を直接文字列置換してはならず、Pandoc 構造を基準に HTML 断片へ変換しなければならない。
- 問題文、選択肢、フィードバック、section 説明は HTML 断片として生成し、XML の `mattext` に CDATA として格納しなければならない。
- サポートしない Pandoc block / inline は入力検証エラーとしなければならない。
- `--shuffle-items` が指定された場合、実装は item 集合を section をまたいで 1 列に並べ、指定 seed に基づいて順序を並べ替えてよい。
- `--item-limit N` が指定された場合、実装は item 列の先頭 N 件だけを出力しなければならない。
- `--shuffle-multiple-choice-options` が指定された場合、実装は `multiple-choice` item の選択肢列を並べ替えてよい。
- item の絞り込み後に空になった section は出力してはならない。
- item を絞り込んだ結果、複数 section に item が残る場合、section の出力順は残存 item が最初に現れた順としなければならない。
- `--horizontal-rule-item-type TYPE` が指定された場合、実装は通常の section / item 構造を読む前に、水平線で区切られた各ブロックを `###` item へ展開した等価 Markdown として扱わなければならない。
- horizontal-rule モードで `--generated-markdown-out PATH` が指定された場合、実装は抽出・並べ替え後の等価 Markdown を指定パスへ書き出さなければならない。

### 8.2 ブロック要素

少なくとも次の block 変換を保証しなければならない。

| Pandoc / Markdown | HTML |
| --- | --- |
| Paragraph | `<p>...</p>` |
| Plain | インライン列 |
| BulletList | `<ul><li>...</li></ul>` |
| OrderedList | `<ol><li>...</li></ol>` |
| CodeBlock | `<pre><code>...</code></pre>` |
| Table | `<table>...</table>` |
| HorizontalRule | `<hr />` |
| BlockQuote | `<blockquote>...</blockquote>` |
| Header | `<hN>...</hN>` |
| Div | 内部 block を再帰展開 |

### 8.3 インライン要素

少なくとも次の inline 変換を保証しなければならない。

| Pandoc / Markdown | HTML |
| --- | --- |
| Str | HTML escape 後の文字列 |
| Space | 半角空白 |
| SoftBreak | 改行文字 |
| LineBreak | `<br />` |
| Emph | `<em>...</em>` |
| Strong | `<strong>...</strong>` |
| Underline | `<u>...</u>` |
| Strikeout | `<s>...</s>` |
| Superscript | `<sup>...</sup>` |
| Subscript | `<sub>...</sub>` |
| SmallCaps | `<span style="font-variant: small-caps;">...</span>` |
| Code | `<code>...</code>` |
| Link | `<a href="...">...</a>` |
| Image | `<img src="..." alt="..." />` |
| Span | `<span>...</span>` |
| Quoted | 引用符付きテキスト |
| Math | escape 済みプレーンテキスト |

### 8.4 raw HTML

- `allow_raw_html=false` の場合、`RawBlock` および `RawInline` の HTML は入力検証エラーでなければならない。
- `allow_raw_html=true` の場合、`html` または `html5` 形式の raw HTML は通過させてよい。
- raw HTML を通過させる場合も、相対 `src` / `href` 参照は asset 管理規則に従って書き換えなければならない。
- `html` / `html5` 以外の raw 形式は HTML として解釈せず、escape 済みテキストとして扱ってよい。

## 9. Asset 仕様

- 相対パスの画像およびリンク参照は package に同梱しなければならない。
- raw HTML 中の相対 `src` / `href` も同様に同梱対象でなければならない。
- asset の解決基準ディレクトリは `--asset-root` 指定時はその値、未指定時は入力 Markdown ファイルのディレクトリとしなければならない。
- 同梱先は `assets/` 配下でなければならない。
- 同一元ファイルへの複数参照は、同一 package 内で同一 `href` を再利用しなければならない。
- 同名衝突時のリネームは決定的でなければならない。
- 存在しない相対参照は入力検証エラーでなければならない。
- 外部 URL はダウンロードしてはならず、そのまま参照として残さなければならない。

## 10. 出力 package 仕様

### 10.1 zip 構造

出力 package は少なくとも次の構造を持たなければならない。

```text
<output>.zip
├── imsmanifest.xml
├── <stem>.xml
└── assets/
    └── ...
```

asset が存在しない場合、`assets/` 配下は省略してよい。

### 10.2 `imsmanifest.xml`

- ルート要素は IMS Content Packaging 名前空間の `manifest` でなければならない。
- `metadata/schema` は `IMS Content` でなければならない。
- `metadata/schemaversion` は `1.1.3` でなければならない。
- `resources` には QTI XML を指す `resource` を 1 つ以上含まなければならない。
- QTI XML を指す `resource` の `type` は `imsqti_xmlv1p1` でなければならない。
- `resource` は QTI XML 本体と全 asset を `file href` として列挙しなければならない。

### 10.3 assessment XML

- ルート要素は `questestinterop` でなければならない。
- `questestinterop` 配下には 1 つの `assessment` がなければならない。
- `assessment` は `ident` と `title` を持たなければならない。
- `assessment` は本仕様の front matter に対応する metadata を持たなければならない。
- 各 section は 1 つの `section` 要素として出力されなければならない。
- 各 item は所属 section 配下の `item` 要素として出力されなければならない。
- item type に応じた応答定義、正答条件、フィードバック参照を出力しなければならない。

### 10.4 ファイル名と ID

- 出力される QTI XML ファイル名は `<stem>.xml` でなければならない。
- `stem` は空であってはならない。
- 同一入力と同一オプションからは、同一のファイル名、同一の識別子、同一の package 構造が得られなければならない。

## 11. CLI 仕様

### 11.1 `build`

```bash
md2imscp build input.md -o out.zip
```

オプション:

- `-o`, `--output`: 出力 zip パス。必須。
- `--stem NAME`: 出力 XML の stem を明示指定する。
- `--asset-root DIR`: 相対 asset 解決の基準ディレクトリを指定する。
- `--validate`: 生成後に `validate` と同等の検証を実行する。
- `--shuffle-items`: item 順を並べ替えてから出力する。
- `--item-limit N`: item を先頭 N 件に制限する。
- `--shuffle-seed SEED`: shuffle 系オプションで使う疑似乱数 seed を指定する。
- `--shuffle-multiple-choice-options`: `multiple-choice` の選択肢順を並べ替えてから出力する。
- `--horizontal-rule-item-type TYPE`: 水平線で区切られた各ブロックを、指定した単一問題形式の item として展開してから build する。
- `--generated-markdown-out PATH`: horizontal-rule モードで使われた展開後 Markdown を保存する。

成功時、`build` は生成した zip パスを標準出力へ表示しなければならない。

### 11.2 `dump-ast`

```bash
md2imscp dump-ast input.md
```

- `dump-ast` は Pandoc JSON AST を整形 JSON として標準出力へ表示しなければならない。

### 11.3 `validate`

```bash
md2imscp validate out.zip
```

- `validate` は既存 package を検証し、成功時には検証済みである旨を標準出力へ表示しなければならない。

### 11.4 終了コード

- `0`: 成功
- `1`: 使い方エラー
- `2`: 入力検証エラー
- `3`: 生成エラー
- `4`: 検証エラー

## 12. 検証仕様

`build --validate` および `validate` は少なくとも次を確認しなければならない。

- package が存在すること
- package 内に `imsmanifest.xml` が存在すること
- `imsmanifest.xml` が well-formed XML であること
- manifest に列挙された `file href` がすべて zip 内に存在すること
- `resource href` が存在し、QTI XML 本体を指すこと
- QTI XML 本体が well-formed XML であること
- `imsmanifest.xml` が同梱 XSD に整合すること

## 13. エラー仕様

少なくとも次の条件はエラーでなければならない。

- 入力ファイルが存在しない
- 入力パスが通常ファイルではない
- package ファイルが存在しない
- front matter に `title` がない、または空である
- 文書に item が存在しない
- section に item が存在しない
- 未知の `type` が指定された
- `single-choice` に task-list 選択肢が存在しない
- `single-choice` の正解数がちょうど 1 個でない
- `multiple-choice` に task-list 選択肢が存在しない
- `multiple-choice` の正解数が 0 個
- `true-false` が task-list 形式も `answer` 属性形式も満たさない
- `true-false` の task-list 選択肢数が 2 個でない
- `true-false` の task-list 正解数が 1 個でない
- `numeric` の受理値が 0 個
- `cloze` の空欄が 0 個
- `cloze` の空欄が空の受理値しか持たない
- `matching` に table が存在しない
- `matching` の本文行が 0 行
- `matching` の行列数が 2 列でない
- `allow_raw_html=false` なのに raw HTML が現れる
- 存在しない相対 asset を参照する
- `imsmanifest.xml` が欠落している
- manifest が存在しない file を参照している
- manifest が `resource href` を持たない
- QTI XML 本体が欠落している
- manifest または QTI XML が well-formed でない

## 14. 非機能要件

- 同一入力、同一オプション、同一 asset 内容からは決定的な output が得られなければならない。
- UTF-8 の日本語本文は失われてはならない。
- Markdown の主要な装飾は HTML 断片として保持されるべきである。
- 生成 package はスナップショット比較しやすい安定した構造を持つべきである。

## 15. 付録 A: 互換性確認用サンプル

参考実体として次を利用できる。

- 入力例: `examples/sample_assessment.md`
- 互換性確認用 package 例: `examples/exportAssessment.zip`
- manifest schema: `examples/imscp_v1p1.xsd`

## 16. 付録 B: 現状実装との差分・既知制約

この付録は参考情報である。本文の規範要件を変更しない。

- 現在の実装は選択式および整合問題の内部選択肢識別子を `A` から `Z` までしか生成できず、27 個以上の選択肢を扱えない。
- 現在の実装は `resprocessing/setvar` に正の得点を設定しておらず、正答条件の構造は出力されるが採点ロジックは本文の意図をまだ完全には満たしていない。
- 現在の manifest schema 検証は `xmllint` に加えてローカルに `xml.xsd` が存在する既知パスを必要とする。
- 現在の実装は未対応の Pandoc block / inline を受け付けず、早期に入力検証エラーとする。

## 17. 付録 C: 参照標準

- [IMS QTI](https://www.1edtech.org/standards/qti/index)
- [IMS Content Packaging Summary of Changes](https://www.imsglobal.org/content/packaging/cpv1p1p4/imscp_sumcv1p1p4.html)
- [IMS Content Packaging XML Binding Specification](https://www.imsglobal.org/content/packaging/cpv1p1p4/imscp_bindv1p1p4.html)
- [IMS Content Packaging Information Model](https://www.imsglobal.org/content/packaging/cpv1p1p4/imscp_infov1p1p4.html)
- [IMS Content Packaging Best Practice Guide](https://www.imsglobal.org/content/packaging/cpv1p1p4/imscp_bestv1p1p4.html)
- XML スキーマ配布元: https://www.imsglobal.org/sites/default/files/imscp_v1p1.xsd
