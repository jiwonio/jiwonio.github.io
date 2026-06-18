---
layout: post
title: 在 Windows 11 上使用 WSL2 创建多个开发环境
meta: 学习如何在 Windows 11 上使用 WSL2 设置和管理多个开发环境。本指南涵盖安装、配置以及优化工作流程的技巧。
tags:
- wsl2
image: /uploads/multiple-wsl2-instances/thumbnail.webp
lang: zh
translation_key: multiple-wsl2-instances
slug: multiple-wsl2-instances
description: 学习如何在 Windows 11 上使用 WSL2 设置和管理多个开发环境。本指南涵盖安装、配置以及优化工作流程的技巧。
permalink: /zh/posts/multiple-wsl2-instances/
---
在当今快节奏的开发世界中，高效地管理**多个开发环境**至关重要。
**适用于 Linux 的 Windows 子系统 2 (WSL2)** 提供了一种强大而灵活的方式，可以直接在您的 **Windows 11** 计算机上创建和管理隔离的环境。
无论您是软件开发人员还是业余爱好者，为不同项目设置独立的环境都可以简化您的工作流程并最大限度地减少冲突。
本指南将引导您在 Windows 11 上设置和配置**多个 WSL2 实例**，确保您可以优化开发生产力。

<!--more-->

![Multiple WSL2 Instances](/uploads/multiple-wsl2-instances/server.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@benofthenorth" title="Content copyright holder" target="_blank">Ben Griffiths</a></small>
</p>

-----

在所有开发环境（如旧版环境或分布式环境）中配置环境是一件相当麻烦的事情。
很少会每次都重新设置环境，通常一次设置好后，会使用数月甚至数年而没有大的变化。
因此，开发人员常常需要每次都通过谷歌搜索来查找环境配置方法。

在开发 PHP 时，可以使用 [MAMP](https://www.mamp.info/ "MAMP"){:target="_blank"} 或 [XAMPP](https://www.apachefriends.org/ "XAMPP"){:target="_blank"} 等工具轻松配置开发环境。
此外，使用 [Docker](https://www.docker.com/ "Docker"){:target="_blank"} 等容器技术，或利用 [VirtualBox](https://www.virtualbox.org/ "VirtualBox"){:target="_blank"}、[VMware](https://www.vmware.com/ "VMware"){:target="_blank"} 等虚拟环境也是不错的替代方案。
这些工具根据各自的需求，以多种方式提供开发环境。

在本文中，我们将详细探讨在众多开发环境配置方法中，如何特别利用 Windows 11 的 [WSL2](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux "Windows Subsystem for Linux"){:target="_blank"} 来配置开发环境。
我们将介绍如何通过 WSL2 更轻松地构建和管理隔离环境，希望能帮助您提高开发生产力。

### 启用 WSL

要在 Windows 11 中使用**适用于 Linux 的 Windows 子系统 (WSL)**，首先需要启用相关功能并将其注册到注册表中。
如果不激活此功能，在安装 WSL 的过程中可能会出现 `wslregisterdistribution failed with error: 0x800701bc` 或 `wslregisterdistribution failed with error: 0x80370102` 等错误。
这些错误意味着 WSL 未能正常安装，需要进行一些设置来解决。

首先，您需要在 Windows 功能中启用“**适用于 Linux 的 Windows 子系统**”和“**虚拟机平台**”。这两个功能是 WSL2 正常运行所必需的。
启用这些功能并重启系统后，必要的注册表设置就会完成，您就可以顺利安装 WSL 了。

![Windows features on or off](/uploads/multiple-wsl2-instances/windows-features.png)

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem auto 0;max-width:100%;">
    <div>
        <img src="/uploads/multiple-wsl2-instances/windows-features-1.png" alt="Windows features on or off" />
    </div>
    <div>
        <img src="/uploads/multiple-wsl2-instances/windows-features-2.png" alt="Windows features on or off" />
    </div>
</div>
<p style="text-align:center;color:gray;"><small>启用或关闭 Windows 功能</small></p>

此外，安装 WSL 后，您可能还需要下载并安装最新的 [Linux 内核更新包](https://learn.microsoft.com/ko-kr/windows/wsl/install-manual#step-4---download-the-linux-kernel-update-package "Linux 内核更新包下载"){:target="_blank"}。
这样可以保持 WSL 环境为最新状态，并防止潜在的错误。
一切准备就绪后，您就可以安装各种 Linux 发行版并配置您的开发环境了。

### 安装 WSL 发行版

安装 WSL 的准备工作已经完成，现在我们来安装一个发行版。

![WSL Installable List](/uploads/multiple-wsl2-instances/wsl-installable-list.png)
<p style="text-align:center;color:gray;"><small>可安装的 WSL 发行版</small></p>

您可以使用 `wsl -l -o` 命令来查看可安装的发行版镜像。
使用此命令会显示当前所有可安装的 Linux 发行版列表。

您可以看到 Ubuntu、Debian、Kali Linux 等多个选项。
下一步是选择并安装您想要的发行版。
要安装发行版，可以使用 `wsl --install -d <发行版名称>` 命令。
例如，如果您想安装 Ubuntu，只需输入 `wsl --install -d Ubuntu` 命令即可。

安装完成后，该发行版将自动启动，您可以进行初始设置。
现在，选择并安装您喜欢的 Linux 发行版，开始在 WSL 环境中进行各种开发工作吧。
每个发行版都提供其独特的特性和工具，因此选择最适合您项目的发行版非常重要。

### 安装多个同类 Linux 实例

以 *2024 年 12 月*为基准，输入 `wsl --install` 命令会安装默认发行版 **Ubuntu**。
安装的版本是最新的 LTS 版本，即 **Ubuntu 24.04.1 LTS**。安装此镜像并完成基本设置后，您可以使用 `export` 命令将其导出，以便将来使用 `import` 命令重新创建。

```shell
wsl --export Ubuntu Ubuntu-clean.tar
wsl --import Ubuntu-clean .\Ubuntu-clean .\Ubuntu-clean.tar
```

运行这些命令后，会将当前配置的 Ubuntu 镜像导出为 Ubuntu-clean.tar 文件，当需要时，可以再次导入该镜像作为一个新的实例使用。
这在创建多个相同的开发环境，或在保持初始状态的同时测试各种配置时非常有用。

之后，输入 `wsl -l -v` 命令可以查看当前已安装的 WSL 发行版列表。
下图显示了已安装完成的镜像列表。之后，您可以输入 `wsl -d Ubuntu-clean` 命令来运行特定的发行版。

![WSL Installed List](/uploads/multiple-wsl2-instances/wsl-installed-list.png)
<p style="text-align:center;color:gray;"><small>已安装完成的镜像</small></p>

通过为每个安装的镜像分别配置开发环境，您可以进行各种实验和测试。
例如，您可以在一个镜像中运行 Apache Web 服务器，在另一个镜像中安装 Nginx Web 服务器，以比较不同 Web 服务器的性能和特性。
此外，您还可以安装同一 Web 服务器的不同版本，或安装不同版本的开发语言，以测试在各自环境中的兼容性和性能。

像这样，通过为每个 WSL2 实例设置独立的开发环境，您可以为特定项目构建最优化的环境。
这可以最大限度地减少开发过程中可能出现的依赖冲突，并为项目之间提供隔离的测试环境，从而支持更高效的开发流程。
要注销测试环境并删除其 vhd 文件，可以输入 `wsl --unregister Ubuntu-clean` 命令。

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem auto 0;max-width:100%;">
    <div>
        <img src="/uploads/multiple-wsl2-instances/wsl-ubuntu-apache2.png" alt="WSL Ubuntu Apache2" />
    </div>
    <div>
        <img src="/uploads/multiple-wsl2-instances/wsl-ubuntu-nginx.png" alt="WSL Ubuntu Nginx" />
    </div>
</div>
<p style="text-align:center;color:gray;"><small>分别配置 Web 服务器</small></p>

总而言之，使用 WSL2 的多实例环境为开发人员提供了灵活性和可扩展性，使其成为一个可以轻松进行各种实验和测试的强大工具。
通过这样配置的环境，您可以最大限度地提高开发生产力，并能更系统地对各种场景进行验证。

### 参考资料

- [如何使用 WSL 在 Windows 上安装 Linux](https://learn.microsoft.com/ko-kr/windows/wsl/install "如何使用 WSL 在 Windows 上安装 Linux"){:target="_blank"}
- [解决 WSL 错误 0x80370102](https://velog.io/@jaylnne/WSL-Error-0x80370102-해결 "wslregisterdistribution failed with error: 0x80370102"){:target="_blank"}
- [运行 WSL/WSL2 Ubuntu 时出现 0x800701bc 错误](https://velog.io/@meek/WSL-WSL2-Ubuntu-구동-시-0x800701bc-에러 "wslregisterdistribution failed with error: 0x800701bc"){:target="_blank"}
- [如何在 Windows WSL 环境中安装多个同类 Linux](https://blog.naver.com/techshare/222596544852 "如何在 Windows WSL 环境中安装多个同类 Linux"){:target="_blank"}