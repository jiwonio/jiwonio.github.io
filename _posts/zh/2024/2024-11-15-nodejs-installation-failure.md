---
layout: post
title: 解决在 Windows 11 上安装 Node.js 时的包安装错误
meta: 了解如何在 Windows 11 上设置 Node.js 时修复常见的包安装错误。本指南为使用 Chocolaty 处理 C/C++ 和 Python
  编译问题提供了清晰的解决方案。
tags:
- nodejs
image: /uploads/nodejs-installation-failure/thumbnail.webp
lang: zh
translation_key: nodejs-installation-failure
slug: nodejs-installation-failure
description: 了解如何在 Windows 11 上设置 Node.js 时修复常见的包安装错误。本指南为使用 Chocolaty 处理 C/C++ 和
  Python 编译问题提供了清晰的解决方案。
permalink: /zh/posts/nodejs-installation-failure/
categories:
- DevOps
post_type: deep-dive
updated: 2024-11-15 10:00:00 +0900
---
在 Windows 11 上安装 [Node.js](https://nodejs.org/ "nodejs"){:target="_blank"} 时，你可能会遇到与附加软件包安装相关的错误。
这些错误通常是由于某些 Node.js 包需要使用 **C/C++** 和 **Python** 进行编译而引起的。
本指南提供了详细的解决方案，以高效地解决这些问题并确保安装过程顺利。
一个常见的错误是使用 `chocolaty` 安装附加工具时产生的。
如果 `visualstudio2019-workload-vctools` 无法安装在现有的 chocolaty 路径中，可能会导致安装失败。
安装过程会显示一个 CMD 屏幕，并使用 PowerShell 进行安装。
尽管多次尝试，你可能会发现无法完成干净的安装。

<!--more-->

![node.js](/uploads/nodejs-installation-failure/nodejs.png)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/copyrightfreepictures-203" title="Content copyright holder" target="_blank">CopyrightFreePictures</a></small>
</p>

-----

在 Windows 11 上安装 **Node.js** 时，可能会出现与附加包安装相关的错误。
这些错误通常是由于某些 Node.js 包需要使用 **C/C++** 和 **Python** 进行编译。
本文旨在记录如何高效解决这些问题，以帮助你顺利完成安装。

一个常见的错误发生在使用 `chocolaty` 安装附加工具时。
如果 `visualstudio2019-workload-vctools` 无法安装到现有的 chocolaty 路径，可能会导致安装失败。

> visualstudio2019-workload-vctools not installed. the package was not found with the source(s) listed.

如果你在 Windows 11 上安装 Node.js 过程中遇到与附加包安装相关的上述错误消息，本文将提供解决方法。
本文旨在为初学者和经验丰富的开发者提供清晰可行的解决方案，以解决安装过程中常见的问题。

![Automatically install](/uploads/nodejs-installation-failure/automatically-install.png)
<p style="text-align:center;color:gray;"><small>在 Node.js 安装过程中安装所需工具</small></p>

在 Node.js 安装过程中，会出现一个如上图所示的选项，帮助你安装所需的附加工具。
通常情况下，勾选此项并继续，安装过程应该能够正常完成。

![Necessary tools installing](/uploads/nodejs-installation-failure/necessary-tools-installing.png)
<p style="text-align:center;color:gray;"><small>正在安装所需工具</small></p>

![Installation failure](/uploads/nodejs-installation-failure/installation-failure.png)
<p style="text-align:center;color:gray;"><small>安装过程中出现错误</small></p>

这时会显示一个 CMD 窗口，通过 PowerShell 来安装使用 Node.js 所需的附加工具。
如果在安装过程中出现如上图所示的错误，无论重试多少次，都无法完成干净的安装。

### 1. 重新安装 Chocolaty

 - 导航到 C:\ProgramData\chocolaty 目录并删除该目录。
   重新安装 Node.js 时，chocolaty 和所需工具也会被重新安装。
   ![Chocolatey folder](/uploads/nodejs-installation-failure/chocolatey.png)

### 2. 安装 Visual Studio Build Tools

 - 下载并安装最新版本的 [Visual Studio 2019 - Build Tools for Visual Studio 2019](https://visualstudio.microsoft.com/downloads/ "Build Tools for Visual Studio 2019"){:target="_blank"}。
   ![Download build tools](/uploads/nodejs-installation-failure/download-build-tools.png)
   ![MSBuild tools download](/uploads/nodejs-installation-failure/msbuild-tools.png)
   ![Install msbuild tools](/uploads/nodejs-installation-failure/install-msbuild-tools.png)
 - 安装完成后，运行以下命令[升级](https://community.chocolatey.org/packages/visualstudio2019-workload-vctools "Choco upgrade"){:target="_blank"} visualstudio2019-workload-vctools：
   ```shell
   choco upgrade visualstudio2019-workload-vctools -y
   ```
   ![Upgrade vctools](/uploads/nodejs-installation-failure/upgrade-vctools.png)

### 安装完成

Node.js 和所需软件包的安装现已全部完成！
你的开发环境已经准备就绪。

以下是一些额外的验证步骤：

1. 检查 Node.js 版本： <br/>
   要验证安装是否成功，请运行以下命令：
   ```shell
   # 此命令可用于检查 Node.js 和 npm 的版本。
   node -v
   npm -v
   ```
2. 创建一个基本项目： <br/>
   为了确认 Node.js 是否已正确安装，可以创建一个简单的项目。导航到你选择的目录并运行以下命令：
   ```shell
   # 此命令将创建一个新的项目目录并初始化基本的包设置。
   mkdir my-node-project
   cd my-node-project
   npm init -y
   ```
3. 安装必要的软件包： <br/>
   尝试为你的项目安装一些基本的软件包。例如，要安装 Express，请运行以下命令：
   ```shell
   # 此命令将安装 Express 包，你可以用它来构建服务器。
   npm install express
   ```
4. 其他配置： <br/>
   如果还有其他需要的配置或软件包，现在是安装它们的好时机。根据你项目的需求安装必要的软件包并完成环境设置。

现在，Node.js 和所需工具已在你的 Windows 11 系统上安装和配置完毕。你已经准备好开始开发了。祝你编码愉快！

![Upgrade successful](/uploads/nodejs-installation-failure/upgrade-successful.png)
<p style="text-align:center;color:gray;"><small>安装完成</small></p>

### 参考资料

- [Windows 11 (Version 22H2)](https://en.wikipedia.org/wiki/Windows_11 "Windows 11"){:target="_blank"}
- [Node.js 18.x LTS (includes npm 9.6.7)](https://nodejs.org/docs/latest-v18.x/api/index.html "Node.js 18.x LTS"){:target="_blank"}
- [choco-install-visualstudio2017-workload-vctools-fails-error-the-install-of](https://stackoverflow.com/questions/65185384/choco-install-visualstudio2017-workload-vctools-fails-error-the-install-of "StackOverflow 참고사항"){:target="_blank"}