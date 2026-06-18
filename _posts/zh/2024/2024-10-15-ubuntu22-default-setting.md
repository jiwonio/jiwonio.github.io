---
layout: post
title: AWS EC2 Ubuntu 实例基本初始设置指南
meta: 了解在 AWS EC2 上设置 Ubuntu 22.04 LTS 的关键初始步骤。本指南重点介绍如何为开发和测试环境配置低规格实例，非常适合免费套餐用户。
tags:
- AWS
image: /uploads/ubuntu22-default-setting/thumbnail.webp
lang: zh
translation_key: ubuntu22-default-setting
slug: ubuntu22-default-setting
description: 了解在 AWS EC2 上设置 Ubuntu 22.04 LTS 的关键初始步骤。本指南重点介绍如何为开发和测试环境配置低规格实例，非常适合免费套餐用户。
permalink: /zh/posts/ubuntu22-default-setting/
---
在 AWS EC2 上设置开发或测试环境时，为您的实例选择正确的配置至关重要。
本指南将引导您完成 **Ubuntu 22.04 LTS** 的初始设置步骤，非常适合希望通过免费套餐来降低成本的用户。
我们将介绍基本配置，而不涉及 Route 53、ELB 或 RDS 等服务，使本指南非常适合简单、必要的设置。
无论您是初学者还是经验丰富的开发人员，拥有一个配置良好的实例都可以节省您的时间并避免常见问题。
本指南确保您的 Ubuntu 服务器设置正确，让您可以专注于项目而不是排查故障。
从设置用于安全访问的密钥对到配置防火墙和存储，我们都已为您准备好。
请按照以下步骤为您的开发或测试需求创建一个稳定高效的环境。

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">我也在 [Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"} 上发布。</small>

![Ubuntu Server](/uploads/ubuntu22-default-setting/ubuntu.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@6heinz3r" title="Content copyright holder" target="_blank">Gabriel Heinzer</a></small>
</p>

-----

在 [Amazon EC2](https://aws.amazon.com/ec2/ "Amazon EC2"){:target="_blank"} 上设置开发或测试环境时，正确配置实例至关重要。本指南将引导您完成 Ubuntu 22.04 LTS 的初始设置步骤。
这对于希望通过使用免费套餐来降低成本的用户尤其有用。本指南不涉及 Route 53、ELB、RDS 等服务，而是专注于基本设置。

### 1. 服务器基本设置

<p style="text-align:right;color:gray;"><small>EC2 规格</small></p>

| EC2 设置项    | 设置值                                           |
|------------|------------------------------------------------|
| 镜像(AMI)     | Ubuntu Server 22.04 LTS (HVM), SSD Volume Type |
| 实例类型      | t2.micro                                       |
| 防火墙(安全组)   | launch-wizard-9                                |
| 存储(卷)     | 1个 - 30GB                                      |
| 密钥对(登录)    | Key pair file                                  |

![Create EC2 instance](/uploads/ubuntu22-default-setting/create-ec2-Instance.png)
<p style="text-align:center;color:gray;"><small>EC2 规格设置</small></p>

对于开发或测试用途，不需要高规格配置。免费套餐的机型就足够了。
launch-wizard-9 安全组是创建实例时自动生成的基本设置值，它向所有人开放了 API 开发所需的端口，如 22、80、3306 等。
为了加强安全性，建议使用 [OpenVPN](https://openvpn.net/ "OpenVPN"){:target="_blank"} 等工具固定 IP 地址，并设置仅允许这些 IP 访问端口。

![Security group - inbound](/uploads/ubuntu22-default-setting/security-inbound.png)
<p style="text-align:center;color:gray;"><small>安全组入站规则设置</small></p>

使用 ubuntu 账户登录，并通过密钥文件代替密码。使用像 [PuTTY](https://www.putty.org/ "PuTTY"){:target="_blank"} 或 [Termius](https://termius.com/ "Termius"){:target="_blank"} 这样易于管理的程序会很方便。
下载 ppk 或 pem 文件进行登录。

### 2. 更改 hostname

```shell
ubuntu@ip-172-0-0-0:~$ sudo hostnamectl set-hostname test
ubuntu@ip-172-0-0-0:~$ sudo reboot

# hostname 更改完成
ubuntu@test:~$
```

### 3. 更新 Ubuntu

```shell
ubuntu@test:~$ sudo apt update
ubuntu@test:~$ sudo apt upgrade
ubuntu@test:~$ sudo apt dist-upgrade
ubuntu@test:~$ sudo apt autoremove
ubuntu@test:~$ sudo apt clean
ubuntu@test:~$ sudo apt autoclean
```

### 4. 更改 history 格式

![History Setup - default format](/uploads/ubuntu22-default-setting/history-default-format.png)
<p style="text-align:center;color:gray;"><small>原有的 history 格式</small></p>

```shell
# 更改 history 格式
ubuntu@test:~$ sudo vi /etc/profile

# 在文件末尾添加以下内容
# 在 VIM 中，按 Shift + G 可跳转到文件末尾
HISTTIMEFORMAT="[%Y-%m-%d %H:%M:%S] "
export HISTTIMEFORMAT
```

![History Setup - default time format](/uploads/ubuntu22-default-setting/history-default-timeformat.png)
<p style="text-align:center;color:gray;"><small>添加 HISTTIMEFORMAT 内容</small></p>

![History setup](/uploads/ubuntu22-default-setting/history-setup.png)
<p style="text-align:center;color:gray;"><small>history 格式更改完成</small></p>

### 5. 增加 history 缓存大小

```shell
# 增加 history 缓存
ubuntu@test:~$ sudo vi /etc/bash.bashrc 

# 在文件末尾添加以下内容
# 在 VIM 中，按 Shift + G 可跳转到文件末尾
export HISTSIZE=10000
export HISEFILESIZE=10000
```

![History default size](/uploads/ubuntu22-default-setting/history-default-size.png)
<p style="text-align:center;color:gray;"><small>添加 HISTSIZE 和 HISEFILESIZE 内容</small></p>

### 6. 设置韩语 locale

```shell
# 检查当前 locale
ubuntu@test:~$ locale
```

![Locale check](/uploads/ubuntu22-default-setting/locale-check.png)
<p style="text-align:center;color:gray;"><small>检查当前 locale 设置值</small></p>

```shell
# 安装韩语语言包
ubuntu@test:~$ sudo apt install language-pack-ko

# 应用韩语设置
ubuntu@test:~$ sudo update-locale LANG=ko_KR.UTF-8 LANGUAGE="ko_KR:ko:en_US:en" LC_MESSAGES=POSIX

# 重启后生效
ubuntu@test:~$ sudo reboot
```

![Setup locale](/uploads/ubuntu22-default-setting/setup-locale.png)
<p style="text-align:center;color:gray;"><small>locale 更改完成</small></p>

### 7. 将 timezone 设置为韩国时间

```shell
# 检查时区
ubuntu@test:~$ timedatectl
```

![Timezone check](/uploads/ubuntu22-default-setting/timezone-check.png)
<p style="text-align:center;color:gray;"><small>检查当前时区设置值</small></p>

```shell
# 检查是否存在首尔时区
ubuntu@test:~$ timedatectl list-timezones | grep Seoul

# 将时区更改为首尔
ubuntu@test:~$ sudo timedatectl set-timezone Asia/Seoul 
```

![Timezone setup](/uploads/ubuntu22-default-setting/timezone-setup.png)
<p style="text-align:center;color:gray;"><small>timezone 更改完成</small></p>

### 参考资料

- [How to set or change timezone](https://linuxize.com/post/how-to-set-or-change-timezone-on-ubuntu-20-04/ "How to set or change timezone"){:target="_blank"}
- [How do I change the default locale](https://askubuntu.com/questions/89976/how-do-i-change-the-default-locale-in-ubuntu-server "How do I change the default locale"){:target="_blank"}