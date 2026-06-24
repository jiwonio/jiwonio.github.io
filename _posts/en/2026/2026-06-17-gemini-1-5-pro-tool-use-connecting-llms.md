---
layout: post
title: 'Gemini 1.5 Pro Tool Use: Connecting LLMs to the External World'
slug: gemini-1-5-pro-tool-use-connecting-llms
date: 2026-06-17 10:34:31 +0900
categories:
- AI
tags:
- Gemini
- LLM
- Tool Use
- Function Calling
description: Learn how to apply the Tool Use (Function Calling) feature of Gemini
  1.5 Pro in practice. This post covers how the model recognizes and requests calls
  to external functions, its configuration, and potential failure scenarios.
image: /uploads/gemini-1-5-pro-tool-use-connecting-llms/thumbnail.webp
lang: en
translation_key: gemini-1-5-pro-tool-use-connecting-llms
permalink: /en/posts/gemini-1-5-pro-tool-use-connecting-llms/
post_type: deep-dive
ai_generated: true
---
Large Language Models (LLMs) demonstrate incredible linguistic abilities based on vast amounts of text data. However, LLMs are inherently disconnected from the external world. They cannot directly perform tasks like fetching real-time stock information, querying a database, or sending an email. The key technology to overcome this limitation is 'Tool Use', also known as Function Calling.

This article explains the concept and operational principles of Tool Use, focusing on Google's Gemini 1.5 Pro model. We'll go beyond simple API calls to delve into the tradeoffs and potential failure scenarios you might encounter in a real-world setting. This will be your first step in transforming an LLM from a simple chatbot into an agent that performs real tasks.

<!--more-->
![Gemini 1.5 Pro Tool Use: Connecting LLMs to the External World](/uploads/gemini-1-5-pro-tool-use-connecting-llms/thumbnail.webp "Gemini 1.5 Pro Tool Use: Connecting LLMs to the External World")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## The Disconnect Between LLMs and the External World, and Tool Use

LLMs cannot access the latest information or private data that wasn't part of their training data. If you ask, "What's the weather like in Seoul today?", the model can't look up real-time data and will simply reply, "I cannot check real-time information."

Tool Use solves this problem. A developer provides the LLM with a list of predefined functions (tools). The model then interprets the user's intent and identifies the most appropriate function and the necessary arguments for it. The crucial point is that the LLM does not *execute* the function itself; it *requests* which function to run with which arguments in a structured data format (JSON). The actual execution happens in our code, and the result is then sent back to the LLM to generate a final answer.

## How Tool Use Works: A Conversational Delegation

Tool Use is a sophisticated conversational process between the LLM and our code. The overall flow is as follows:

1.  **Send User Prompt and Function Specifications**: We send the user's prompt to the model, along with a list of 'available tools' we've defined (function name, description, parameter information).
2.  **Model's Judgment and Function Call Request**: The model analyzes the prompt to determine if any of the defined tools can help handle the request. If so, it returns a JSON object containing the function name and the required arguments.
3.  **Function Execution in Our Code**: Our code parses the JSON returned by the model and executes the actual logic (e.g., fetching weather information).
4.  **Return Execution Result**: The result of the function execution is sent back to the model.
5.  **Generate Final Answer**: Based on the function execution result, the model generates a final, natural language answer for the user.

In this process, the LLM acts as the 'reasoning engine,' and our code acts as the 'executor' in a collaborative model.

## Implementing Gemini Tool Use with Python

Now, let's implement Gemini 1.5 Pro's Tool Use feature with actual code. You will need the `google-generativeai` library.

### 1. Prerequisites

First, install the necessary library and set up your API key.

```python
# Install the required library
# pip install google-generativeai

import os
import google.generativeai as genai

# Configure the API key
# In production code, use environment variables or a secret management tool.
genai.configure(api_key="<YOUR_GEMINI_API_KEY>")
```

### 2. Defining Functions to Execute

We'll define two simple functions for the model to use. One is a mock function that returns weather information, and the other returns a stock price.

```python
def get_current_weather(location: str, unit: str = "celsius"):
    """Returns the current weather information for a given location."""
    # In a real application, this would call an external weather API.
    if "seoul" in location.lower():
        return {"location": "Seoul", "temperature": "15", "unit": unit}
    elif "tokyo" in location.lower():
        return {"location": "Tokyo", "temperature": "18", "unit": unit}
    else:
        return {"location": location, "temperature": "unknown"}

def get_stock_price(ticker_symbol: str):
    """Returns the current stock price for a given ticker symbol."""
    # In a real application, this would call an external stock information API.
    if ticker_symbol.upper() == "GOOG":
        return {"symbol": "GOOG", "price": "175.50", "currency": "USD"}
    elif ticker_symbol.upper() == "AAPL":
        return {"symbol": "AAPL", "price": "190.20", "currency": "USD"}
    else:
        return {"symbol": ticker_symbol, "price": "not found"}
```

### 3. Providing Function Specifications to the Model

Initialize the Gemini model and register the functions we defined above as 'tools'.

```python
# Map the available functions to a dictionary
available_tools = {
    "get_current_weather": get_current_weather,
    "get_stock_price": get_stock_price,
}

# Initialize the model, passing the list of available functions
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    tools=list(available_tools.values())
)
```

### 4. Calling the Model and Processing the Response

This is the complete logic for starting a chat with a user's question and processing the model's response.

```python
# Start the chat
chat = model.start_chat()

# First question
prompt = "What's the weather in Seoul and the stock price for Google? Please give me the temperature in Fahrenheit."
response = chat.send_message(prompt)

# Check if the model requested function calls
function_calls = response.candidates[0].content.parts[0].function_call
if function_calls:
    print(f"Model wants to call functions: {function_calls}")

    # Process multiple function calls sequentially
    for function_call in function_calls:
        function_name = function_call.name
        function_args = function_call.args

        # 1. Find the function to call
        function_to_call = available_tools.get(function_name)
        if not function_to_call:
            print(f"Error: Function '{function_name}' not found.")
            continue

        # 2. Execute the actual function
        try:
            # The ** operator unpacks the dictionary into keyword arguments
            function_response = function_to_call(**function_args)
            print(f"Executed '{function_name}' with args {function_args}, got: {function_response}")

            # 3. Send the execution result back to the model
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
            # You can also pass error information back to the model.

# Print the final answer
final_response = response.candidates[0].content.parts[0].text
print(f"\nFinal Answer:\n{final_response}")
```

When you run this code, the model will return a request to call the `get_current_weather` and `get_stock_price` functions with the appropriate arguments (`location='Seoul', unit='fahrenheit'` and `ticker_symbol='GOOG'`). Our code then executes these functions according to the request and sends the results back. The model then synthesizes this information to generate the final answer.

## Practical Considerations and Failure Cases

Tool Use is powerful, but there are several things to consider carefully when applying it in a real-world setting.

### The Importance of Clear Function Specifications

The model decides which function to choose based on its name and docstring (description). If the description is ambiguous or the parameter names are not intuitive, the model might choose the wrong function or infer incorrect arguments.

-   **Failure Case**: Instead of a generic name and description like `get_data(source, query)`, use specific and clear names like `get_user_profile_by_email(email_address)`.
-   **Tip**: A function's docstring should clearly answer "What does this function do?" and "What does each parameter mean?"

### Handling Return Values and Error Reporting

The functions we execute might fail. An external service could be down, or we might not find the desired result in the database. In such cases, you should not simply return `None` or let an exception crash the program.

-   **Failure Case**: If a weather API call fails and you just return `None`, the model won't know that information is missing and might hallucinate an answer based on previous conversation context.
-   **Tip**: If a function execution fails, you should return a clear message to the model explaining the reason for the failure (e.g., `{"error": "API rate limit exceeded"}`). The model can then accurately inform the user, "I'm sorry, but I failed to retrieve the weather information at this time. Please try again later."

### Security: Executing Only Trusted Code

You must never pass the function name and arguments returned by the LLM directly into a dangerous function like `eval()`. What the model returns is merely a 'request,' and the final decision on what code to execute rests with us.

-   **Tip**: Create an allowlist of predefined and security-vetted functions. Only execute a function if the name requested by the model is on this list.

### Latency and Cost

Tool Use requires at least two LLM calls (Question → Function Call Request → Result → Final Answer). This increases response latency and API call costs. Therefore, instead of overusing Tool Use for every interaction, it should be used selectively only when external information or actions are absolutely necessary.

## Conclusion

The Tool Use feature in Gemini 1.5 Pro serves as a powerful bridge, allowing LLMs to overcome their limitations and interact with the real world as intelligent agents. To fully unleash its potential, we must go beyond simply using the feature and also consider practical aspects like clear specifications, robust error handling, security, and cost. I hope the principles and code covered in this article will help you add new capabilities to your services.

### References
- [Google AI for Developers - Tool use](https://ai.google.dev/docs/function_calling "Gemini Function Calling Official Documentation"){:target="_blank"}
- [GoogleCloudPlatform/generative-ai-samples on GitHub](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/function-calling/intro_function_calling.ipynb "Gemini Function Calling Examples"){:target="_blank"}
---