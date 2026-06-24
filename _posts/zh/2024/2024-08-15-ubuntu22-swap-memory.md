---
layout: post
title: 在 Ubuntu 22.04 LTS 上配置交换内存
meta: 学习如何在 Ubuntu 22.04 LTS 上配置交换内存，以解决低规格服务器上的 RAM 短缺问题。非常适合运行资源密集型应用的 AWS EC2 和自托管服务器。
tags:
- ubuntu
image: /uploads/ubuntu22-swap-memory/thumbnail.webp
lang: zh
translation_key: ubuntu22-swap-memory
slug: ubuntu22-swap-memory
description: 学习如何在 Ubuntu 22.04 LTS 上配置交换内存，以解决低规格服务器上的 RAM 短缺问题。非常适合运行资源密集型应用的 AWS
  EC2 和自托管服务器。
permalink: /zh/posts/ubuntu22-swap-memory/
categories:
- DevOps
post_type: deep-dive
---
在使用 **Amazon Web Services EC2** 等服务的免费套餐或其他自托管服务器时，安装大型外部资源时偶尔会遇到内存不足的问题。
这可能导致服务器长时间卡顿，并最终崩溃。
虽然这种情况不常发生，但如果您在规格非常有限的服务器上运行用于商业用途的个人项目并实施**微服务架构（Micro Service Architecture）**，这个问题可能会非常关键。
在这种情况下，**交换内存（swap memory）**会非常有帮助。在这篇文章中，我将介绍什么是交换内存以及如何创建它。

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">我也在 [Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"} 上发布。</small>

![Random Access Memory](/uploads/ubuntu22-swap-memory/ram.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@akshar_dave" title="Content copyright holder" target="_blank">Akshar Dave🌻</a></small>
</p>

-----

**交换内存**（Swap Memory）的作用是使用物理磁盘的一部分作为易失性内存 RAM（以下简称内存），以补充不足的内存容量。
有时，在安装像 [Laravel](https://laravel.com/ "Laravel"){:target="_blank"} 或 [NestJS](https://nestjs.com/ "NestJS"){:target="_blank"} 这样的大型软件包时，会需要大量的内存和 CPU 资源，即计算机资源。如果资源不足，安装可能会失败。

在大多数虚拟机服务中，如 [Google Compute Engine](https://cloud.google.com/products/compute "Google Compute Engine"){:target="_blank"}、[Amazon EC2](https://aws.amazon.com/ko/ec2/ "Amazon EC2"){:target="_blank"} 等，要增加内存容量，需要先停止实例，然后更改实例类型。
如果在意想不到的情况下因内存不足而发生系统错误导致需要重启，那么在实例停止期间会持续产生损失，因此有必要提前做好准备。
在这种情况下，设置交换内存可以临时性地缓解内存不足的问题。

在大多数商业服务环境中，通常会采用各种基础设施管理技术，因此很少会发生上述情况。但是，对于用于开发测试或玩具项目（toy project）的免费套餐等低规格环境，设置交换内存会非常方便且有帮助。

![Windows 11 virtual memory](/uploads/ubuntu22-swap-memory/windows11-virtual-memory.png)

<p style="text-align:center;color:gray;"><small>Windows 的虚拟内存</small></p>

交换内存这个概念并不仅限于 Ubuntu 等 Linux 或 Unix 系统。在 Windows 中，它以虚拟内存的名称存在，并在低配置电脑上被有效地使用。

### 配置交换内存

1. 检查是否已配置交换内存
   ```shell
      sudo free -m
      sudo swapon -s
   ```
   ![Check swap memory](/uploads/ubuntu22-swap-memory/check-swap-memory.png)
2. 如果已配置交换内存，请先禁用
   ```shell
      sudo swapoff -a
   ```
3. 创建用作交换内存的 swapfile
   ```shell
      # 创建一个 4G 大小的交换文件
      sudo fallocate -l 4G /swapfile
   ```
4. 将创建的 swapfile 设置为交换内存
    ```shell
      # 修改权限
      sudo chmod 600 /swapfile
    
      # 准备激活
      sudo mkswap /swapfile
    
      # 激活
      sudo swapon /swapfile
    ```
   ![Make swapfile](/uploads/ubuntu22-swap-memory/make-swapfile.png)
5. 设置服务器重启后也能使用交换内存
    ```shell
      # 编辑文件
      sudo nano /etc/fstab 
    
      # 添加以下内容
      /swapfile swap swap defaults 0 0
    ```
   ![Swap setup for rebooting](/uploads/ubuntu22-swap-memory/swap-setup-for-rebooting.png)
6. 交换内存配置完成
   ![Complete make swapfile](/uploads/ubuntu22-swap-memory/complete-make-swapfile.png)

### 禁用交换内存

如果不再需要使用交换内存，可以将其禁用。
```shell
# 禁用交换分区
sudo swapoff -v /swapfile 

# 编辑文件并删除以下行
sudo nano /etc/fstab      
/swapfile swap swap defaults 0 0

# 删除 swap 文件
sudo rm /swapfile 
```

### 参考资料
- 维基百科：[虚拟内存](https://en.wikipedia.org/wiki/Virtual_memory "虚拟内存"){:target="_blank"}
- 维基百科：[内存分页](https://en.wikipedia.org/wiki/Memory_paging "内存分页"){:target="_blank"}