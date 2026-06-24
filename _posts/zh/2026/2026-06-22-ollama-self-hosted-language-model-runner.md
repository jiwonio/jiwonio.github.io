---
layout: post
title: Ollama：在自己的机器上运行语言模型
slug: ollama-self-hosted-language-model-runner
lang: zh
translation_key: ollama-self-hosted-language-model-runner
date: 2026-06-22 10:21:40 +0900
categories:
- AI
tags:
- Ollama
- Self-Hosting
- AI-Tooling
- Offline-AI
description: 了解如何使用 Ollama 在个人机器上自行安装和运行语言模型。本文将探讨设置过程、模型选择标准以及实际应用中的性能权衡。
image: /uploads/ollama-self-hosted-language-model-runner/thumbnail.webp
permalink: /zh/posts/ollama-self-hosted-language-model-runner/
post_type: deep-dive
ai_generated: true
updated: 2026-06-22 10:21:40 +0900
---
基于云的 AI 服务虽然功能强大，但也存在一些缺点，例如成本、数据隐私和网络依赖性。当需要处理敏感数据、在离线环境中使用 AI 功能，或者只是想控制实验成本时，自托管方案便成了一个可行的选择。然而，自行配置语言模型的过程通常复杂且耗时。

Ollama 是一个出色的开源项目，旨在解决这些问题。它让你只需几条命令，就能在个人计算机上运行强大的语言模型，无需复杂的设置。它极大地简化了下载、运行特定模型以及通过 HTTP 端点与其他服务集成等过程，让开发者能更专注于模型本身的应用。

<!--more-->
![Ollama：在自己的机器上运行语言模型](/uploads/ollama-self-hosted-language-model-runner/thumbnail.webp "Ollama：在自己的机器上运行语言模型")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI 生成图像</small>
</p>
-----

## 什么是 Ollama？

Ollama 扮演着运行语言模型的服务器角色。它在内部利用像 [llama.cpp](https://github.com/ggerganov/llama.cpp "llama.cpp GitHub Repository"){:target="_blank"} 这样的优化推理引擎，将模型加载到内存中并处理用户请求。开发者可以通过 Ollama 提供的简单命令行界面（CLI）或 RESTful API 端点与模型进行交互。

其核心价值在于“简洁”。它将模型下载、权重管理、GPU 分配等复杂任务进行了抽象，让你在终端中仅用 `ollama run <model_name>` 一行命令就能启动一切。

## 基本安装与运行

根据你的操作系统，Ollama 的安装过程非常简单，只需执行一个脚本即可。

**macOS & Linux**
```bash
# 下载并执行脚本
curl -fsSL https://ollama.com/install.sh | sh
```

安装完成后，你就可以立即运行所需的模型。以下是运行 Meta Llama 3 8B 模型的示例。

```bash
# 首次运行时会自动下载模型
ollama run llama3:8b

# 出现提示符后，输入你的问题
>>> Tell me a joke about programming.
```

你可以使用 `ollama list` 命令查看当前机器上已安装的模型列表。

## 通过 HTTP 服务器进行交互

Ollama 真正的强大之处在于其内置的 HTTP 服务器。执行 `ollama run` 命令时，服务器会在后台启动。该服务器通过 `/api/generate` 端点向外部提供模型推理功能。

以下是使用 `curl` 向 Llama 3 模型发送请求的示例。

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

`stream: false` 选项意味着一次性接收完整响应。如果将其设置为 `true`，你就可以像 ChatGPT 一样，以流式方式接收逐个生成的词元（token）。此功能在实现实时聊天界面时非常有用。

## 通过 Modelfile 进行自定义

Ollama 提供了通过名为 `Modelfile` 的配置文件来自定义现有模型的功能。其语法类似于 Dockerfile。你可以通过更改系统提示（system prompt）或调整特定参数来创建自己的模型。

例如，我们来创建一个只以 JSON 格式回答的模型。

**JsonLlama.modelfile**
```
# 指定基础模型
FROM llama3:8b

# 定义模型默认行为的系统消息
SYSTEM """
You are a helpful expert JSON generator.
You will only respond with valid JSON.
Do not add any other text outside of the JSON response.
"""
```

使用这个 `Modelfile` 来构建一个名为 `json-llama` 的新模型。

```bash
ollama create json-llama -f ./JsonLlama.modelfile
```

现在，运行 `ollama run json-llama`，你就可以与一个应用了我们定义的系统提示的模型进行对话了。

## 实际应用中的考量与权衡

### 硬件限制

在自己的设备上运行语言模型时，最大的限制来自硬件，特别是显存（VRAM）。所需的 VRAM 大小与模型的参数量成正比。

- **8B 模型 (Llama 3, Mistral):** 建议至少 8GB VRAM
- **13B 模型:** 建议至少 16GB VRAM
- **70B 模型:** 需要 48GB 以上的 VRAM，在普通个人设备上难以运行。

如果 VRAM 不足，模型的一部分会被转移到系统内存（RAM）中，导致推理速度急剧下降。

### 模型选择的重要性

并非所有任务都需要最大的模型。根据任务的复杂性选择合适大小的模型至关重要。对于简单的文本分类或摘要任务，7B 或 8B 模型就能表现出足够好的性能。而对于复杂的逻辑推理或专业写作，则可能需要更大的模型。

你可以在 [Ollama 模型库](https://ollama.com/library "Ollama Model Library"){:target="_blank"}中查看各种模型及其特性。

### 常见失败场景：VRAM 不足

尝试运行新模型时，最常见的失败原因是 VRAM 不足导致的异常速度下降。具体表现为终端响应极其缓慢，或者 GPU 风扇满负荷运转却迟迟没有结果。在这种情况下，你需要换用更小的模型，或者关闭其他正在运行的进程以释放 VRAM。

## 结论

Ollama 极大地降低了自托管语言模型的入门门槛。开发者可以摆脱基础设施配置的负担，快速构建原型，或将个性化的 AI 功能集成到自己的工作流中。当然，这其中存在硬件限制和模型选择的权衡，但从成本和隐私的角度来看，它无疑是云服务的一个绝佳替代方案。对于任何探索 AI 功能的开发者来说，Ollama 都将成为其工具箱中不可或缺的一员。

### 参考资料
- [Ollama 官方网站](https://ollama.com/ "Ollama Official Website"){:target="_blank"}
- [Ollama GitHub 仓库](https://github.com/ollama/ollama "Ollama on GitHub"){:target="_blank"}