---
layout: post
title: '用长上下文缩短遗留代码分析时间（Gemini 1.5 Pro 工作流）'
slug: gemini-1-5-pro-legacy-code-analysis-long-context
lang: zh
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
description: 用长上下文一次读懂散落在多文件中的遗留依赖：该装什么、该排除什么、失败案例与校验闭环。
image: /uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp
ai_generated: true
permalink: /zh/posts/gemini-1-5-pro-legacy-code-analysis-long-context/
---
旧服务接到修改需求。负责人已离职，Wiki 只剩发布顺序。支付逻辑分散在控制器、服务、模型与外部客户端，仅靠函数名搜索很难辨认真实调用栈。把代码按文件粘进 LLM 时，问到文件 B 往往已丢掉 A 的上下文，反复粘贴旧答案的成本比读代码还高。

长上下文窗口通过让模型 **一次性阅读相关模块** 来缓解这一问题。Gemini 1.5 Pro 把百万级 token 上下文带进日常工作流，后续模型仍沿用同一套路。本文聚焦 **装什么、丢什么**，以及 **答案出错时如何校验**。Tool Use（函数调用）见[另一篇文章](/zh/posts/gemini-1-5-pro-tool-use-connecting-llms/)。

<!--more-->
![用长上下文缩短遗留代码分析时间（Gemini 1.5 Pro 工作流）](/uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp "用长上下文缩短遗留代码分析时间（Gemini 1.5 Pro 工作流）")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 问题：碎片化的上下文

遗留分析慢，往往不是「单文件难」，而是 **上下文被文件边界切开**。假设一次支付请求大致分散如下：

* `controllers/payment_controller.rb` — HTTP 入口、参数校验
* `services/payment_service.rb` — 业务规则、多模型调用
* `models/order.rb` / `models/user.rb` — 状态与权限
* `lib/external_api_client.rb` — 支付网关

只贴 `payment_service.rb` 并要求找 bug 时，模型不知道订单状态迁移与客户端超时策略，只能基于一半信息给出 **看起来合理的猜测**。短上下文还会在会话中途[丢失更早的文件](/zh/posts/antigravity-cli-context-loss-mistakes/)。长上下文试图用 **同一提示中固定相关文件** 同时压住这两类问题。

## 长上下文改变什么、不改变什么

百万 token 足以一次塞进多数中小型模块源码。窗口变大 **不会** 自动解决一切：

| 有帮助的一侧 | 无法替代的一侧 |
| --- | --- |
| 跨文件调用流的初稿 | 捏造不存在的方法或配置键 |
| 「哪些文件相关」的地图 | 把 `vendor`/`node_modules` 一并灌入的噪声 |
| 重构候选列表 | 生产故障的真实复现 |

把长上下文当作 **画地图的工具**，而不是上线前验证的替代品。

## 实务流程：定界 → 打包 → 提问 → 校验

### 1. 从模块边界开始，而不是 monorepo 根目录

常见失败是「仓库根目录一次 `find`」。测试夹具、生成代码与依赖目录只会烧 token、稀释信号。先收窄领域：

1. 锁定 1～2 个入口文件（如 `PaymentController#create`）
2. 按 import/require 与调用收集 1-hop、2-hop
3. 仍不足时再扩大同域目录（`app/services/payment*`）

### 2. 带排除列表的打包脚本

```bash
cd path/to/legacy/project

# 粗算：ASCII 为主的代码可按 字符数/4 估 token
# 首轮目标示例：8万～20万 token（核对产品上限与计价）

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
```

失败案例：曾把无关的整个 `app/admin` 与 spec 夹具一起塞入，模型把 **并不存在的 `PaymentService#settle_async!`** 总结成「核心路径」（更像是 double/mock 名与真实方法混杂）。此后固定一步：**对答案中的每个符号用 `rg` 回搜仓库**。

### 3. 提示词：强制执行流与证据

```text
你是接手遗留支付模块的后端工程师。
仅依据下方代码作答。代码中不存在的类、方法或配置键请写「提供代码中无法确认」，
禁止编造。

[目标]
1. 从 PaymentController#create 到外部 PG 调用的编号执行流。
   每步：文件路径 / 类#方法 / 一行职责。
2. PaymentService 的核心职责 1～2 句，括号内写作为证据的方法名。
3. 最多 3 条 bug/性能风险，每条必须引用邻近符号/文件。
4. Mermaid ERD 仅包含代码/迁移中可见的关系，禁止猜测列。

用简体中文 Markdown 输出。不确定时明确降低置信度。

--- BEGINNING OF CODEBASE ---
(combined_payment.txt 全文)
--- END OF CODEBASE ---
```

**强制证据** 通常比「20 年架构师人设」更能压幻觉。若第 1 步执行流错误，应丢弃其余结论。

### 4. 校验闭环（预留 15～30 分钟）

| 步骤 | 动作 | 通过标准 |
| --- | --- | --- |
| 符号校验 | 对答案中的类/方法跑 `rg` | 全部存在于代码 |
| 入口追踪 | IDE Find Usages：create → service | 与声称的下一跳一致 |
| 反证提问 | 「有无 early return 打断该流？」 | 分支真实存在 |
| 成本检查 | 输入 token 与延迟 | 琐碎追问不再整包重放 |

不加夸张的 Before/After（因团队而异）：

* **Before**：找相关文件 + 画调用栈草稿 3～6 小时，错误入口假设 1～2 次
* **After（模块范围长上下文）**：打包与一阶地图 20～40 分钟，符号校验约 15 分钟，其余时间做真实调试
* **After 反而更慢**：整仓倾倒 + 不做校验 → 错误重构计划浪费半天

## 成本、限制与运维

* **成本**：不要每个小问题都重发超大打包。大图 1～2 次即可，后续用少数文件的短上下文往往够用。预算对齐 [Vertex AI / Gemini 价格](https://cloud.google.com/vertex-ai/generative-ai/pricing)。
* **大海捞针**：上下文越长，对特定片段的召回可能越不稳。在问题中重申关键路径，或约束「仅以 `external_api_client.rb` 为据」。见官方 [Long context](https://ai.google.dev/gemini-api/docs/long-context)。
* **延迟**：数十秒到数分钟更适合 **异步分析**，而不是每次结对编程的微问题。
* **模型名会变**：可沉淀的是「长上下文 + 窄范围 + 符号校验」；1.5 Pro 是把该模式带进实务的里程碑。

## 何时使用

| 场景 | 做法 | 原因 |
| --- | --- | --- |
| 小型 side project | 短上下文 IDE 对话 | 模块一屏能看完 |
| 新功能，3～5 个文件 | 直接附加这些文件 | 长窗口性价比低 |
| 接手领域，15+ 文件 | 长上下文 **画地图** 再收窄调试 | 探索时间占比高 |
| 生产热修 | 日志/指标优先，模型辅助 | 幻觉代价高 |

## 结论

长上下文是把遗留分析中 **碎片化上下文摊到同一张图上的工具**。要见效需要：(1) 按模块切范围，(2) 设排除列表，(3) 把答案里每个符号再对回仓库，(4) 不频繁重放巨型打包。只会整仓粘贴，往往先制造错误自信，而不是理解。

### 参考文献
- [Google AI, "Our next-generation model: Gemini 1.5"](https://blog.google/technology/ai/google-gemini-next-generation-model-february-2024/ "Google AI Blog on Gemini 1.5"){:target="_blank"}
- [Google AI for Developers, "Long context"](https://ai.google.dev/gemini-api/docs/long-context "Gemini API long context"){:target="_blank"}
- [Google Cloud, "Vertex AI pricing"](https://cloud.google.com/vertex-ai/generative-ai/pricing "Vertex AI Pricing Page"){:target="_blank"}
