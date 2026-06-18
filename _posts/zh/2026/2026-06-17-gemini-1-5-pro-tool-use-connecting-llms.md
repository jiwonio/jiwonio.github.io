---
layout: post
title: Gemini 1.5 Pro 工具使用：连接 LLM 与外部世界
slug: gemini-1-5-pro-tool-use-connecting-llms
date: 2026-06-17 10:34:31 +0900
categories:
- AI
tags:
- Gemini
- LLM
- Tool Use
- Function Calling
description: 了解如何将 Gemini 1.5 Pro 的工具使用（函数调用）功能应用于实际工作。本文将探讨模型识别并请求调用外部函数的过程、相关设置以及潜在的失败案例。
image: /uploads/gemini-1-5-pro-tool-use-connecting-llms/thumbnail.webp
lang: zh
translation_key: gemini-1-5-pro-tool-use-connecting-llms
permalink: /zh/posts/gemini-1-5-pro-tool-use-connecting-llms/
---
大型语言模型（LLM）基于海量文本数据展现出惊人的语言能力。但 LLM 本身与外部世界是隔绝的。它们无法直接执行诸如获取实时股票信息、查询数据库或发送电子邮件等任务。克服这一限制的核心技术便是“工具使用（Tool Use）”，也称为“函数调用（Function Calling）”。

本文将以 Google 的 Gemini 1.5 Pro 模型为中心，解释工具使用的概念和工作原理。我们将不仅仅停留在调用 API 的层面，而是深入探讨在实际工作中可能遇到的权衡和潜在的失败案例。通过本文，您将迈出第一步，将 LLM 从一个简单的聊天机器人转变为能够执行实际任务的代理（Agent）。

<!--more-->
![Gemini 1.5 Pro 工具使用：连接 LLM 与外部世界](/uploads/gemini-1-5-pro-tool-use-connecting-llms/thumbnail.webp "Gemini 1.5 Pro 工具使用：连接 LLM 与外部世界")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## LLM 与外部世界的隔阂及工具使用

LLM 无法访问其训练数据之外的最新信息或私有数据。如果你问“今天首尔的天气怎么样？”，模型无法查询实时数据，因此只会回答“我无法确认实时信息”。

工具使用解决了这个问题。开发者向 LLM 提供一个预先定义的函数（工具）列表，模型会理解用户问题的意图，并找出最合适的函数及其所需参数。关键在于，LLM 并不直接*执行*函数，而是以结构化数据（JSON）的形式*请求*应该用什么参数来执行哪个函数。实际的执行在我们的代码中完成，然后将执行结果返回给 LLM，以生成最终答案。

## 工具使用的工作原理：对话式委托

工具使用是 LLM 与我们的代码之间一个精密的对话过程。整个流程如下：

1.  **传递用户问题和函数规范**：我们将用户的提示以及我们定义的“可用工具”列表（函数名称、描述、参数信息）一同传递给模型。
2.  **模型的判断与函数调用请求**：模型分析提示，判断已定义的工具中是否有助于处理当前请求的工具。如果有，它会返回一个包含该函数名称和所需参数的 JSON 对象。
3.  **我们的代码执行函数**：我们的代码解析模型返回的 JSON，并执行实际逻辑（例如：查询天气信息）。
4.  **返回执行结果**：将函数执行结果再次传递给模型。
5.  **生成最终答案**：模型基于函数执行结果，以自然语言为用户生成并传递最终答案。

在这个过程中，LLM 扮演着“推理引擎”的角色，而我们的代码则扮演着“执行器”的角色，形成了一个协作模型。

## 使用 Python 实现 Gemini 工具使用

现在，我们通过实际代码来实现 Gemini 1.5 Pro 的工具使用功能。这需要 `google-generativeai` 库。

### 1. 准备工作

首先，安装必要的库并设置 API 密钥。

```python
# 安装必要的库
# pip install google-generativeai

import os
import google.generativeai as genai

# 设置 API 密钥
# 在实际代码中，请使用环境变量或密钥管理工具。
genai.configure(api_key="<YOUR_GEMINI_API_KEY>")
```

### 2. 定义待执行函数

我们定义两个简单的函数供模型使用。一个返回天气信息，另一个返回虚拟的股票价格。

```python
def get_current_weather(location: str, unit: str = "celsius"):
    """返回指定位置的当前天气信息。"""
    # 实际上，这里会包含调用外部天气 API 的逻辑。
    if "seoul" in location.lower():
        return {"location": "Seoul", "temperature": "15", "unit": unit}
    elif "tokyo" in location.lower():
        return {"location": "Tokyo", "temperature": "18", "unit": unit}
    else:
        return {"location": location, "temperature": "unknown"}

def get_stock_price(ticker_symbol: str):
    """返回指定股票代码的当前股价。"""
    # 实际上，这里会包含调用外部股票信息 API 的逻辑。
    if ticker_symbol.upper() == "GOOG":
        return {"symbol": "GOOG", "price": "175.50", "currency": "USD"}
    elif ticker_symbol.upper() == "AAPL":
        return {"symbol": "AAPL", "price": "190.20", "currency": "USD"}
    else:
        return {"symbol": ticker_symbol, "price": "not found"}
```

### 3. 向模型传递函数规范

初始化 Gemini 模型，并将上面定义的函数注册为“工具”。

```python
# 将可用函数映射到字典中
available_tools = {
    "get_current_weather": get_current_weather,
    "get_stock_price": get_stock_price,
}

# 初始化模型时，一并传递可用的函数列表
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    tools=list(available_tools.values())
)
```

### 4. 调用模型并处理响应

这是处理用户提问、启动对话并处理模型响应的完整逻辑。

```python
# 开始对话
chat = model.start_chat()

# 第一个问题
prompt = "请告诉我首尔的天气和谷歌的股价。温度请用华氏度显示。"
response = chat.send_message(prompt)

# 检查模型是否请求了函数调用
function_calls = response.candidates[0].content.parts[0].function_call
if function_calls:
    print(f"Model wants to call functions: {function_calls}")

    # 顺序处理多个函数调用
    for function_call in function_calls:
        function_name = function_call.name
        function_args = function_call.args

        # 1. 查找要调用的函数
        function_to_call = available_tools.get(function_name)
        if not function_to_call:
            print(f"Error: Function '{function_name}' not found.")
            continue

        # 2. 实际执行函数
        try:
            # 使用 ** 运算符将字典解包为关键字参数
            function_response = function_to_call(**function_args)
            print(f"Executed '{function_name}' with args {function_args}, got: {function_response}")

            # 3. 将执行结果再次传递给模型
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
            # 发生错误时，也可以将错误信息传递给模型。

# 输出最终答案
final_response = response.candidates[0].content.parts[0].text
print(f"\nFinal Answer:\n{final_response}")
```

运行以上代码，模型会返回一个请求，要求分别使用适当的参数（`location='Seoul', unit='fahrenheit'` 和 `ticker_symbol='GOOG'`）调用 `get_current_weather` 和 `get_stock_price` 函数。我们的代码根据这个请求执行函数并将结果返回后，模型会综合这些信息生成最终答案。

## 实际应用中的考量与失败案例

工具使用功能虽然强大，但在实际应用时需要谨慎考虑以下几点。

### 清晰函数规范的重要性

模型通过函数的名称和文档字符串（docstring，即描述）来决定选择哪个函数。如果描述模糊或参数名称不直观，模型可能会选择错误的函数或推断出错误的参数。

-   **失败案例**：不要使用像 `get_data(source, query)` 这样泛化的名称和描述，而应使用像 `get_user_profile_by_email(email_address)` 这样具体明确的名称和描述。
-   **提示**：函数的文档字符串应明确回答“这个函数做什么？”以及“每个参数代表什么？”。

### 返回值处理与错误报告

我们执行的函数可能会失败。外部服务可能宕机，或者在数据库中找不到所需结果。此时，不应简单地返回 `None` 或抛出异常就结束。

-   **失败案例**：当天气 API 调用失败时，如果只返回 `None`，模型可能无法意识到信息缺失，并可能基于之前的对话内容产生幻觉（hallucination）。
-   **提示**：如果函数执行失败，应向模型返回包含失败原因的明确消息（例如：`{"error": "API rate limit exceeded"}`）。这样，模型就能准确地向用户传达情况，例如“很抱歉，当前无法获取天气信息。请稍后再试。”

### 安全性：仅执行可信代码

绝不能将 LLM 返回的函数名和参数直接传递给像 `eval()` 这样的危险函数。模型返回的只是一个“请求”，执行何种代码的最终决定权在我们手中。

-   **提示**：应创建一个预定义且经过安全验证的函数列表（白名单），并限制只有当模型请求的函数名在该列表中时才执行。

### 延迟与成本

工具使用至少需要两次 LLM 调用（提问 → 函数调用请求 → 传递结果 → 最终答案）。这会增加响应延迟并提高 API 调用成本。因此，不应在所有交互中滥用工具使用，而应选择性地在确实需要外部信息或操作时使用。

## 结论

Gemini 1.5 Pro 的工具使用功能是一座强大的桥梁，它使 LLM 能够超越自身限制，与现实世界互动，从而构建智能代理。仅仅使用该功能还不够，只有同时从实际应用的角度考虑清晰的规范、稳健的错误处理、安全性及成本等因素，才能完全发挥其潜力。希望本文探讨的原理和代码能为您的服务增添新的可能性。

### 参考资料
- [Google AI for Developers - Tool use](https://ai.google.dev/docs/function_calling "Gemini Function Calling Official Documentation"){:target="_blank"}
- [GoogleCloudPlatform/generative-ai-samples on GitHub](https://github.com/GoogleCloudPlatform/generative-ai-samples/blob/main/gemini/function-calling/intro_function_calling.ipynb "Gemini Function Calling Examples"){:target="_blank"}