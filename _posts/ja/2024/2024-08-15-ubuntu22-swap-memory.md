---
layout: post
title: Ubuntu 22.04 LTSでのスワップメモリ設定
tags:
- ubuntu
image: /uploads/ubuntu22-swap-memory/thumbnail.webp
lang: ja
translation_key: ubuntu22-swap-memory
slug: ubuntu22-swap-memory
description: Ubuntu 22.04 LTSでスワップファイルを作成し再起動後も有効にする手順と、サイズ・swappinessの選び方、本番で避けるべき落とし穴を整理します。
permalink: /ja/posts/ubuntu22-swap-memory/
categories:
- DevOps
post_type: deep-dive
updated: 2026-07-13 12:00:00 +0900
---
AWS EC2 の無料枠や低スペックの自己ホストサーバーでは、大きなパッケージ導入時に RAM が足りず、フリーズや OOM でプロセスが落ちることがあります。インスタンスタイプを上げる前に **スワップファイル** でディスクの一部を緊急メモリにすると、インストールやビルド中のピークを乗り越えやすくなります。Ubuntu 22.04 LTS の手順に加え、**いつ使い、いつ使わないべきか** をまとめます。

<!--more-->

![Random Access Memory](/uploads/ubuntu22-swap-memory/ram.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@akshar_dave" title="Content copyright holder" target="_blank">Akshar Dave🌻</a></small>
</p>

-----

## スワップの役割

**スワップ** はディスク（パーティションまたはファイル）の一部を RAM の退避領域として使う仕組みです。カーネルはすぐ使わないページをディスクへ移し、必要になったら戻します。[Laravel](https://laravel.com/ "Laravel"){:target="_blank"} や [NestJS](https://nestjs.com/ "NestJS"){:target="_blank"} のような大きなパッケージ、`npm`/`composer` の依存解決など **短時間のメモリピーク** では、物理 RAM だけでは足りない瞬間を埋められます。

ただしディスク I/O は RAM より大幅に遅いです。スワップが **常時フル稼働** ならレイテンシが悪化します。スワップは「余裕バッファ」であり「RAM の代替」ではありません。

[Google Compute Engine](https://cloud.google.com/products/compute "Google Compute Engine"){:target="_blank"} や [Amazon EC2](https://aws.amazon.com/ec2/ "Amazon EC2"){:target="_blank"} でメモリを増やすには、多くの場合インスタンスを停止してタイプ変更が必要です。予期しない OOM 再起動が続くと障害時間が伸びるため、**開発・実験・低スペック試験ノード** ではあらかじめスワップを用意しておくと安全です。商用本番は適切なサイジングやオートスケールが本筋です。

Windows では **仮想メモリ（ページファイル）** として同じ概念があります。

![Windows 11 virtual memory](/uploads/ubuntu22-swap-memory/windows11-virtual-memory.png)

<p style="text-align:center;color:gray;"><small>Windows の仮想メモリ</small></p>

## サイズの目安

環境ごとに正解は違いますが、実務で使いやすい出発点は次のとおりです。

| 物理 RAM | スワップ目安 | 備考 |
| --- | --- | --- |
| 1–2 GB（t2/t3.micro 級） | 2–4 GB | パッケージ導入・軽いビルド用 |
| 4 GB | 2–4 GB | ハイバネ不要なら RAM の 0.5–1 倍 |
| 8 GB 以上 | 1–2 GB または無し | 必要が明確でないなら最小限 |

- ディスク余裕が少ないのに巨大スワップを作らないでください。
- `fallocate` が失敗する場合は `dd` を使えます。
- 以下は **4GB** の `/swapfile` 例です。数字だけ変えれば流用できます。

## 設定手順

### 1. 現状確認

```shell
sudo free -m
sudo swapon --show
```

![Check swap memory](/uploads/ubuntu22-swap-memory/check-swap-memory.png)

### 2. 既存スワップをオフ（サイズ変更時）

```shell
sudo swapoff -a
```

### 3. スワップファイル作成

```shell
sudo fallocate -l 4G /swapfile
```

失敗時:

```shell
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
```

### 4. 権限・フォーマット・有効化

ルートのみ読み書き可能にします。

```shell
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo swapon --show
sudo free -m
```

![Make swapfile](/uploads/ubuntu22-swap-memory/make-swapfile.png)

### 5. 再起動後も有効化（`/etc/fstab`）

```shell
grep -n swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

![Swap setup for rebooting](/uploads/ubuntu22-swap-memory/swap-setup-for-rebooting.png)

### 6. 確認

```shell
sudo free -m
sudo swapon --show
```

![Complete make swapfile](/uploads/ubuntu22-swap-memory/complete-make-swapfile.png)

## swappiness と性能

`vm.swappiness`（0–100）はメモリ逼迫時にスワップをどれだけ積極的に使うかを決めます。Ubuntu Server では 60 前後がよく見られます。

- **DB や遅延に敏感なサービス**: 10–30 に下げる例が多いです。
- **低スペックのビルド専用**: デフォルトのままで問題ないことも多いです。

一時適用:

```shell
sudo sysctl vm.swappiness=20
```

永続化例:

```shell
echo 'vm.swappiness=20' | sudo tee /etc/sysctl.d/99-swap.conf
sudo sysctl --system
```

swappiness を下げても OOM そのものは消えません。RAM が絶対的に不足していればプロセスは落ちるか極端に遅くなります。

## 本番での注意点

- 継続的なスワップ thrashing は障害です。`vmstat 1` などで `si`/`so` を監視してください。
- ルートボリュームが満杯の状態で大きなスワップを作ると、デプロイやログも同時に失敗します。
- 規制の厳しい環境では、メモリア内容がディスクに残る点を踏まえ暗号化スワップなどを検討してください。
- オーケストレータノードではプラットフォーム推奨を優先してください。

## スワップの無効化

```shell
sudo swapoff -v /swapfile
sudo sed -i.bak '/swapfile/d' /etc/fstab
sudo rm /swapfile
sudo free -m
```

`/etc/fstab` 編集後は誤記で起動不能になり得るため、コンソール復旧手段を確認してから再起動してください。

## 参考文献

- Wikipedia: [Virtual memory](https://en.wikipedia.org/wiki/Virtual_memory "Virtual memory"){:target="_blank"}
- Wikipedia: [Paging](https://en.wikipedia.org/wiki/Memory_paging "Paging"){:target="_blank"}
- Ubuntu Server: [Swap](https://documentation.ubuntu.com/server/how-to/system-tuning/swap-faq/ "Ubuntu swap FAQ"){:target="_blank"}
