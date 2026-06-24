---
layout: post
title: 解决 DataGrip 连接 Amazon RDS 时的驱动程序错误
meta: 了解如何解决将 Amazon RDS 连接到 JetBrains DataGrip 时的驱动程序错误。本指南涵盖了常见问题和实用解决方案，以实现无缝的数据库管理。
tags:
- mysql
image: /uploads/datagrip-driver-error/thumbnail.webp
lang: zh
translation_key: datagrip-driver-error
slug: datagrip-driver-error
description: 了解如何解决将 Amazon RDS 连接到 JetBrains DataGrip 时的驱动程序错误。本指南涵盖了常见问题和实用解决方案，以实现无缝的数据库管理。
permalink: /zh/posts/datagrip-driver-error/
categories:
- DevOps
post_type: deep-dive
---
JetBrains 提供了 **DataGrip**，这是一款用于处理关系型和 NoSQL 数据库的跨平台工具。
该工具支持多种数据库，包括 MySQL、Oracle Database、PostgreSQL、SQLite、MongoDB 和 Redis。
它还提供了轻松连接到 Amazon Redshift 等云数据库的选项。
最近，新增了 **AI 助手**插件，使得编写查询变得更加方便和高效。
此功能可帮助开发人员在处理数据时提高生产力。
在本文中，我们将讨论使用 JetBrains DataGrip 连接到 **Amazon RDS** 时可能发生的**驱动程序错误**，并探讨解决方法。

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">我也在 [Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"} 上发布文章。</small>

![Cloud Databases](/uploads/datagrip-driver-error/cloud-database.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/avnsuresh-19928520" title="Content copyright holder" target="_blank">Suresh anchan</a></small>
</p>

-----

数据库连接是应用程序开发和运维中至关重要的步骤之一。
特别是在**云环境**中使用数据库时，必须充分了解连接设置过程中的细节以及可能出现的错误。
**Amazon RDS** 是云环境中常用的托管数据库服务，由于其稳定性和灵活性，受到许多开发人员和企业的青睐。
然而，当将 Amazon RDS 连接到像 **JetBrains DataGrip** 这样的数据库管理工具时，有时可能会出现意想不到的问题。

本文旨在帮助遇到类似问题的开发人员有效解决问题，并更稳定地将 Amazon RDS 与 DataGrip 集成。
数据库连接过程中的一个小错误都可能对开发流程产生重大影响，因此查明问题的根本原因并找到合适的解决方案至关重要。
现在，让我们在正文中逐一探讨解决这些问题的具体步骤。

### 驱动程序错误

```
DBMS: MySQL (no ver.)
Case sensitivity: plain=mixed, delimited=exact
NotAfter: Wed Jun 01 12:00:00 UTC 2022.
```

![MySQL connection failed](/uploads/datagrip-driver-error/failed.png)

<p style="text-align:center;color:gray;"><small>连接 Amazon RDS 时的驱动程序错误</small></p>

由于 MySQL 驱动程序无法正常连接，连接持续失败。
要查看详细的错误信息，您需要检查 DataGrip 的日志消息。

### 检查 DataGrip 日志

```shell
# DataGrip 日志文件
vi ~/AppData/Local/JetBrains/DataGrip{{ VERSION }}/log/idea.log
```

![SSL Handshake exception error](/uploads/datagrip-driver-error/ssl-handshake-exception-error.png)
<p style="text-align:center;color:gray;"><small>SSLHandshakeException 错误</small></p>

![Communications line failure](/uploads/datagrip-driver-error/communications-link-failure.png)
<p style="text-align:center;color:gray;"><small>Communications link failure</small></p>

在 DataGrip 日志文件中，您可以通过搜索 `Connecting to: jdbc:mysql://{HOST}:3306` 或尝试连接的主机地址来确定发生了什么错误。
已确认出现 `javax.net.ssl.SSLHandshakeException` 或 `[08S01] Communications link failure` 等通信错误。

这似乎是 **TLS** 通信过程中出现了问题，我个人认为，当 Amazon RDS 实例设置中的**存储加密**选项被激活时，可能会出现此问题。

<h3 style="word-wrap: break-word;">1. javax.net.ssl.SSLHandshakeException</h3>

此错误通常与 SSL/TLS 设置有关，由客户端和服务器之间的身份验证问题引起。

解决方法：
1. 更新 JDBC 驱动程序：
    - 将 JetBrains DataGrip 中使用的 MySQL JDBC 驱动程序更新到最新版本。最新的驱动程序解决了许多与 SSL/TLS 协议相关的问题。

2. 检查 TLS 版本：
    - Amazon RDS 实例支持的 TLS 版本必须与 JDBC 驱动程序使用的 TLS 版本相匹配。
    - 在 Amazon RDS 控制台中检查**实例设置（TLS 版本）**，如有必要，请更改为较低版本（例如 TLS 1.2）。

3. 配置 SSL 证书：
    - Amazon RDS 默认使用 SSL 证书。
    - 从 RDS 控制台下载 AWS 提供的证书，并将其添加到 DataGrip 的连接设置中。<br/>
      例如：在 MySQL 连接 URL 中添加 ?useSSL=true&requireSSL=true。

4. 禁用 SSL 连接：
   - 在连接设置的“高级”选项卡中，将 useSSL 的值更改为 FALSE。
     ![useSSL false](/uploads/datagrip-driver-error/usessl-false.png)

### 2. [08S01] Communications link failure

当客户端因网络连接问题无法访问 Amazon RDS 实例时，会发生此错误。

解决方法：
1. 检查 RDS 安全组设置：
   - 确认尝试连接的客户端 IP 地址是否在 Amazon RDS 的安全组中被允许。<br/>
     例如：在安全组中开放 3306 端口，并添加客户端的公共 IP 地址。

2. 检查 VPC 子网：
   - 如果 Amazon RDS 不允许公共访问，则只能从同一 VPC 内进行连接。<br/>
     确认 Amazon RDS 实例使用了正确的子网和路由设置。

3. 检查 DNS 和主机：
   - 确认连接 URL 中使用的 RDS 主机名是否正确。<br/>
     例如：<span style="word-wrap: break-word;">jdbc:mysql://your-instance-name.region.rds.amazonaws.com:3306.</span>

虽然有禁用安全连接或停用存储加密等简单方法，
但由于不启用加密通常不被推荐，因此我不建议这样做。
另一种方法似乎是使用 **Amazon Aurora MySQL** 或 **MariaDB** 驱动程序。
但是，为了稳定运行，建议使用正确的驱动程序。

### 连接成功

<div style="display:flex;flex-direction:row;justify-content:center;">
   <img src="/uploads/datagrip-driver-error/dbms-connection.png" alt="DBMS connection">
</div>
<p style="text-align:center;color:gray;"><small>数据库连接成功</small></p>

### 参考资料

- [Amazon RDS](https://aws.amazon.com/rds/ "Amazon RDS"){:target="_blank"} - [MySQL Community 5.7.38](https://dev.mysql.com/doc/refman/5.7/en/ "MySQL 5.7"){:target="_blank"}
- DataGrip Log : [https://intellij-support.jetbrains.com/hc/en-us/community/posts/10252570443282-Datagrip-cannot-access-containerized-database](https://stackoverflow.com/questions/22544754/failed-to-build-gem-native-extension-installing-compass "Datagrip-cannot-access-containerized-database"){:target="_blank"}
- DataGrip DB Connection Error : [https://youtrack.jetbrains.com/issue/DBE-13313/Cant-connect-to-remote-MySQL-since-last-version-of-IntelliJ#focus=Comments-27-4921748.0-0](https://youtrack.jetbrains.com/issue/DBE-13313/Cant-connect-to-remote-MySQL-since-last-version-of-IntelliJ#focus=Comments-27-4921748.0-0 "DataGrip DB Connection Error"){:target="_blank"}