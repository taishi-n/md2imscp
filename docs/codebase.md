# Codebase

## 全体像

現在のコードベースは、ほぼ 2 つのモジュールに集約されています。

- `md2imscp.cli`
  - CLI の入口
- `md2imscp.core`
  - 実処理のすべて

責務が `core.py` に集中しているため、機能追加や問題形式追加は基本的にこのファイルを読むことから始まります。

## CLI 層

`md2imscp/cli.py` は `argparse` ベースの薄いラッパです。

- `build`
  - `build_package(...)` を呼ぶ
- `dump-ast`
  - `dump_ast(...)` を呼ぶ
- `validate`
  - `validate_package(...)` を呼ぶ

例外は `Md2ImscpError` 系で受け、終了コードへ変換します。

## 主要データモデル

`core.py` には中間表現として dataclass 群があります。

- `Assessment`
  - 出力 package 全体
- `Section`
  - assessment 配下の section
- `Item`
  - 問題 1 件
- `ChoiceOption`
  - 選択式の選択肢
- `ClozeBlank`
  - 穴埋めの 1 空欄
- `MatchingPrompt`
  - 整合問題の左側項目
- `MatchingTarget`
  - 整合問題の右側候補
- `AssetRecord`
  - zip に同梱する asset

また、Pandoc AST を段階的に処理するために `RawSection` と `RawItem` も持っています。これは Markdown の構造をいったん保ったまま section / item 単位へ切り出すためのものです。

## build の処理フロー

`build_package(...)` は次の順序で動きます。

1. 入力 Markdown ファイルの存在確認
2. `run_pandoc_json(...)` で Pandoc JSON AST を取得
3. `parse_meta_map(...)` で front matter を Python 値へ変換
4. `build_assessment_model(...)` で内部モデルを構築
5. `build_package_files(...)` で `imsmanifest.xml` と QTI XML を生成
6. `write_zip(...)` で deterministic な zip を書き出す
7. `--validate` 指定時は `validate_package(...)` を実行

## Markdown 解析の流れ

Markdown は直接文字列処理せず、Pandoc AST から読み取ります。

assessment レベルの `description` だけは front matter の生 metadata AST から HTML 化し、assessment 直下の `presentation_material` に入れます。

### section / item の切り出し

`parse_sections(...)` が見出しレベルで文書を切ります。

- `##` を section とみなす
- `###` を item とみなす
- section がない場合は `Default` section を自動生成する
- 最初の `##` / `###` より前にある本文ブロックは捨てる

### item の具体化

`build_item(...)` が `type` 属性に応じて問題データへ変換します。

- `single-choice`, `multiple-choice`
  - `extract_task_choices(...)`
  - Pandoc が task list を `☐` / `☒` として出す前提で解析する
- `true-false`
  - まず task list を探す
  - task list がなければ `answer=true|false` を読む
- `numeric`
  - `answer` または `answers` を読む
- `cloze`
  - `parse_cloze_prompt(...)` で `[[...]]` を検出する
- `matching`
  - `extract_matching(...)` で 2 列 table を解析する

### フィードバック

`split_feedback_blocks(...)` が `::: {.feedback kind="correct"}` と `kind="incorrect"` を取り出します。

## HTML レンダリング

`HtmlRenderer` は Pandoc AST の block / inline を HTML 断片へ変換します。

主な対応は次です。

- inline code -> `<code>`
- 太字 -> `<strong>`
- イタリック -> `<em>`
- リンク -> `<a>`
- 画像 -> `<img>`
- コードブロック -> `<pre><code>`
- table -> `<table>`

この HTML は XML の `mattext` にそのままテキストとして入るのではなく、`CDataSerializer` により CDATA 化されます。

## asset 管理

`AssetManager` が画像やリンク先の相対パスを `assets/` 配下へ再配置する前提で管理します。

- 同じ元ファイルは同じ `href` を再利用する
- 名前衝突時は SHA-1 由来の短いサフィックスを付ける
- 存在しない相対パスは `InputValidationError`
- 外部 URL はそのまま残す

## XML 生成

XML 生成は `xml.etree.ElementTree` ベースです。

- `build_manifest_xml(...)`
  - `imsmanifest.xml` を生成
- `build_assessment_xml(...)`
  - assessment 本体 XML を生成
- `build_item_xml(...)`
  - 問題形式ごとに分岐

問題形式ごとの詳細は次の関数に分かれています。

- `build_choice_item(...)`
- `build_numeric_item(...)`
- `build_cloze_item(...)`
- `build_matching_item(...)`

## 検証

`validate_package(...)` は次を見ます。

- `imsmanifest.xml` があるか
- manifest に列挙された `file href` が zip 内に存在するか
- resource の `href` が指す QTI XML が存在するか
- manifest と QTI XML が well-formed か
- `run_manifest_schema_validation(...)` が成功するか

manifest の XSD は package resource の `md2imscp/resources/imscp_v1p1.xsd` を使います。さらにその XSD が参照する `xml.xsd` は `find_local_xml_schema(...)` がローカル環境から探索します。

## 現時点の制約

現状コードの重要な制約は次です。

- `core.py` が大きく、責務分割はまだ粗い
- 選択肢 ID は `A` から `Z` までで、27 個以上は扱えない
- `matching` は 2 列 table 前提
- raw HTML は `allow_raw_html: true` のときだけ許可される
- 採点ロジックはまだ簡易で、`single-choice`, `true-false`, `numeric`, `cloze`, `matching` は既定で 1 問 1 点相当を出力するが、`multiple-choice` の配点は未実装のまま `0.0` を入れている
- manifest の検証はローカルに `xmllint` と `xml.xsd` があることを前提としている

最後の 2 点は将来の改善候補として認識しておくべきです。
