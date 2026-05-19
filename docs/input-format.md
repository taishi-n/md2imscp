# Input Format

この文書は入力記法の要約であり、正本仕様ではありません。正式な定義は `SPEC.md` を参照してください。

## 基本方針

入力は `pandoc markdown` として解釈されます。実装は生の Markdown 文字列ではなく Pandoc JSON AST を読むため、記法の実質的な意味は Pandoc の出力に依存します。

## 文書の骨格

- YAML front matter
- `##` section
- `###` item

section がない場合は `Default` が自動生成されます。
最初の `##` または `###` より前にある本文ブロックは出力に含まれません。

通常形式に加えて、`build --horizontal-rule-item-type TYPE` を付けた場合は、水平線で区切られた各ブロックを 1 問として展開する問題バンク形式も使えます。

## front matter

現在の実装が読むキーは次です。

- `title`
  - 必須
- `author`
- `creator`
- `open_at`
- `due_at`
- `time_limit`
- `timezone`
- `released_to`
- `navigation`
- `question_layout`
- `question_layout` には次の値を指定できます
  - `I`: 各問題は別のウェブページにあります
  - `S`: 問題グループは別のウェブページにあります
  - `A`: テスト全体が一画面で表示されます
- `question_numbering`
- `max_attempts`
- `allow_raw_html`
- `stem`
- `ident`

`open_at` と `due_at` は ISO 8601 文字列を想定し、タイムゾーンが省略された場合は `timezone` を使って補います。

## item 属性

`###` 見出しには Pandoc 属性構文を使います。

```md
### 問題 1 {#q1 type="single-choice" shuffle="false"}
```

現在使われる属性は次です。

- `type`
- `shuffle`
- `answer`
- `answers`
- `id`

`id` はコード上では見出しの ID として渡るため、Markdown では `#q1` のように指定します。

## 問題形式ごとの記法

### `single-choice`

task list を使います。

```md
### 問題 {type="single-choice"}
- [ ] 選択肢 1
- [x] 選択肢 2
- [ ] 選択肢 3
```

正解はちょうど 1 個必要です。

### `multiple-choice`

記法は `single-choice` と同じです。

```md
### 問題 {type="multiple-choice"}
- [x] 正解 1
- [x] 正解 2
- [ ] 不正解
```

正解は 1 個以上必要です。

CLI の `--shuffle-multiple-choice-options` を使うと、`multiple-choice` の選択肢順を build 時に実際に並べ替えられます。`--shuffle-seed` を併用すると順序を再現できます。

### `true-false`

`single-choice` と同じ task list 記法で書けます。

```md
### 問題 {type="true-false"}
- [x] True
- [ ] False
```

この場合、選択肢は 2 個ちょうどで、正解は 1 個ちょうど必要です。

従来どおり `answer` 属性でも書けます。

```md
### 問題 {type="true-false" answer="true"}
本文
```

### `numeric`

```md
### 問題 {type="numeric" answer="1"}
```

または:

```md
### 問題 {type="numeric" answers="1,1.0,01"}
```

### `cloze`

本文中の `[[...]]` が空欄です。

```md
### 問題 {type="cloze"}
`[[std::cout]] << "Hello";`
```

複数受理値は `[[a|b|c]]` です。

### `matching`

本文の後に 2 列 table を置きます。

```md
### 問題 {type="matching"}
左と右を対応づけよ。

| 項目 | 対応 |
| --- | --- |
| `int` | 整数 |
| `double` | 実数 |
```

右列の重複は 1 つの候補へまとめられます。

## 水平線区切り問題バンク形式

`build --horizontal-rule-item-type TYPE` を使うと、水平線で区切られた各ブロックを同一問題形式の item 群として扱えます。

```md
---
title: C++ 小テスト問題バンク
---

---
`cout` で改行するものを選べ。

- [ ] `<<`
- [x] `endl`
- [ ] `::`

---
**整数型** をひとつ選べ。

- [x] `int`
- [ ] `double`
- [ ] `std::string`
```

この入力に対して次を実行すると、

```bash
md2imscp build bank.md -o bank.zip --horizontal-rule-item-type single-choice --shuffle-items --shuffle-seed 1 --item-limit 2 --generated-markdown-out /tmp/bank.generated.md
```

`/tmp/bank.generated.md` には通常の `### 問題 N {type="single-choice"}` 形式へ展開された Markdown が出力されます。

現状このモードで明示サポートする問題形式は次です。

- `single-choice`
- `multiple-choice`
- `true-false`
- `cloze`
- `matching`

対応するサンプルは `examples/` に別ファイルで用意されています。

- `horizontal_rule_single_choice_bank.md`
- `horizontal_rule_multiple_choice_bank.md`
- `horizontal_rule_true_false_bank.md`
- `horizontal_rule_cloze_bank.md`
- `horizontal_rule_matching_bank.md`

前提は次です。

- 問題集合は水平線で区切られた連続ブロックとして書く
- 各ブロックは同一問題形式の本文として解釈できる内容にする
- `shuffle-items` と `item-limit` はブロックを並べ替え・抽出した結果に対して適用される

## フィードバック

現在の実装は fenced div でフィードバックを拾います。

```md
::: {.feedback kind="correct"}
正解時
:::

::: {.feedback kind="incorrect"}
不正解時
:::
```

## Markdown 装飾

`HtmlRenderer` が HTML へ変換して XML に埋め込みます。

- `` `code` `` -> `<code>`
- `**bold**` -> `<strong>`
- `*italic*` -> `<em>`
- link -> `<a>`
- image -> `<img>`
- table -> `<table>`
- code block -> `<pre><code>`

## asset

相対パスの画像やリンクは `assets/` へ同梱されます。

- 存在しない相対パスはエラー
- 外部 URL はダウンロードしない
- 同名衝突時は自動で別名になる

## 現状の注意点

- task list の判定は Pandoc が生成する `☐` / `☒` に依存する
- `cloze` は HTML 化後の文字列に対して `[[...]]` を正規表現で探す
- raw HTML は既定で禁止
- 未対応の block / inline が来ると `InputValidationError` になる
