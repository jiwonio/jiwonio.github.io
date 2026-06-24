---
layout: post
title: PostgreSQLストリーミングレプリケーション完全ガイド：本番環境向けの高可用性(HA)と読み取り専用スケーリングの構築
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
description: PostgreSQLストリーミングレプリケーションを用いてデータベースの高可用性(HA)を実現し、読み取り専用レプリカ(Read Replica)で負荷を分散する実践ガイド。本番環境向けのpostgresql.conf、pg_hba.confの設定、フェイルオーバー戦略、モニタリングのベストプラクティスを解説します。
image: /uploads/postgresql-streaming-replication-high-availability-guide/thumbnail.webp
lang: ja
translation_key: postgresql-streaming-replication-high-availability-guide
permalink: /ja/posts/postgresql-streaming-replication-high-availability-guide/
post_type: deep-dive
ai_generated: true
updated: 2026-05-11 10:07:00 +0900
---
すべての本番サービスの心臓部にはデータベースがあります。しかし、単一のデータベースインスタンスのみに依存するアーキテクチャは、予期せぬハードウェア障害、ネットワーク問題、またはメンテナンス作業によってサービス全体が停止する可能性のある、致命的な単一障害点(Single Point of Failure)となります。このようなリスクを解決し、サービスの安定性を最大化するために、**データベースの高可用性(High Availability, HA)** の確保は選択ではなく必須です。

PostgreSQLは、これらの要求を満たすために強力で信頼性の高い**ストリーミングレプリケーション(Streaming Replication)**機能を提供します。この機能を利用すると、プライマリサーバーのデータを1つ以上のスタンバイサーバーにリアルタイムに近い形で複製できます。これにより、プライマリサーバーに障害が発生しても迅速にスタンバイサーバーに切り替えることでサービスの中断を最小限に抑え、同時に読み取りクエリをスタンバイサーバーに分散させてデータベース全体のパフォーマンスを向上させる**読み取り専用スケーリング(Read Scaling)**まで実現できます。本稿では、実務現場ですぐに適用できる、本番レベルのPostgreSQLストリーミングレプリケーションの構築方法を深く掘り下げて解説します。

<!--more-->
![PostgreSQLストリーミングレプリケーション完全ガイド：本番環境向けの高可用性(HA)と読み取り専用スケーリングの構築](/uploads/postgresql-streaming-replication-high-availability-guide/thumbnail.webp "PostgreSQLストリーミングレプリケーション完全ガイド：本番環境向けの高可用性(HA)と読み取り専用スケーリングの構築")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 1. 背景と課題：なぜストリーミングレプリケーションが必要なのか？

現代のWebアプリケーションは、24時間365日の無停止運用を目指しています。データベースサーバーが1台しか存在しない場合、次のような深刻な問題に直面します。

- **単一障害点 (SPOF):** 唯一のデータベースサーバーに障害が発生すると、サービス全体が麻痺します。目標復旧時間(RTO)が長くなるほど、ビジネス上の損失は指数関数的に増加します。
- **メンテナンス時のサービス停止:** データベースのバージョンアップやシステムパッチ適用といった計画的なメンテナンス作業中にも、サービス停止が避けられません。
- **読み取り性能の限界:** ユーザーが増加し、読み取りリクエストが殺到すると、単一のサーバーでは負荷に耐えきれず、パフォーマンスの低下を引き起こします。特に、複雑な分析クエリは書き込み処理を妨げる可能性もあります。

**PostgreSQLストリーミングレプリケーション**は、これらの問題を解決するための中心的なソリューションです。プライマリサーバーの変更履歴(WAL, Write-Ahead Log)をネットワーク経由でスタンバイサーバーに継続的に転送し、ほぼ同一の状態のデータ複製を維持します。これにより、**高可用性**と**負荷分散**という二つの目標を同時に達成できるのです。

## 2. 主要アーキテクチャと原理

ストリーミングレプリケーションは、プライマリサーバー(Primary)と1つ以上のスタンバイサーバー(Standby/Replica)で構成されます。その動作原理は以下の通りです。

1.  **WAL (Write-Ahead Logging):** PostgreSQLは、すべてのデータ変更(INSERT, UPDATE, DELETEなど)をデータファイルに適用する前に、まずWALレコードというログファイルに記録します。これは、データベースの原子性(Atomicity)と永続性(Durability)を保証する重要なメカニズムです。
2.  **WAL転送:** プライマリサーバーの`WAL Sender`プロセスは、生成されたWALレコードをネットワーク経由でスタンバイサーバーの`WAL Receiver`プロセスにストリーミングします。
3.  **WAL適用:** スタンバイサーバーは、受信したWALレコードを再生(replay)し、自身のデータをプライマリサーバーと一貫性のある状態に更新します。

この過程で、レプリケーション方式は**同期(Synchronous)**と**非同期(Asynchronous)**に分かれます。

| レプリケーション方式 | 特徴 | メリット | デメリット |
| :--- | :--- | :--- | :--- |
| **非同期レプリケーション (デフォルト)** | プライマリサーバーはWALレコードを送信後、スタンバイサーバーの応答を待たずにトランザクションをコミットします。 | 書き込み性能への影響がほとんどありません。 | プライマリサーバー障害時、まだ転送されていない一部のデータが失われる可能性があります。(RPO > 0) |
| **同期レプリケーション** | プライマリサーバーはWALレコードがスタンバイサーバーに書き込まれたことを確認した後にトランザクションをコミットします。 | データの損失が発生しません。(RPO = 0) | スタンバイサーバーの応答を待つ必要があるため、書き込み性能(レイテンシ)が低下する可能性があります。 |

本番環境では、サービスの特性とデータ整合性の要求レベルに応じて適切な方式を選択する必要があります。多くの場合、パフォーマンスを重視して**非同期レプリケーション**を基本とし、極めて重要なデータに限り同期レプリケーションを検討します。

## 3. 実践：ストリーミングレプリケーション構築の詳細解説

それでは、実際の本番環境でPostgreSQLストリーミングレプリケーションを構築するプロセスを段階的に見ていきましょう。このガイドでは、1台のプライマリサーバーと1台のスタンバイサーバーを構成します。

- **プライマリサーバー (Primary):** `192.168.0.10`
- **スタンバイサーバー (Standby):** `192.168.0.20`

### 3.1. プライマリサーバーの設定

まず、レプリケーション専用のユーザーを作成し、`postgresql.conf`と`pg_hba.conf`ファイルを修正する必要があります。

**1. レプリケーション用ユーザーの作成**

```sql
-- psql に接続して実行
CREATE USER replicator REPLICATION LOGIN PASSWORD '<YOUR_REPLICATION_PASSWORD>';
```
[🚨 セキュリティ注意] 上記コマンドの`<YOUR_REPLICATION_PASSWORD>`は、必ず安全で強力なパスワードに置き換えてください。

**2. `postgresql.conf` の設定変更**

`postgresql.conf`ファイルは、PostgreSQLインスタンスの主要な動作を制御します。レプリケーションのために、以下の設定を修正または追加します。

```ini
# /var/lib/pgsql/14/data/postgresql.conf または環境に応じたパス

# 1. Listen Addresses
# 全てのIPアドレスからの接続を許可するか、特定のIPを指定します。
listen_addresses = '*'

# 2. WAL (Write-Ahead Log) 設定
# ストリーミングレプリケーションのためには 'replica' または 'logical' に設定する必要があります。
wal_level = replica

# 3. WAL Sender プロセス設定
# 同時に接続できるスタンバイサーバーの最大数。最低でも1以上に設定します。
max_wal_senders = 5

# 4. WAL アーカイブ (任意だが推奨)
# PITR(Point-in-Time Recovery)のためにWALファイルを別の場所に保管します。
# archive_mode = on
# archive_command = 'cp %p /path/to/archive/%f'
```

**3. `pg_hba.conf` の設定変更**

`pg_hba.conf`ファイルは、クライアント認証を制御します。スタンバイサーバーがプライマリサーバーに接続してレプリケーションできるように、許可ルールを追加する必要があります。

```ini
# /var/lib/pgsql/14/data/pg_hba.conf または環境に応じたパス
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# 末尾に以下の行を追加します。
# スタンバイサーバー(192.168.0.20)からreplicatorユーザーがレプリケーション接続できるように許可します。
host    replication     replicator      192.168.0.20/32         scram-sha-256
```
> **注:** PostgreSQL 13以降では、`md5`の代わりに`scram-sha-256`の使用が推奨されます。古いバージョンを使用している場合は`md5`に設定する必要があるかもしれません。

**4. 設定の適用**

すべての設定が完了したら、PostgreSQLサービスを再起動して変更を適用します。

```bash
sudo systemctl restart postgresql-14
```

### 3.2. スタンバイサーバーの設定

次に、プライマリサーバーのデータを基にスタンバイサーバーを構築します。

**1. プライマリサーバーデータの複製 (`pg_basebackup`)**

スタンバイサーバーで作業を進める前に、PostgreSQLサービスが停止していることを確認してください。

```bash
sudo systemctl stop postgresql-14
```

既存のデータディレクトリがあればバックアップ後に削除し、`pg_basebackup`ユーティリティを使用してプライマリサーバーの全データを複製します。

```bash
# 既存のデータディレクトリをバックアップして削除
sudo mv /var/lib/pgsql/14/data /var/lib/pgsql/14/data_old

# pg_basebackup の実行 (postgresユーザーで実行)
sudo -u postgres pg_basebackup -h 192.168.0.10 -U replicator -p 5432 -D /var/lib/pgsql/14/data -Fp -Xs -P -R
```

`pg_basebackup`の主なオプションは以下の通りです。
- `-h`: プライマリサーバーのIPアドレス
- `-U`: レプリケーション用ユーザー名
- `-D`: データが保存されるディレクトリ
- `-Fp`: Plainフォーマットでバックアップ
- `-Xs`: ストリーム方式でWALファイルを転送
- `-P`: 進捗状況を表示
- `-R`: レプリケーションに必要な設定を`standby.signal`ファイルと`postgresql.auto.conf`に自動生成してくれる非常に便利なオプションです。

**2. 自動生成された設定の確認**

`-R`オプションを使用すると、データディレクトリ(`-D`)内に以下のファイルが自動的に生成されます。

- **`standby.signal`:** このファイルの存在は、そのPostgreSQLインスタンスがスタンバイモードで起動すべきであることを示すシグナルです。空のファイルです。
- **`postgresql.auto.conf`:** プライマリサーバーに接続するための`primary_conninfo`設定が自動的に記録されます。

```ini
# /var/lib/pgsql/14/data/postgresql.auto.conf の内容例
# DO NOT EDIT...
primary_conninfo = 'user=replicator password=<YOUR_REPLICATION_PASSWORD> host=192.168.0.10 port=5432 sslmode=prefer sslcompression=0 gssencmode=prefer krbsrvname=postgres target_session_attrs=any'
```

**3. スタンバイサーバーの `postgresql.conf` 設定 (任意)**

スタンバイサーバーを読み取り専用クエリ(Read Replica)として活用するには、`hot_standby`オプションを有効にする必要があります。

```ini
# /var/lib/pgsql/14/data/postgresql.conf
hot_standby = on
```

`hot_standby = on` に設定すると、サーバーがリカバリ処理中であっても読み取り専用クエリを実行できます。

**4. スタンバイサーバーの起動**

スタンバイサーバーのPostgreSQLサービスを起動します。

```bash
sudo systemctl start postgresql-14
```

サービスが正常に起動すると、スタンバイサーバーはプライマリサーバーに接続し、WALストリーミングを開始してデータを同期します。

## 4. パフォーマンス最適化とベストプラクティス

### 4.1. レプリケーション状態のモニタリング

レプリケーションが正常に行われているかを定期的に確認することは非常に重要です。

**プライマリサーバーでの確認:** `pg_stat_replication`ビューを照会し、スタンバイサーバーの接続状態とレプリケーションの遅延状況を確認できます。

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
`sent_lag`や`replay_lag`などの値が継続的に大きい場合、ネットワークの問題やスタンバイサーバーのI/Oボトルネックが疑われます。

**スタンバイサーバーでの確認:** ログファイルを確認するか、`pg_stat_wal_receiver`ビューを通じてWALの受信状態を確認できます。

```sql
-- スタンバイサーバーで実行
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

### 4.2. フェイルオーバーと昇格(Promotion)

プライマリサーバーに障害が発生した場合、スタンバイサーバーを新しいプライマリサーバーとして**昇格(Promote)**させる必要があります。

**手動フェイルオーバー(Manual Failover):**
最も簡単な方法は、スタンバイサーバーで`pg_promote()`関数を呼び出すか、`pg_ctl promote`コマンドを実行することです。

```bash
# スタンバイサーバーで実行 (postgresユーザー)
pg_ctl promote -D /var/lib/pgsql/14/data
```

昇格が完了すると、`standby.signal`ファイルは`promote.done`に名前が変更され、スタンバイサーバーは読み書き両方が可能なプライマリサーバーに切り替わります。その後、元のプライマリサーバーが復旧した際には、新しいプライマリサーバーのスタンバイサーバーとして再構成する必要があります。

**自動フェイルオーバー(Automatic Failover):**
本番環境では、手動での介入を最小限にするため、自動フェイルオーバーソリューションを導入することが推奨されます。[Patroni](https://patroni.readthedocs.io/ "Patroni公式ドキュメント"){:target="_blank"}や[repmgr](https://repmgr.org/ "repmgr公式ドキュメント"){:target="_blank"}のようなオープンソースツールが広く利用されています。これらのツールは、プライマリサーバーの状態を継続的に監視し、障害を検知すると自動的にスタンバイサーバーを昇格させ、アプリケーションの接続情報を更新する、といった複雑なプロセスを自動化します。

### 4.3. 同期レプリケーションの設定

データの損失が絶対に許されない場合には、同期レプリケーションを設定することができます。

**プライマリサーバーの `postgresql.conf` を修正:**

```ini
# 最低1台のスタンバイサーバーに同期的にコミットするよう設定
synchronous_commit = on
synchronous_standby_names = '1 (standby_1)' # '1'は同期適用するサーバー数、'standby_1'はスタンバイサーバーのapplication_name
```

**スタンバイサーバーの `postgresql.auto.conf` を修正:**

`primary_conninfo`に`application_name`を明記する必要があります。

```ini
primary_conninfo = '... application_name=standby_1'
```

このように設定すると、プライマリサーバーは`standby_1`という名前のスタンバイサーバーにWALが安全に書き込まれたことを確認した後にのみ、クライアントにコミット完了を応答します。これはデータ整合性を保証しますが、書き込みのレイテンシを増加させる可能性があることを必ず認識しておく必要があります。

## 5. 結論

**PostgreSQLストリーミングレプリケーション**は、本番データベースの安定性と拡張性を確保するための強力かつ必須の機能です。本ガイドで解説した内容を基にプライマリ/スタンバイサーバーを構成すれば、予期せぬ障害時にもデータ損失を最小限に抑え、迅速にサービスを復旧できる**高可用性環境**を構築できます。さらに、読み取りクエリをスタンバイサーバーに分散させることで、**データベースの負荷を効果的に管理**し、システム全体の応答性を向上させることが可能です。

単にレプリケーションを設定するだけでなく、`pg_stat_replication`などを活用した継続的な**モニタリング**や、Patroniのような**自動フェイルオーバーソリューション**の導入も併せて検討し、より堅牢で信頼性の高いデータインフラを完成させてください。

### 参考資料
- [PostgreSQL 14 Documentation: Chapter 27. High Availability, Load Balancing, and Replication](https://www.postgresql.org/docs/14/high-availability.html "PostgreSQL 14公式ドキュメント"){:target="_blank"}
- [PostgreSQL 14 Documentation: pg_basebackup](https://www.postgresql.org/docs/14/app-pgbasebackup.html "pg_basebackup公式ドキュメント"){:target="_blank"}
- [PostgreSQL 14 Documentation: The pg_hba.conf File](https://www.postgresql.org/docs/14/auth-pg-hba-conf.html "pg_hba.conf公式ドキュメント"){:target="_blank"}
- [Patroni: A Template for PostgreSQL High Availability with ZooKeeper, etcd or Consul](https://patroni.readthedocs.io/ "Patroni公式ドキュメント"){:target="_blank"}
---