---
layout: post
title: Essential Initial Setup Guide for Ubuntu on AWS EC2 Instances
tags:
- AWS
image: /uploads/ubuntu22-default-setting/thumbnail.webp
lang: en
translation_key: ubuntu22-default-setting
slug: ubuntu22-default-setting
description: Discover the key initial setup steps for Ubuntu 22.04 LTS on AWS EC2.
  This guide focuses on configuring low-spec instances for development and testing
  environments, perfect for free tier usage.
permalink: /en/posts/ubuntu22-default-setting/
categories:
- DevOps
post_type: deep-dive
updated: 2026-07-13 12:00:00 +0900
---
When setting up a development or testing environment on AWS EC2, starting with the right configurations for your instance is essential. 
This guide walks you through the initial setup steps for **Ubuntu 22.04 LTS**, ideal for those utilizing the free tier to keep costs down. 
We'll cover the basic configurations without going into services like Route 53, ELB, or RDS, making this guide perfect for straightforward, essential setups.
Whether you're a beginner or an experienced developer, having a well-configured instance can save you time and prevent common issues. 
This guide ensures your Ubuntu server is set up correctly, allowing you to focus on your projects rather than troubleshooting. 
From setting up key pairs for secure access to configuring the firewall and storage, we've got you covered. 
Follow these steps to create a stable and efficient environment for your development or testing needs.

<!--more-->

![Ubuntu Server](/uploads/ubuntu22-default-setting/ubuntu.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@6heinz3r" title="Content copyright holder" target="_blank">Gabriel Heinzer</a></small>
</p>

-----

## Scope of this guide

Out of scope: Route 53, ALB/ELB, RDS, multi-AZ production topology.
In scope: **one EC2 Ubuntu 22.04** host for development and testing.

Even on free-tier sizes, leaving 22/80/3306 open to `0.0.0.0/0` for a long time is a bad default.

## Before you launch

1. Restrict local `.pem` permissions
2. SSH (22) only from your IP / VPN / bastion
3. Give the root volume room if you will use Docker or large logs
4. Decide whether a public or Elastic IP is required

When setting up a development or testing environment on [Amazon EC2](https://aws.amazon.com/ec2/ "Amazon EC2"){:target="_blank"}, it's crucial to configure your instance correctly. This guide will walk you through the initial setup steps for Ubuntu 22.04 LTS. It's especially useful if you're using the free tier to keep costs down. We will focus on basic configurations and won't cover services like Route 53, ELB, or RDS.

### 1. Basic Server Setup

<p style="text-align:right;color:gray;"><small>EC2 Specifications</small></p>

| EC2 Configuration Item  | Setting Value                                           |
|------------|------------------------------------------------|
| Image (AMI)   | Ubuntu Server 22.04 LTS (HVM), SSD Volume Type |
| Instance Type    | t2.micro                                       |
| Firewall (Security Group) | launch-wizard-9                                |
| Storage (Volumes)   | 1 volume - 30GB                                      |
| Key Pair (Login)  | Key pair file                                  |

![Create EC2 instance](/uploads/ubuntu22-default-setting/create-ec2-Instance.png)
<p style="text-align:center;color:gray;"><small>EC2 Specification Settings</small></p>

For development or testing purposes, high specifications are not required; the free tier model is sufficient. 
The `launch-wizard-9` security group is the default setting automatically created with the instance. It opens ports necessary for API development, such as 22, 80, and 3306, to all IP addresses. 
To enhance security, it is recommended to use a tool like [OpenVPN](https://openvpn.net/ "OpenVPN"){:target="_blank"} to get a static IP address and configure the security group to allow access only from that IP.

![Security group - inbound](/uploads/ubuntu22-default-setting/security-inbound.png)
<p style="text-align:center;color:gray;"><small>Security Group Inbound Settings</small></p>

Log in as the `ubuntu` user, using a key file instead of a password. Using an easy-to-manage client like [PuTTY](https://www.putty.org/ "PuTTY"){:target="_blank"} or [Termius](https://termius.com/ "Termius"){:target="_blank"} is convenient.
Download the .ppk or .pem file to log in.

### 2. Change Hostname

```shell
ubuntu@ip-172-0-0-0:~$ sudo hostnamectl set-hostname test
ubuntu@ip-172-0-0-0:~$ sudo reboot

# Hostname change complete
ubuntu@test:~$
```

### 3. Update Ubuntu

```shell
ubuntu@test:~$ sudo apt update
ubuntu@test:~$ sudo apt upgrade
ubuntu@test:~$ sudo apt dist-upgrade
ubuntu@test:~$ sudo apt autoremove
ubuntu@test:~$ sudo apt clean
ubuntu@test:~$ sudo apt autoclean
```

### 4. Change History Format

![History Setup - default format](/uploads/ubuntu22-default-setting/history-default-format.png)
<p style="text-align:center;color:gray;"><small>Original history format</small></p>

```shell
# Change history format
ubuntu@test:~$ sudo vi /etc/profile

# Add the following lines to the end of the file
# In VIM, press Shift + G to go to the end of the file
HISTTIMEFORMAT="[%Y-%m-%d %H:%M:%S] "
export HISTTIMEFORMAT
```

![History Setup - default time format](/uploads/ubuntu22-default-setting/history-default-timeformat.png)
<p style="text-align:center;color:gray;"><small>Adding HISTTIMEFORMAT configuration</small></p>

![History setup](/uploads/ubuntu22-default-setting/history-setup.png)
<p style="text-align:center;color:gray;"><small>History format change complete</small></p>

### 5. Increase History Cache Size

```shell
# Increase history cache size
ubuntu@test:~$ sudo vi /etc/bash.bashrc 

# Add the following lines to the end of the file
# In VIM, press Shift + G to go to the end of the file
export HISTSIZE=10000
export HISTFILESIZE=10000
```

![History default size](/uploads/ubuntu22-default-setting/history-default-size.png)
<p style="text-align:center;color:gray;"><small>Adding HISTSIZE and HISTFILESIZE configuration</small></p>

### 6. Set Locale to Korean

```shell
# Check the current locale
ubuntu@test:~$ locale
```

![Locale check](/uploads/ubuntu22-default-setting/locale-check.png)
<p style="text-align:center;color:gray;"><small>Checking the current locale settings</small></p>

```shell
# Install the Korean language pack
ubuntu@test:~$ sudo apt install language-pack-ko

# Apply the Korean locale
ubuntu@test:~$ sudo update-locale LANG=ko_KR.UTF-8 LANGUAGE="ko_KR:ko:en_US:en" LC_MESSAGES=POSIX

# Apply after reboot
ubuntu@test:~$ sudo reboot
```

![Setup locale](/uploads/ubuntu22-default-setting/setup-locale.png)
<p style="text-align:center;color:gray;"><small>Locale change complete</small></p>

### 7. Set Timezone to Seoul

```shell
# Check the timezone
ubuntu@test:~$ timedatectl
```

![Timezone check](/uploads/ubuntu22-default-setting/timezone-check.png)
<p style="text-align:center;color:gray;"><small>Checking the current timezone settings</small></p>

```shell
# Check if the Seoul timezone exists
ubuntu@test:~$ timedatectl list-timezones | grep Seoul

# Change the timezone to Seoul
ubuntu@test:~$ sudo timedatectl set-timezone Asia/Seoul 
```

![Timezone setup](/uploads/ubuntu22-default-setting/timezone-setup.png)
<p style="text-align:center;color:gray;"><small>Timezone change complete</small></p>



## Common mistakes

- Opening MySQL 3306 to the world
- Typo `HISTFILESIZE` instead of `HISTFILESIZE`
- Kernel updates without reboot when required
- Sharing key files in chat

## Suggested next steps

- Add swap if installs OOM: [swap guide](/en/posts/ubuntu22-swap-memory/)
- Consider `ufw` for host firewall defense in depth
- For longer life: unattended-upgrades, fail2ban, snapshots

## References

- [How to set or change timezone](https://linuxize.com/post/how-to-set-or-change-timezone-on-ubuntu-20-04/ "How to set or change timezone"){:target="_blank"}
- [How do I change the default locale](https://askubuntu.com/questions/89976/how-do-i-change-the-default-locale-in-ubuntu-server "How do I change the default locale"){:target="_blank"}