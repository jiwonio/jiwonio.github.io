---
layout: post
title: Configuring Swap Memory on Ubuntu 22.04 LTS
meta: Learn to configure swap memory on Ubuntu 22.04 LTS to address RAM shortages
  on low-spec servers. Perfect for AWS EC2 and self-hosted servers running resource-heavy
  applications.
tags:
- ubuntu
image: /uploads/ubuntu22-swap-memory/thumbnail.webp
lang: en
translation_key: ubuntu22-swap-memory
slug: ubuntu22-swap-memory
description: Learn to configure swap memory on Ubuntu 22.04 LTS to address RAM shortages
  on low-spec servers. Perfect for AWS EC2 and self-hosted servers running resource-heavy
  applications.
permalink: /en/posts/ubuntu22-swap-memory/
categories:
- DevOps
post_type: deep-dive
updated: 2024-08-15 10:00:00 +0900
---
When using the free tier of services like **Amazon Web Services EC2** or other self-hosted servers,
you might occasionally run into issues with insufficient RAM when installing large external resources.
This can cause the server to freeze for extended periods and eventually crash.
While this doesn't happen often, it can be quite critical if you're running a personal project
for commercial use and implementing a **Micro Service Architecture** on a server with very limited specifications.
In such situations, **swap memory** can be extremely helpful. In this post, I've written about how to create swap memory and what it is.

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">I also publish on [Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"}.</small>

![Random Access Memory](/uploads/ubuntu22-swap-memory/ram.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@akshar_dave" title="Content copyright holder" target="_blank">Akshar Dave🌻</a></small>
</p>

-----

**Swap memory** serves to supplement insufficient memory capacity by using a portion of the physical disk as volatile RAM (hereinafter referred to as memory).
Occasionally, when installing large packages like [Laravel](https://laravel.com/ "Laravel"){:target="_blank"} or [NestJS](https://nestjs.com/ "NestJS"){:target="_blank"}, the installation can fail due to insufficient resources, as it requires a significant amount of computer resources like memory and CPU.

On most virtual machine services, such as [Google Compute Engine](https://cloud.google.com/products/compute "Google Compute Engine"){:target="_blank"} and [Amazon EC2](https://aws.amazon.com/ko/ec2/ "Amazon EC2"){:target="_blank"}, you need to stop the instance and change its type to increase the memory capacity.
If a system error due to insufficient memory occurs unexpectedly and forces a reboot, it's crucial to be prepared in advance, as losses will continue to mount while the service is down.
In such cases, configuring swap memory can provide at least temporary relief from memory shortages.

While such situations are rare in most commercial service environments due to the adoption of sophisticated infrastructure management technologies, setting up swap memory is very convenient and helpful on low-spec systems, like free-tier instances used for development testing or toy projects.

![Windows 11 virtual memory](/uploads/ubuntu22-swap-memory/windows11-virtual-memory.png)

<p style="text-align:center;color:gray;"><small>Virtual memory in Windows</small></p>

The concept of swap memory isn't exclusive to Linux or Unix-like systems such as Ubuntu. It's also utilized in Windows under the name "virtual memory" and is particularly useful on low-spec PCs.

### Setting Up Swap Memory

1. Check if swap memory is already configured
   ```shell
      sudo free -m
      sudo swapon -s
   ```
   ![Check swap memory](/uploads/ubuntu22-swap-memory/check-swap-memory.png)
2. If swap memory is configured, disable it
   ```shell
      sudo swapoff -a
   ```
3. Create a swapfile to be used as swap memory
   ```shell
      # Create a 4G swap file
      sudo fallocate -l 4G /swapfile
   ```
4. Configure the created swapfile to be used as swap memory
    ```shell
      # Modify permissions
      sudo chmod 600 /swapfile
    
      # Prepare for activation
      sudo mkswap /swapfile
    
      # Activate
      sudo swapon /swapfile
    ```
   ![Make swapfile](/uploads/ubuntu22-swap-memory/make-swapfile.png)
5. Configure swap memory to persist after a server reboot
    ```shell
      # Edit the file
      sudo nano /etc/fstab 
    
      # Add the following line
      /swapfile swap swap defaults 0 0
    ```
   ![Swap setup for rebooting](/uploads/ubuntu22-swap-memory/swap-setup-for-rebooting.png)
6. Swap memory setup complete
   ![Complete make swapfile](/uploads/ubuntu22-swap-memory/complete-make-swapfile.png)

### Disabling Swap Memory

If you no longer need swap memory, disable it.
```shell
# Disable swap
sudo swapoff -v /swapfile 

# Edit /etc/fstab and remove the following line
sudo nano /etc/fstab      
/swapfile swap swap defaults 0 0

# Delete the swap file
sudo rm /swapfile 
```

### References
- Wikipedia: [Virtual memory](https://en.wikipedia.org/wiki/Virtual_memory "Virtual memory"){:target="_blank"}
- Wikipedia: [Paging](https://en.wikipedia.org/wiki/Memory_paging "Paging"){:target="_blank"}