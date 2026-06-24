---
layout: post
title: PostgreSQL 流复制终极指南：为生产环境构建高可用性 (HA) 与只读扩展
slug: postgresql-streaming-replication-high-availability-guide
date: 2026-05-11 10:07:00 +0900
categories:
- DevOps
- Backend
tags:
- PostgreSQL
- Database
- Replication
- High Availability
- HA
- DevOps
- Backend
description: 本实战指南将指导您如何使用 PostgreSQL 流复制来实现数据库高可用性 (HA)，并通过只读副本 (Read Replica) 分散负载。内容涵盖面向生产环境的
  postgresql.conf、pg_hba.conf 配置、故障转移 (Failover) 策略及监控最佳实践。
image: /uploads/postgresql-streaming-replication-high-availability-guide/thumbnail.webp
lang: zh
translation_key: postgresql-streaming-replication-high-availability-guide
permalink: /zh/posts/postgresql-streaming-replication-high-availability-guide/
post_type: deep-dive
---
数据库是所有生产服务的心脏。然而，一个仅依赖单一数据库实例的架构，会因意外的硬件故障、网络问题或维护工作而成为致命的单点故障（Single Point of Failure），导致整个服务中断。为了解决这些风险并最大化服务的稳定性，确保**数据库高可用性（High Availability, HA）**已不再是可选项，而是必需品。

为满足这一需求，PostgreSQL 提供了强大而可靠的**流复制（Streaming Replication）**功能。利用该功能，可以将主（Primary）服务器的数据近乎实时地复制到一个或多个备用（Standby）服务器。这样，即使主服务器发生故障，也能迅速切换到备用服务器，从而最大限度地减少服务中断。同时，还可以将读查询分散到备用服务器，实现**只读扩展（Read Scaling）**，提升整体数据库性能。本文将深入探讨如何在实际业务中构建生产级别的 PostgreSQL 流复制。

<!--more-->
![PostgreSQL 流复制终极指南：为生产环境构建高可用性 (HA) 与只读扩展](/uploads/postgresql-streaming-replication-high-availability-guide/thumbnail.webp "PostgreSQL 流复制终极指南：为生产环境构建高可用性 (HA) 与只读扩展")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 1. 背景与问题：为什么需要流复制？

现代 Web 应用程序的目标是 24/7 不间断运行。如果只有一个数据库服务器，将面临以下严重问题：

- **单点故障 (SPOF):** 唯一的数据库服务器发生故障将导致整个服务瘫痪。恢复时间（RTO）越长，业务损失就越大。
- **维护期间服务中断:** 在进行数据库版本升级或系统补丁等计划性维护工作时，服务中断也无法避免。
- **读取性能瓶颈:** 随着用户增多和读取请求的激增，单个服务器将无法承受负载，导致性能下降。特别是复杂的分析查询可能会干扰写入操作。

**PostgreSQL 流复制**是解决这些问题的核心方案。它将主服务器的变更（WAL, Write-Ahead Log）通过网络持续传输到备用服务器，从而维持一个几乎相同的数据副本。通过这种方式，可以同时实现**高可用性**和**负载均衡**这两个目标。

## 2. 核心架构与原理

流复制由一个主服务器（Primary）和一个或多个备用服务器（Standby/Replica）组成。其工作原理如下：

1.  **WAL (Write-Ahead Logging):** PostgreSQL 在将所有数据变更（INSERT, UPDATE, DELETE 等）应用到数据文件之前，会先将这些变更记录到一个名为 WAL 记录的日志文件中。这是保证数据库原子性（Atomicity）和持久性（Durability）的核心机制。
2.  **WAL 传输:** 主服务器的 `WAL Sender` 进程将生成的 WAL 记录通过网络流式传输到备用服务器的 `WAL Receiver` 进程。
3.  **WAL 应用:** 备用服务器重放（replay）接收到的 WAL 记录，更新自身数据，使其与主服务器保持一致。

在此过程中，复制方式分为**同步（Synchronous）**和**异步（Asynchronous）**两种。

| 复制方式 | 特点 | 优点 | 缺点 |
| :--- | :--- | :--- | :--- |
| **异步复制 (默认)** | 主服务器发送 WAL 记录后，不等待备用服务器的响应即提交事务。 | 对写入性能影响极小。 | 主服务器发生故障时，可能丢失部分尚未传输的数据。(RPO > 0) |
| **同步复制** | 主服务器在确认 WAL 记录已写入备用服务器后，才提交事务。 | 不会发生数据丢失。(RPO = 0) | 由于需要等待备用服务器的响应，写入性能（延迟）可能会下降。 |

在生产环境中，应根据服务的特性和数据一致性要求选择合适的复制方式。大多数情况下，为了性能考虑，会默认使用**异步复制**，仅在处理极其关键的数据时才考虑同步复制。

## 3. 实战：深入构建流复制

现在，我们分步来了解如何在真实的生产环境中构建 PostgreSQL 流复制。本指南将配置 1 台主服务器（Primary）和 1 台备用服务器（Standby）。

- **主服务器 (Primary):** `192.168.0.10`
- **备用服务器 (Standby):** `192.168.0.20`

### 3.1. 主服务器 (Primary) 配置

首先，需要为复制创建一个专用用户，并修改 `postgresql.conf` 和 `pg_hba.conf` 文件。

**1. 创建复制用户**

```sql
-- 使用 psql 连接后执行
CREATE USER replicator REPLICATION LOGIN PASSWORD '<YOUR_REPLICATION_PASSWORD>';
```
[🚨 安全提示] 在上述命令中，`<YOUR_REPLICATION_PASSWORD>` 必须替换为一个安全且强壮的密码。

**2. 修改 `postgresql.conf` 配置**

`postgresql.conf` 文件控制着 PostgreSQL 实例的主要行为。为实现复制，需要修改或添加以下配置。

```ini
# /var/lib/pgsql/14/data/postgresql.conf 或根据你的环境找到对应路径

# 1. Listen Addresses
# 允许来自所有 IP 地址的连接，或指定特定 IP。
listen_addresses = '*'

# 2. WAL (Write-Ahead Log) 设置
# 为了流复制，必须设置为 'replica' 或 'logical'。
wal_level = replica

# 3. WAL Sender 进程设置
# 可同时连接的备用服务器最大数量。至少设置为 1。
max_wal_senders = 5

# 4. WAL 归档 (可选，但推荐)
# 为实现 PITR (Point-in-Time Recovery)，将 WAL 文件备份到单独的位置。
# archive_mode = on
# archive_command = 'cp %p /path/to/archive/%f'
```

**3. 修改 `pg_hba.conf` 配置**

`pg_hba.conf` 文件用于控制客户端认证。需要添加规则，允许备用服务器连接到主服务器进行复制。

```ini
# /var/lib/pgsql/14/data/pg_hba.conf 或根据你的环境找到对应路径
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# 在文件末尾添加以下行。
# 允许来自备用服务器 (192.168.0.20) 的 replicator 用户进行复制连接。
host    replication     replicator      192.168.0.20/32         scram-sha-256
```
> **注意:** PostgreSQL 13 及更高版本推荐使用 `scram-sha-256` 而不是 `md5`。如果使用旧版本，可能需要设置为 `md5`。

**4. 应用配置**

完成所有配置后，重启 PostgreSQL 服务以使更改生效。

```bash
sudo systemctl restart postgresql-14
```

### 3.2. 备用服务器 (Standby) 配置

现在，我们基于主服务器的数据来构建备用服务器。

**1. 从主服务器复制数据 (`pg_basebackup`)**

在备用服务器上进行操作前，请确保 PostgreSQL 服务处于停止状态。

```bash
sudo systemctl stop postgresql-14
```

如果存在旧的数据目录，请先备份后删除，然后使用 `pg_basebackup` 工具从主服务器复制全部数据。

```bash
# 备份并删除旧数据目录
sudo mv /var/lib/pgsql/14/data /var/lib/pgsql/14/data_old

# 执行 pg_basebackup (以 postgres 用户身份运行)
sudo -u postgres pg_basebackup -h 192.168.0.10 -U replicator -p 5432 -D /var/lib/pgsql/14/data -Fp -Xs -P -R
```

`pg_basebackup` 的主要选项如下：
- `-h`: 主服务器的 IP 地址
- `-U`: 复制用户的用户名
- `-D`: 数据存储的目标目录
- `-Fp`: 使用普通格式备份
- `-Xs`: 以流式传输 WAL 文件
- `-P`: 显示进度
- `-R`: 一个非常有用的选项，它会自动在 `standby.signal` 文件和 `postgresql.auto.conf` 中生成复制所需的配置。

**2. 检查自动生成的配置**

使用 `-R` 选项后，数据目录（`-D`）中会自动生成以下文件：

- **`standby.signal`:** 这个空文件的存在告诉 PostgreSQL 实例应该以备用（Standby）模式启动。
- **`postgresql.auto.conf`:** 用于连接主服务器的 `primary_conninfo` 设置会自动写入此文件。

```ini
# /var/lib/pgsql/14/data/postgresql.auto.conf 文件内容示例
# DO NOT EDIT...
primary_conninfo = 'user=replicator password=<YOUR_REPLICATION_PASSWORD> host=192.168.0.10 port=5432 sslmode=prefer sslcompression=0 gssencmode=prefer krbsrvname=postgres target_session_attrs=any'
```

**3. 备用服务器 `postgresql.conf` 配置 (可选)**

如果希望将备用服务器用作只读查询副本（Read Replica），需要启用 `hot_standby` 选项。

```ini
# /var/lib/pgsql/14/data/postgresql.conf
hot_standby = on
```

设置 `hot_standby = on` 后，服务器在恢复过程中也能执行只读查询。

**4. 启动备用服务器**

现在，启动备用服务器的 PostgreSQL 服务。

```bash
sudo systemctl start postgresql-14
```

服务正常启动后，备用服务器将连接到主服务器，开始流式传输 WAL 并同步数据。

## 4. 性能优化与最佳实践

### 4.1. 监控复制状态

定期检查复制是否正常运行至关重要。

**在主服务器上检查:** 查询 `pg_stat_replication` 视图可以查看备用服务器的连接状态和复制延迟。

```sql
SELECT
    client_addr,
    state,
    sync_state,
    pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) AS sent_lag,
    pg_wal_lsn_diff(sent_lsn, write_lsn) AS write_lag,
    pg_wal_lsn_diff(write_lsn, flush_lsn) AS flush_lag,
    pg_wal_lsn_diff(flush_lsn, replay_lsn) AS replay_lag
FROM
    pg_stat_replication;
```
如果 `sent_lag`、`replay_lag` 等值持续偏高，可能意味着存在网络问题或备用服务器的 I/O 瓶颈。

**在备用服务器上检查:** 可以查看日志文件，或通过查询 `pg_stat_wal_receiver` 视图来确认 WAL 接收状态。

```sql
-- 在备用服务器上执行
SELECT
    status,
    received_tli,
    last_msg_send_time,
    last_msg_receipt_time,
    latest_end_lsn,
    latest_end_time
FROM
    pg_stat_wal_receiver;
```

### 4.2. 故障转移 (Failover) 与提升 (Promotion)

当主服务器发生故障时，需要将备用服务器**提升（Promote）**为新的主服务器。

**手动故障转移 (Manual Failover):**
最简单的方法是在备用服务器上调用 `pg_promote()` 函数或执行 `pg_ctl promote` 命令。

```bash
# 在备用服务器上执行 (以 postgres 用户身份)
pg_ctl promote -D /var/lib/pgsql/14/data
```

提升完成后，`standby.signal` 文件将重命名为 `promote.done`，备用服务器转变为一个可读写的标准主服务器。之后，当原主服务器恢复后，需要将其重新配置为新主服务器的备用服务器。

**自动故障转移 (Automatic Failover):**
在生产环境中，为尽量减少手动干预，推荐引入自动故障转移解决方案。像 [Patroni](https://patroni.readthedocs.io/ "Patroni 官方文档"){:target="_blank"} 和 [repmgr](https://repmgr.org/ "repmgr 官方文档"){:target="_blank"} 这样的开源工具被广泛使用。这些工具能持续监控主服务器的状态，在检测到故障时自动提升备用服务器，并更新应用程序的连接信息，从而自动化整个复杂流程。

### 4.3. 配置同步复制

在要求数据零丢失的场景下，可以配置同步复制。

**修改主服务器 `postgresql.conf`:**

```ini
# 设置至少向 1 个备用服务器同步提交
synchronous_commit = on
synchronous_standby_names = '1 (standby_1)' # '1' 是同步应用的服务器数量, 'standby_1' 是备用服务器的 application_name
```

**修改备用服务器 `postgresql.auto.conf`:**

需要在 `primary_conninfo` 中明确指定 `application_name`。

```ini
primary_conninfo = '... application_name=standby_1'
```

这样配置后，主服务器只有在确认名为 `standby_1` 的备用服务器已安全写入 WAL 后，才会向客户端返回提交成功的响应。这保证了数据的强一致性，但必须注意，这会增加写入延迟。

## 5. 结论

**PostgreSQL 流复制**是确保生产数据库稳定性和可扩展性的强大且必要的功能。基于本指南的内容搭建主/备服务器，您便可以构建一个**高可用性环境**，在意外故障发生时最大限度地减少数据丢失并快速恢复服务。此外，通过将读查询分散到备用服务器，您可以**有效管理数据库负载**，提升整个系统的响应能力。

不要止步于简单地配置复制。建议您结合使用 `pg_stat_replication` 等工具进行持续**监控**，并考虑引入像 Patroni 这样的**自动故障转移解决方案**，以构建一个更加健壮和可靠的数据基础设施。

### 参考资料
- [PostgreSQL 14 Documentation: Chapter 27. High Availability, Load Balancing, and Replication](https://www.postgresql.org/docs/14/high-availability.html "PostgreSQL 14 官方文档"){:target="_blank"}
- [PostgreSQL 14 Documentation: pg_basebackup](https://www.postgresql.org/docs/14/app-pgbasebackup.html "pg_basebackup 官方文档"){:target="_blank"}
- [PostgreSQL 14 Documentation: The pg_hba.conf File](https://www.postgresql.org/docs/14/auth-pg-hba-conf.html "pg_hba.conf 官方文档"){:target="_blank"}
- [Patroni: A Template for PostgreSQL High Availability with ZooKeeper, etcd or Consul](https://patroni.readthedocs.io/ "Patroni 官方文档"){:target="_blank"}
---