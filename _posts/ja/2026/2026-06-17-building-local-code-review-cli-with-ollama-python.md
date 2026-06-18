---
layout: post
title: OllamaとPythonで自分だけのローカルコードレビューCLIを作る
slug: building-local-code-review-cli-with-ollama-python
date: 2026-06-17 11:15:25 +0900
categories:
- AI
tags:
- Ollama
- LLM
- Code Review
- Python
- CLI
description: APIコストやセキュリティの心配なく、OllamaとLlama 3を活用してローカル環境で動作するコードレビューCLIツールを自作します。プロンプト設計から限界点まで、実用的なヒントを解説します。
image: /uploads/building-local-code-review-cli-with-ollama-python/thumbnail.webp
lang: ja
translation_key: building-local-code-review-cli-with-ollama-python
permalink: /ja/posts/building-local-code-review-cli-with-ollama-python/
---
コードレビューはソフトウェアの品質を維持するための重要なプロセスですが、同僚の時間を多く消費する作業でもあります。GitHub CopilotやChatGPTのようなAIツールは優れた補助手段となりましたが、機密性の高いコードを外部APIに送信することに対するセキュリティ上の懸念やコストの問題は依然として残っています。

この記事では、これらの問題を解決するため、ローカル環境で完全に独立して動作するコードレビューCLI（コマンドラインインターフェース）ツールを自作します。人気のローカルLLM実行ツールである**Ollama**と**Python**を使用し、外部ネットワーク接続なしで安全かつ迅速にコードのフィードバックを得る方法を探ります。

<!--more-->
![OllamaとPythonで自分だけのローカルコードレビューCLIを作る](/uploads/building-local-code-review-cli-with-ollama-python/thumbnail.webp "OllamaとPythonで自分だけのローカルコードレビューCLIを作る")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AIが生成した画像</small>
</p>
-----

## なぜローカルコードレビュアーなのか？

商用のAIサービスを利用する代わりに、ローカルで直接LLMを実行してコードレビューツールを作成することには、いくつかの明確な利点があります。

1.  **セキュリティ**: ソースコードが個人のコンピュータや内部サーバーから外に出ることがありません。企業のセキュリティポリシーが厳格であったり、外部に漏洩してはならないコードを扱う場合に決定的な利点となります。
2.  **コスト**: 初期のハードウェア投資を除けば、API呼び出しに伴う追加費用は発生しません。心置きなく実験し、好きなだけ使用できます。
3.  **オフラインでの動作**: インターネット接続が不安定であったり、ない環境でもコードレビューを実行できます。
4.  **カスタマイズ**: プロンプトとモデルを自由に変更し、私たちのチームだけのコードレビューのスタイルやルールに合ったツールを作成できます。

## 事前準備：OllamaとLlama 3のインストール

まず、ローカルでLLMを実行できる環境を準備する必要があります。Ollamaは、複雑な設定なしに簡単なコマンドでLLMをインストールして実行できる優れたツールです。

公式サイト[ollama.com](https://ollama.com "Ollama公式サイト"){:target="_blank"}から、お使いのオペレーティングシステムに合ったインストーラーをダウンロードしてインストールします。

インストールが完了したら、ターミナルで次のコマンドを実行し、最新のLlama 3 8Bモデルをダウンロードします。Llama 3 8Bモデルは、一般的な開発者向けノートPCでも比較的に快適に動作し、コード関連のタスクで良好なパフォーマンスを発揮します。

```bash
# Llama 3 8Bモデルをローカルにダウンロードします。
ollama pull llama3
```

モデルのダウンロードが完了したら、`ollama list`コマンドでインストール済みのモデル一覧を確認できます。

## 中核ロジック：Python CLIスクリプトの設計

それでは、Pythonでコードファイルを読み込み、Ollamaで実行中のLlama 3モデルにレビューを依頼するCLIスクリプトを作成してみましょう。

### 1. プロジェクト構造と依存関係のインストール

シンプルな構造から始めます。必要なのは`review.py`というファイル1つだけです。スクリプトの実行に必要な`ollama` Pythonライブラリをインストールします。

```bash
# Ollama Pythonクライアントライブラリをインストール
pip install ollama
```

### 2. CLIスクリプトの作成（`review.py`）

ユーザーがターミナルで`python review.py <ファイル名>`という形式で簡単に実行できるよう、`argparse`を使用してファイルパスを引数として受け取ります。

```python
# review.py

import ollama
import argparse
import sys

# コードレビューのためのシステムプロンプトを定義
# モデルがどのような役割を果たすべきかを明確に指示します。
SYSTEM_PROMPT = """
You are an expert software developer acting as a code reviewer.
Your task is to provide a constructive and concise code review.
Focus on the following aspects:
1.  **Logic and Bugs**: Identify potential logical errors, edge cases not handled, or bugs.
2.  **Clarity and Readability**: Suggest improvements for variable names, comments, and overall structure to make the code easier to understand.
3.  **Performance**: Point out potential performance bottlenecks and suggest optimizations.
4.  **Best Practices**: Check if the code follows common language-specific best practices and conventions.

Provide your feedback in a clear, bulleted list. Do not be overly verbose.
Start the review directly without any introductory phrases.
"""

def review_code(file_path: str):
    """
    指定されたファイルのコードを読み込み、Ollamaを通じてコードレビューを実行します。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # OllamaストリーミングAPIを呼び出す
        stream = ollama.chat(
            model='llama3',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f"Please review the following Python code:\n\n```python\n{code_content}\n```"},
            ],
            stream=True,
        )

        print(f"\n--- Code Review for {file_path} ---\n")
        # ストリーミング応答をリアルタイムで出力
        for chunk in stream:
            print(chunk['message']['content'], end='', flush=True)
        print("\n--- End of Review ---")

    except Exception as e:
        print(f"An error occurred during the API call: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform a code review on a given file using a local LLM with Ollama.")
    parser.add_argument("file", help="The path to the file you want to review.")
    args = parser.parse_args()
    
    review_code(args.file)

```

このスクリプトの核心は`SYSTEM_PROMPT`です。ここでLLMの役割を「専門のコードレビュアー」と明確に指定し、どのような観点（バグ、可読性、パフォーマンスなど）でコードを分析すべきか具体的な指示を与えます。これは、より一貫性のある質の高いレビュー結果を得るために非常に重要です。

## 実行と結果の分析

レビュー対象となる簡単なPythonのサンプルファイルを作成してみましょう。

**`example.py`**
```python
# ユーザーの名前と年齢を受け取って挨拶する関数
def great_user(name, age):
    # 年齢が18歳未満の場合は別のメッセージを出力
    if age < 18:
        msg = "Hello " + name + ", you are still young!"
    else:
        msg = "Hello " + name + ", welcome!"
    
    # メッセージを複数回出力して強調
    for i in range(5):
        print(msg)

# 関数のテスト
great_user("Alice", 25)
great_user("Bob", 15)
```

では、ターミナルで先ほど作成したレビュースクリプトを実行します。

```bash
python review.py example.py
```

しばらくすると、Llama 3モデルが生成したコードレビューの結果がストリーミング形式で出力されます。

```
--- Code Review for example.py ---

*   **Clarity and Readability**: The function name `great_user` could be more descriptive, perhaps `greet_user` would be clearer. Using f-strings for string formatting is more modern and readable than string concatenation (e.g., `f"Hello {name}, welcome!"`).
*   **Best Practices**: The magic number `18` could be defined as a constant, like `LEGAL_ADULT_AGE = 18`, to improve maintainability.
*   **Logic and Bugs**: The loop `for i in range(5):` prints the same message five times. This might not be the intended behavior. If the goal is emphasis, a comment explaining why would be helpful. Otherwise, it seems redundant.
*   **Performance**: For this simple function, performance is not a concern. However, in a real-world scenario, printing inside a loop within a function that returns a value can be an undesirable side effect. It's often better to return the message and let the caller handle the printing.

--- End of Review ---
```

結果からわかるように、ローカルLLMは関数名のタイポの指摘、f-stringの使用推奨、マジックナンバーの問題、不要なループなど、かなり有意義なフィードバックを提供しています。

## 実用性を高めるための考察：限界とトレードオフ

このツールは確かに便利ですが、実務にすぐに適用する前に、いくつかの明確な限界点を認識しておく必要があります。

-   **コンテキスト不足**: このスクリプトは単一のファイルのみを分析します。プロジェクト全体の構造、他のファイルとの依存関係、ビジネスロジック全体を全く理解していません。したがって、アーキテクチャレベルのレビューや複雑なロジックのエラーを見つけ出すことには限界があります。
-   **モデルの性能**: Llama 3 8Bのような小型モデルは、GPT-4やClaude 3 Opusのような最上位モデルに比べてコードの理解度や推論能力が劣る可能性があります。時には不正確であったり、ありきたりなフィードバックを生成することもあります。より大きなモデル（例：`llama3:70b`）を使用すると品質は向上しますが、より高いスペックのハードウェア（特にVRAM）が必要になります。
-   **ハルシネーション（幻覚）**: すべてのLLMと同様に、ローカルモデルも事実でない内容をもっともらしく作り出すことがあります。「このコードはXライブラリの最新バージョンと互換性がありません」といった具体的な主張は、必ず自分で確認する必要があります。
-   **結果の非一貫性**: 同じコードを複数回レビューしても、少しずつ異なる結果が出ることがあります。

## 結論

Ollamaを活用したローカルコードレビューCLIは、外部サービスへの依存なく、セキュリティとコストの問題を解決しながらAIの助けを借りられる素晴らしい方法です。特に、機密性の高いコードを扱う場合や、簡単なコードスタイルに関する一次レビューを自動化する用途で非常に役立ちます。

このツールは、熟練した同僚開発者による深いレビューを代替することはできませんが、レビューを依頼する前に自らコードを改善するための「セルフチェック」ツールや、レビュアーの負担を軽減する「補助手段」として十分な価値があります。さらに、Gitのpre-commitフックと連携させてコミット前に自動でレビューを実行するようにしたり、チームのコーディング規約をプロンプトにさらに具体的に明記して、カスタマイズされたレビュアーに発展させたりすることもできるでしょう。

### 参考資料
- [Ollama 公式サイト](https://ollama.com "Ollama"){:target="_blank"}
- [Ollama Python Library (GitHub)](https://github.com/ollama/ollama-python "ollama-python on GitHub"){:target="_blank"}