---
layout: post
title: Ubuntu 22.04 LTSでのスワップメモリ設定
meta: 低スペックサーバーのRAM不足を解消するために、Ubuntu 22.04 LTSでスワップメモリを設定する方法を学びます。リソースを大量に消費するアプリケーションを実行するAWS
  EC2や自己ホスト型サーバーに最適です。
tags:
- ubuntu
image: /uploads/ubuntu22-swap-memory/thumbnail.webp
lang: ja
translation_key: ubuntu22-swap-memory
slug: ubuntu22-swap-memory
description: 低スペックサーバーのRAM不足を解消するために、Ubuntu 22.04 LTSでスワップメモリを設定する方法を学びます。リソースを大量に消費するアプリケーションを実行するAWS
  EC2や自己ホスト型サーバーに最適です。
permalink: /ja/posts/ubuntu22-swap-memory/
---
**Amazon Web Services EC2**のような無料利用枠のサービスや、その他の自己ホスト型サーバーを使用していると、大規模な外部リソースをインストールする際にRAM不足の問題に直面することがあります。
これにより、サーバーが長時間フリーズし、最終的にクラッシュする可能性があります。
これは頻繁に起こることではありませんが、非常に限られたスペックのサーバーで商用利用の個人プロジェクトを実行し、**マイクロサービスアーキテクチャ**を実装している場合には、非常に深刻な問題となり得ます。
このような状況では、**スワップメモリ**が非常に役立ちます。この記事では、スワップメモリの作成方法とその概要について解説します。

<!--more-->

![Random Access Memory](/uploads/ubuntu22-swap-memory/ram.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@akshar_dave" title="Content copyright holder" target="_blank">Akshar Dave🌻</a></small>
</p>

-----

**スワップメモリ**は、物理ディスクの一部を揮発性メモリであるRAM（以下、メモリ）として使用し、不足しているメモリ容量を補う役割を果たします。
時折、[Laravel](https://laravel.com/ "Laravel"){:target="_blank"}や[NestJS](https://nestjs.com/ "NestJS"){:target="_blank"}のような大きなパッケージをインストールする際には、メモリやCPUリソースといったコンピュータのリソースを大量に必要とするため、リソースが不足しているとインストールに失敗することがあります。

[Google Compute Engine](https://cloud.google.com/products/compute "Google Compute Engine"){:target="_blank"}や[Amazon EC2](https://aws.amazon.com/ko/ec2/ "Amazon EC2"){:target="_blank"}など、ほとんどの仮想マシンサービスでは、メモリ容量を追加するにはインスタンスを停止してからインスタンスタイプを変更する必要があります。
予期せぬ状況でメモリ不足によるシステムエラーが発生し再起動が必要になった場合、停止している間も損失が発生し続けるため、事前の対策が不可欠です。
このような場合にスワップメモリを設定しておけば、一時的にでもメモリ不足の問題を少しでも緩和することができます。

ほとんどの商用サービス環境では、各々のインフラ管理技術が導入されているため、上記のような状況はあまり発生しませんが、開発テストやトイプロジェクトのような用途で使用する無料利用枠程度の低スペックな環境では、スワップメモリを設定しておくと非常に便利で役立ちます。

![Windows 11 virtual memory](/uploads/ubuntu22-swap-memory/windows11-virtual-memory.png)

<p style="text-align:center;color:gray;"><small>Windowsの仮想メモリ</small></p>

スワップメモリという概念は、UbuntuのようなLinuxやUnixだけに存在するものではありません。Windowsにも「仮想メモリ」という名前で活用されており、低スペックのPCで便利に利用されています。

### スワップメモリの設定

1. スワップメモリが設定されているか確認
   ```shell
      sudo free -m
      sudo swapon -s
   ```
   ![Check swap memory](/uploads/ubuntu22-swap-memory/check-swap-memory.png)
2. スワップメモリが設定されている場合は無効化
   ```shell
      sudo swapoff -a
   ```
3. スワップメモリとして使用するswapfileを作成
   ```shell
      # 4Gサイズのスワップファイルを作成
      sudo fallocate -l 4G /swapfile
   ```
4. 作成したswapfileをスワップメモリとして使用するように設定
    ```shell
      # 権限を修正
      sudo chmod 600 /swapfile
    
      # 有効化の準備
      sudo mkswap /swapfile
    
      # 有効化
      sudo swapon /swapfile
    ```
   ![Make swapfile](/uploads/ubuntu22-swap-memory/make-swapfile.png)
5. サーバー再起動後もスワップメモリを使用できるように設定
    ```shell
      # ファイルを編集
      sudo nano /etc/fstab 
    
      # 以下の内容を追加
      /swapfile swap swap defaults 0 0
    ```
   ![Swap setup for rebooting](/uploads/ubuntu22-swap-memory/swap-setup-for-rebooting.png)
6. スワップメモリの設定完了
   ![Complete make swapfile](/uploads/ubuntu22-swap-memory/complete-make-swapfile.png)

### スワップメモリの無効化

スワップメモリをこれ以上使用しない場合は無効化します。
```shell
# スワップの無効化
sudo swapoff -v /swapfile 

# ファイルを開き、以下の行を削除
sudo nano /etc/fstab      
/swapfile swap swap defaults 0 0

# swapファイルを削除
sudo rm /swapfile 
```

### 参考文献
- ウィキペディア : [仮想メモリ](https://en.wikipedia.org/wiki/Virtual_memory "仮想メモリ"){:target="_blank"}
- ウィキペディア : [メモリ管理 - ページング](https://en.wikipedia.org/wiki/Memory_paging "メモリ管理 - ページング"){:target="_blank"}