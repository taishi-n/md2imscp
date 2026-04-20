# md2imscp

`md2imscp` は、Markdown で記述した問題セットを Pandoc AST 経由で解析し、IMS Content Packaging 形式の zip を生成する Python パッケージです。

このドキュメントは、現在のコードベースが何を実装しているかを素早く把握するためのものです。仕様上の正本は `SPEC.md` であり、この `docs/` 配下は **いまリポジトリに存在する実装**を説明する参考文書です。

## できること

- `build` コマンドで Markdown から zip を生成する
- `dump-ast` コマンドで Pandoc JSON AST を確認する
- `validate` コマンドで生成済み package を検証する
- 次の問題形式を扱う
  - `single-choice`
  - `multiple-choice`
  - `true-false`
  - `numeric`
  - `cloze`
  - `matching`
- 問題文や選択肢に含まれる inline code、太字、リンク、画像などを HTML 断片へ変換して XML に埋め込む
- front matter からタイトル、作成者、公開日時、締切日時、制限時間などを設定する

## 最短の使い方

```bash
uv sync
uv run md2imscp build examples/sample_assessment.md -o out.zip --validate
```

出力された `out.zip` には、少なくとも次の 2 ファイルが含まれます。

- `imsmanifest.xml`
- `<stem>.xml`

画像や相対パス asset を使った場合は `assets/` 配下も含まれます。

## リポジトリ構成

- `md2imscp/cli.py`
  - CLI 定義とサブコマンド振り分け
- `md2imscp/core.py`
  - 変換、XML 生成、zip 化、検証の本体
- `md2imscp/resources/imscp_v1p1.xsd`
  - manifest 検証時に使う同梱 XSD
- `examples/sample_assessment.md`
  - 動作確認用のサンプル入力
- `tests/test_build.py`
  - build と validate をまとめて見る統合テスト
- `SPEC.md`
  - 正本仕様

## このドキュメントの読み方

- 実装の責務分割を知りたい場合は [Codebase](codebase.md)
- Markdown の入力記法の要約を知りたい場合は [Input Format](input-format.md)
- テストと確認手順を見たい場合は [Testing](testing.md)
