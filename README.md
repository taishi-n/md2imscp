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

### `uv` を使わない場合

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
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

## 主要コマンド

```bash
uv run md2imscp build examples/sample_assessment.md -o out.zip --validate
uv run md2imscp dump-ast examples/sample_assessment.md
uv run md2imscp validate out.zip
```

`examples/sample_assessment.md` はもう少し大きいサンプル、`examples/exportAssessment.zip` は互換性確認用の出力例です。
