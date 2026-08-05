---
layout: post
title: 'Reducing Legacy Analysis Time with Gemini 1.5 Pro: How to Leverage Long Context
  Windows'
slug: gemini-1-5-pro-legacy-code-analysis-long-context
lang: en
translation_key: gemini-1-5-pro-legacy-code-analysis-long-context
post_type: deep-dive
date: 2026-08-05 11:36:38 +0900
categories:
- AI
tags:
- Gemini
- LLM
- Legacy Code
description: This post covers practical ways to leverage Gemini 1.5 Pro's million-token
  context window to understand dependencies in legacy code scattered across multiple
  files and devise refactoring plans.
image: /uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp
ai_generated: true
permalink: /en/posts/gemini-1-5-pro-legacy-code-analysis-long-context/
---
A new feature request came in for an old project. The original developer has left, and documentation is sparse. I need to modify a specific feature, but its logic is spread across at least 10 files. Searching for a function name yields dozens of results, and just identifying the true call stack takes half a day.

Pasting code file by file into existing LLM tools and asking questions had clear limitations. After asking about File A and moving to File B, the model quickly lost context of File A. Repeating the process of re-pasting previous answers and code to maintain conversational context was more tiring than analyzing the code itself. Ultimately, I ended up reading the code and mapping dependencies manually, just like before LLMs.

In this post, I'll introduce a concrete workflow that uses Gemini 1.5 Pro's million-token context window to analyze an entire distributed legacy codebase at once and identify core logic.

<!--more-->
![Reducing Legacy Analysis Time with Gemini 1.5 Pro: How to Leverage Long Context Windows](/uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp "Reducing Legacy Analysis Time with Gemini 1.5 Pro: How to Leverage Long Context Windows")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## Problem Definition: Fragmented Context

The fundamental reason legacy code analysis is difficult is that code context is fragmented across multiple files. For instance, logic handling a user's payment request might be scattered like this:

*   `controllers/payment_controller.rb`: Receives HTTP requests and calls services.
*   `services/payment_service.rb`: Handles business logic, interacts with multiple models.
*   `models/order.rb`: Manages order status.
*   `models/user.rb`: Retrieves user information.
*   `lib/external_api_client.rb`: Integrates with external payment gateway APIs.

In such a scenario, if I input only the `payment_service.rb` file into an LLM and ask, "Find problems in this code," the model won't know the internal implementations of `Order` or `User` models, nor the `ExternalAPIClient`'s interface. It will only provide speculative answers based on partial information. Existing models' context windows (e.g., 32K, 128K tokens) were utterly insufficient to contain code of this scale at once. This is the core of the problem we face.

## How Gemini 1.5 Pro's Long Context is Different

Gemini 1.5 Pro supports a context window of up to 1 million tokens. This is equivalent to several full-length novels, and enough to input the entire source code of a typical small to medium-sized service or module at once.

A large context window means more than just being able to input more text. It allows the model to "read" all files in a codebase simultaneously, comprehensively understanding cross-references, data flows, and hidden dependencies between files. In essence, it provides the foundation to directly address the fragmented context problem.

## Practical Workflow: Codebase Consolidation and Prompt Design

Now, let's look at the specific steps for effectively inputting a legacy codebase into Gemini 1.5 Pro and requesting analysis.

### 1. Consolidate Target Code

First, you need to combine all source code files related to the module you want to analyze into a single text file. Manually copying and pasting dozens of files is inefficient, so using a simple shell script is recommended.

```bash
# Move to the directory to be analyzed
cd path/to/legacy/project

# 1. First, understand the file structure,
# 2. Then, combine relevant files into a single text file.
echo "Project structure:" > combined_code.txt
tree . -I 'tmp|log|vendor' >> combined_code.txt
echo "\n--- End of structure ---\n" >> combined_code.txt

# Example for combining the entire 'app' directory of a Ruby on Rails project
# You should modify the `find` command's path and extensions to suit your project.
find app -name "*.rb" -print0 | while IFS= read -r -d $'\0' file; do
    echo "--- File: $file ---" >> combined_code.txt
    cat "$file" >> combined_code.txt
    echo "\n" >> combined_code.txt
done
```

This script first records the entire file structure at the top of the text file using the `tree` command, helping the model understand code locations. Then, it uses the `find` command to locate all files with specific extensions and sequentially appends them to `combined_code.txt`.

### 2. Design the Prompt

Just as important as well-consolidated code is the prompt itself. You need to specify a clear role, objective, and output format for the model to get the desired analysis results.

Here is an example prompt for legacy code analysis:

```text
You are a backend architect with 20 years of experience in Ruby on Rails. I need to analyze an old payment module for maintenance. The entire content of the `combined_code.txt` file is provided below.

After thoroughly analyzing this entire codebase, please answer the following questions in detail:

[Analysis Goals]
1.  Explain the complete code execution flow, starting from the `create` action in `controllers/payment_controller.rb` to the external payment gateway API call, when a user requests a payment via the API. Specify which class and method in which file is called at each step.
2.  What is the core responsibility of the `PaymentService` class?
3.  Identify 3 potential bugs or severe performance bottlenecks in this codebase. For each, explain the reason and suggest improvements. Examples include N+1 query issues, improper exception handling, or hardcoded configuration values.
4.  Draw the database schema for this payment module in Mermaid JS ERD diagram format.

Please provide the answers in Korean, clearly separating each item with Markdown.

--- BEGINNING OF CODEBASE ---
(Paste the entire content of the combined_code.txt file generated above here)
--- END OF CODEBASE ---
```

This prompt includes the following key elements:

*   **Persona Assignment**: Assigns the role of a "20-year experienced backend architect" to encourage analysis from a professional perspective.
*   **Clear Context Provision**: Explicitly states that the entire codebase is provided.
*   **Specific Questions**: Demands concrete and actionable deliverables—such as execution flow, class responsibilities, potential issues, and database schema visualization—rather than just a general analysis request.

## Considerations: Token Cost and Limitations

While powerful, a long context window isn't a silver bullet. There are several considerations before applying it to real-world tasks.

*   **API Cost**: Using 1 million tokens as input can incur significant costs. Instead of inputting the entire code for every minor question, it's reasonable to use it intermittently for important analyses, such as grasping the big picture or planning complex refactorings.
*   **"Needle in a Haystack" Problem**: Research suggests that as context becomes very long, the model might miss specific information within it. When performing critical analysis, it's essential to guide the model's attention to specific files or logic via the prompt, and to critically review the answers.
*   **Response Latency**: Due to the large input size, receiving a response can take tens of seconds to several minutes. It's more suitable for asynchronous analysis tasks than real-time conversations.

## Conclusion: Choosing the Right Tool for the Situation

Gemini 1.5 Pro's long context window offers a highly effective solution for the specific problem of legacy code analysis. However, it's not optimal for all situations. Choosing the right model and approach for your specific circumstances is crucial.

| Situation                            | Recommendation                 | Reason                                                                                                                                                                                                                                                                                                            |
| :----------------------------------- | :----------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Solo Developer's Side Project**    | **GPT-4o or Claude 3 Sonnet**  | Free tiers are often sufficient, and the overall codebase is small, reducing the need for long context. Faster response times are more important.                                                                                                                                                                |
| **New Feature Development at a 5-Person Startup** | **Gemini 1.5 Pro (Use as needed)** | Normally, use short-context models for rapid development. Only leverage long context when taking on complex new modules or requiring large-scale refactoring to maximize productivity.                                                                                                                 |
| **Maintaining Large-Scale Legacy Systems** | **Gemini 1.5 Pro (Actively utilize)** | Dramatically reduces the time spent understanding complex dependencies across multiple files. The benefit of saving developer analysis time far outweighs the token costs.                                                                                                                                |

Ultimately, what's crucial is to precisely understand the characteristics of new technologies and intelligently apply them to the nature of the problems we face. Long context windows have the potential to change how we understand code, and will become a new weapon for many developers wrestling with legacy systems.

## References
- [Google Gemini Next-Generation Model (February 2024)](https://blog.google/technology/ai/google-gemini-next-generation-model-february-2024/){:target="_blank"}
- [Vertex AI Generative AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing){:target="_blank"}
