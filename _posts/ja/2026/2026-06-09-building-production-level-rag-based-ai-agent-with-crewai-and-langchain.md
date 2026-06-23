---
layout: post
title: プロダクションレベルのRAGベースAIエージェント構築：CrewAIとLangChainを活用した自律リサーチ自動化システム
slug: building-production-level-rag-based-ai-agent-with-crewai-and-langchain
date: 2026-06-09 15:10:01 +0900
categories:
- DevOps
- Backend
tags:
- AI
- LLM
- RAG
- CrewAI
- LangChain
- Agent
- Python
description: CrewAIとLangChainを活用し、本番環境で動作するRAGベースAIエージェントを構築する方法を深掘りします。自律リサーチ自動化システムのアーキテクチャ、実際のコード実装、パフォーマンス最適化、そして運用のベストプラクティスまで、「実践的なノウハウ」を網羅的に解説します。
image: /uploads/building-production-level-rag-based-ai-agent-with-crewai-and-langchain/thumbnail.webp
lang: ja
translation_key: building-production-level-rag-based-ai-agent-with-crewai-and-langchain
post_type: deep-dive
permalink: /ja/posts/building-production-level-rag-based-ai-agent-with-crewai-and-langchain/
---
単純な質問に答えるチャットボットを超え、複数段階の複雑なタスクを自律的に実行するAIシステムへの要求が高まっています。例えば、「最新のAI半導体市場の動向」に関するリサーチを任せると、AIが自らWebを検索し、重要な情報を要約し、競合他社を分析して最終的なレポートを作成する、といった具合です。これこそが**AIエージェント（AI Agent）**の核心的な概念であり、これを実現する最も強力な技術の一つが、**RAG（Retrieval-Augmented Generation）**と組み合わせたマルチエージェントシステムです。

この記事では、単なるRAGのチュートリアルにとどまらず、本番環境で安定して運用可能な**RAGベースの自律リサーチAIエージェント**を構築する全プロセスを詳細に解説します。役割ベースの協調型エージェントフレームワークである**CrewAI**を中心に、**LangChain**を活用して強力なRAGベースの検索ツールを実装し、複数のエージェントが協力して一つの目標を達成する、洗練されたワークフローを設計します。本ガイドを通じて、読者の皆さんは単なるLLM APIの呼び出しを超え、実際に動作する「AIチーム」を作るための実践的なノウハウを得られるでしょう。

<!--more-->
![プロダクションレベルのRAGベースAIエージェント構築：CrewAIとLangChainを活用した自律リサーチ自動化システム](/uploads/building-production-level-rag-based-ai-agent-with-crewai-and-langchain/thumbnail.webp "プロダクションレベルのRAGベースAIエージェント構築：CrewAIとLangChainを活用した自律リサーチ自動化システム")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI生成画像</small>
</p>
-----

## 導入の背景と問題定義

既存の多くのLLMベースのアプリケーションは、ユーザーの単一の質問に対して回答を生成するという一方向のコミュニケーションに留まっています。RAGを導入して外部データベースの情報を参照するようにしても、依然として「受動的な」情報提供者という役割から抜け出すことは困難です。しかし、実際のビジネス上の問題は、複数段階の情報収集、分析、統合、そして最終的な成果物の導出という複雑なプロセスを必要とします。

例えば、新規事業企画のために競合他社の分析レポートを作成する業務を考えてみましょう。このプロセスには、以下のような複雑なタスクが含まれます。

1.  **情報収集：** 最新のニュース記事、市場レポート、競合他社の公式発表資料など、様々なソースを検索・収集します。
2.  **情報分析：** 収集した資料から核心となる情報を抽出し、各競合他社の強み、弱み、機会、脅威（SWOT）を分析します。
3.  **統合と要約：** 分析内容を基に市場全体のトレンドを把握し、実行可能なインサイトを導き出します。
4.  **レポート作成：** 最終的に、構造化された形式のレポートを作成します。

このような多段階のプロセスを単一のLLMプロンプトで処理することはほぼ不可能であり、結果の品質も保証できません。まさにこの点において、**自律AIエージェント**、特に複数のエージェントが協調する**マルチエージェントシステム**の必要性が高まります。各エージェントに特定の役割（リサーチャー、アナリストなど）とツール（Web検索、データベース照会）を与え、彼らが協力して共通の目標を達成するように仕向けるのです。

本稿では、**CrewAI**と**LangChain**を用いてこのような「AI専門家チーム」を構築し、**RAG**を通じて彼らの作業品質を最大化する実質的な方法を提示します。

## 主要なアーキテクチャと原理

私たちが構築するシステムは、「AI専門家チーム」が協力してリサーチレポートを作成するプロセスを模倣します。このシステムの主要な構成要素は、**CrewAI**の`Agent`、`Task`、`Tool`、そして`Crew`です。

### 1. CrewAI：役割ベースの協調型エージェントフレームワーク

CrewAIは、自律AIエージェントが役割（Role）に基づいて協調するように設計されたフレームワークです。実際の会社のチームのように、各エージェントは独自の専門分野、目標、そして利用可能なツールを持っています。

-   **Agent：** LLMを頭脳として使用する実行者です。`role`（役割）、`goal`（目標）、`backstory`（背景設定）、`tools`（利用可能なツール）などの属性を通じてアイデンティティが定義されます。
-   **Task：** エージェントが実行すべき具体的な作業単位です。明確な`description`（説明）と`expected_output`（期待される成果物）を通じて、タスクの成功基準を提示します。
-   **Tool：** エージェントが外部の世界と相互作用したり、特定のタスクを実行するために使用する関数です。Web検索、データベース照会、API呼び出しなどがこれにあたります。**RAGパイプライン**は、このシステムで最も重要な`Tool`の一つとなります。
-   **Crew：** エージェントとタスクをまとめ、全体のワークフローを管理・実行するオーケストレーターです。

### 2. RAGベースのTool：エージェントの知識強化

AIエージェントが信頼性の高いタスクを遂行するためには、最新の情報や社内独自のデータにアクセスできる必要があります。**RAG（Retrieval-Augmented Generation）**は、まさにこの問題を解決します。

私たちはLangChainを活用して、2種類のRAGベースの検索`Tool`を実装し、エージェントに提供します。

1.  **リアルタイムWeb検索ツール：** `DuckDuckGoSearchRunTool`などを活用し、エージェントが最新情報をリアルタイムでWebから検索できるようにします。
2.  **内部ドキュメント検索ツール（Vector Store）：** 事前に構築された内部ドキュメントや特定のトピックの資料を埋め込み（Embedding）、Vector Store（例：FAISS、ChromaDB）に保存します。エージェントはこの`Tool`を使い、LLMの事前学習データにはない、ドメイン特化の情報を正確に見つけ出すことができます。

### 3. システムアーキテクチャ

私たちが構築する自律リサーチシステムは、以下のようなアーキテクチャで構成されます。

| コンポーネント | 役割 | 主要技術 |
| :--- | :--- | :--- |
| **ユーザー** | リサーチのトピックを入力（例：「2024年第2四半期AIチップ市場の動向」） | - |
| **Crewオーケストレーター** | 全体のタスクフローを順次管理し、エージェント間で成果物を渡す | `CrewAI` |
| ┗ **エージェント1: シニアリサーチャー** | Webと内部ドキュメントを検索し、トピックに関連する全ての生データを収集 | `CrewAI Agent`, `LangChain Tools` |
| &nbsp;&nbsp;&nbsp;&nbsp;┗ **ツール1: Web検索** | リアルタイムのインターネット検索を実行 | `DuckDuckGoSearchRunTool` |
| &nbsp;&nbsp;&nbsp;&nbsp;┗ **ツール2: 内部ドキュメントRAG** | Vector Storeから関連ドキュメントを検索 | `LangChain`, `FAISS` |
| ┗ **エージェント2: 主席アナリスト** | リサーチャーが収集したデータを分析、統合し、核心的なインサイトを導き出してレポートの草案を作成 | `CrewAI Agent` |
| **最終成果物** | 構造化されたリサーチレポート | Markdown形式のテキスト |

この構造は、情報収集と分析・作成の役割を明確に分離し、各エージェントが自身の専門分野に集中することで、最終成果物の品質を最大化します。

## 実践的なコードと設定の深掘り

それでは、実際のPythonコードを通じて自律リサーチエージェントシステムを構築していきましょう。

### 1. 環境設定とライブラリのインストール

まず、必要なライブラリをインストールし、APIキーのための環境変数を設定します。

```bash
pip install crewai crewai-tools langchain-community langchain-openai duckduckgo-search python-dotenv faiss-cpu
```

プロジェクトのルートに`.env`ファイルを作成し、OpenAIのAPIキーを追加します。

```env
# .env
OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
```

### 2. RAGベースのツールを定義する

エージェントが使用するツールを最初に定義します。ここでは、リアルタイムのWeb検索と、仮想の内部ドキュメントを検索するRAGツールを作成します。

```python
import os
from dotenv import load_dotenv
from crewai_tools import tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool

# .envファイルから環境変数をロード
load_dotenv()

# Tool 1: DuckDuckGo Web検索ツール（CrewAIに標準で付属）
from crewai_tools import DuckDuckGoSearchRunTool
search_tool = DuckDuckGoSearchRunTool()

# Tool 2: 内部ドキュメント用のRAGパイプラインツールを作成
# 仮想の社内技術ブログ記事をロードしてVector Storeを構築
# 実際の本番環境では、DBやファイルシステムからドキュメントをロードする必要があります。
loader = WebBaseLoader("https://blog.langchain.dev/langchain-v0-1-0/")
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = splitter.split_documents(docs)
vectorstore = FAISS.from_documents(documents=splits, embedding=OpenAIEmbeddings())
retriever = vectorstore.as_retriever()

# LangChainのcreate_retriever_toolを使い、RetrieverをCrewAI Toolに変換
# このツールの名前と説明は、LLMがいつこのツールを使うべきか判断する上で非常に重要です。
retriever_tool = create_retriever_tool(
    retriever,
    "langchain_blog_retriever",
    "Search and return information about the LangChain v0.1.0 blog post. Use this tool for any questions related to LangChain's recent updates and features."
)
```

**[🚨 セキュリティ上の注意]** コードに直接APIキーをハードコーディングせず、`dotenv`を使用して環境変数から安全にロードすることが重要です。

### 3. エージェント（Agent）を定義する

次に、「シニアリサーチャー」と「主席アナリスト」の役割を担う2つのエージェントを定義します。

```python
from crewai import Agent
from langchain_openai import ChatOpenAI

# 使用するLLMモデルを設定（ここではGPT-4 Turbo）
llm = ChatOpenAI(model="gpt-4-turbo")

# エージェント1: シニアリサーチャー
researcher = Agent(
  role='Senior AI Research Analyst',
  goal='Uncover the latest advancements and trends in AI chip technology.',
  backstory="""You are a renowned AI Research Analyst with a knack for digging up
  in-depth information and identifying emerging patterns. You are an expert at
  using search tools to find the most relevant and up-to-date information.""",
  verbose=True,
  allow_delegation=False,
  tools=[search_tool, retriever_tool], # 上で定義したツールを割り当てる
  llm=llm
)

# エージェント2: シニアテクニカルライター（アナリスト役）
writer = Agent(
  role='Senior Technology Writer',
  goal='Craft a compelling and insightful report on the AI chip market trends.',
  backstory="""You are a celebrated Technology Writer, known for your ability to
  transform complex technical data into clear, engaging narratives. You can synthesize
  information from various sources to create a comprehensive report.""",
  verbose=True,
  allow_delegation=True, # 他のエージェントへの委任が可能（必要に応じて）
  llm=llm
)
```

`backstory`はエージェントのペルソナを設定し、より質の高い結果を生成させるための重要な要素です。

### 4. タスク（Task）を定義する

次に、各エージェントが実行するタスクを具体的に定義します。分析タスクは、リサーチタスクの成果物を`context`として受け取って実行されます。

```python
from crewai import Task

# タスク1: 情報収集
research_task = Task(
  description="""Conduct a comprehensive analysis of the latest AI chip market
  trends in 2024. Identify key players, emerging technologies, and major investments.
  Gather all relevant articles, press releases, and analysis reports.""",
  expected_output='A detailed summary of the top 5 key findings, including sources.',
  agent=researcher
)

# タスク2: レポート作成
write_report_task = Task(
  description="""Using the research findings, write a comprehensive report on the
  AI chip market. The report should have an introduction, sections for each key
  finding, and a concluding summary. It must be well-structured and easy to read.""",
  expected_output='A full, formatted report in Markdown format, at least 4 paragraphs long.',
  agent=writer,
  context=[research_task] # research_taskの出力を入力として使用
)
```

`context`を設定することでタスク間の依存関係を定義し、パイプラインのように順次タスクを処理できます。

### 5. クルー（Crew）の組み立てと実行

最後に、エージェントとタスクを`Crew`としてまとめ、全体のワークフローを実行します。

```python
from crewai import Crew, Process

# Crewの作成と実行
ai_chip_crew = Crew(
  agents=[researcher, writer],
  tasks=[research_task, write_report_task],
  process=Process.sequential, # シーケンシャルプロセスで実行
  verbose=2 # 実行過程を詳細にログ出力
)

# Crewの実行を開始！
result = ai_chip_crew.kickoff()

print("######################")
print("## Final Report")
print("######################")
print(result)

```

`kickoff()`メソッドを呼び出すと、CrewAIはまず`research_task`を`researcher`エージェントに割り当てます。`researcher`は自身の目標を達成するために`search_tool`と`retriever_tool`を繰り返し使用して情報を収集します。タスクが完了すると、その結果が`write_report_task`のコンテキストとして渡され、`writer`エージェントがそれを基に最終的なレポートを作成するという流れで進行します。

## パフォーマンス最適化とベストプラクティス

本番環境でAIエージェントを安定して運用するためには、いくつかの追加の考慮事項が必要です。

### 1. LLMモデルの選択とコスト管理

-   **モデルのトレードオフ：** GPT-4のような高性能モデルは結果の品質が高いですが、コストと遅延が大きくなります。一方、GPT-3.5やClaude 3 Sonnetのようなモデルはより高速で安価です。各エージェントの役割に応じて異なるモデルを割り当てることで、コストとパフォーマンスのバランスを取ることができます。（例：リサーチャーには高速なモデル、最終レポートの作成者には高品質なモデルを使用）
-   **キャッシング：** 同じ入力に対して繰り返しツールを呼び出したり、LLMの推論を行ったりするのを防ぐために、キャッシング層を導入することが重要です。CrewAIはデフォルトで簡単なキャッシングをサポートしており、LangChainの`LCEL`と組み合わせることで、より洗練されたキャッシング戦略を実装できます。

### 2. 堅牢なツールの設計

-   **明確な説明：** ツールの名前と説明（`description`）は、LLMがいつ、どのようにそのツールを使用すべきかを決定する唯一の手がかりです。曖昧な説明はエージェントのパフォーマンス低下に直結します。できるだけ具体的かつ明確に記述する必要があります。
-   **エラーハンドリングとリトライ：** 外部APIを呼び出すツールは、ネットワークエラーやAPIの制限などによって失敗する可能性があります。`tenacity`のようなライブラリを使用してリトライロジックを追加し、失敗した場合にはエージェントに明確なエラーメッセージを返すように設計する必要があります。

### 3. モニタリングとロギング

-   **詳細なロギング：** CrewAIの`verbose=2`オプションはデバッグに非常に役立ちますが、本番環境では構造化されたロギングが必要です。各エージェントの思考プロセス（Thought）、使用したツール、ツールの結果、最終的な回答などをJSON形式でロギングし、後の分析やパフォーマンス改善に活用すべきです。
-   **LLM Observability：** [LangSmith](https://www.langchain.com/langsmith "LangSmith"){:target="_blank"}や[Helicone](https://www.helicone.ai/ "Helicone"){:target="_blank"}のようなLLMオブザーバビリティプラットフォームと連携させることで、エージェントの動作過程を視覚的に追跡し、コスト、遅延、エラー発生率を体系的にモニタリングできます。

### 4. 人間の介入（Human-in-the-Loop）

完全な自律システムはまだ理想に近いものです。重要な決定を下す際や、エージェントがループに陥った場合に、人間の承認やフィードバックを受けられる「Human-in-the-Loop」メカニズムを設計することが重要です。CrewAIでは、特定のタスクを人間の入力を待つように設計することで、これを実現できます。

## 結論

これまで、私たちは**CrewAI**と**LangChain**を活用し、単なるRAGチャットボットを超えて、複数のAIエージェントが協調して複雑なリサーチ業務を自律的に遂行する**プロダクションレベルのRAGベースAIエージェントシステム**を構築する方法を深く探ってきました。役割ベースのエージェント設計、RAGによる知識の強化、そして体系的なタスク管理を通じて、既存のLLMアプリケーションの限界を超える洗練された自動化ワークフローを作成できることを確認しました。

AIエージェント技術はまだ始まったばかりの段階にあり、今後、ソフトウェア開発、ビジネスオートメーション、コンテンツ生成など、ほぼすべての領域で革新を主導する可能性を秘めています。本日紹介したアーキテクチャとコードを基に、皆さん独自の特化したAIエージェントチームを構築してみてください。その過程で経験する数多くの試行錯誤とデバッグの経験こそが、来たるべき「エージェントの時代」をリードする核心的な能力となるでしょう。

### 参考文献
- [CrewAI公式ドキュメント](https://docs.crewai.com/ "CrewAI Documentation"){:target="_blank"}
- [LangChain公式ドキュメント - Tools](https://python.langchain.com/docs/modules/tools/ "LangChain Tools Documentation"){:target="_blank"}
- [LangChain公式ドキュメント - RAG](https://python.langchain.com/docs/use_cases/question_answering/ "LangChain RAG Documentation"){:target="_blank"}
- [ReAct: Synergizing Reasoning and Acting in Language Models (原論文)](https://arxiv.org/abs/2210.03629 "ReAct Paper on arXiv"){:target="_blank"}