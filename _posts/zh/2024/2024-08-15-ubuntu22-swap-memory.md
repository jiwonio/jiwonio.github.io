---
layout: post
title: 在 Ubuntu 22.04 LTS 上配置交换内存
tags:
- ubuntu
image: /uploads/ubuntu22-swap-memory/thumbnail.webp
lang: zh
translation_key: ubuntu22-swap-memory
slug: ubuntu22-swap-memory
description: 在 Ubuntu 22.04 LTS 上创建并持久化 swap 文件，说明容量与 swappiness 的选择，以及生产环境应避免的陷阱。
permalink: /zh/posts/ubuntu22-swap-memory/
categories:
- DevOps
post_type: deep-dive
updated: 2026-07-13 12:00:00 +0900
---
在 AWS EC2 免费套餐或其他低配自托管服务器上，安装大型软件包时经常会把 RAM 打满，导致卡死或 OOM 杀进程。在升级实例类型之前，用 **swap 文件** 把一部分磁盘当作应急内存，有助于扛过安装和构建时的瞬时峰值。本文以 Ubuntu 22.04 LTS 为例，给出步骤，并说明 **什么时候该用、什么时候不该用**。

<!--more-->

![Random Access Memory](/uploads/ubuntu22-swap-memory/ram.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@akshar_dave" title="Content copyright holder" target="_blank">Akshar Dave🌻</a></small>
</p>

-----

## Swap 做什么

**Swap（交换区）** 把磁盘（分区或文件）的一部分当作 RAM 页的溢出区。内核会把暂时不用的页换出到磁盘，需要时再换回。[Laravel](https://laravel.com/ "Laravel"){:target="_blank"}、[NestJS](https://nestjs.com/ "NestJS"){:target="_blank"} 这类大体量安装，或 `npm`/`composer` 解析依赖时，常出现 **短时间内存峰值**，仅靠物理内存可能扛不住。

但磁盘 I/O 远慢于内存。如果主机 **长期泡在 swap 里**，延迟会明显变差。Swap 是“缓冲”，不是“内存替代品”。

在 [Google Compute Engine](https://cloud.google.com/products/compute "Google Compute Engine"){:target="_blank"}、[Amazon EC2](https://aws.amazon.com/ec2/ "Amazon EC2"){:target="_blank"} 上增加内存通常需要停机改机型。意外 OOM 重启会拉长故障窗口，因此 **开发、玩具项目、低配测试节点** 预先开 swap 更稳妥。正式生产更应靠合理规格或自动扩缩。

Windows 里对应概念叫 **虚拟内存（页面文件）**。

![Windows 11 virtual memory](/uploads/ubuntu22-swap-memory/windows11-virtual-memory.png)

<p style="text-align:center;color:gray;"><small>Windows 虚拟内存</small></p>

## 容量怎么选

没有放之四海皆准的公式，实务上可从下表起步：

| 物理 RAM | Swap 起点 | 说明 |
| --- | --- | --- |
| 1–2 GB（t2/t3.micro 级） | 2–4 GB | 装包、轻量构建缓冲 |
| 4 GB | 2–4 GB | 不需要休眠时约 0.5–1 倍 RAM |
| 8 GB 以上 | 1–2 GB 或不用 | 没有明确需求就保持最小 |

- 磁盘快满时不要建超大 swap。
- `fallocate` 失败可用 `dd`。
- 下文示例为 **4GB** 的 `/swapfile`，按需改数字即可。

## 配置步骤

### 1. 查看当前 swap

```shell
sudo free -m
sudo swapon --show
```

![Check swap memory](/uploads/ubuntu22-swap-memory/check-swap-memory.png)

### 2. 关闭已有 swap（仅在调整大小时）

```shell
sudo swapoff -a
```

### 3. 创建 swap 文件

```shell
sudo fallocate -l 4G /swapfile
```

失败时：

```shell
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
```

### 4. 权限、格式化、启用

文件必须仅 root 可读写。

```shell
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo swapon --show
sudo free -m
```

![Make swapfile](/uploads/ubuntu22-swap-memory/make-swapfile.png)

### 5. 重启后仍生效（`/etc/fstab`）

```shell
grep -n swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

![Swap setup for rebooting](/uploads/ubuntu22-swap-memory/swap-setup-for-rebooting.png)

### 6. 验证

```shell
sudo free -m
sudo swapon --show
```

![Complete make swapfile](/uploads/ubuntu22-swap-memory/complete-make-swapfile.png)

## swappiness 与性能

`vm.swappiness`（0–100）控制内存压力下使用 swap 的积极程度。Ubuntu Server 常见默认值约 60。

- **数据库或延迟敏感服务**：常降到 10–30。
- **仅作低配构建节点**：保持默认往往可以。

临时：

```shell
sudo sysctl vm.swappiness=20
```

持久化：

```shell
echo 'vm.swappiness=20' | sudo tee /etc/sysctl.d/99-swap.conf
sudo sysctl --system
```

调低 swappiness 并不能消灭 OOM。内存本身不够时，进程仍会死亡或极慢。

## 生产注意点

- 持续 swap thrashing 就是故障，用 `vmstat 1` 等观察 `si`/`so`。
- 根卷已满时再建大 swap，部署和日志也会一起失败。
- 合规环境需考虑内存页落盘问题，必要时加密 swap。
- 编排节点请优先遵循平台建议。

## 关闭 swap

```shell
sudo swapoff -v /swapfile
sudo sed -i.bak '/swapfile/d' /etc/fstab
sudo rm /swapfile
sudo free -m
```

修改 `/etc/fstab` 后务必确认有控制台/串口恢复手段再重启，笔误可能导致无法启动。

## 参考文献

- 维基百科：[Virtual memory](https://en.wikipedia.org/wiki/Virtual_memory "Virtual memory"){:target="_blank"}
- 维基百科：[Paging](https://en.wikipedia.org/wiki/Memory_paging "Paging"){:target="_blank"}
- Ubuntu Server：[Swap](https://documentation.ubuntu.com/server/how-to/system-tuning/swap-faq/ "Ubuntu swap FAQ"){:target="_blank"}
