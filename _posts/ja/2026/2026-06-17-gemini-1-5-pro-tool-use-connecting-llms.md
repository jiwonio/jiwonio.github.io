---
layout: post
title: Gemini 1.5 Pro Tool Use：LLMと外部世界を接続する
slug: gemini-1-5-pro-tool-use-connecting-llms
date: 2026-06-17 10:34:31 +0900
categories:
- AI
tags:
- Gemini
- LLM
- Tool Use
- Function Calling
description: Gemini 1.5 ProのTool Use（関数呼び出し）機能を実務に適用する方法を学びます。モデルが外部関数を認識し、呼び出しをリクエストするプロセス、設定、そして潜在的な失敗例について説明します。
image: /uploads/gemini-1-5-pro-tool-use-connecting-llms/thumbnail.webp
lang: ja
translation_key: gemini-1-5-pro-tool-use-connecting-llms
permalink: /ja/posts/gemini-1-5-pro-tool-use-connecting-llms/
post_type: deep-dive
ai_generated: true
updated: 2026-06-17 10:34:31 +0900
---
大規模言語モデル（LLM）は、膨大なテキストデータに基づいて驚くべき言語能力を発揮します。しかし、LLMはそれ自体では外部世界から切り離されています。リアルタイムの株価情報を取得したり、データベースにクエリを実行したり、メールを送信したりといったタスクを直接実行することはできません。この限界を克服する核心技術が、まさに「Tool Use」、すなわち関数呼び出し（Function Calling）です。

この記事では、GoogleのGemini 1.5 Proモデルを中心に、Tool Useの概念と動作原理を説明します。単にAPIを呼び出すだけでなく、実務で直面しうるトレードオフや潜在的な失敗例まで深く掘り下げます。これにより、LLMを単なるチャットボットではなく、実際のタスクを遂行するエージェントへと変える第一歩を踏み出すことができるでしょう。

<!--more-->
![Gemini 1.5 Pro Tool Use: LLMと外部世界を接続する](/uploads/gemini-1-5-pro-tool-use-connecting-llms/thumbnail.webp "Gemini 1.5 Pro Tool Use: LLMと外部世界を接続する")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## LLMと外部世界の断絶、そしてTool Use

LLMは、学習データにない最新情報や非公開データにアクセスできません。「今日のソウルの天気は？」と尋ねても、モデルはリアルタイムデータを照会できないため、「私はリアルタイムの情報を確認できません」と答えるだけです。

Tool Useは、この問題を解決します。開発者があらかじめ定義した関数（ツール）のリストをLLMに提供すると、モデルはユーザーの質問の意図を把握し、最も適切な関数とそのために必要な引数を見つけ出します。重要な点は、LLMが直接関数を*実行*するのではなく、どの関数をどの引数で実行すべきかを構造化されたデータ（JSON）で*リクエスト*するということです。実際の実行は私たちのコードで行われ、その結果を再びLLMに渡して最終的な回答を生成させます。

## Tool Useの動作原理：対話型の委任

Tool Useは、LLMと私たちのコードとの間の洗練された対話プロセスです。全体の流れは以下の通りです。

1.  **ユーザーの質問と関数仕様の伝達**：ユーザーのプロンプトと共に、私たちが定義した「利用可能なツール」のリスト（関数名、説明、パラメータ情報）をモデルに渡します。
2.  **モデルの判断と関数呼び出しリクエスト**：モデルはプロンプトを分析し、定義されたツールの中に現在のリクエストを処理するのに役立つものがあるか判断します。もしあれば、該当する関数名と必要な引数が含まれたJSONオブジェクトを返します。
3.  **私たちのコードによる関数実行**：私たちのコードは、モデルが返したJSONを解析して実際のロジック（例：天気情報の照会）を実行します。
4.  **実行結果の返却**：関数の実行結果を再度モデルに渡します。
5.  **最終的な回答の生成**：モデルは関数の実行結果を基に、ユーザーに自然な言語で最終的な回答を生成して伝えます。

このプロセスは、LLMが「推論エンジン」として、私たちのコードが「実行機」として役割を分担する協調モデルです。

## PythonでGemini Tool Useを実装する

では、実際のコードを使ってGemini 1.5 ProのTool Useを実装してみましょう。`google-generativeai`ライブラリが必要です。

### 1. 事前準備

まず、必要なライブラリをインストールし、APIキーを設定します。

```python
# 必要なライブラリをインストール
# pip install google-generativeai

import os
import google.generativeai as genai

# APIキーの設定
# 実際のコードでは環境変数やシークレット管理ツールを使用してください。
genai.configure(api_key="<YOUR_GEMINI_API_KEY>")
```

### 2. 実行する関数の定義

モデルが使用できる簡単な関数を2つ定義します。1つは天気情報を、もう1つは株価を返す仮想の関数です。

```python
def get_current_weather(location: str, unit: str = "celsius"):
    """指定された場所の現在の天気情報を返します。"""
    # 実際には外部の天気APIを呼び出すロジックが入ります。
    if "seoul" in location.lower():
        return {"location": "Seoul", "temperature": "15", "unit": unit}
    elif "tokyo" in location.lower():
        return {"location": "Tokyo", "temperature": "18", "unit": unit}
    else:
        return {"location": location, "temperature": "unknown"}

def get_stock_price(ticker_symbol: str):
    """指定されたティッカーシンボルの現在の株価を返します。"""
    # 実際には外部の株価情報APIを呼び出すロジックが入ります。
    if ticker_symbol.upper() == "GOOG":
        return {"symbol": "GOOG", "price": "175.50", "currency": "USD"}
    elif ticker_symbol.upper() == "AAPL":
        return {"symbol": "AAPL", "price": "190.20", "currency": "USD"}
    else:
        return {"symbol": ticker_symbol, "price": "not found"}
```

### 3. モデルに関数仕様を渡す

Geminiモデルを初期化し、上で定義した関数を「ツール」として登録します。

```python
# 使用する関数を辞書にマッピング
available_tools = {
    "get_current_weather": get_current_weather,
    "get_stock_price": get_stock_price,
}

# モデルの初期化時に、使用する関数のリストを渡す
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    tools=list(available_tools.values())
)
```

### 4. モデルの呼び出しと応答処理

ユーザーの質問で対話を開始し、モデルの応答を処理する全体のロジックです。

```python
# 対話を開始
chat = model.start_chat()

# 最初の質問
prompt = "ソウルの天気とGoogleの株価を教えて。温度は華氏でお願い。"
response = chat.send_message(prompt)

# モデルが関数呼び出しをリクエストしたか確認
function_calls = response.candidates[0].content.parts[0].function_call
if function_calls:
    print(f"Model wants to call functions: {function_calls}")

    # 複数の関数呼び出しを順次処理
    for function_call in function_calls:
        function_name = function_call.name
        function_args = function_call.args

        # 1. 呼び出す関数を検索
        function_to_call = available_tools.get(function_name)
        if not function_to_call:
            print(f"Error: Function '{function_name}' not found.")
            continue

        # 2. 実際の関数を実行
        try:
            # ** 演算子で辞書をキーワード引数として展開して渡す
            function_response = function_to_call(**function_args)
            print(f"Executed '{function_name}' with args {function_args}, got: {function_response}")

            # 3. 実行結果を再度モデルに渡す
            response = chat.send_message(
                part=genai.Part(
                    function_response={
                        "name": function_name,
                        "response": function_response,
                    }
                ),
            )
        except Exception as e:
            print(f"Error executing function {function_name}: {e}")
            # エラー発生時、エラー情報をモデルに渡すこともできます。

# 最終的な回答を出力
final_response = response.candidates[0].content.parts[0].text
print(f"\nFinal Answer:\n{final_response}")
```

上記のコードを実行すると、モデルは`get_current_weather`と`get_stock_price`関数をそれぞれ適切な引数（`location='Seoul', unit='fahrenheit'`、`ticker_symbol='GOOG'`）で呼び出すようリクエストを返します。私たちのコードがこのリクエストに従って関数を実行し、結果を再度渡すと、モデルはその情報を統合して最終的な回答を生成します。

## 実務適用時の考慮事項と失敗例

Tool Useは強力ですが、実務に適用する際には、いくつかの事項を慎重に考慮する必要があります。

### 明確な関数仕様の重要性

モデルは、関数の名前とdocstring（説明）を見て、どの関数を選択するかを決定します。説明が曖昧であったり、パラメータ名が直感的でなかったりすると、モデルは見当違いの関数を選択したり、引数を誤って推論したりする可能性があります。

-   **失敗例**：`get_data(source, query)`のような一般的な名前と説明ではなく、`get_user_profile_by_email(email_address)`のように具体的で明確な名前と説明を使用すべきです。
-   **ヒント**：関数のdocstringには、「何をする関数か？」と「各パラメータは何を意味するか？」についての答えを明確に含めるべきです。

### 戻り値の処理とエラー報告

私たちが実行した関数が失敗することもあります。外部サービスがダウンしていたり、データベースで目的の結果が見つからなかったりするかもしれません。このとき、`None`を返したり、例外を発生させて終了したりしてはいけません。

-   **失敗例**：天気APIの呼び出しに失敗したときに単に`None`を返すと、モデルは情報がないという事実を認識できず、以前の対話内容に基づいて幻覚（ハルシネーション）を引き起こす可能性があります。
-   **ヒント**：関数の実行が失敗した場合、失敗の原因が含まれた明確なメッセージ（例：`{"error": "API rate limit exceeded"}`）をモデルに返すべきです。そうすれば、モデルは「申し訳ありませんが、現在天気情報の取得に失敗しました。しばらくしてから再度お試しください」のように、ユーザーに状況を正確に伝えることができます。

### セキュリティ：信頼できるコードのみを実行

LLMが返す関数名と引数をそのまま`eval()`のような危険な関数に渡しては絶対にいけません。モデルが返すのはあくまで「リクエスト」であり、どのコードを実行するかの最終的な決定権は私たちにあります。

-   **ヒント**：あらかじめ定義され、安全性が検証された関数のリスト（許可リスト）を作成し、モデルがリクエストした関数名がこのリストにある場合にのみ実行するように制限すべきです。

### 遅延時間とコスト

Tool Useは、最低でも2回のLLM呼び出し（質問 → 関数呼び出しリクエスト → 結果の伝達 → 最終回答）を必要とします。これは応答遅延時間を増加させ、API呼び出しコストを高める要因となります。したがって、すべてのインタラクションでTool Useを乱用するのではなく、外部情報やタスクが必須の場合にのみ選択的に使用すべきです。

## 結論

Gemini 1.5 ProのTool Use機能は、LLMの限界を超え、現実世界と相互作用するインテリジェントエージェントを構築するための強力な架け橋となります。単に機能を使用するだけでなく、明確な仕様、堅牢なエラー処理、セキュリティ、コストといった実務的な観点を併せて考慮することで、そのポテンシャルを最大限に発揮することができます。この記事で扱った原理とコードを基に、皆さんのサービスに新たな可能性を加えてみてください。

### 参考文献
- [Google AI for Developers - Tool use](https://ai.google.dev/docs/function_calling "Gemini Function Calling Official Documentation"){:target="_blank"}
- [GoogleCloudPlatform/generative-ai-samples on GitHub](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/function-calling/intro_function_calling.ipynb "Gemini Function Calling Examples"){:target="_blank"}
---