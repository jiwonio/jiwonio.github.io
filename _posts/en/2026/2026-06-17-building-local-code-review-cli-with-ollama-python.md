---
layout: post
title: Building a Local Code Review CLI with Ollama and Python
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
description: Learn how to build a code review CLI tool that runs locally using Ollama
  and Llama 3, avoiding API costs and security concerns. This guide covers practical
  tips, from prompt design to understanding its limitations.
image: /uploads/building-local-code-review-cli-with-ollama-python/thumbnail.webp
lang: en
translation_key: building-local-code-review-cli-with-ollama-python
permalink: /en/posts/building-local-code-review-cli-with-ollama-python/
post_type: deep-dive
ai_generated: true
---
Code review is a core process for maintaining software quality, but it can also be a time-consuming task for team members. While AI tools like GitHub Copilot and ChatGPT have become excellent aids, security concerns about sending sensitive code to external APIs and ongoing cost issues remain.

In this article, we'll build our own code review CLI (Command-Line Interface) tool that operates completely independently in a local environment to solve these problems. Using **Ollama**, a popular local LLM execution tool, and **Python**, we will explore how to get fast and secure feedback on your code without an external network connection.

<!--more-->
![Building a Local Code Review CLI with Ollama and Python](/uploads/building-local-code-review-cli-with-ollama-python/thumbnail.webp "Building a Local Code Review CLI with Ollama and Python")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## Why a Local Code Reviewer?

Instead of using commercial AI services, running an LLM locally to create a code review tool offers several clear advantages.

1.  **Security**: Your source code never leaves your personal computer or internal servers. This is a crucial advantage when dealing with code that is subject to strict corporate security policies or should not be exposed externally.
2.  **Cost**: Apart from the initial hardware investment, there are no additional costs for API calls. You can experiment and use it as much as you want without worry.
3.  **Offline Operation**: You can perform code reviews even in environments with unstable or no internet connection.
4.  **Customization**: You can freely modify the prompts and models to create a tool that fits your team's specific code review style and rules.

## Prerequisites: Installing Ollama and Llama 3

First, you need to prepare an environment to run LLMs locally. Ollama is an excellent tool that allows you to install and run LLMs with simple commands, without complex configurations.

Visit the official website, [ollama.com](https://ollama.com "Ollama Official Website"){:target="_blank"}, to download and install the program for your operating system.

Once the installation is complete, run the following command in your terminal to download the latest Llama 3 8B model. The Llama 3 8B model runs relatively smoothly even on a typical developer's laptop and shows decent performance for code-related tasks.

```bash
# Download the Llama 3 8B model locally.
ollama pull llama3
```

After the model download is complete, you can check the list of installed models with the `ollama list` command.

## Core Logic: Designing the Python CLI Script

Now, let's write a Python CLI script that reads a code file and requests a review from the Llama 3 model running via Ollama.

### 1. Project Structure and Dependency Installation

Let's start with a simple structure. All we need is a single file, `review.py`. Install the `ollama` Python library required to run the script.

```bash
# Install the Ollama Python client library
pip install ollama
```

### 2. Writing the CLI Script (`review.py`)

We'll use `argparse` to accept a file path as an argument, allowing users to easily run the script from the terminal with `python review.py <file_name>`.

```python
# review.py

import ollama
import argparse
import sys

# Define the system prompt for code review.
# It clearly instructs the model on the role it should assume.
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
    Reads the code from a specified file and performs a code review via Ollama.
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
        # Call the Ollama streaming API
        stream = ollama.chat(
            model='llama3',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f"Please review the following Python code:\n\n```python\n{code_content}\n```"},
            ],
            stream=True,
        )

        print(f"\n--- Code Review for {file_path} ---\n")
        # Print the streaming response in real-time
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

The core of this script is the `SYSTEM_PROMPT`. It clearly defines the LLM's role as an "expert code reviewer" and provides specific instructions on what aspects to analyze (e.g., bugs, readability, performance). This is crucial for obtaining more consistent and high-quality review results.

## Execution and Result Analysis

Let's create a simple example Python file to review.

**`example.py`**
```python
# A function that takes a user's name and age and greets them
def great_user(name, age):
    # Prints a different message if the age is under 18
    if age < 18:
        msg = "Hello " + name + ", you are still young!"
    else:
        msg = "Hello " + name + ", welcome!"
    
    # Prints the message multiple times for emphasis
    for i in range(5):
        print(msg)

# Test the function
great_user("Alice", 25)
great_user("Bob", 15)
```

Now, let's run our review script in the terminal.

```bash
python review.py example.py
```

After a moment, the code review results generated by the Llama 3 model will be printed in a streaming format.

```
--- Code Review for example.py ---

*   **Clarity and Readability**: The function name `great_user` could be more descriptive, perhaps `greet_user` would be clearer. Using f-strings for string formatting is more modern and readable than string concatenation (e.g., `f"Hello {name}, welcome!"`).
*   **Best Practices**: The magic number `18` could be defined as a constant, like `LEGAL_ADULT_AGE = 18`, to improve maintainability.
*   **Logic and Bugs**: The loop `for i in range(5):` prints the same message five times. This might not be the intended behavior. If the goal is emphasis, a comment explaining why would be helpful. Otherwise, it seems redundant.
*   **Performance**: For this simple function, performance is not a concern. However, in a real-world scenario, printing inside a loop within a function that returns a value can be an undesirable side effect. It's often better to return the message and let the caller handle the printing.

--- End of Review ---
```

As you can see from the results, the local LLM provides quite meaningful feedback, such as suggesting a fix for a typo in the function name, recommending the use of f-strings, pointing out the magic number issue, and identifying the unnecessary loop.

## Practical Considerations: Limitations and Trade-offs

While this tool is clearly useful, it's important to be aware of some obvious limitations before applying it directly in a real-world setting.

-   **Lack of Context**: This script only analyzes a single file. It doesn't understand the project's overall structure, dependencies on other files, or the complete business logic. Therefore, it has limitations in performing architectural-level reviews or finding errors in complex logic.
-   **Model Performance**: Smaller models like Llama 3 8B may have lower code comprehension and reasoning abilities compared to top-tier models like GPT-4 or Claude 3 Opus. They can sometimes generate inaccurate or generic feedback. Using a larger model (e.g., `llama3:70b`) can improve quality but requires higher-spec hardware (especially VRAM).
-   **Hallucination**: Like all LLMs, local models can also make up plausible-sounding but incorrect information. Specific claims like "This code is not compatible with the latest version of library X" must be verified manually.
-   **Inconsistent Results**: Reviewing the same code multiple times may produce slightly different results.

## Conclusion

A local code review CLI using Ollama is an excellent way to get AI assistance while resolving security and cost issues, without relying on external services. It is particularly useful for handling sensitive code or for automating a first-pass review of simple code styles.

This tool cannot replace an in-depth review by an experienced human developer, but it holds significant value as a `self-check` tool for improving code before requesting a review, or as an `assistant` to reduce the reviewer's workload. You could take this further by integrating it with Git pre-commit hooks to perform reviews automatically before committing, or by specifying your team's coding conventions more concretely in the prompt to develop it into a customized reviewer.

### References
- [Ollama Official Website](https://ollama.com "Ollama"){:target="_blank"}
- [Ollama Python Library (GitHub)](https://github.com/ollama/ollama-python "ollama-python on GitHub"){:target="_blank"}