---
layout: post
title: 本番環境LLMアプリケーションの監視：LangSmithを活用した完全なオブザーバビリティ（Observability）構築ガイド
slug: llm-application-monitoring-observability-with-langsmith
date: 2026-06-15 10:22:24 +0900
categories:
- AI
- DevOps
tags:
- LLMOps
- Observability
- LangSmith
- Monitoring
- LLM
- LangChain
- AI
description: LLMアプリケーションの「ブラックボックス」な運用に疲れていませんか？本ガイドでは、LangSmithを活用してトークンコスト、遅延、実行トレースなど、本番環境に不可欠なLLMオブザーバビリティシステムを構築する実践的な方法を解説します。単なるロギングを超え、AIのパフォーマンスを最適化しましょう。
image: /uploads/llm-application-monitoring-observability-with-langsmith/thumbnail.webp
lang: ja
translation_key: llm-application-monitoring-observability-with-langsmith
post_type: deep-dive
permalink: /ja/posts/llm-application-monitoring-observability-with-langsmith/
ai_generated: true
---
AIベースのアプリケーション、特にLLM（大規模言語モデル）を活用するシステムは、その複雑な内部動作のため、しばしば「ブラックボックス」のように感じられます。ユーザーのプロンプトが入力され、もっともらしい結果が出力されますが、その過程で何が起こっているのか、コストはどれくらいかかっているのか、どこでボトルネックが発生しているのかを把握するのは非常に困難です。従来のサーバー監視方法では、CPUやメモリ使用量程度しかわからず、LLMアプリケーションの核心である「品質」「コスト」「遅延」を追跡することはできません。

このような問題を解決するために、**LLMOps（LLM Operations）**の中核要素である**オブザーバビリティ（Observability、観測可能性）**の確保が不可欠です。LLMオブザーバビリティは、単にログを記録することを超え、モデルのすべてのリクエストとレスポンス、内部の処理プロセスを詳細に追跡し、パフォーマンス指標を可視化し、ユーザーフィードバックを収集することで、AIアプリケーションをデータ駆動で改善できるようにするエンジニアリングの実践です。優れたオブザーバビリティシステムがなければ、問題発生時に原因を推測に頼らざるを得ず、コスト最適化やパフォーマンス改善はほぼ不可能です。

本記事では、LangChain開発チームが作成したLLMアプリケーション開発プラットフォームである**LangSmith**を活用し、本番環境でLLMアプリケーションのオブザーバビリティを完全に構築する方法をステップバイステップで詳しく解説します。LangSmithを通じて、複雑なRAG（Retrieval-Augmented Generation）パイプラインやAIエージェントの実行過程を追跡し、トークンコストと遅延を分析し、品質評価を自動化する実践的なノウハウをぜひ身につけてください。

<!--more-->
![本番環境LLMアプリケーションの監視：LangSmithを活用した完全なオブザーバビリティ（Observability）構築ガイド](/uploads/llm-application-monitoring-observability-with-langsmith/thumbnail.webp "本番環境LLMアプリケーションの監視：LangSmithを活用した完全なオブザーバビリティ（Observability）構築ガイド")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## LLMアプリケーションにおけるオブザーバビリティの3つの柱

LLMアプリケーションの状態を完全に把握するためには、従来のモニタリングを超えた3つの核心的な要素が必要です。これらは互いに有機的に連携し、システムの内部動作に関する深い洞察を提供します。

### 1. トレース (Tracing)

トレースは、LLMアプリケーションで発生した単一リクエストのライフサイクル全体を可視化する技術です。ユーザーの入力から始まり、内部のすべてのコンポーネント（LLM呼び出し、データベース検索、APIリクエストなど）を経て、最終的なレスポンスが生成されるまでの過程を、まるでフローチャートのように示します。

例えば、RAGパイプラインの場合、トレースを通じて次のような過程を一目で把握できます。
- **入力 (Input):** ユーザーが入力した質問
- **文書検索 (Retriever):** ベクトルDBからどの文書をどの検索クエリで取得したか？
- **プロンプト生成 (Prompt Generation):** 検索された文脈と質問を組み合わせて、最終的なプロンプトをどのように作成したか？
- **LLM呼び出し (LLM Call):** 最終的なプロンプトをどのモデル（例: `gpt-4-turbo`）に渡したか？
- **出力 (Output):** モデルが生成した最終的な回答は何か？

このような詳細なトレース情報は、**「なぜAIはこのような回答をしたのか？」**という問いに対する根本的な原因を見つけ出し、デバッグする上で決定的な役割を果たします。

### 2. メトリクス (Metrics)

メトリクスは、システムのパフォーマンスとコストを定量的に測定する核心的な指標です。LLMアプリケーションでは、特に次のようなメトリクスが重要です。

- **遅延 (Latency):** リクエスト開始から最終的なレスポンスまでの所要時間。特に、最初のトークンが生成されるまでの時間（Time to First Token）は、ユーザーエクスペリエンスに直接影響します。
- **コスト (Cost) / トークン使用量 (Token Usage):** 各LLM呼び出しで使用されたプロンプトトークンと生成されたトークンの数。これはAPIコストに直結するため、必ず追跡し最適化する必要があります。
- **エラー率 (Error Rate):** LLM API呼び出しの失敗、タイムアウト、無効なレスポンス形式など、さまざまな種類のエラー発生頻度。
- **スループット (Throughput):** 単位時間あたりに処理するリクエストの数。

これらのメトリクスをダッシュボードで可視化し、しきい値ベースのアラートを設定することで、システムの異常の兆候を早期に発見し、迅速に対応できます。

### 3. フィードバック (Feedback)

フィードバックは、モデルが生成した結果物の「品質」を測定する最も重要な手段です。どんなに速く、安価に回答を生成しても、その内容が不正確であったり、ユーザーの意図と合っていなければ意味がありません。

フィードバックは様々な形で収集できます。
- **ユーザーフィードバック:** チャットボットインターフェースの「いいね/よくないね」ボタン、星評価、コメントなど。
- **プログラムによるフィードバック:** 生成された回答が特定の形式（例: JSON）に準拠しているか、内部のビジネスロジック検証を通過するかなどをコードで評価。
- **専門家による評価:** 内部の運用チームや専門家が直接回答の品質を評価し、スコアを付けます。

収集されたフィードバックデータは、特定のプロンプトの問題点を特定したり、将来のモデル性能評価（Evaluation）やファインチューニング（Fine-tuning）のための貴重なデータセットとして活用されます。

## LangSmithを活用した実践的な監視システムの構築

それでは、LangSmithを使って上記で説明したオブザーバビリティの3つの柱を実際に構築してみましょう。LangSmithは環境変数を設定するだけで、既存のLangChainやOpenAI SDKのコードに完全に統合できるため、非常に便利です。

### 1. 環境設定とAPIキーの発行

まず、[LangSmith公式ウェブサイト](https://smith.langchain.com/ "LangSmith Website"){:target="_blank"}にアクセスしてサインアップします。その後、**Settings > API Keys**メニューで新しいAPIキーを生成します。

生成されたキーは非常に機密性の高い情報ですので、コードに直接ハードコーディングせず、必ず環境変数として管理してください。プロジェクトのルートディレクトリに`.env`ファイルを作成し、以下のようにキーを追加します。

**.env**
```env
# [🚨 セキュリティ注意] 実際のキー値に置き換え、このファイルは.gitignoreに追加してください。
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="<YOUR_LANGCHAIN_API_KEY>"
LANGCHAIN_PROJECT="My-AI-Project" # プロジェクトごとにトレースをグループ化します。

OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
```

- `LANGCHAIN_TRACING_V2="true"`: LangSmithのトレース機能を有効にするための核心的な設定です。
- `LANGCHAIN_ENDPOINT`: LangSmith APIサーバーのアドレスです。
- `LANGCHAIN_API_KEY`: 発行されたLangSmith APIキーです。
- `LANGCHAIN_PROJECT`: 生成されるトレースをグループ化するプロジェクト名です。指定しない場合は'default'に設定されます。

### 2. PythonアプリケーションへのLangSmith連携

次に、PythonコードでLangSmithを連携させてみましょう。まず必要なライブラリをインストールします。

```bash
pip install openai langchain langchain-openai python-dotenv
```

環境変数をロードし、OpenAIクライアントを使用する簡単なコードを作成します。

**simple_llm_call.py**
```python
import os
from openai import OpenAI
from dotenv import load_dotenv

# .envファイルから環境変数をロード
load_dotenv()

# 環境変数を設定するだけで、LangSmithが自動的にOpenAIの呼び出しを追跡します。
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_question(question):
    print("質問を開始します...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": question}],
        temperature=0.7,
    )
    answer = response.choices[0].message.content
    print("回答:", answer)
    return answer

if __name__ == "__main__":
    ask_question("LLMOpsにおけるオブザーバビリティの重要性について説明して。")
```

上記のコードを実行するだけで、`LANGCHAIN_TRACING_V2`環境変数のおかげで、OpenAI API呼び出しに関するすべての情報（プロンプト、レスポンス、トークン使用量、遅延など）が自動的にLangSmithの'My-AI-Project'プロジェクトに記録されます。

次に、LangChainを使用する、より複雑なRAGの例を見てみましょう。

**rag_chain_example.py**
```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# .envファイルから環境変数をロード
load_dotenv()

# ダミーのRetriever（実際にはVectorDBを使用）
def fake_retriever(query: str) -> str:
    print(f"'{query}'に関する文書を検索します...")
    # 実際の実装ではここでVectorDBを照会します。
    return "LangSmithはLLMアプリケーションのトレース、モニタリング、評価のためのプラットフォームです。"

# LangChain Expression Language (LCEL) を使用したRAG Chainの定義
template = """
あなたは質問に答えるAIアシスタントです。
提供されたコンテキストを使用して質問に答えてください。

コンテキスト: {context}

質問: {question}

回答:
"""
prompt = ChatPromptTemplate.from_template(template)
model = ChatOpenAI(model="gpt-4-turbo-preview")

rag_chain = (
    {"context": fake_retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

if __name__ == "__main__":
    print("RAG Chainを実行します...")
    result = rag_chain.invoke("LangSmithとは何ですか？")
    print("最終結果:", result)
```

このコードを実行すると、LangSmithのダッシュボードで`rag_chain`の実行フロー全体を視覚的に確認できます。`fake_retriever`関数の呼び出し、`prompt`の生成、`model`の呼び出しなど、各ステップの入力、出力、所要時間をすべて分解して見ることができるため、デバッグが非常に容易になります。

### 3. LangSmithダッシュボードの探索

コードを実行した後、LangSmithのダッシュボードにアクセスすると、収集されたデータを様々な方法で探索できます。

- **Projects/Tracesビュー:** 実行されたすべてのリクエストのリストが表示されます。各項目をクリックすると、そのリクエストの詳細なトレース情報を見ることができます。RAGの例の場合、retrieverとLLMの呼び出しが階層的に表示され、パイプライン全体の流れを直感的に理解できます。
- **Monitoringタブ:** プロジェクト全体の主要メトリクス（遅延、トークンコスト、エラー率など）を時系列で表示するダッシュボードです。これにより、「先週から急にAPIコストが急増した」とか「特定の時間帯に遅延が長くなる」といった問題を即座に把握できます。

## 高度な活用：パフォーマンス最適化と評価(Evals)

LangSmithは、単なるロギングやモニタリングにとどまらず、アプリケーションを改善するために必要な強力な機能を提供します。

### 1. ユーザーフィードバックのプログラムによる記録

アプリケーションでユーザーが「いいね/よくないね」ボタンを押した際、そのフィードバックを特定のLLM実行（run）に関連付けてLangSmithに記録できます。

```python
from langsmith import Client

client = Client()

# ... LLM呼び出し後にrun_idを取得したと仮定 ...
# rag_chain.invoke()はrun_idを含むオブジェクトを返すように設定できます。
# run_idの例 (実際にはinvokeの結果から抽出)
example_run_id = "a1b2c3d4-e5f6-..." 

# ユーザーが「いいね」を押した場合
client.create_feedback(
    run_id=example_run_id,
    key="user_score",  # フィードバックの種類を示すキー
    score=1,           # 1: 良い, 0: 悪い
    comment="回答が非常に正確で役立ちました。"
)

# ユーザーが「よくないね」を押した場合
client.create_feedback(
    run_id=example_run_id,
    key="user_score",
    score=0,
    comment="質問と関係のない回答をします。"
)
```
このように収集されたフィードバックは、LangSmithのダッシュボードで各トレースと共に表示され、「ユーザーが好まない回答は、主にどのような種類の質問で発生するのか？」を分析するのに役立ちます。

### 2. データセットの作成と評価の実行

運用中に見つかった重要な成功/失敗事例を、LangSmithのUIから「データセット」として保存できます。例えば、「回答が不正確だった事例集」データセットを作成できます。

このように作成したデータセットを基準に、新しいプロンプトやモデルのパフォーマンスを自動的に評価できます。

```python
from langsmith.evaluation import evaluate

# ... 事前に定義したrag_chain ...

# 「回答が不正確だった事例集」データセットに対してrag_chainのパフォーマンスを評価
# LangSmithは正解(ground truth)とモデルの回答を比較する様々な評価者(evaluator)を提供します。
evaluation_results = evaluate(
    rag_chain.invoke, # 評価対象の関数
    data="incorrect-answers-dataset", # LangSmithに保存されたデータセット名
    # 必要に応じてカスタム評価者を追加可能
)
```
`evaluate`関数は、データセットの各項目に対して`rag_chain`を実行し、その結果を事前に定義された基準（例: 正解との類似度）に従って採点し、レポートを生成します。これにより、プロンプトを修正した後にパフォーマンスが実際に改善されたかどうかを客観的に検証できます。

## 結論：オブザーバビリティは「あれば良い」ではなく「必須」

LLMベースのAIアプリケーション開発は、一度作って終わりではなく、継続的な測定と改善が必要な旅です。LangSmithのようなオブザーバビリティツールは、この旅に不可欠な羅針盤の役割を果たします。推測や勘に頼ってプロンプトを修正し、問題を解決していた時代は終わり、今やデータとメトリクスに基づいてAIアプリケーションのパフォーマンス、コスト、品質を体系的に管理すべきです。

本ガイドで紹介した方法を通じて、LLMアプリケーションの内部を透明に可視化し、問題の根本原因を迅速に特定し、最終的にはユーザーにより良い価値を提供するスマートなAIシステムを構築されることを願っています。**本番環境でAIを運用するなら、オブザーバビリティシステムは選択肢ではなく、必須です。**

### 参考文献
- [LangSmith Official Documentation](https://docs.smith.langchain.com/ "LangSmith Official Documentation"){:target="_blank"}
- [LangChain Python Documentation](https://python.langchain.com/docs/get_started/introduction "LangChain Python Documentation"){:target="_blank"}
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference "OpenAI API Reference"){:target="_blank"}
---