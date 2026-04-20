# Testing

## 現在あるテスト

テストは `tests/test_build.py` の 1 本です。これは単体テストというより、最小の統合テストです。

見ている内容は次です。

- `examples/sample_assessment.md` から zip を生成できる
- `validate_package(...)` が通る
- zip 内に `imsmanifest.xml` と `sample.xml` がある
- 生成 XML に `<code>cout</code>` が含まれる
- 生成 XML に `<strong>どれ</strong>` が含まれる
- `open_at` と `time_limit` が XML に反映される

## テスト実行

```bash
uv run python -m unittest discover -s tests
```

## 手動確認で見るべき点

現在のテストだけでは、次は十分に見ていません。

- 各問題形式の XML 詳細が実運用環境でどう解釈されるか
- asset 同梱を含むケース
- raw HTML 許可時の安全性
- 採点ロジックの妥当性
- 多数の選択肢や複数 section を持つ大きな入力

そのため、機能追加後は次のコマンドも併用するのが安全です。

```bash
uv run md2imscp build examples/sample_assessment.md -o /tmp/sample.zip --validate
unzip -l /tmp/sample.zip
```

## 今後増やしたいテスト

- 問題形式ごとの fixture テスト
- 壊れやすい Markdown 記法の回帰テスト
- asset 同梱のテスト
- `validate` 単体の異常系テスト
- XML のスナップショット比較
