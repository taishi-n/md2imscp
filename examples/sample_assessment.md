---
title: C++ 基礎テスト
author: 山田太郎
creator: 山田太郎
open_at: 2026-04-20T09:00:00+09:00
due_at: 2026-04-27T23:59:00+09:00
# assessment-level time limit: 30 minutes
time_limit: PT30M
timezone: Asia/Tokyo
navigation: RANDOM
question_layout: I
question_numbering: CONTINUOUS
max_attempts: 1
allow_raw_html: false
---

## 基本

### 問題 1 {#q1 type="single-choice"}
`cout` で改行するマニピュレータは **どれ** か。

- [ ] `<<`
- [x] `endl`
- [ ] `::`

::: {.feedback kind="correct"}
**正解**です。
:::

::: {.feedback kind="incorrect"}
`endl` は改行を出力する。
:::

### 問題 2 {#q2 type="true-false"}
`int` は **整数型** である。

- [x] True
- [ ] False

::: {.feedback kind="correct"}
**正解**です。`int` は C++ の基本的な整数型である。
:::

::: {.feedback kind="incorrect"}
`int` は実数型ではなく、整数を表す基本型である。
:::

### 問題 3 {#q3 type="numeric" answers="1,1.0,01"}
`true` を整数として表した値を入力せよ。

::: {.feedback kind="correct"}
**正解**です。C++ では `true` を整数に変換すると `1` になる。
:::

::: {.feedback kind="incorrect"}
`bool` 値の `true` を整数として扱うと `1` になる。
:::

### 問題 4 {#q4 type="cloze"}
`cout` で `"Hello"` を出力した後に改行するには `[[<<]] "Hello" [[endl]];` と書く。

::: {.feedback kind="correct"}
**正解**です。出力演算子 `<<` と改行マニピュレータ `endl` を使う。
:::

::: {.feedback kind="incorrect"}
文字列の前には `<<`、末尾の改行には `endl` を入れる。
:::

### 問題 5 {#q5 type="matching"}
左と右を対応づけよ。

| 項目 | 対応 |
| --- | --- |
| `int` | 整数 |
| `double` | 実数 |

::: {.feedback kind="correct"}
**正解**です。`int` は整数、`double` は実数を表す。
:::

::: {.feedback kind="incorrect"}
`int` は整数型、`double` は浮動小数点型である。
:::

### 問題 6 {#q6 type="multiple-choice"}
**整数型** をすべて選べ。

- [x] `int`
- [x] `long`
- [ ] `double`

::: {.feedback kind="correct"}
**正解**です。`int` と `long` は整数型で、`double` は実数型である。
:::

::: {.feedback kind="incorrect"}
`double` は浮動小数点型なので、整数型には含まれない。
:::

## プリプロセッサと出力

### 問題 7 {#q7 type="single-choice"}
`#include` とは何か。

- [x] 必要なヘッダファイルの内容を取り込むための**プリプロセッサディレクティブ**である。
- [ ] 関数を定義するための予約語である。
- [ ] 名前空間を宣言するための構文である。
- [ ] プログラム実行後に標準ライブラリを初期化する命令である。

::: {.feedback kind="correct"}
**正解**です。`#include` は前処理の段階で別ファイルの内容を取り込む。
:::

::: {.feedback kind="incorrect"}
`#include` は関数定義や名前空間宣言ではなく、プリプロセッサディレクティブである。
:::

### 問題 8 {#q8 type="single-choice"}
`#include <iostream>` とは何か。

- [x] 標準入出力に関する宣言を含む `iostream` ヘッダを取り込む前処理指令である。
- [ ] `iostream` という関数を呼び出して標準出力を有効にする式である。
- [ ] `iostream` という名前空間を新しく定義する宣言である。
- [ ] コンパイル後に `iostream` を動的に読み込む命令である。

::: {.feedback kind="correct"}
**正解**です。`iostream` には `std::cout` などの宣言が含まれる。
:::

::: {.feedback kind="incorrect"}
`#include <iostream>` はヘッダの取り込みであり、関数呼び出しや動的ロードではない。
:::

### 問題 9 {#q9 type="true-false"}
C++ 言語の関数名や変数名は **case-sensitive** であり，`main` と `Main` は別の識別子として扱われる。

- [x] True
- [ ] False

::: {.feedback kind="correct"}
**正解**です。C++ の識別子は大文字と小文字を区別する。
:::

::: {.feedback kind="incorrect"}
`main` と `Main` は別名として扱われるため、C++ は case-sensitive である。
:::

### 問題 10 {#q10 type="cloze"}
`Hello World!` を標準出力する文は `[[std::cout << "Hello World!";]]` である。

::: {.feedback kind="correct"}
**正解**です。名前空間を含めると `std::cout << "Hello World!";` になる。
:::

::: {.feedback kind="incorrect"}
`std::cout` と出力演算子 `<<` を使って文字列を標準出力する。
:::

### 問題 11 {#q11 type="single-choice"}
次のコードはコンパイルエラーになる。正しい理由を**ひとつ**選べ。

```cpp
#include <iostream>

int main() {
    cout << "Hello";
}
```

- [ ] 文字列リテラルは `"` ではなく `'` で囲まなければならないから。
- [ ] `cout` は整数しか出力できないから。
- [x] `cout` を使うには `std::cout` と書くか `using namespace std;` などが必要だから。
- [ ] `main` 関数は戻り値型を持てないから。

::: {.feedback kind="correct"}
**正解**です。`cout` は `std` 名前空間に属するため、そのままでは見つからない。
:::

::: {.feedback kind="incorrect"}
このコードの問題は文字列でも `main` の戻り値型でもなく、`cout` の名前解決である。
:::
