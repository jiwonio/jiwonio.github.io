---
layout: post
title: AWS EC2インスタンスにおけるUbuntuの必須初期セットアップガイド
meta: AWS EC2上のUbuntu 22.04 LTSにおける主要な初期セットアップ手順を解説します。このガイドは、開発およびテスト環境向けの低スペックインスタンスの設定に焦点を当てており、無料利用枠の使用に最適です。
tags:
- AWS
image: /uploads/ubuntu22-default-setting/thumbnail.webp
lang: ja
translation_key: ubuntu22-default-setting
slug: ubuntu22-default-setting
description: AWS EC2上のUbuntu 22.04 LTSにおける主要な初期セットアップ手順を解説します。このガイドは、開発およびテスト環境向けの低スペックインスタンスの設定に焦点を当てており、無料利用枠の使用に最適です。
permalink: /ja/posts/ubuntu22-default-setting/
categories:
- DevOps
post_type: deep-dive
updated: 2026-07-13 12:00:00 +0900
---
AWS EC2で開発またはテスト環境をセットアップする際、インスタンスに適切な初期設定を行うことは不可欠です。
このガイドでは、**Ubuntu 22.04 LTS**の初期セットアップ手順を解説します。コストを抑えるために無料利用枠を活用している方に最適です。
Route 53、ELB、RDSといったサービスには触れず、基本的な設定に焦点を当てるため、このガイドはシンプルで必要不可欠なセットアップにぴったりです。
初心者でも経験豊富な開発者でも、適切に設定されたインスタンスがあれば、時間を節約し、よくある問題を未然に防ぐことができます。
このガイドに従うことで、Ubuntuサーバーが正しく設定され、トラブルシューティングではなくプロジェクトに集中できるようになります。
安全なアクセスのためのキーペアの設定から、ファイアウォールやストレージの設定まで、すべてを網羅しています。
以下の手順に従って、開発やテストのニーズに合った、安定した効率的な環境を構築しましょう。

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">[Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"} でも公開しています。</small>

![Ubuntu Server](/uploads/ubuntu22-default-setting/ubuntu.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@6heinz3r" title="Content copyright holder" target="_blank">Gabriel Heinzer</a></small>
</p>

-----

## このガイドの範囲

対象外: Route 53、ALB/ELB、RDS、本格的なマルチ AZ 構成。
対象: 開発・テスト向けの **EC2 Ubuntu 22.04 1 台**。

無料枠でも 22/80/3306 を長期間 `0.0.0.0/0` に開けるのは避けてください。

## 起動前チェック

1. ローカル `.pem` 権限を制限
2. SSH(22) は自分の IP / VPN / bastion のみ
3. Docker や大量ログを使うならルートボリュームに余裕を
4. パブリック IP / Elastic IP の要否

[Amazon EC2](https://aws.amazon.com/ec2/ "Amazon EC2"){:target="_blank"}で開発またはテスト環境をセットアップする際は、インスタンスを正しく設定することが重要です。このガイドでは、Ubuntu 22.04 LTSの初期設定手順を説明します。
コストを削減するために無料利用枠を利用する場合に特に役立ちます。Route 53、ELB、RDSなどのサービスには触れず、基本的な設定に重点を置いています。

### 1. サーバーの基本設定

<p style="text-align:right;color:gray;"><small>EC2仕様</small></p>

| EC2設定項目  | 設定値                                           |
|------------|------------------------------------------------|
| イメージ(AMI)   | Ubuntu Server 22.04 LTS (HVM), SSD Volume Type |
| インスタンスタイプ    | t2.micro                                       |
| ファイアウォール(セキュリティグループ) | launch-wizard-9                                |
| ストレージ(ボリューム)   | 1個 - 30GB                                      |
| キーペア(ログイン)  | Key pair file                                  |

![Create EC2 instance](/uploads/ubuntu22-default-setting/create-ec2-Instance.png)
<p style="text-align:center;color:gray;"><small>EC2仕様設定</small></p>

開発またはテスト用途では、高いスペックは必要ありません。無料利用枠のモデルで十分です。
`launch-wizard-9`セキュリティグループは、インスタンスを作成すると自動的に生成されるデフォルト設定で、22、80、3306といったAPI開発に必要なポートをすべてに開放します。
セキュリティを強化するには、[OpenVPN](https://openvpn.net/ "OpenVPN"){:target="_blank"}のようなツールを使用してIPアドレスを固定し、これらのIPからのみポートにアクセスできるように設定することをお勧めします。

![Security group - inbound](/uploads/ubuntu22-default-setting/security-inbound.png)
<p style="text-align:center;color:gray;"><small>セキュリティグループ インバウンド設定</small></p>

`ubuntu`アカウントでログインし、パスワードの代わりにキーファイルを使用します。[PuTTY](https://www.putty.org/ "PuTTY"){:target="_blank"}や[Termius](https://termius.com/ "Termius"){:target="_blank"}のような管理しやすいプログラムを使用すると便利です。
ppkファイルまたはpemファイルをダウンロードしてログインします。

### 2. hostnameの変更

```shell
ubuntu@ip-172-0-0-0:~$ sudo hostnamectl set-hostname test
ubuntu@ip-172-0-0-0:~$ sudo reboot

# hostnameの変更完了
ubuntu@test:~$
```

### 3. Ubuntuのアップデート

```shell
ubuntu@test:~$ sudo apt update
ubuntu@test:~$ sudo apt upgrade
ubuntu@test:~$ sudo apt dist-upgrade
ubuntu@test:~$ sudo apt autoremove
ubuntu@test:~$ sudo apt clean
ubuntu@test:~$ sudo apt autoclean
```

### 4. history形式の変更

![History Setup - default format](/uploads/ubuntu22-default-setting/history-default-format.png)
<p style="text-align:center;color:gray;"><small>既存のhistory形式</small></p>

```shell
# history形式の変更
ubuntu@test:~$ sudo vi /etc/profile

# 最下部に以下の内容を追加
# VIMの場合、Shift + Gで最下部に移動
HISTTIMEFORMAT="[%Y-%m-%d %H:%M:%S] "
export HISTTIMEFORMAT
```

![History Setup - default time format](/uploads/ubuntu22-default-setting/history-default-timeformat.png)
<p style="text-align:center;color:gray;"><small>HISTTIMEFORMATの内容を追加</small></p>

![History setup](/uploads/ubuntu22-default-setting/history-setup.png)
<p style="text-align:center;color:gray;"><small>history形式の変更完了</small></p>

### 5. historyキャッシュの増加

```shell
# historyキャッシュを増やす
ubuntu@test:~$ sudo vi /etc/bash.bashrc 

# 最下部に以下の内容を追加
# VIMの場合、Shift + Gで最下部に移動
export HISTSIZE=10000
export HISTFILESIZE=10000
```

![History default size](/uploads/ubuntu22-default-setting/history-default-size.png)
<p style="text-align:center;color:gray;"><small>HISTSIZEとHISTFILESIZEの内容を追加</small></p>

### 6. ロケールを韓国語に設定

```shell
# 現在のロケールを確認
ubuntu@test:~$ locale
```

![Locale check](/uploads/ubuntu22-default-setting/locale-check.png)
<p style="text-align:center;color:gray;"><small>現在のロケール設定値を確認</small></p>

```shell
# 韓国語言語パックのインストール
ubuntu@test:~$ sudo apt install language-pack-ko

# 韓国語を適用
ubuntu@test:~$ sudo update-locale LANG=ko_KR.UTF-8 LANGUAGE="ko_KR:ko:en_US:en" LC_MESSAGES=POSIX

# 再起動後に適用
ubuntu@test:~$ sudo reboot
```

![Setup locale](/uploads/ubuntu22-default-setting/setup-locale.png)
<p style="text-align:center;color:gray;"><small>ロケールの変更完了</small></p>

### 7. タイムゾーンを韓国に設定

```shell
# タイムゾーンの確認
ubuntu@test:~$ timedatectl
```

![Timezone check](/uploads/ubuntu22-default-setting/timezone-check.png)
<p style="text-align:center;color:gray;"><small>現在のタイムゾーン設定値を確認</small></p>

```shell
# ソウルのタイムゾーンがあるか確認
ubuntu@test:~$ timedatectl list-timezones | grep Seoul

# タイムゾーンをソウルに変更
ubuntu@test:~$ sudo timedatectl set-timezone Asia/Seoul 
```

![Timezone setup](/uploads/ubuntu22-default-setting/timezone-setup.png)
<p style="text-align:center;color:gray;"><small>タイムゾーンの変更完了</small></p>

## よくあるミス

- MySQL 3306 の全世界公開
- HISTFILESIZE の誤字
- 再起動が必要なカーネル更新の放置
- 鍵ファイルのチャット共有

## 次のステップ

- OOM 対策のスワップ: [スワップ設定](/ja/posts/ubuntu22-swap-memory/)
- ホスト FW として ufw を検討
- 長期運用なら unattended-upgrades、fail2ban、スナップショット

## 参考文献


- [How to set or change timezone](https://linuxize.com/post/how-to-set-or-change-timezone-on-ubuntu-20-04/ "How to set or change timezone"){:target="_blank"}
- [How do I change the default locale](https://askubuntu.com/questions/89976/how-do-i-change-the-default-locale-in-ubuntu-server "How do I change the default locale"){:target="_blank"}