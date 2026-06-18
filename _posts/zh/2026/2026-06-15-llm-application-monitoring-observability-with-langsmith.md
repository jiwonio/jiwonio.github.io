---
layout: post
title: 生产级 LLM 应用监控：使用 LangSmith 构建完善的可观测性（Observability）指南
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
description: 您是否厌倦了 LLM 应用的“黑盒”式运营？本指南将详细介绍如何利用 LangSmith 构建生产环境中必不可少的 LLM 可观测性（Observability）系统，涵盖令牌成本、延迟、执行追踪等实战方法。超越简单的日志记录，优化您的
  AI 性能。
image: /uploads/llm-application-monitoring-observability-with-langsmith/thumbnail.webp
lang: zh
translation_key: llm-application-monitoring-observability-with-langsmith
permalink: /zh/posts/llm-application-monitoring-observability-with-langsmith/
---
基于 AI 的应用程序，特别是利用 LLM（大型语言模型）的系统，由于其复杂的内部运作，常常让人感觉像一个“黑匣子”。用户的提示被输入，看似合理的结果被输出，但在这个过程中发生了什么，成本是多少，瓶颈在哪里，都极难掌握。传统的服务器监控方法只能告诉我们 CPU、内存使用率等信息，无法追踪 LLM 应用的核心——“质量”、“成本”和“延迟”。

为了解决这些问题，确保 **LLMOps（LLM Operations）** 的核心要素——**可观测性（Observability）** 变得至关重要。LLM 可观测性超越了简单的日志堆积，它是一种工程实践，能够详细追踪模型的每一次请求、响应及其内部处理过程，将性能指标可视化，并收集用户反馈，从而让我们能够基于数据改进 AI 应用程序。没有一个好的可观测性系统，我们在问题发生时只能依赖猜测来寻找原因，成本优化和性能改进几乎是不可能的。

本文将详细介绍如何利用 LangChain 开发团队创建的 LLM 应用开发平台 **LangSmith**，一步步地在生产环境中为 LLM 应用构建完善的可观测性。希望您能通过 LangSmith，学习到追踪复杂的 RAG（Retrieval-Augmented Generation）管道或 AI 代理的执行过程、分析令牌成本和延迟、以及自动化质量评估的实战技巧。

<!--more-->
![生产级 LLM 应用监控：使用 LangSmith 构建完善的可观测性（Observability）指南](/uploads/llm-application-monitoring-observability-with-langsmith/thumbnail.webp "生产级 LLM 应用监控：使用 LangSmith 构建完善的可观测性（Observability）指南")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI 生成的图像</small>
</p>
-----

## LLM 应用可观测性（Observability）的三大支柱

为了全面了解 LLM 应用的状态，我们需要超越传统监控的三个核心要素。它们相互有机地连接，为我们提供对系统内部运作的深刻洞察。

### 1. 追踪（Tracing）

追踪是一种将 LLM 应用中单个请求的整个生命周期可视化的技术。它像流程图一样展示了从用户输入开始，经过所有内部组件（如 LLM 调用、数据库查询、API 请求等），直到生成最终响应的全过程。

例如，对于一个 RAG 管道，通过追踪可以一目了然地掌握以下过程：
- **输入（Input）：** 用户输入的问题。
- **文档检索（Retriever）：** 从向量数据库中用什么查询（query）检索了哪些文档？
- **提示词生成（Prompt Generation）：** 如何将检索到的上下文和问题组合成最终的提示词？
- **LLM 调用（LLM Call）：** 将最终的提示词传递给了哪个模型（例如 `gpt-4-turbo`）？
- **输出（Output）：** 模型生成的最终答案是什么？

这些详细的追踪信息在寻找 **“为什么 AI 会给出这样的回答？”** 这个问题的根本原因和进行调试时起着决定性作用。

### 2. 指标（Metrics）

指标是定量衡量系统性能和成本的核心数据。在 LLM 应用中，以下指标尤为重要：

- **延迟（Latency）：** 从请求开始到收到最终响应所花费的时间。特别是，生成第一个令牌的时间（Time to First Token）直接影响用户体验。
- **成本（Cost）/ 令牌使用量（Token Usage）：** 每次 LLM 调用所使用的提示词令牌和生成令牌的数量。这与 API 成本直接相关，必须进行追踪和优化。
- **错误率（Error Rate）：** 各类错误（如 LLM API 调用失败、超时、响应格式无效等）的发生频率。
- **吞吐量（Throughput）：** 单位时间内处理的请求数量。

将这些指标在仪表盘上进行可视化，并设置基于阈值的告警，可以帮助我们及早发现系统异常迹象并迅速响应。

### 3. 反馈（Feedback）

反馈是衡量模型生成结果“质量”的最重要手段。无论生成答案的速度多快、成本多低，如果内容不准确或不符合用户意图，就毫无意义。

反馈可以通过多种形式收集：
- **用户反馈：** 聊天机器人界面上的“赞/踩”按钮、星级评分、评论等。
- **程序化反馈：** 通过代码评估生成的答案是否符合特定格式（如 JSON），是否通过了内部业务逻辑的验证。
- **专家评估：** 内部运营团队或专家直接评估答案质量并打分。

收集到的反馈数据可用于识别特定提示词的问题，或作为宝贵的数据集用于未来的模型性能评估（Evaluation）和微调（Fine-tuning）。

## 利用 LangSmith 构建实战监控系统

现在，我们来实际使用 LangSmith 构建上述可观测性的三大支柱。LangSmith 仅需设置环境变量，就能与现有的 LangChain、OpenAI SDK 代码完美集成，非常方便。

### 1. 环境配置与 API 密钥签发

首先，访问 [LangSmith 官方网站](https://smith.langchain.com/ "LangSmith Website"){:target="_blank"} 并注册。然后，在 **Settings > API Keys** 菜单中创建一个新的 API 密钥。

生成的密钥是高度敏感的信息，切勿将其硬编码在代码中，务必通过环境变量进行管理。在项目根目录下创建一个 `.env` 文件，并添加如下密钥。

**.env**
```env
# [🚨 安全警告] 请替换为您的实际密钥，并将此文件添加到 .gitignore 中。
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="<YOUR_LANGCHAIN_API_KEY>"
LANGCHAIN_PROJECT="My-AI-Project" # 按项目对追踪进行分组。

OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
```

- `LANGCHAIN_TRACING_V2="true"`：这是启用 LangSmith 追踪功能的核心设置。
- `LANGCHAIN_ENDPOINT`：LangSmith API 服务器地址。
- `LANGCHAIN_API_KEY`：您签发的 LangSmith API 密钥。
- `LANGCHAIN_PROJECT`：用于对生成的追踪（Trace）进行分组的项目名称。如果未指定，将默认为 'default'。

### 2. 将 LangSmith 集成到 Python 应用中

现在，我们将 LangSmith 集成到 Python 代码中。首先，安装所需的库。

```bash
pip install openai langchain langchain-openai python-dotenv
```

编写一个加载环境变量并使用 OpenAI 客户端的简单代码。

**simple_llm_call.py**
```python
import os
from openai import OpenAI
from dotenv import load_dotenv

# 从 .env 文件加载环境变量
load_dotenv()

# 仅通过设置环境变量，LangSmith 就会自动追踪 OpenAI 的调用。
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_question(question):
    print("开始提问...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": question}],
        temperature=0.7,
    )
    answer = response.choices[0].message.content
    print("回答:", answer)
    return answer

if __name__ == "__main__":
    ask_question("请说明 LLMOps 中可观测性的重要性。")
```

只需运行以上代码，得益于 `LANGCHAIN_TRACING_V2` 环境变量，关于 OpenAI API 调用的所有信息（提示词、响应、令牌使用量、延迟等）都会自动记录到 LangSmith 的 'My-AI-Project' 项目中。

接下来，我们来看一个使用 LangChain 的更复杂的 RAG 示例。

**rag_chain_example.py**
```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 从 .env 文件加载环境变量
load_dotenv()

# 伪 Retriever（实际应使用 VectorDB）
def fake_retriever(query: str) -> str:
    print(f"正在为 '{query}' 检索文档...")
    # 在实际实现中，这里会查询 VectorDB。
    return "LangSmith 是一个用于 LLM 应用追踪、监控和评估的平台。"

# 使用 LangChain 表达式语言（LCEL）定义 RAG 链
template = """
你是一个回答问题的 AI 助手。
请使用提供的上下文来回答问题。

上下文: {context}

问题: {question}

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
    print("正在运行 RAG Chain...")
    result = rag_chain.invoke("LangSmith 是什么？")
    print("最终结果:", result)
```

运行此代码后，您可以在 LangSmith 仪表盘中直观地看到 `rag_chain` 的整个执行流程。`fake_retriever` 函数调用、`prompt` 生成、`model` 调用等每个步骤的输入、输出和耗时都可以分解查看，这使得调试变得非常容易。

### 3. LangSmith 仪表盘探索

运行代码后，访问 LangSmith 仪表盘，您可以通过多种方式探索收集到的数据。

- **Projects/Traces 视图：** 显示所有已执行请求的列表。点击每个条目可以查看该请求的详细追踪信息。在 RAG 示例中，retriever 和 LLM 调用会以层级结构显示，让您直观地理解整个管道的流程。
- **Monitoring 选项卡：** 这是一个仪表盘，按时间序列展示了整个项目的核心指标（延迟、令牌成本、错误率等）。通过它，您可以立即发现诸如“上周开始 API 成本突然飙升”或“特定时间段延迟变长”等问题。

## 高级用法：性能优化与评估（Evals）

LangSmith 不仅仅是简单的日志记录和监控工具，它还提供了强大的功能来帮助您改进应用程序。

### 1. 以编程方式记录用户反馈（Feedback）

当用户在应用中点击“赞/踩”按钮时，您可以将该反馈与特定的 LLM 执行（run）关联起来，并记录到 LangSmith。

```python
from langsmith import Client

client = Client()

# ... 假设在 LLM 调用后获得了 run_id ...
# 可以将 rag_chain.invoke() 设置为返回一个包含 run_id 的对象。
# 示例 run_id（实际上是从 invoke 结果中提取）
example_run_id = "a1b2c3d4-e5f6-..." 

# 当用户点击“赞”时
client.create_feedback(
    run_id=example_run_id,
    key="user_score",  # 表示反馈类型的键
    score=1,           # 1: 好, 0: 坏
    comment="回答非常准确且有用。"
)

# 当用户点击“踩”时
client.create_feedback(
    run_id=example_run_id,
    key="user_score",
    score=0,
    comment="回答与问题无关。"
)
```
这样收集的反馈会在 LangSmith 仪表盘上与每个追踪一起显示，可用于分析“用户不喜欢的回答主要出现在哪类问题中？”。

### 2. 创建数据集并执行评估

在运营过程中发现的重要成功/失败案例，可以在 LangSmith UI 中保存为“数据集”。例如，您可以创建一个名为“回答不准确案例集”的数据集。

基于这样创建的数据集，您可以自动评估新提示词或模型的性能。

```python
from langsmith.evaluation import evaluate

# ... 先前定义的 rag_chain ...

# 针对“回答不准确案例集”数据集评估 rag_chain 的性能
# LangSmith 提供了多种评估器（evaluator），用于比较正确答案（ground truth）和模型的回答。
evaluation_results = evaluate(
    rag_chain.invoke, # 评估目标函数
    data="incorrect-answers-dataset", # 保存在 LangSmith 中的数据集名称
    # 可根据需要添加自定义评估器
)
```
`evaluate` 函数会针对数据集中的每个条目运行 `rag_chain`，并根据预定义的标准（例如，与正确答案的相似度）对其结果进行评分，最终生成一份报告。通过这种方式，您可以在修改提示词后客观地验证性能是否确实得到了改善。

## 结论：可观测性不是“锦上添花”，而是“必备之选”

开发基于 LLM 的 AI 应用不是一次性的工作，而是一个需要持续测量和改进的旅程。像 LangSmith 这样的可观测性工具在这个旅程中扮演着必不可少的指南针角色。我们已经走过了依赖猜测和感觉来修改提示词和解决问题的时代，现在应该基于数据和指标，系统地管理 AI 应用的性能、成本和质量。

希望通过本指南介绍的方法，您能透明地洞察 LLM 应用的内部，迅速定位问题的根本原因，并最终构建出为用户提供更大价值的智能 AI 系统。**如果在生产环境中运营 AI，那么可观测性系统不是一个选项，而是一个必需品。**

### 参考资料
- [LangSmith 官方文档](https://docs.smith.langchain.com/ "LangSmith Official Documentation"){:target="_blank"}
- [LangChain Python 官方文档](https://python.langchain.com/docs/get_started/introduction "LangChain Python Documentation"){:target="_blank"}
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference "OpenAI API Reference"){:target="_blank"}