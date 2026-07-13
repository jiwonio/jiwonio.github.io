---
layout: post
title: 使用 Antigravity CLI 时遇到的上下文丢失问题
slug: antigravity-cli-context-loss-mistakes
lang: zh
translation_key: antigravity-cli-context-loss-mistakes
post_type: deep-dive
date: 2026-07-08 00:00:00 +0900
categories:
- AI
tags:
- Antigravity CLI
- 上下文管理
- CLI 工作流
- 编码自动化
description: 本文重现了 Antigravity CLI 在实际应用中因上下文丢失导致的问题，并逐步整理了防范模式。
image: /uploads/antigravity-cli-context-loss-mistakes/thumbnail.webp
ai_generated: true
permalink: /zh/posts/antigravity-cli-context-loss-mistakes/
---
我在遗留服务迁移工作中首次引入了 Antigravity CLI。最初几天一切顺利，但随着文件数量的增加，CLI 开始重复修改“已修改的文件”。经检查发现，是会话之间上下文被重置，导致 CLI 在完全不了解之前决策的情况下继续执行后续操作。结果，同一个函数的签名被修改了两次，期间编写的测试也因此两次都失效了。

本文将探讨 Antigravity CLI 如何处理上下文、上下文丢失发生在哪里，以及如何确保意图跨会话持续存在的模式。如果你正在经历“CLI 随意修改代码”的症状，那么原因很可能不是工具本身的 bug。

阅读本文，你将了解 Antigravity CLI 在跨越会话边界时上下文为何会中断，以及应采用何种文件结构和调用模式来防止这种情况发生。

<!--more-->

![使用 Antigravity CLI 时遇到的上下文丢失问题](/uploads/antigravity-cli-context-loss-mistakes/thumbnail.webp "使用 Antigravity CLI 时遇到的上下文丢失问题")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI 生成图片</small>
</p>

-----

## 确认症状

可重现的场景如下：

1. 在第一个会话中，指示将 `user_service.py` 中 `get_user` 函数的返回类型从 `dict` 更改为 `UserDTO`。
2. CLI 完成修改。
3. 关闭终端，第二天开启新会话。
4. 指示重构 `order_service.py` 中调用 `get_user` 的部分。
5. CLI 将 `get_user` 的返回类型再次改回 `dict`。

原因很简单。Antigravity CLI 默认按会话管理上下文。当新会话开始时，前一个会话中做出的决策或文件修改历史都不会被传递。CLI 只读取当前文件状态，如果文件中的注释或类型提示不完整，它就会推断回原始模式。

---

## 上下文丢失的三个点

### 1. 会话边界

这是最常见的点。`antigravity session` 对象在进程终止时会从内存中消失。虽然可以使用 `--session-file` 选项将会话状态保存到文件中，但其默认值是关闭的。

```bash
# 将会话状态保存到文件 — 默认不保存
antigravity run --session-file .ag/session.json "将 get_user 返回类型更改为 UserDTO"
```

如果省略此选项，下次运行时将没有会话文件，导致上下文完全为空的状态下开始。

### 2. 超出范围

一次性包含太多文件会导致内部上下文窗口被截断。Antigravity CLI 会将指令中提及的文件列表转换为令牌，如果超出限制，后面的文件就会丢失。此时，丢失文件中定义的类型或接口也会被截断，从而导致与之前的决策相矛盾的修改。

```bash
# 错误示例：一次性传递整个目录
antigravity run --include "src/**/*.py" "应用 UserDTO"

# 较优示例：按模块拆分
antigravity run --include "src/user/*.py" "应用 UserDTO"
antigravity run --include "src/order/*.py" --session-file .ag/session.json "修改 UserDTO 调用部分"
```

### 3. 隐式决策的缺失

CLI 读取文件并推断模式。如果领域决策（“此服务强制使用 DTO 层”）未在代码中明确说明，那么在新会话中就没有依据再次推断该决策。结果，CLI 会遵循文件中显示的最简单模式。

---

## 防范模式

### 使用上下文文件明确决策

在项目根目录下放置一个 `.ag/context.md` 文件，并将其自动包含到所有会话中。此文件中只写入代码中无法读取的领域决策。

```markdown
<!-- .ag/context.md -->
# 项目上下文

## 架构决策 (ADR)
- 服务层返回 DTO。禁止直接返回 dict。
- UserDTO：参考 src/models/dto.py
- 外部 API 响应必须解析后转换为 DTO。

## 当前进行的迁移
- get_user：dict → UserDTO 转换完成 (2025-07-01)
- get_order：进行中
```

始终使用 `--context` 选项包含此文件。

```bash
antigravity run \
  --context .ag/context.md \
  --session-file .ag/session.json \
  --include "src/order/*.py" \
  "将 UserDTO 模式应用于 get_order"
```

### 决定是否 Git 跟踪会话文件

是否将 `.ag/session.json` 添加到 Git 取决于团队规模。

- **单独工作**：可以添加。会话状态会随分支一同管理。
- **团队协作**：添加到 `.gitignore` 中，只共享 `context.md`。会话文件包含着每个开发者的个人执行状态，容易产生冲突。

```gitignore
# .gitignore
.ag/session.json
.ag/*.log
# context.md 进行跟踪 — 团队共享决策文件
```

### 拆分执行单元

限制单个执行所修改的文件数量。根据经验，单个执行中文件数量不超过 10 个，每个文件行数不超过 200 行，是上下文不会被截断的安全范围。准确的令牌限制可能因版本而异，因此建议首先使用 `--dry-run` 检查包含的文件列表。

```bash
# 实际修改前检查包含的文件列表
antigravity run --dry-run \
  --context .ag/context.md \
  --include "src/**/*.py" \
  "应用 UserDTO"
```

如果在输出中看到“context truncated”警告，则需要缩小 `--include` 的范围。

---

## 实际工作流的改变

以前，我都是即兴调用 Antigravity CLI。在终端中，需要时就敲一行命令，没有会话文件，也没有上下文文件。如果结果不满意，就回滚并重新尝试。

现在，我采用的模式是先根据迁移单元更新 `.ag/context.md`，然后按模块延续会话。这看起来可能很麻烦，但实际花费的时间大约在 5 分钟以内。相比之下，跟踪并回滚错误的修改所需的时间要长得多。

```bash
# 迁移开始时更新上下文文件
echo "- get_order: 进行中 ($(date +%Y-%m-%d))" >> .ag/context.md

# 按模块顺序执行
antigravity run \
  --context .ag/context.md \
  --session-file .ag/session.json \
  --include "src/order/service.py" \
  "将 get_order 返回类型更改为 OrderDTO"

antigravity run \
  --context .ag/context.md \
  --session-file .ag/session.json \
  --include "src/order/repository.py" \
  "根据 service 变更调整 repository"
```

---

## 团队引入时需要额外注意的事项

如果团队成员超过 3 人，需要确定 `context.md` 的所有权。如果任何人都可以修改，不同的决策可能会混杂在一起，反而产生噪音。将 `context.md` 纳入 PR 审查范围，并以 ADR（架构决策记录）的形式进行管理，可以更容易追踪变更原因。

此外，如果在 CI 中自动运行 Antigravity CLI，如果不将会话文件路径通过环境变量进行隔离，并行工作流之间会话文件会发生冲突。

```yaml
# .github/workflows/antigravity.yml 部分
- name: Run Antigravity
  env:
    AG_SESSION_FILE: .ag/session-${{ github.run_id }}.json
  run: |
    antigravity run \
      --context .ag/context.md \
      --session-file $AG_SESSION_FILE \
      --include "src/**/*.py" \
      "修复 lint"
```

---

## 结论

| 情况 | 推荐模式 | 原因 |
|------|-----------|------|
| 个人副项目 | `--session-file` + `context.md` 基础配置 | 足以防止会话重启时上下文丢失 |
| 3-5人初创团队 | Git 跟踪 `context.md`，将会话文件加入 `.gitignore` | 需要共享决策，但要避免会话冲突 |
| 遗留系统迁移中 | 按模块执行 + ADR 格式的 `context.md` | 文件数量越多，上下文被截断的风险越大 |
| 包含 CI 自动化 | 基于 `run_id` 区分会话文件 | 防止并行工作流之间会话文件冲突 |

Antigravity CLI 本身并没有错误。问题在于我没有理解工具如何处理会话边界。仅仅通过显式管理上下文文件和会话文件，大多数“随意修改”的症状就会消失。

---

### 参考资料
- [OpenAI: Best practices for prompt engineering](https://platform.openai.com/docs/guides/prompt-engineering){:target="_blank"}
- [Anthropic: Long context tips](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips){:target="_blank"}
