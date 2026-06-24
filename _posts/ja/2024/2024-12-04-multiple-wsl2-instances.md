---
layout: post
title: Windows 11のWSL2で複数の開発環境を構築する
meta: Windows 11でWSL2を使用して複数の開発環境をセットアップ・管理する方法を学びます。このガイドでは、インストール、設定、ワークフローを最適化するためのヒントを解説します。
tags:
- wsl2
image: /uploads/multiple-wsl2-instances/thumbnail.webp
lang: ja
translation_key: multiple-wsl2-instances
slug: multiple-wsl2-instances
description: Windows 11でWSL2を使用して複数の開発環境をセットアップ・管理する方法を学びます。このガイドでは、インストール、設定、ワークフローを最適化するためのヒントを解説します。
permalink: /ja/posts/multiple-wsl2-instances/
categories:
- DevOps
post_type: deep-dive
updated: 2024-12-04 10:00:00 +0900
---
今日のペースの速い開発の世界では、**複数の開発環境**を効率的に管理することが不可欠です。
Windows Subsystem for Linux 2 (**WSL2**) は、**Windows 11** マシン上で直接、分離された環境を作成・管理するための強力で柔軟な方法を提供します。
ソフトウェア開発者であれ、趣味で開発を行っている人であれ、プロジェクトごとに別々の環境を持つことで、ワークフローを効率化し、コンフリクトを最小限に抑えることができます。
このガイドでは、Windows 11で**複数のWSL2インスタンス**をセットアップおよび設定する方法を順を追って説明し、開発の生産性を最適化できるようにします。

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">この記事は[Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"}でも公開しています。</small>

![Multiple WSL2 Instances](/uploads/multiple-wsl2-instances/server.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@benofthenorth" title="コンテンツの著作権者" target="_blank">Ben Griffiths</a></small>
</p>

-----

レガシー環境や分散環境など、あらゆる開発環境で環境設定を行うのは、非常に手間のかかる作業です。
毎回環境を新規にセットアップすることは稀で、一度設定すれば数ヶ月、あるいは数年間大きな変更なしに使用することが多いです。
そのため、開発者は環境設定の方法をその都度Googleで検索することがよくあります。

PHPを開発する際には、[MAMP](https://www.mamp.info/ "MAMP"){:target="_blank"}や[XAMPP](https://www.apachefriends.org/ "XAMPP"){:target="_blank"}のようなツールを使用して、開発環境を簡単に構築できます。
また、[Docker](https://www.docker.com/ "Docker"){:target="_blank"}のようなコンテナ技術を利用したり、[VirtualBox](https://www.virtualbox.org/ "VirtualBox"){:target="_blank"}や[VMware](https://www.vmware.com/ "VMware"){:target="_blank"}のような仮想環境を活用する方法も良い代替案となり得ます。
これらのツールは、それぞれのニーズに合わせて様々な方法で開発環境を提供します。

この記事では、さまざまな開発環境の設定方法の中でも、特にWindows 11の[WSL2](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux "Windows Subsystem for Linux"){:target="_blank"}を利用した開発環境の設定方法について詳しく見ていきます。
WSL2を通じて、より簡単に隔離された環境を構築・管理する方法を紹介し、皆さんの開発生産性を向上させる手助けをしたいと思います。

### WSLの使用設定

Windows 11で**Windows Subsystem for Linux (WSL)**を使用するには、まず関連する機能を有効にしてレジストリに登録する必要があります。
この機能を有効にしないと、WSLのインストール中に`wslregisterdistribution failed with error: 0x800701bc`や`wslregisterdistribution failed with error: 0x80370102`といったエラーが発生することがあります。
これらのエラーはWSLが正常にインストールされなかったことを意味し、解決するためにはいくつかの設定が必要です。

まず、Windowsの機能で「**Linux用 Windows サブシステム**」と「**仮想マシン プラットフォーム**」を有効にする必要があります。この2つの機能は、WSL2が正しく動作するために不可欠です。
機能を有効にした後、システムを再起動すると、必要なレジストリ設定が完了し、WSLを問題なくインストールできるようになります。

![Windowsの機能の有効化または無効化](/uploads/multiple-wsl2-instances/windows-features.png)

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem auto 0;max-width:100%;">
    <div>
        <img src="/uploads/multiple-wsl2-instances/windows-features-1.png" alt="Windowsの機能の有効化または無効化" />
    </div>
    <div>
        <img src="/uploads/multiple-wsl2-instances/windows-features-2.png" alt="Windowsの機能の有効化または無効化" />
    </div>
</div>
<p style="text-align:center;color:gray;"><small>Windowsの機能の有効化/無効化</small></p>

さらに、WSLのインストール後、最新の[Linuxカーネル更新プログラム パッケージ](https://learn.microsoft.com/ja-jp/windows/wsl/install-manual#step-4---download-the-linux-kernel-update-package "Linux カーネル更新プログラム パッケージのダウンロード"){:target="_blank"}をダウンロードしてインストールする必要がある場合もあります。
これにより、WSL環境が最新の状態に保たれ、潜在的なエラーを防ぐことができます。
すべての準備が完了すれば、様々なLinuxディストリビューションをインストールして開発環境を構築できます。

### WSLディストリビューションのインストール

WSLをインストールする準備はすべて完了したので、ディストリビューションをインストールしてみましょう。

![WSLインストール可能リスト](/uploads/multiple-wsl2-instances/wsl-installable-list.png)
<p style="text-align:center;color:gray;"><small>WSLでインストール可能なディストリビューション</small></p>

`wsl -l -o`コマンドでインストール可能なディストリビューションイメージを確認できます。
このコマンドを使用すると、現在インストール可能なすべてのLinuxディストリビューションのリストが表示されます。

Ubuntu、Debian、Kali Linuxなど、複数のオプションを確認できます。
次のステップは、希望するディストリビューションを選択してインストールすることです。
ディストリビューションをインストールするには、次のように`wsl --install -d <ディストリビューション名>`コマンドを使用します。
例えば、Ubuntuをインストールしたい場合は`wsl --install -d Ubuntu`コマンドを入力します。

インストールが完了すると、自動的にそのディストリビューションが起動し、初期設定を進めることができます。
さあ、お好みのLinuxディストリビューションを選択・インストールして、WSL環境で様々な開発作業を始めましょう。
各ディストリビューションは独自の特性とツールを提供しているため、プロジェクトに最も適したものを選択することが重要です。

### 同じ種類のLinuxを複数インストールする

*2024年12月*現在、`wsl --install`コマンドを入力すると、デフォルトのディストリビューションである**Ubuntu**がインストールされます。
インストールされるバージョンは、最新のLTSバージョンである**Ubuntu 24.04.1 LTS**です。このイメージをインストールし、基本設定を完了した後、`export`コマンドでイメージをエクスポートし、後で`import`コマンドを使用して再生成することができます。

```shell
wsl --export Ubuntu Ubuntu-clean.tar
wsl --import Ubuntu-clean .\Ubuntu-clean .\Ubuntu-clean.tar
```

これらのコマンドを実行すると、現在設定されているUbuntuイメージが`Ubuntu-clean.tar`ファイルにエクスポートされ、必要なときにそのイメージを再度インポートして新しいインスタンスとして使用できます。
これは、同じ開発環境を複数作成したり、初期状態を維持しながら様々な設定をテストしたりする際に便利です。

その後、`wsl -l -v`コマンドを入力すると、現在インストールされているWSLディストリビューションのリストを確認できます。
下の画像は、インストールが完了したイメージのリストを示しています。その後は`wsl -d Ubuntu-clean`コマンドを入力して、特定のディストリビューションを実行できます。

![WSLインストール済みリスト](/uploads/multiple-wsl2-instances/wsl-installed-list.png)
<p style="text-align:center;color:gray;"><small>インストールが完了したイメージ</small></p>

このようにインストールされた各イメージごとに開発環境を別々に構成することで、様々な実験やテストを行うことができます。
例えば、あるイメージではApacheウェブサーバーを稼働させ、別のイメージではNginxウェブサーバーをインストールして、異なるウェブサーバーの性能や特性を比較することができます。
また、同じウェブサーバーの異なるバージョンをインストールしたり、様々な開発言語のバージョンをインストールして、各環境での互換性やパフォーマンスをテストすることも可能です。

このように、各WSL2インスタンスに個別の開発環境を設定することで、特定のプロジェクトに合わせた最適な環境を構築できます。
これは、開発中に発生しうる依存関係の競合を最小限に抑え、プロジェクト間に隔離されたテスト環境を提供することで、より効率的な開発プロセスをサポートします。
テスト環境の登録を解除し、VHDファイルまで削除するには、`wsl --unregister Ubuntu-clean`コマンドを入力します。

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem auto 0;max-width:100%;">
    <div>
        <img src="/uploads/multiple-wsl2-instances/wsl-ubuntu-apache2.png" alt="WSL Ubuntu Apache2" />
    </div>
    <div>
        <img src="/uploads/multiple-wsl2-instances/wsl-ubuntu-nginx.png" alt="WSL Ubuntu Nginx" />
    </div>
</div>
<p style="text-align:center;color:gray;"><small>各ウェブサーバーの設定</small></p>

結論として、WSL2を利用したマルチインスタンス環境は、開発者に柔軟性と拡張性を提供し、様々な実験やテストを容易に実行できる強力なツールとなります。
このように設定された環境を通じて、開発の生産性を最大化し、多様なシナリオに対する検証をより体系的に行うことができます。

### 参考資料

- [WSL を使用して Windows に Linux をインストールする方法](https://learn.microsoft.com/ja-jp/windows/wsl/install "WSL を使用して Windows に Linux をインストールする方法"){:target="_blank"}
- [WSL-Error-0x80370102-解決策](https://velog.io/@jaylnne/WSL-Error-0x80370102-해결 "wslregisterdistribution failed with error: 0x80370102"){:target="_blank"}
- [WSL-WSL2-Ubuntu-起動-時の-0x800701bc-エラー](https://velog.io/@meek/WSL-WSL2-Ubuntu-구동-시-0x800701bc-에러 "wslregisterdistribution failed with error: 0x800701bc"){:target="_blank"}
- [Windows WSL 環境で同じ種類の Linux を複数インストールする方法](https://blog.naver.com/techshare/222596544852 "Windows WSL 環境で同じ種類の Linux を複数インストールする方法"){:target="_blank"}