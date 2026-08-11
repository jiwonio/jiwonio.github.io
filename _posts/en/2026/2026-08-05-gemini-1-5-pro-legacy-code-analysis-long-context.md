---
layout: post
title: 'Cutting Legacy Analysis Time with Long Context (Gemini 1.5 Pro Workflow)'
slug: gemini-1-5-pro-legacy-code-analysis-long-context
lang: en
translation_key: gemini-1-5-pro-legacy-code-analysis-long-context
post_type: deep-dive
date: 2026-08-05 11:36:38 +0900
updated: 2026-08-11 12:00:00 +0900
categories:
- AI
tags:
- Gemini
- LLM
- Legacy Code
description: A practical long-context workflow for reading legacy dependencies across
  many files—what to include, what to exclude, failure modes, and a verification loop.
image: /uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp
ai_generated: true
permalink: /en/posts/gemini-1-5-pro-legacy-code-analysis-long-context/
---
A change request lands on an old service. The original owner has left; the wiki only documents deploy order. Payment logic is split across controllers, services, models, and an external client, so name search alone does not reveal the real call stack. Pasting one file at a time into an LLM loses File A’s context by the time you ask about File B, and re-pasting prior answers costs more energy than reading the code.

A long context window helps by letting the model **read a related module in one shot**. Gemini 1.5 Pro popularized million-token context; later models reuse the same workflow pattern. This post focuses on **what to pack and what to drop**, and **where to verify when the answer is wrong**. Tool Use (function calling) is covered in a [separate post](/en/posts/gemini-1-5-pro-tool-use-connecting-llms/).

<!--more-->
![Cutting Legacy Analysis Time with Long Context (Gemini 1.5 Pro Workflow)](/uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp "Cutting Legacy Analysis Time with Long Context (Gemini 1.5 Pro Workflow)")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## Problem: fragmented context

Legacy analysis is slow less because one file is hard, and more because **context is sliced by file boundaries**. Suppose a payment request spans roughly:

* `controllers/payment_controller.rb` — HTTP entry, parameter checks
* `services/payment_service.rb` — business rules, multiple models
* `models/order.rb` / `models/user.rb` — state and permissions
* `lib/external_api_client.rb` — payment gateway

If you only paste `payment_service.rb` and ask for bugs, the model lacks order transitions and client timeouts, so it invents **plausible guesses from half the story**. Short-context chat also [loses earlier files mid-session](/en/posts/antigravity-cli-context-loss-mistakes/). Long context tries to fix both by **pinning related files in one prompt**.

## What long context changes (and what it does not)

A million tokens is enough for most mid-size modules. A larger window does **not** automatically fix everything:

| Helps | Does not replace |
| --- | --- |
| First draft of cross-file call flow | Hallucinated methods or config keys |
| A map of which files matter | Noise from `vendor` / `node_modules` dumps |
| Refactor candidate lists | Real production incident reproduction |

Treat long context as a **map-drawing tool**, not a substitute for pre-deploy verification.

## Workflow: scope → pack → ask → verify

### 1. Start at the module boundary, not the monorepo root

A common first failure is “one `find` from repo root.” Fixtures, generated code, and dependency trees burn tokens and dilute attention. Narrow the domain first:

1. Lock 1–2 entry files (e.g. `PaymentController#create`)
2. Collect 1-hop and 2-hop files from imports and call sites
3. Only then expand the domain directory (`app/services/payment*`)

### 2. Pack script with exclusions

```bash
cd path/to/legacy/project

# Rough token gauge: for ASCII-heavy code, chars / 4 is a ballpark
# Aim first pass ~80k–200k tokens (check product limits and pricing)

OUT=combined_payment.txt
rm -f "$OUT"

{
  echo "Project structure (payment-related):"
  find app/controllers app/services app/models lib \
    -type f -name '*payment*' -o -name '*order*' 2>/dev/null | head -200
  echo
  echo "--- End of structure ---"
  echo
} > "$OUT"

find app lib \
  \( -path '*/node_modules/*' -o -path '*/vendor/*' -o -path '*/tmp/*' \
     -o -path '*/.git/*' -o -name '*.min.js' \) -prune -o \
  -type f \( -name '*.rb' -o -name '*.rake' \) -print0 \
| while IFS= read -r -d '' file; do
    case "$file" in
      *payment*|*order*|*checkout*) ;;
      *) continue ;;
    esac
    echo "--- File: $file ---" >> "$OUT"
    cat "$file" >> "$OUT"
    echo >> "$OUT"
  done

wc -c "$OUT"
# e.g. 400KB ≈ ~100k tokens (high variance) — leave headroom under the limit
```

Failure case: dumping unrelated `app/admin` plus spec fixtures once produced a summary where **`PaymentService#settle_async!` was the “core path”**—a symbol that did not exist in production code (it looked like a mix of doubles/mocks and real methods). The hard rule afterward: **re-search every symbol in the answer with `rg`**.

### 3. Prompt: force execution flow + evidence

```text
You are a backend engineer inheriting a legacy payment module.
Answer using ONLY the code below. If a class, method, or config key is not
present, write "not found in provided code" — do not invent.

[Goals]
1. Numbered execution flow from PaymentController#create to external PG call.
   Each step: file path / Class#method / one-line role.
2. PaymentService core responsibility in 1–2 sentences, with method names in
   parentheses as evidence.
3. At most 3 bug or performance risks. Each must cite a nearby symbol/file.
4. Mermaid ERD only for relationships visible in code/migrations.
   No guessed columns.

Output English Markdown. Mark low confidence explicitly.

--- BEGINNING OF CODEBASE ---
(full combined_payment.txt)
--- END OF CODEBASE ---
```

Forcing **evidence** beats a “20-year veteran” persona. If step 1’s flow is wrong, discard the rest.

### 4. Verification loop (budget 15–30 minutes)

| Step | Action | Pass bar |
| --- | --- | --- |
| Symbol check | `rg` every class/method in the answer | All exist in code |
| Entry trace | IDE Find Usages from `create` | Matches claimed next hop |
| Counter-question | “Any early return that breaks this flow?” | Branches exist in code |
| Cost check | Input tokens and latency | No full dump for trivial follow-ups |

Honest Before/After ranges (highly team-dependent):

* **Before**: 3–6 hours to find files and sketch the stack, with 1–2 wrong entry assumptions
* **After (scoped long context)**: 20–40 minutes pack + first map, ~15 minutes symbol verify, remaining time on real debugging
* **When After is worse**: whole-repo dump + no verification → half a day on a bad refactor plan

## Cost, limits, and ops notes

* **Cost**: Do not re-send a huge pack for every tiny question. Use long context for 1–2 map passes, then short context on a few files. Align budget with [Vertex AI / Gemini pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing).
* **Needle in a haystack**: Retrieval quality can get uneven as context grows. Re-mention critical paths in the question, or constrain (“use only `external_api_client.rb` as evidence”). See the [Long context](https://ai.google.dev/gemini-api/docs/long-context) guide.
* **Latency**: Tens of seconds to minutes fit **async analysis**, not every pair-programming micro-question.
* **Model names change**: The durable pattern is long context + narrow scope + symbol verification. 1.5 Pro is the milestone that made that pattern practical.

## When to use it

| Situation | Approach | Why |
| --- | --- | --- |
| Small side project | Short-context IDE chat | Module fits on one screen |
| New feature, 3–5 files | Attach those files | Long window cost not worth it |
| Inherited domain, 15+ files | Long context **map**, then narrow debug | Exploration time dominates |
| Production hot-fix | Logs/metrics first; model secondary | Hallucination cost is high |

## Conclusion

Long context is a tool for **putting fragmented legacy context on one board**. It works when you (1) cut scope to a module, (2) exclude noise, (3) re-verify every symbol against the repo, and (4) avoid replaying giant dumps. Blind paste creates false confidence faster than it creates understanding.

### References
- [Google AI, "Our next-generation model: Gemini 1.5"](https://blog.google/technology/ai/google-gemini-next-generation-model-february-2024/ "Google AI Blog on Gemini 1.5"){:target="_blank"}
- [Google AI for Developers, "Long context"](https://ai.google.dev/gemini-api/docs/long-context "Gemini API long context"){:target="_blank"}
- [Google Cloud, "Vertex AI pricing"](https://cloud.google.com/vertex-ai/generative-ai/pricing "Vertex AI Pricing Page"){:target="_blank"}
