---
layout: post
title: 'A Comprehensive Guide to PostgreSQL Streaming Replication: Building High Availability
  (HA) and Read Scaling for Production Environments'
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
description: Discover a practical guide to achieving database high availability (HA)
  and load balancing with read replicas using PostgreSQL streaming replication. This
  guide covers postgresql.conf and pg_hba.conf settings, failover strategies, and
  monitoring best practices for production environments.
image: /uploads/postgresql-streaming-replication-high-availability-guide/thumbnail.webp
lang: en
translation_key: postgresql-streaming-replication-high-availability-guide
permalink: /en/posts/postgresql-streaming-replication-high-availability-guide/
post_type: deep-dive
---
At the heart of every production service lies a database. However, an architecture that relies on a single database instance becomes a critical Single Point of Failure, where an unexpected hardware failure, network issue, or maintenance task can bring down the entire service. To address these risks and maximize service reliability, ensuring **database high availability (HA)** is not an option—it's a necessity.

PostgreSQL offers a powerful and reliable **Streaming Replication** feature to meet these demands. This feature allows you to replicate data from a primary server to one or more standby servers in near real-time. This minimizes service interruptions by enabling a quick switch to a standby server if the primary fails. Simultaneously, it allows for **Read Scaling** by distributing read queries to standby servers, improving overall database performance. This post provides an in-depth guide on how to build a production-level PostgreSQL streaming replication setup that can be applied directly in a real-world environment.

<!--more-->
![A Comprehensive Guide to PostgreSQL Streaming Replication: Building High Availability (HA) and Read Scaling for Production Environments](/uploads/postgresql-streaming-replication-high-availability-guide/thumbnail.webp "A Comprehensive Guide to PostgreSQL Streaming Replication: Building High Availability (HA) and Read Scaling for Production Environments")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 1. Background and Problem Definition: Why is Streaming Replication Necessary?

Modern web applications aim for 24/7 uninterrupted operation. If only one database server exists, it faces several critical problems:

- **Single Point of Failure (SPOF):** If the sole database server fails, the entire service goes down. The longer the Recovery Time Objective (RTO), the more business losses grow exponentially.
- **Service Downtime During Maintenance:** Even planned maintenance tasks like database version upgrades or system patches inevitably cause service interruptions.
- **Read Performance Limitations:** As user numbers grow and read requests surge, a single server can't handle the load, leading to performance degradation. Complex analytical queries can especially interfere with write operations.

**PostgreSQL Streaming Replication** is a core solution to these problems. It continuously sends changes from the primary server (WAL, Write-Ahead Log) over the network to a standby server, maintaining a nearly identical data replica. This allows you to kill two birds with one stone: achieving **high availability** and **load balancing**.

## 2. Core Architecture and Principles

Streaming replication consists of a primary server and one or more standby servers (replicas). Here's how it works:

1.  **WAL (Write-Ahead Logging):** Before applying any data modifications (INSERT, UPDATE, DELETE, etc.) to data files, PostgreSQL first writes them to log files called WAL records. This is a core mechanism that ensures the database's Atomicity and Durability.
2.  **WAL Transmission:** The primary server's `WAL Sender` process streams the generated WAL records over the network to the standby server's `WAL Receiver` process.
3.  **WAL Application:** The standby server replays the received WAL records to update its data to a state consistent with the primary server.

In this process, replication can be either **Synchronous** or **Asynchronous**.

| Replication Method | Characteristics | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Asynchronous Replication (Default)** | The primary server commits a transaction without waiting for a response from the standby server after sending the WAL record. | Has almost no impact on write performance. | In case of primary server failure, some data that has not yet been sent may be lost. (RPO > 0) |
| **Synchronous Replication** | The primary server commits a transaction only after confirming that the WAL record has been written on the standby server. | No data loss occurs. (RPO = 0) | Write performance (latency) can be degraded as it must wait for the standby server's response. |

In a production environment, you should choose the appropriate method based on your service's characteristics and data consistency requirements. In most cases, **asynchronous replication** is used by default for performance, with synchronous replication considered only for extremely critical data.

## 3. Practical Application: A Deep Dive into Building Streaming Replication

Let's now go through the step-by-step process of building a PostgreSQL streaming replication setup in a real production environment. This guide will configure one primary server and one standby server.

- **Primary Server:** `192.168.0.10`
- **Standby Server:** `192.168.0.20`

### 3.1. Primary Server Configuration

First, we need to create a dedicated user for replication and modify the `postgresql.conf` and `pg_hba.conf` files.

**1. Create a Replication User**

```sql
-- Connect via psql and execute
CREATE USER replicator REPLICATION LOGIN PASSWORD '<YOUR_REPLICATION_PASSWORD>';
```
[🚨 Security Note] In the command above, be sure to replace `<YOUR_REPLICATION_PASSWORD>` with a secure, strong password.

**2. Modify `postgresql.conf` Settings**

The `postgresql.conf` file controls the main behavior of the PostgreSQL instance. Modify or add the following settings for replication.

```ini
# /var/lib/pgsql/14/data/postgresql.conf or the path appropriate for your environment

# 1. Listen Addresses
# Allow connections from all IP addresses or specify a particular one.
listen_addresses = '*'

# 2. WAL (Write-Ahead Log) Settings
# Must be set to 'replica' or 'logical' for streaming replication.
wal_level = replica

# 3. WAL Sender Process Settings
# Maximum number of standby servers that can connect simultaneously. Set to at least 1.
max_wal_senders = 5

# 4. WAL Archiving (Optional but recommended)
# Stores WAL files in a separate location for Point-in-Time Recovery (PITR).
# archive_mode = on
# archive_command = 'cp %p /path/to/archive/%f'
```

**3. Modify `pg_hba.conf` Settings**

The `pg_hba.conf` file controls client authentication. You need to add a rule to allow the standby server to connect to the primary for replication.

```ini
# /var/lib/pgsql/14/data/pg_hba.conf or the path appropriate for your environment
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Add the following line at the end.
# Allows the 'replicator' user from the standby server (192.168.0.20) to make a replication connection.
host    replication     replicator      192.168.0.20/32         scram-sha-256
```
> **Note:** For PostgreSQL 13 and later, `scram-sha-256` is recommended over `md5`. If you are using an older version, you may need to set it to `md5`.

**4. Apply the Configuration**

Once all settings are configured, restart the PostgreSQL service to apply the changes.

```bash
sudo systemctl restart postgresql-14
```

### 3.2. Standby Server Configuration

Now it's time to build the standby server based on the primary server's data.

**1. Replicate Primary Server Data (`pg_basebackup`)**

Before proceeding on the standby server, ensure the PostgreSQL service is stopped.

```bash
sudo systemctl stop postgresql-14
```

If an existing data directory exists, back it up and then remove it. Use the `pg_basebackup` utility to replicate the entire data from the primary server.

```bash
# Back up and remove the existing data directory
sudo mv /var/lib/pgsql/14/data /var/lib/pgsql/14/data_old

# Run pg_basebackup (as the postgres user)
sudo -u postgres pg_basebackup -h 192.168.0.10 -U replicator -p 5432 -D /var/lib/pgsql/14/data -Fp -Xs -P -R
```

Here are the key options for `pg_basebackup`:
- `-h`: Primary server IP address
- `-U`: Replication username
- `-D`: Directory where the data will be stored
- `-Fp`: Backup in plain format
- `-Xs`: Stream WAL files
- `-P`: Show progress
- `-R`: A very useful option that automatically creates the necessary replication settings in `standby.signal` and `postgresql.auto.conf`.

**2. Verify Auto-Generated Configuration**

Using the `-R` option automatically creates the following files in the data directory (`-D`):

- **`standby.signal`:** The presence of this empty file signals that the PostgreSQL instance should start in standby mode.
- **`postgresql.auto.conf`:** The `primary_conninfo` setting for connecting to the primary server is automatically written here.

```ini
# Example content of /var/lib/pgsql/14/data/postgresql.auto.conf
# DO NOT EDIT...
primary_conninfo = 'user=replicator password=<YOUR_REPLICATION_PASSWORD> host=192.168.0.10 port=5432 sslmode=prefer sslcompression=0 gssencmode=prefer krbsrvname=postgres target_session_attrs=any'
```

**3. Configure Standby Server's `postgresql.conf` (Optional)**

To use the standby server for read-only queries (as a Read Replica), you need to enable the `hot_standby` option.

```ini
# /var/lib/pgsql/14/data/postgresql.conf
hot_standby = on
```

Setting `hot_standby = on` allows the server to execute read-only queries even while it is in recovery mode.

**4. Start the Standby Server**

Now, start the PostgreSQL service on the standby server.

```bash
sudo systemctl start postgresql-14
```

If the service starts correctly, the standby server will connect to the primary, begin WAL streaming, and synchronize its data.

## 4. Performance Optimization and Best Practices

### 4.1. Monitoring Replication Status

It is crucial to periodically check if replication is functioning correctly.

**On the Primary Server:** You can query the `pg_stat_replication` view to check the connection status and replication lag of the standby server.

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
If values like `sent_lag` or `replay_lag` are consistently large, it could indicate network issues or an I/O bottleneck on the standby server.

**On the Standby Server:** You can check the log files or query the `pg_stat_wal_receiver` view to check the WAL reception status.

```sql
-- Execute on the standby server
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

### 4.2. Failover and Promotion

When the primary server fails, the standby server must be **promoted** to become the new primary.

**Manual Failover:**
The simplest method is to call the `pg_promote()` function or run the `pg_ctl promote` command on the standby server.

```bash
# Execute on the standby server (as the postgres user)
pg_ctl promote -D /var/lib/pgsql/14/data
```

Once promotion is complete, the `standby.signal` file is renamed to `promote.done`, and the standby server transitions to a primary server capable of both reads and writes. Later, when the old primary server is recovered, it must be reconfigured as a standby for the new primary.

**Automatic Failover:**
In a production environment, it is highly recommended to implement an automatic failover solution to minimize manual intervention. Open-source tools like [Patroni](https://patroni.readthedocs.io/ "Patroni official documentation"){:target="_blank"} and [repmgr](https://repmgr.org/ "repmgr official documentation"){:target="_blank"} are widely used. These tools continuously monitor the primary server's health, automatically promote a standby server upon failure detection, and automate the complex process of updating application connection information.

### 4.3. Configuring Synchronous Replication

If zero data loss is a critical requirement, you can configure synchronous replication.

**Modify `postgresql.conf` on the Primary Server:**

```ini
# Configure synchronous commit to at least one standby server
synchronous_commit = on
synchronous_standby_names = '1 (standby_1)' # '1' is the number of servers to apply synchronously, 'standby_1' is the application_name of the standby
```

**Modify `postgresql.auto.conf` on the Standby Server:**

You must specify the `application_name` in `primary_conninfo`.

```ini
primary_conninfo = '... application_name=standby_1'
```

With this configuration, the primary server will only respond to the client with a successful commit after confirming that the WAL has been safely written to the standby server named `standby_1`. It is essential to be aware that while this guarantees data consistency, it can increase write latency.

## 5. Conclusion

**PostgreSQL Streaming Replication** is a powerful and essential feature for ensuring the stability and scalability of production databases. By configuring a primary/standby setup based on this guide, you can build a **high-availability environment** that minimizes data loss and allows for rapid service recovery in the event of an unexpected failure. Furthermore, by distributing read queries to standby servers, you can **effectively manage database load** and improve the responsiveness of your entire system.

Don't stop at just setting up replication. Consider continuous **monitoring** using tools like `pg_stat_replication` and the adoption of **automatic failover solutions** like Patroni to build a more robust and reliable data infrastructure.

### References
- [PostgreSQL 14 Documentation: Chapter 27. High Availability, Load Balancing, and Replication](https://www.postgresql.org/docs/14/high-availability.html "PostgreSQL 14 official documentation"){:target="_blank"}
- [PostgreSQL 14 Documentation: pg_basebackup](https://www.postgresql.org/docs/14/app-pgbasebackup.html "pg_basebackup official documentation"){:target="_blank"}
- [PostgreSQL 14 Documentation: The pg_hba.conf File](https://www.postgresql.org/docs/14/auth-pg-hba-conf.html "pg_hba.conf official documentation"){:target="_blank"}
- [Patroni: A Template for PostgreSQL High Availability with ZooKeeper, etcd or Consul](https://patroni.readthedocs.io/ "Patroni official documentation"){:target="_blank"}