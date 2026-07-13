---
layout: post
title: Configuring Swap Memory on Ubuntu 22.04 LTS
tags:
- ubuntu
image: /uploads/ubuntu22-swap-memory/thumbnail.webp
lang: en
translation_key: ubuntu22-swap-memory
slug: ubuntu22-swap-memory
description: Create a persistent swap file on Ubuntu 22.04 LTS, choose size and swappiness
  wisely, and know when swap helps versus when it hides a real capacity problem.
permalink: /en/posts/ubuntu22-swap-memory/
categories:
- DevOps
post_type: deep-dive
updated: 2026-07-13 12:00:00 +0900
---
On AWS EC2 free-tier or other low-spec hosts, large package installs can exhaust RAM and freeze the machine or trigger OOM kills. Before you resize the instance, a **swap file** can absorb short memory peaks during install and build work. This guide covers Ubuntu 22.04 LTS setup steps plus **when swap helps and when it is the wrong fix**.

<!--more-->

![Random Access Memory](/uploads/ubuntu22-swap-memory/ram.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@akshar_dave" title="Content copyright holder" target="_blank">Akshar Dave🌻</a></small>
</p>

-----

## What swap does

**Swap** uses part of disk (partition or file) as overflow for RAM pages. The kernel moves cold pages to disk and brings them back when needed. Heavy installs such as [Laravel](https://laravel.com/ "Laravel"){:target="_blank"} or [NestJS](https://nestjs.com/ "NestJS"){:target="_blank"}, or dependency resolution with `npm`/`composer`, often create **short memory peaks** that a tiny free-tier box cannot hold in RAM alone.

Disk I/O is far slower than RAM. If the host **lives in swap**, latency will spike. Treat swap as an emergency buffer, not a substitute for memory capacity.

On [Google Compute Engine](https://cloud.google.com/products/compute "Google Compute Engine"){:target="_blank"} and [Amazon EC2](https://aws.amazon.com/ec2/ "Amazon EC2"){:target="_blank"}, growing RAM usually means stopping the instance and changing type. Unexpected OOM reboots mean downtime until you recover, so **dev, toy, and small test nodes** often benefit from swap prepared in advance. Production services should usually right-size instances or autoscale instead.

Windows exposes the same idea as **virtual memory (page file)**.

![Windows 11 virtual memory](/uploads/ubuntu22-swap-memory/windows11-virtual-memory.png)

<p style="text-align:center;color:gray;"><small>Virtual memory in Windows</small></p>

## Choosing a size

There is no single correct formula, but these starting points work well in practice:

| Physical RAM | Swap starting point | Notes |
| --- | --- | --- |
| 1–2 GB (t2/t3.micro class) | 2–4 GB | Buffer for package installs and light builds |
| 4 GB | 2–4 GB | About 0.5–1× RAM if hibernation is not required |
| 8 GB+ | 1–2 GB or none | Minimum only unless you know you need more |

- Do not create a huge swap file on a nearly full disk.
- If `fallocate` fails, use `dd` (see below).
- Examples below use a **4 GB** file at `/swapfile`. Change the size to match your host.

## Setup steps

### 1. Check current swap

```shell
sudo free -m
sudo swapon --show
```

![Check swap memory](/uploads/ubuntu22-swap-memory/check-swap-memory.png)

If the Swap row in `free -m` is all zeros, swap is missing or inactive.

### 2. Turn off existing swap (only when resizing)

```shell
sudo swapoff -a
```

### 3. Create the swap file

```shell
sudo fallocate -l 4G /swapfile
```

If `fallocate` is unavailable or errors:

```shell
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
```

### 4. Permissions, format, enable

The file must be **readable/writable only by root**.

```shell
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo swapon --show
sudo free -m
```

![Make swapfile](/uploads/ubuntu22-swap-memory/make-swapfile.png)

### 5. Persist across reboot (`/etc/fstab`)

```shell
grep -n swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Older examples with `defaults` often still work; the `none swap sw 0 0` form matches common Ubuntu guidance for swap entries.

![Swap setup for rebooting](/uploads/ubuntu22-swap-memory/swap-setup-for-rebooting.png)

### 6. Verify

```shell
sudo free -m
sudo swapon --show
```

![Complete make swapfile](/uploads/ubuntu22-swap-memory/complete-make-swapfile.png)

## swappiness and performance

`vm.swappiness` (0–100) controls how aggressively the kernel uses swap under pressure. Ubuntu Server often defaults near 60.

- **Latency-sensitive services / databases**: many operators lower it to 10–30.
- **Low-spec build-only nodes**: the default is often fine.

Temporary:

```shell
sudo sysctl vm.swappiness=20
```

Persistent (`/etc/sysctl.d/99-swap.conf`):

```shell
echo 'vm.swappiness=20' | sudo tee /etc/sysctl.d/99-swap.conf
sudo sysctl --system
```

Lowering swappiness does not remove OOM risk. If RAM is simply too small, processes still die or crawl.

## Production caveats

- Persistent swap thrashing is an incident. Watch `si`/`so` with `vmstat 1` and your monitors.
- Creating a large swap file on a full root volume can break deploys and logging together.
- Regulated environments may require encrypted swap because page contents can hit disk.
- Orchestrator node swap policies may differ from generic Linux advice—follow the platform guide first.

## Disabling swap

```shell
sudo swapoff -v /swapfile
sudo sed -i.bak '/swapfile/d' /etc/fstab
sudo rm /swapfile
sudo free -m
```

After editing `/etc/fstab`, confirm you have console/serial recovery before rebooting—a typo can prevent boot.

## References

- Wikipedia: [Virtual memory](https://en.wikipedia.org/wiki/Virtual_memory "Virtual memory"){:target="_blank"}
- Wikipedia: [Paging](https://en.wikipedia.org/wiki/Memory_paging "Paging"){:target="_blank"}
- Ubuntu Server docs: [Swap](https://documentation.ubuntu.com/server/how-to/system-tuning/swap-faq/ "Ubuntu swap FAQ"){:target="_blank"}
