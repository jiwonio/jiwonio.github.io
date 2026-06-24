---
layout: post
title: Windows 11でのNode.jsセットアップ中に発生するパッケージインストールエラーの解決方法
meta: Windows 11にNode.jsをセットアップする際に発生する一般的なパッケージインストールエラーの修正方法をご紹介します。このガイドでは、Chocolatyを使用したC/C++およびPythonのコンパイル問題に対処するための明確な解決策を提供します。
tags:
- nodejs
image: /uploads/nodejs-installation-failure/thumbnail.webp
lang: ja
translation_key: nodejs-installation-failure
slug: nodejs-installation-failure
description: Windows 11にNode.jsをセットアップする際に発生する一般的なパッケージインストールエラーの修正方法をご紹介します。このガイドでは、Chocolatyを使用したC/C++およびPythonのコンパイル問題に対処するための明確な解決策を提供します。
permalink: /ja/posts/nodejs-installation-failure/
categories:
- DevOps
post_type: deep-dive
updated: 2024-11-15 10:00:00 +0900
---
Windows 11に[Node.js](https://nodejs.org/ "nodejs"){:target="_blank"}をインストールする際、追加のパッケージインストールに関連するエラーに遭遇することがあります。
これらのエラーは、一部のNode.jsパッケージを**C/C++**や**Python**でコンパイルする必要があるために頻繁に発生します。
このガイドでは、これらの問題を効率的に解決し、スムーズなインストールプロセスを保証するための詳細な解決策を提供します。
一般的なエラーの1つに、追加ツールをインストールするために`chocolaty`を使用する際に発生するものがあります。
既存のchocolatyパスに`visualstudio2019-workload-vctools`がインストールできない場合、インストール失敗につながることがあります。
インストールプロセスではCMD画面が表示され、PowerShellを使用してインストールが進行しますが、
何度試してもクリーンインストールができない場合があります。

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">[Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"}にも投稿しています。</small>

![node.js](/uploads/nodejs-installation-failure/nodejs.png)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/copyrightfreepictures-203" title="Content copyright holder" target="_blank">CopyrightFreePictures</a></small>
</p>

-----

Windows 11で**Node.js**をインストールする際、追加パッケージのインストールに関連するエラーが発生することがあります。
これらのエラーは、一部のNode.jsパッケージを**C/C++**と**Python**を使用してコンパイルする必要があるために発生します。
この記事では、これらの問題を効率的に解決し、円滑なインストールプロセスを支援するために、その方法を記録として残します。

一般的なエラーの1つは、追加ツールをインストールするために`chocolaty`を使用するときに発生します。
既存のchocolatyパスに`visualstudio2019-workload-vctools`をインストールできない場合、インストール失敗が発生する可能性があります。

> visualstudio2019-workload-vctools not installed. the package was not found with the source(s) listed.

Windows 11でNode.jsをインストール中に追加パッケージのインストールエラーに関連して上記のようなメッセージが表示された場合の解決方法です。
この記事は、初心者から経験豊富な開発者まで、インストール過程でよく遭遇する問題に対して、明確で実行可能な解決策を提供することを目的としています。

![Automatically install](/uploads/nodejs-installation-failure/automatically-install.png)
<p style="text-align:center;color:gray;"><small>Node.jsのインストール中に必要なツールのインストール</small></p>

Node.jsのインストール中には、上記のように、インストールに必要な追加の必須項目をインストールするのに役立つオプションが存在します。
このまま進めると、通常は正常にインストールされるはずです。

![Necessary tools installing](/uploads/nodejs-installation-failure/necessary-tools-installing.png)
<p style="text-align:center;color:gray;"><small>必要なツールのインストール中</small></p>

![Installation failure](/uploads/nodejs-installation-failure/installation-failure.png)
<p style="text-align:center;color:gray;"><small>インストール中にエラーが発生</small></p>

Node.jsの使用に必要な追加ツールをインストールするためのCMD画面が表示され、PowerShellを使用してインストールが進行します。
インストール中に上記のようなエラーが表示され、何度再実行してもクリーンインストールができません。

### 1. Chocolatyの再インストール

 - C:\ProgramData\chocolaty ディレクトリに移動し、そのディレクトリを削除します。
   Node.jsを再インストールすると、chocolatyと必要なツールも一緒に再インストールされます。
   ![Chocolatey folder](/uploads/nodejs-installation-failure/chocolatey.png)

### 2. Visual Studio Build Toolsのインストール

 - 最新バージョンの[Visual Studio 2019 - Build Tools for Visual Studio 2019](https://visualstudio.microsoft.com/downloads/ "Build Tools for Visual Studio 2019"){:target="_blank"}をダウンロードしてインストールします。
   ![Download build tools](/uploads/nodejs-installation-failure/download-build-tools.png)
   ![MSBuild tools download](/uploads/nodejs-installation-failure/msbuild-tools.png)
   ![Install msbuild tools](/uploads/nodejs-installation-failure/install-msbuild-tools.png)
 - インストールが完了したら、次のコマンドを実行してvisualstudio2019-workload-vctoolsを[アップグレード](https://community.chocolatey.org/packages/visualstudio2019-workload-vctools "Choco upgrade"){:target="_blank"}します:
   ```shell
   choco upgrade visualstudio2019-workload-vctools -y
   ```
   ![Upgrade vctools](/uploads/nodejs-installation-failure/upgrade-vctools.png)

### インストール完了

Node.jsのインストールと必要なパッケージのインストールがすべて完了しました！
これで開発環境の準備が整いました。

以下は追加で確認すべき項目です：

1. Node.jsのバージョン確認: <br/>
   インストールが正しく行われたか確認するために、次のコマンドを実行してください：
   ```shell
   # このコマンドでNode.jsとnpmのバージョンを確認できます。
   node -v
   npm -v
   ```
2. 基本プロジェクトの作成: <br/>
   Node.jsが正しくインストールされたか確認するために、簡単なプロジェクトを作成してみることができます。任意のディレクトリに移動した後、次のコマンドを実行してください：
   ```shell
   # このコマンドで新しいプロジェクトディレクトリを作成し、基本的なパッケージ設定ができます。
   mkdir my-node-project
   cd my-node-project
   npm init -y
   ```
3. 必須パッケージのインストール: <br/>
   プロジェクトに必要な基本的なパッケージをインストールしてみてください。例えば、Expressをインストールするには、次のコマンドを実行します：
   ```shell
   # このコマンドでExpressパッケージをインストールし、サーバーを構築できます。
   npm install express
   ```
4. その他の設定: <br/>
   追加で必要な設定やパッケージがあれば、この時点でインストールしておくことをお勧めします。プロジェクトの要件に応じて必要なパッケージをインストールし、環境設定を完了させてください。

これで、Windows 11にNode.jsと必要なツールがインストールされ、設定されました。開発を始める準備は完了です。コーディングを楽しんでください！

![Upgrade successful](/uploads/nodejs-installation-failure/upgrade-successful.png)
<p style="text-align:center;color:gray;"><small>インストール完了</small></p>

### 参考資料

- [Windows 11 (Version 22H2)](https://en.wikipedia.org/wiki/Windows_11 "Windows 11"){:target="_blank"}
- [Node.js 18.x LTS (includes npm 9.6.7)](https://nodejs.org/docs/latest-v18.x/api/index.html "Node.js 18.x LTS"){:target="_blank"}
- [choco-install-visualstudio2017-workload-vctools-fails-error-the-install-of](https://stackoverflow.com/questions/65185384/choco-install-visualstudio2017-workload-vctools-fails-error-the-install-of "StackOverflow 参考事項"){:target="_blank"}