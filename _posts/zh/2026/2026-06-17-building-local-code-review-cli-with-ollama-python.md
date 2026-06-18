---
layout: post
title: 使用 Ollama 和 Python 构建自己的本地代码审查 CLI
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
description: 无需担心 API 成本和安全问题，利用 Ollama 和 Llama 3 亲手打造一个在本地环境中运行的代码审查 CLI 工具。本文将涵盖从提示词设计到工具局限性的实用技巧。
image: /uploads/building-local-code-review-cli-with-ollama-python/thumbnail.webp
lang: zh
translation_key: building-local-code-review-cli-with-ollama-python
permalink: /zh/posts/building-local-code-review-cli-with-ollama-python/
---
代码审查是维护软件质量的核心过程，但它也常常消耗同事大量的时间。虽然像 GitHub Copilot 或 ChatGPT 这样的 AI 工具已经成为出色的辅助手段，但将敏感代码发送到外部 API 的安全顾虑和成本问题依然存在。

在本文中，为了解决这些问题，我们将亲手构建一个在本地环境中完全独立运行的代码审查 CLI（命令行界面）工具。我们将使用流行的本地 LLM 运行工具 **Ollama** 和 **Python**，学习如何在没有外部网络连接的情况下，安全、快速地获取代码反馈。

<!--more-->
![使用 Ollama 和 Python 构建自己的本地代码审查 CLI](/uploads/building-local-code-review-cli-with-ollama-python/thumbnail.webp "使用 Ollama 和 Python 构建自己的本地代码审查 CLI")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 为什么选择本地代码审查器？

与使用商业 AI 服务相比，在本地直接运行 LLM 来创建代码审查工具有几个明显的优势。

1.  **安全性**：源代码不会离开个人计算机或内部服务器。在处理有严格安全策略或不应外泄代码的公司环境中，这是一个决定性的优点。
2.  **成本**：除了初始的硬件投资外，不会产生因 API 调用而产生的额外费用。您可以随心所欲地进行实验和使用。
3.  **离线工作**：即使在网络连接不稳定或没有网络的环境中，也可以进行代码审查。
4.  **定制化**：可以自由修改提示词和模型，打造符合我们团队特有的代码审查风格和规则的工具。

## 准备工作：安装 Ollama 和 Llama 3

首先，需要准备一个可以在本地运行 LLM 的环境。Ollama 是一个出色的工具，它让我们可以通过简单的命令安装和运行 LLM，无需复杂的设置。

请访问官方网站 [ollama.com](https://ollama.com "Ollama 官方网站"){:target="_blank"}，下载并安装适合您操作系统的安装程序。

安装完成后，在终端中运行以下命令来下载最新的 Llama 3 8B 模型。Llama 3 8B 模型在普通的开发人员笔记本电脑上也能相对流畅地运行，并且在代码相关任务上表现出不错的性能。

```bash
# 在本地下载 Llama 3 8B 模型
ollama pull llama3
```

模型下载完成后，可以使用 `ollama list` 命令查看已安装的模型列表。

## 核心逻辑：Python CLI 脚本设计

现在，我们来编写一个 Python CLI 脚本，该脚本会读取代码文件，并请求正在通过 Ollama 运行的 Llama 3 模型进行审查。

### 1. 项目结构与依赖安装

我们从一个简单的结构开始。只需要一个 `review.py` 文件即可。安装脚本运行所需的 `ollama` Python 库。

```bash
# 安装 Ollama Python 客户端库
pip install ollama
```

### 2. 编写 CLI 脚本 (`review.py`)

为了让用户可以在终端中以 `python review.py <文件名>` 的形式轻松运行，我们使用 `argparse` 来接收文件路径作为参数。

```python
# review.py

import ollama
import argparse
import sys

# 定义用于代码审查的系统提示词
# 明确指示模型应该扮演什么角色。
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
    读取指定文件的代码，并通过 Ollama 进行代码审查。
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
        # 调用 Ollama 流式 API
        stream = ollama.chat(
            model='llama3',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f"Please review the following Python code:\n\n```python\n{code_content}\n```"},
            ],
            stream=True,
        )

        print(f"\n--- Code Review for {file_path} ---\n")
        # 实时输出流式响应
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

这个脚本的核心是 `SYSTEM_PROMPT`。在这里，我们明确地将 LLM 的角色指定为“专业代码审查员”，并提供了具体的指导，说明应该从哪些角度（如 bug、可读性、性能等）来分析代码。这对于获得更一致、更高质量的审查结果至关重要。

## 运行与结果分析

让我们创建一个简单的 Python 示例文件来进行审查。

**`example.py`**
```python
# 接收用户的姓名和年龄并打招呼的函数
def great_user(name, age):
    # 如果年龄小于18岁，则输出不同的消息
    if age < 18:
        msg = "Hello " + name + ", you are still young!"
    else:
        msg = "Hello " + name + ", welcome!"
    
    # 多次输出消息以示强调
    for i in range(5):
        print(msg)

# 测试函数
great_user("Alice", 25)
great_user("Bob", 15)
```

现在，在终端中运行我们创建的审查脚本。

```bash
python review.py example.py
```

稍后，Llama 3 模型生成的代码审查结果将以流式形式输出。

```
--- Code Review for example.py ---

*   **Clarity and Readability**: The function name `great_user` could be more descriptive, perhaps `greet_user` would be clearer. Using f-strings for string formatting is more modern and readable than string concatenation (e.g., `f"Hello {name}, welcome!"`).
*   **Best Practices**: The magic number `18` could be defined as a constant, like `LEGAL_ADULT_AGE = 18`, to improve maintainability.
*   **Logic and Bugs**: The loop `for i in range(5):` prints the same message five times. This might not be the intended behavior. If the goal is emphasis, a comment explaining why would be helpful. Otherwise, it seems redundant.
*   **Performance**: For this simple function, performance is not a concern. However, in a real-world scenario, printing inside a loop within a function that returns a value can be an undesirable side effect. It's often better to return the message and let the caller handle the printing.

--- End of Review ---
```

从结果中可以看出，本地 LLM 提供了相当有意义的反馈，例如函数名拼写错误建议、推荐使用 f-string、魔术数字问题以及不必要的循环等。

## 提升实用性的思考：局限与权衡

这个工具无疑是有用的，但在直接应用于实际工作之前，需要认识到它的一些明显局限性。

-   **缺乏上下文**：该脚本只分析单个文件。它完全不了解整个项目的结构、与其他文件的依赖关系以及整体的业务逻辑。因此，在进行架构层面的审查或发现复杂逻辑错误方面存在局限。
-   **模型性能**：像 Llama 3 8B 这样的小型模型，其代码理解能力和推理能力可能不如 GPT-4 或 Claude 3 Opus 等顶级模型。有时它可能会生成不准确或陈词滥调的反馈。使用更大的模型（例如 `llama3:70b`）可以提高质量，但这需要更高规格的硬件（尤其是 VRAM）。
-   **幻觉 (Hallucination)**：与所有 LLM 一样，本地模型也可能“煞有介事”地编造不实内容。对于像“这段代码与 X 库的最新版本不兼容”这样的具体断言，必须亲自进行验证。
-   **结果不一致**：即使对同一段代码进行多次审查，也可能会得到略有不同的结果。

## 结论

利用 Ollama 构建的本地代码审查 CLI，是一种无需依赖外部服务、解决了安全和成本问题，同时又能获得 AI 辅助的绝佳方法。它在处理敏感代码或自动化简单代码风格的初步检查方面尤其有用。

虽然这个工具无法替代经验丰富的同事进行的深入审查，但作为提交审查前自我改进的“自查工具”，或减轻审查者负担的“辅助手段”，它具有足够的价值。在此基础上，还可以将其与 Git 的 pre-commit 钩子（hook）集成，在提交前自动执行审查，或者在提示词中更具体地指明团队的编码规范，将其发展为定制化的审查器。

### 参考文献
- [Ollama 官方网站](https://ollama.com "Ollama"){:target="_blank"}
- [Ollama Python Library (GitHub)](https://github.com/ollama/ollama-python "ollama-python on GitHub"){:target="_blank"}