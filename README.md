# md2imscp

`md2imscp` は Markdown で書いた設問を、IMS Content Packaging 形式の zip に変換する CLI ツールです。入力 Markdown は `pandoc` で JSON AST に変換してから処理します。

詳細な入力仕様、front matter、問題形式、変換規則は [SPEC.md](./SPEC.md) を参照してください。補足資料は `docs/` 配下にあります。

## 必要環境

- Python 3.11 以上
- `pandoc`
- `xmllint` (`build --validate` と `validate` で使用)
- `uv`（推奨、任意）

## 関連ツールのインストール

### `uv`

公式インストーラ（macOS / Linux）:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Homebrew:

```bash
brew install uv
```

### `pandoc`

macOS / Homebrew:

```bash
brew install pandoc
```

Ubuntu / Debian:

```bash
sudo apt-get update
sudo apt-get install -y pandoc
```

### `xmllint`

`xmllint` は libxml2 に含まれます。

macOS / Homebrew:

```bash
brew install libxml2
# Homebrew の libxml2 は keg-only のため、xmllint が見つからない場合だけ PATH に追加する
export PATH="$(brew --prefix libxml2)/bin:$PATH"
```

Ubuntu / Debian:

```bash
sudo apt-get update
sudo apt-get install -y libxml2-utils
```

## セットアップ

### `uv` を使う場合

```bash
uv sync
```

この方法は開発用です。リポジトリ外の任意の場所から `md2imscp` を直接実行したい場合は、下の「ローカルインストール」を使ってください。

### `uv` を使わない場合

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

## ローカルインストール

このリポジトリをチェックアウトしたまま、別ディレクトリから `md2imscp` を直接実行したい場合の方法です。

### `uv` を使う場合

Astral の公式ドキュメントでは、CLI ツールの常用には `uv tool install` が案内されています。このリポジトリ直下で次を実行してください。

```bash
uv tool install -e .
```

`uv` の実行ファイルディレクトリが `PATH` に入っていなければ追加してください。

```bash
export PATH="$(uv tool dir --bin):$PATH"
```

実行例:

```bash
md2imscp --help
cd /tmp
md2imscp build /Users/you/work/input.md -o /tmp/out.zip --validate
md2imscp build /Users/you/work/input.md -o /tmp/out-10.zip --shuffle-items --shuffle-seed 42 --item-limit 10
md2imscp build /Users/you/work/input.md -o /tmp/out-shuffled-choices.zip --shuffle-multiple-choice-options --shuffle-seed 42
```

更新を反映したい場合は、必要に応じて再実行してください。

```bash
uv tool install -e . --reinstall
```

### `uv` を使わない場合

`pip` で CLI エントリーポイントを入れる場合は、任意の仮想環境を作ってこのリポジトリを editable install します。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools
python -m pip install -e .
```

この方法では、`md2imscp` はその仮想環境を activate している間だけ実行できます。別ディレクトリから使う例:

```bash
source /path/to/md2imscp/.venv/bin/activate
cd /tmp
md2imscp validate /tmp/out.zip
```

activate せずに使う場合は、その仮想環境の実行ファイルを直接呼びます。

```bash
/path/to/md2imscp/.venv/bin/md2imscp dump-ast /path/to/input.md
```

Python パッケージ依存:

- ランタイム依存はありません（`pyproject.toml` の `dependencies = []`）
- インストール時のビルド依存は `setuptools>=61` です
- ただし外部コマンドとして `pandoc` と、検証時には `xmllint` が必要です

## 最小サンプル

`minimal.md`

この 1 ファイルで、現在サポートしている全問題種別を一通り試せます。

```md
---
title: 最小サンプル
description: |
  **小テストの説明**です。

  `md2imscp` はこの内容を assessment の説明として出力します。
---

### 問題 1 {type="single-choice"}
`cout` で改行するものを選べ。

- [ ] `<<`
- [x] `endl`

### 問題 2 {type="multiple-choice"}
整数型をすべて選べ。

- [x] `int`
- [x] `long`
- [ ] `double`

### 問題 3 {type="true-false"}
`int` は整数型である。

- [x] True
- [ ] False

### 問題 4 {type="numeric" answers="1,1.0,01"}
`true` を整数として表した値を入力せよ。

### 問題 5 {type="cloze"}
`cout` で `"Hello"` を出力して改行するには `[[<<]] "Hello" [[endl]];` と書く。

### 問題 6 {type="matching"}
左と右を対応づけよ。

| 項目 | 対応 |
| --- | --- |
| `int` | 整数 |
| `double` | 実数 |
```

変換:

```bash
uv run md2imscp build minimal.md -o minimal.zip --validate
```

`uv` を使わない場合:

```bash
python -m md2imscp build minimal.md -o minimal.zip --validate
```

生成結果:

```text
minimal.zip
├── imsmanifest.xml
└── minimal.xml
```

`minimal.xml` には、6 問ぶんの item が出力されます。たとえば 1 問目の本文は次のように入ります。

```xml
<assessment ident="assessment-minimal" title="最小サンプル">
...
<mattext charset="ascii-us" texttype="text/plain" xml:space="default"><![CDATA[<p><code>cout</code> で改行するものを選べ。</p>]]></mattext>
```

`multiple-choice` 問題の選択肢順を実際に並べ替えたい場合は、`--shuffle-multiple-choice-options` を使います。再現可能な順序が必要なら `--shuffle-seed` を併用します。

## 問題バンク形式のサンプル

水平線区切り問題バンクのサンプルを、対応している各問題タイプごとに用意しています。

- `examples/horizontal_rule_single_choice_bank.md`
- `examples/horizontal_rule_multiple_choice_bank.md`
- `examples/horizontal_rule_true_false_bank.md`
- `examples/horizontal_rule_cloze_bank.md`
- `examples/horizontal_rule_matching_bank.md`

このモードでは、`--horizontal-rule-item-type` で問題形式を指定し、必要なら `--generated-markdown-out` で展開後の Markdown を保存できます。

単一選択の例:

```bash
uv run md2imscp build \
  examples/horizontal_rule_single_choice_bank.md \
  -o bank.zip \
  --horizontal-rule-item-type single-choice \
  --shuffle-items \
  --shuffle-seed 1 \
  --item-limit 2 \
  --generated-markdown-out /tmp/bank.generated.md \
  --validate
```

`/tmp/bank.generated.md` には、抽出・シャッフル後の通常形式 Markdown が保存されます。

他の問題タイプの例:

```bash
uv run md2imscp build examples/horizontal_rule_multiple_choice_bank.md -o bank-mc.zip --horizontal-rule-item-type multiple-choice --shuffle-items --shuffle-seed 1 --item-limit 2 --generated-markdown-out /tmp/bank-mc.generated.md --validate
uv run md2imscp build examples/horizontal_rule_true_false_bank.md -o bank-tf.zip --horizontal-rule-item-type true-false --shuffle-items --shuffle-seed 1 --item-limit 2 --generated-markdown-out /tmp/bank-tf.generated.md --validate
uv run md2imscp build examples/horizontal_rule_cloze_bank.md -o bank-cloze.zip --horizontal-rule-item-type cloze --shuffle-items --shuffle-seed 1 --item-limit 2 --generated-markdown-out /tmp/bank-cloze.generated.md --validate
uv run md2imscp build examples/horizontal_rule_matching_bank.md -o bank-matching.zip --horizontal-rule-item-type matching --shuffle-items --shuffle-seed 1 --item-limit 2 --generated-markdown-out /tmp/bank-matching.generated.md --validate
```

## 主要コマンド

```bash
uv run md2imscp build examples/sample_assessment.md -o out.zip --validate
uv run md2imscp build examples/sample_assessment.md -o sample10.zip --shuffle-items --shuffle-seed 42 --item-limit 10
uv run md2imscp build examples/sample_assessment.md -o sample-choices.zip --shuffle-multiple-choice-options --shuffle-seed 42
uv run md2imscp build examples/horizontal_rule_single_choice_bank.md -o bank.zip --horizontal-rule-item-type single-choice --shuffle-items --shuffle-seed 1 --item-limit 2 --generated-markdown-out /tmp/bank.generated.md --validate
uv run md2imscp build examples/horizontal_rule_multiple_choice_bank.md -o bank-mc.zip --horizontal-rule-item-type multiple-choice --shuffle-items --shuffle-seed 1 --item-limit 2 --validate
uv run md2imscp dump-ast examples/sample_assessment.md
uv run md2imscp validate out.zip
```

ローカルインストール後は、`uv run` を付けずに同じ CLI をそのまま使えます。

```bash
md2imscp build examples/sample_assessment.md -o out.zip --validate
md2imscp build examples/sample_assessment.md -o sample10.zip --shuffle-items --shuffle-seed 42 --item-limit 10
md2imscp build examples/sample_assessment.md -o sample-choices.zip --shuffle-multiple-choice-options --shuffle-seed 42
md2imscp build examples/horizontal_rule_single_choice_bank.md -o bank.zip --horizontal-rule-item-type single-choice --shuffle-items --shuffle-seed 1 --item-limit 2 --generated-markdown-out /tmp/bank.generated.md --validate
md2imscp build examples/horizontal_rule_multiple_choice_bank.md -o bank-mc.zip --horizontal-rule-item-type multiple-choice --shuffle-items --shuffle-seed 1 --item-limit 2 --validate
md2imscp dump-ast examples/sample_assessment.md
md2imscp validate out.zip
```

`examples/sample_assessment.md` は通常形式のサンプル、`examples/horizontal_rule_*_bank.md` は問題バンク形式のサンプル、`examples/exportAssessment.zip` は互換性確認用の出力例です。
