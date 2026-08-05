---
layout: post
title: 使用 Gemini 1.5 Pro 缩短遗留代码分析时间：长上下文窗口的应用
slug: gemini-1-5-pro-legacy-code-analysis-long-context
lang: zh
translation_key: gemini-1-5-pro-legacy-code-analysis-long-context
post_type: deep-dive
date: 2026-08-05 11:36:38 +0900
categories:
- AI
tags:
- Gemini
- LLM
- Legacy Code
description: 本文探讨了如何利用 Gemini 1.5 Pro 的百万级 token 上下文窗口，识别分散在多个文件中的遗留代码依赖关系，并制定重构计划的实用方法。
image: /uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp
ai_generated: true
permalink: /zh/posts/gemini-1-5-pro-legacy-code-analysis-long-context/
---
一个旧项目收到了新功能开发请求。负责人员已经离职，文档几乎没有留下。需要修改特定功能，但相关逻辑分散在至少十个文件中。搜索函数名会得到几十个结果，仅仅是弄清楚哪个是真正的调用堆栈，就需要半天时间。

将代码按文件粘贴到现有 LLM 工具中进行提问的方式有明显的局限性。当我问完文件 A 的内容转到文件 B 时，模型很快就会忘记文件 A 的上下文。为了维持对话上下文，重复粘贴之前的回答和代码的过程，比代码分析本身更令人疲惫。最终，我还是只能像使用 LLM 之前一样，通过阅读代码来梳理依赖关系。

本文将介绍如何利用 Gemini 1.5 Pro 的百万级 token 上下文窗口，一次性分析这种分散的遗留代码库，并识别核心逻辑的具体工作流程。

<!--more-->
![使用 Gemini 1.5 Pro 缩短遗留代码分析时间：长上下文窗口的应用](/uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp "使用 Gemini 1.5 Pro 缩短遗留代码分析时间：长上下文窗口的应用")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI 生成图像</small>
</p>
-----

## 问题定义：碎片化的上下文

遗留代码分析困难的根本原因在于代码上下文分散在多个文件中。例如，处理用户支付请求的逻辑可能分散如下：

*   `controllers/payment_controller.rb`: 接收 HTTP 请求并调用服务
*   `services/payment_service.rb`: 处理业务逻辑，与多个模型交互
*   `models/order.rb`: 管理订单状态
*   `models/user.rb`: 查询用户信息
*   `lib/external_api_client.rb`: 集成外部支付网关 API

在这种情况下，如果只将 `payment_service.rb` 文件输入到 LLM 中，并提问“找出这段代码的问题”，模型由于完全不了解 `Order` 或 `User` 模型的内部实现，也不知道 `ExternalAPIClient` 的接口，因此只会给出基于一半信息的猜测性回答。

现有模型的上下文窗口（例如：32K、128K token）对于一次性容纳如此规模的代码来说远远不足。这是我们面临问题的核心。

## Gemini 1.5 Pro 的长上下文有何不同

Gemini 1.5 Pro 支持高达 100 万 token 的上下文窗口。这相当于几本普通小说的内容量，足以一次性输入中小型服务或整个模块的源代码。

上下文窗口大，不仅仅意味着可以输入更多的文本。模型能够同时“阅读”代码库中的所有文件，并综合理解文件间的相互引用、数据流以及隐藏的依赖关系。这意味着，解决了碎片化上下文问题的基础已经奠定。

## 实际工作流程：代码库压缩与提示词设计

现在，让我们来了解如何有效地将遗留代码库输入 Gemini 1.5 Pro 并请求分析的具体步骤。

### 1. 收集待分析代码

首先，需要将与待分析模块相关的所有源代码文件合并到一个文本文件中。手动复制粘贴几十个文件效率低下，建议使用简单的 shell 脚本。

```bash
# 分析할 디렉터리로 이동
cd path/to/legacy/project

# 1. 파일 구조를 먼저 파악하고,
# 2. 관련 있는 파일들을 하나의 텍스트 파일로 합칩니다.
echo "Project structure:" > combined_code.txt
tree . -I 'tmp|log|vendor' >> combined_code.txt
echo "\n--- End of structure ---\n" >> combined_code.txt

# Ruby on Rails 프로젝트의 app 디렉터리 전체를 합치는 예시
# 프로젝트에 맞게 `find` 명령어의 경로와 확장자를 수정해야 합니다.
find app -name "*.rb" -print0 | while IFS= read -r -d $'\0' file; do
    echo "--- File: $file ---" >> combined_code.txt
    cat "$file" >> combined_code.txt
    echo "\n" >> combined_code.txt
done
```

此脚本首先使用 `tree` 命令将整个文件结构记录在文本文件顶部，以帮助模型理解代码的位置。然后，使用 `find` 命令查找所有具有特定扩展名的文件，并按顺序追加到 `combined_code.txt` 文件中。

### 2. 设计提示词

与精心收集的代码同等重要的是提示词。需要为模型明确指定角色、目标和输出格式，才能获得所需的分析结果。

以下是一个用于遗留代码分析的提示词示例。

```text
你是一名拥有 20 年经验的 Ruby on Rails 后端架构师。我需要分析一个旧的支付模块以进行维护。下面提供了 `combined_code.txt` 文件的全部内容。

请深入分析整个代码库，并详细回答以下问题。

[分析目标]
1. 当用户通过 API 请求支付时，请从 `controllers/payment_controller.rb` 的 `create` 动作开始，逐步描述直到调用外部支付网关 API 的完整代码执行流程。每个步骤都必须指明调用了哪个文件、哪个类和哪个方法。
2. `PaymentService` 类的核心职责是什么？
3. 请找出代码库中可能导致潜在 bug 或严重性能下降的 3 个地方，并说明原因及提出改进方案。例如，找出 N+1 查询问题、不恰当的异常处理、硬编码的配置值等。
4. 请以 Mermaid JS 的 ERD 图格式绘制此支付模块的数据库 Schema。

请用中文回答，并用 Markdown 清晰地分隔每个项目。

--- 代码库开始 ---
(在此处粘贴上面生成的 combined_code.txt 文件的全部内容)
--- 代码库结束 ---
```

此提示词包含以下核心要素：

*   **赋予角色**: 赋予“20 年经验的后端架构师”角色，引导模型以专业视角进行分析。
*   **提供明确上下文**: 明确指出提供了整个代码库。
*   **具体问题**: 不仅仅是简单的分析请求，而是要求提供执行流程、类职责、潜在问题、数据库 Schema 可视化等具体且可操作的结果。

## 注意事项：Token 成本与局限性

长上下文窗口虽然强大，但并非万能。在实际应用于工作之前，有几点需要考虑。

*   **API 成本**: 使用 100 万 token 作为输入可能会产生相当高的成本。与其每次提出小问题都输入全部代码，不如将其间歇性地用于重要的分析，例如掌握全局或制定复杂的重构计划，这样更合理。
*   **“大海捞针”问题**: 有研究结果表明，当上下文变得非常长时，模型可能会遗漏其中的特定信息。在进行重要分析时，务必通过提示词引导模型的注意力到特定文件或逻辑，并批判性地审查其回答。
*   **响应延迟**: 由于输入量大，接收响应可能需要几十秒到几分钟。这更适合异步分析任务，而非实时对话。

## 结论：选择适合场景的工具

Gemini 1.5 Pro 的长上下文窗口为遗留代码分析这一特定问题提供了非常有效的解决方案。但它并非适用于所有情况。根据自身情况选择合适的模型和使用方法至关重要。

| 场景 | 推荐 | 原因 |
| :--- | :--- | :--- |
| **个人开发者的副项目** | **GPT-4o 或 Claude 3 Sonnet** | 免费额度充足，整个代码库较小，对长上下文的需求较低。更重要的是快速响应速度。 |
| **5 人规模初创公司的新功能开发** | **Gemini 1.5 Pro (按需使用)** | 平时使用短上下文模型进行快速开发，但在接手复杂模块或需要大规模重构时，利用长上下文来最大化生产力。 |
| **大型遗留系统的维护** | **Gemini 1.5 Pro (积极利用)** | 显著缩短理解多文件复杂依赖关系所需的时间。节省的开发者分析时间远大于 token 成本。 |

最终，重要的是准确理解最新技术的特点，并根据我们所面临问题的性质巧妙地加以利用。长上下文窗口具有改变我们理解代码方式的潜力，并将成为许多与遗留系统搏斗的开发者的新武器。

### 参考资料
- [Google AI 博客：Gemini 1.5 Pro 更新](https://blog.google/technology/ai/google-gemini-next-generation-model-february-2024/){:target="_blank"}
- [Vertex AI 生成式 AI 定价](https://cloud.google.com/vertex-ai/generative-ai/pricing){:target="_blank"}
