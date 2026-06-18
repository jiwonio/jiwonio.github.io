---
layout: post
title: 'PostgreSQL 스트리밍 복제 완벽 가이드: 프로덕션 환경을 위한 고가용성(HA) 및 읽기 전용 확장 구축'
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
description: PostgreSQL 스트리밍 복제를 사용하여 데이터베이스 고가용성(HA)을 달성하고 읽기 전용 복제(Read Replica)로
  부하를 분산하는 실전 가이드를 확인하세요. 프로덕션 환경을 위한 postgresql.conf, pg_hba.conf 설정, 장애 조치(Failover)
  전략 및 모니터링 Best Practice를 다룹니다.
image: /uploads/postgresql-streaming-replication-high-availability-guide/thumbnail.webp
---
모든 프로덕션 서비스의 심장에는 데이터베이스가 있습니다. 하지만 단일 데이터베이스 인스턴스에만 의존하는 아키텍처는 예기치 않은 하드웨어 장애, 네트워크 문제, 또는 유지보수 작업으로 인해 전체 서비스가 중단될 수 있는 치명적인 단일 장애점(Single Point of Failure)이 됩니다. 이러한 위험을 해결하고 서비스의 안정성을 극대화하기 위해 **데이터베이스 고가용성(High Availability, HA)** 확보는 선택이 아닌 필수입니다.

PostgreSQL은 이러한 요구사항을 충족시키기 위해 강력하고 신뢰성 높은 **스트리밍 복제(Streaming Replication)** 기능을 제공합니다. 이 기능을 활용하면 주(Primary) 서버의 데이터를 하나 이상의 대기(Standby) 서버로 실시간에 가깝게 복제할 수 있습니다. 이를 통해 주 서버에 장애가 발생하더라도 신속하게 대기 서버로 전환하여 서비스 중단을 최소화하고, 동시에 읽기 쿼리를 대기 서버로 분산시켜 전체적인 데이터베이스 성능을 향상시키는 **읽기 전용 확장(Read Scaling)**까지 구현할 수 있습니다. 본 포스트에서는 실무 현장에서 바로 적용할 수 있는 프로덕션 레벨의 PostgreSQL 스트리밍 복제 구축 방법을 심도 있게 다룹니다.

<!--more-->
![PostgreSQL 스트리밍 복제 완벽 가이드: 프로덕션 환경을 위한 고가용성(HA) 및 읽기 전용 확장 구축](/uploads/postgresql-streaming-replication-high-availability-guide/thumbnail.webp "PostgreSQL 스트리밍 복제 완벽 가이드: 프로덕션 환경을 위한 고가용성(HA) 및 읽기 전용 확장 구축")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 1. 도입 배경 및 문제 정의: 왜 스트리밍 복제가 필요한가?

현대 웹 애플리케이션은 24/7 무중단 운영을 목표로 합니다. 데이터베이스 서버가 하나만 존재할 경우, 다음과 같은 심각한 문제에 직면하게 됩니다.

- **단일 장애점 (SPOF):** 유일한 데이터베이스 서버에 장애가 발생하면 전체 서비스가 마비됩니다. 복구 시간(RTO)이 길어질수록 비즈니스 손실은 기하급수적으로 증가합니다.
- **유지보수 시 서비스 중단:** 데이터베이스 버전 업그레이드나 시스템 패치와 같은 계획된 유지보수 작업 중에도 서비스 중단이 불가피합니다.
- **읽기 성능 한계:** 사용자가 증가하고 읽기 요청이 폭주하면 단일 서버는 부하를 감당하지 못하고 성능 저하를 일으킵니다. 특히 복잡한 분석 쿼리는 쓰기 작업을 방해할 수도 있습니다.

**PostgreSQL 스트리밍 복제**는 이러한 문제들을 해결하기 위한 핵심적인 솔루션입니다. 주 서버의 변경 사항(WAL, Write-Ahead Log)을 네트워크를 통해 대기 서버로 지속적으로 전송하여 거의 동일한 상태의 데이터 복제본을 유지합니다. 이를 통해 **고가용성**과 **부하 분산**이라는 두 마리 토끼를 모두 잡을 수 있습니다.

## 2. 핵심 아키텍처 및 원리

스트리밍 복제는 주 서버(Primary)와 하나 이상의 대기 서버(Standby/Replica)로 구성됩니다. 작동 원리는 다음과 같습니다.

1.  **WAL (Write-Ahead Logging):** PostgreSQL은 모든 데이터 변경 사항(INSERT, UPDATE, DELETE 등)을 데이터 파일에 적용하기 전에 먼저 WAL 레코드라는 로그 파일에 기록합니다. 이는 데이터베이스의 원자성(Atomicity)과 내구성(Durability)을 보장하는 핵심 메커니즘입니다.
2.  **WAL 전송:** 주 서버의 `WAL Sender` 프로세스는 생성된 WAL 레코드를 네트워크를 통해 대기 서버의 `WAL Receiver` 프로세스로 스트리밍합니다.
3.  **WAL 적용:** 대기 서버는 수신한 WAL 레코드를 재현(replay)하여 자신의 데이터를 주 서버와 일관된 상태로 갱신합니다.

이 과정에서 복제 방식은 **동기(Synchronous)**와 **비동기(Asynchronous)**로 나뉩니다.

| 복제 방식 | 특징 | 장점 | 단점 |
| :--- | :--- | :--- | :--- |
| **비동기 복제 (기본값)** | 주 서버는 WAL 레코드를 전송한 후 대기 서버의 응답을 기다리지 않고 트랜잭션을 커밋합니다. | 쓰기 성능에 미치는 영향이 거의 없습니다. | 주 서버 장애 시, 아직 전송되지 못한 일부 데이터가 유실될 수 있습니다. (RPO > 0) |
| **동기 복제** | 주 서버는 WAL 레코드가 대기 서버에 기록되었음을 확인한 후에야 트랜잭션을 커밋합니다. | 데이터 유실이 발생하지 않습니다. (RPO = 0) | 대기 서버의 응답을 기다려야 하므로 쓰기 성능(latency)이 저하될 수 있습니다. |

프로덕션 환경에서는 서비스의 특성과 데이터 정합성 요구 수준에 따라 적절한 방식을 선택해야 합니다. 대부분의 경우, 성능을 위해 **비동기 복제**를 기본으로 사용하고, 극도로 중요한 데이터에 한해 동기 복제를 고려합니다.

## 3. 실무 적용: 스트리밍 복제 구축 딥다이브

이제 실제 프로덕션 환경에서 PostgreSQL 스트리밍 복제를 구축하는 과정을 단계별로 살펴보겠습니다. 이 가이드에서는 1개의 주 서버(Primary)와 1개의 대기 서버(Standby)를 구성합니다.

- **주 서버 (Primary):** `192.168.0.10`
- **대기 서버 (Standby):** `192.168.0.20`

### 3.1. 주 서버(Primary) 설정

먼저 복제를 위한 전용 사용자를 생성하고, `postgresql.conf`와 `pg_hba.conf` 파일을 수정해야 합니다.

**1. 복제용 사용자 생성**

```sql
-- psql 로 접속하여 실행
CREATE USER replicator REPLICATION LOGIN PASSWORD '<YOUR_REPLICATION_PASSWORD>';
```
[🚨 보안 주의] 위 명령어에서 `<YOUR_REPLICATION_PASSWORD>`는 반드시 안전하고 강력한 비밀번호로 교체해야 합니다.

**2. `postgresql.conf` 설정 수정**

`postgresql.conf` 파일은 PostgreSQL 인스턴스의 주요 동작을 제어합니다. 복제를 위해 다음 설정들을 수정하거나 추가합니다.

```ini
# /var/lib/pgsql/14/data/postgresql.conf 또는 환경에 맞는 경로

# 1. Listen Addresses
# 모든 IP 주소에서 연결을 허용하거나 특정 IP를 지정합니다.
listen_addresses = '*'

# 2. WAL (Write-Ahead Log) 설정
# 스트리밍 복제를 위해 'replica' 또는 'logical' 로 설정해야 합니다.
wal_level = replica

# 3. WAL Sender 프로세스 설정
# 동시 접속할 수 있는 대기 서버의 최대 수. 최소 1개 이상으로 설정합니다.
max_wal_senders = 5

# 4. WAL 아카이빙 (선택 사항이지만 권장)
# PITR(Point-in-Time Recovery)을 위해 WAL 파일을 별도 공간에 보관합니다.
# archive_mode = on
# archive_command = 'cp %p /path/to/archive/%f'
```

**3. `pg_hba.conf` 설정 수정**

`pg_hba.conf` 파일은 클라이언트 인증을 제어합니다. 대기 서버가 주 서버에 접속하여 복제할 수 있도록 허용하는 규칙을 추가해야 합니다.

```ini
# /var/lib/pgsql/14/data/pg_hba.conf 또는 환경에 맞는 경로
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# 맨 아래에 다음 라인을 추가합니다.
# 대기 서버(192.168.0.20)에서 replicator 사용자가 복제 연결을 할 수 있도록 허용합니다.
host    replication     replicator      192.168.0.20/32         scram-sha-256
```
> **참고:** PostgreSQL 13 이상에서는 `md5` 대신 `scram-sha-256` 사용이 권장됩니다. 이전 버전을 사용한다면 `md5`로 설정해야 할 수 있습니다.

**4. 설정 적용**

모든 설정이 완료되면 PostgreSQL 서비스를 재시작하여 변경 사항을 적용합니다.

```bash
sudo systemctl restart postgresql-14
```

### 3.2. 대기 서버(Standby) 설정

이제 주 서버의 데이터를 기반으로 대기 서버를 구축할 차례입니다.

**1. 주 서버 데이터 복제 (`pg_basebackup`)**

대기 서버에서 작업을 진행하기 전에, PostgreSQL 서비스가 중지된 상태인지 확인해야 합니다.

```bash
sudo systemctl stop postgresql-14
```

기존 데이터 디렉토리가 있다면 백업 후 삭제하고, `pg_basebackup` 유틸리티를 사용하여 주 서버의 전체 데이터를 복제합니다.

```bash
# 기존 데이터 디렉토리 백업 및 삭제
sudo mv /var/lib/pgsql/14/data /var/lib/pgsql/14/data_old

# pg_basebackup 실행 (postgres 사용자로 실행)
sudo -u postgres pg_basebackup -h 192.168.0.10 -U replicator -p 5432 -D /var/lib/pgsql/14/data -Fp -Xs -P -R
```

`pg_basebackup`의 주요 옵션은 다음과 같습니다.
- `-h`: 주 서버 IP 주소
- `-U`: 복제용 사용자 이름
- `-D`: 데이터가 저장될 디렉토리
- `-Fp`: Plain 포맷으로 백업
- `-Xs`: 스트림 방식으로 WAL 파일 전송
- `-P`: 진행 상황 표시
- `-R`: 복제에 필요한 설정을 `standby.signal` 파일과 `postgresql.auto.conf`에 자동으로 생성해주는 매우 유용한 옵션입니다.

**2. 자동 생성된 설정 확인**

`-R` 옵션을 사용하면 데이터 디렉토리(`-D`) 내에 다음 파일들이 자동으로 생성됩니다.

- **`standby.signal`:** 이 파일의 존재는 해당 PostgreSQL 인스턴스가 대기(Standby) 모드로 시작해야 함을 알리는 신호입니다. 비어있는 파일입니다.
- **`postgresql.auto.conf`:** 주 서버에 연결하기 위한 `primary_conninfo` 설정이 자동으로 기록됩니다.

```ini
# /var/lib/pgsql/14/data/postgresql.auto.conf 파일 내용 예시
# DO NOT EDIT...
primary_conninfo = 'user=replicator password=<YOUR_REPLICATION_PASSWORD> host=192.168.0.10 port=5432 sslmode=prefer sslcompression=0 gssencmode=prefer krbsrvname=postgres target_session_attrs=any'
```

**3. 대기 서버 `postgresql.conf` 설정 (선택 사항)**

대기 서버를 읽기 전용 쿼리(Read Replica)로 활용하려면 `hot_standby` 옵션을 활성화해야 합니다.

```ini
# /var/lib/pgsql/14/data/postgresql.conf
hot_standby = on
```

`hot_standby = on` 으로 설정하면 서버가 복구를 진행하는 동안에도 읽기 전용 쿼리를 실행할 수 있습니다.

**4. 대기 서버 시작**

이제 대기 서버의 PostgreSQL 서비스를 시작합니다.

```bash
sudo systemctl start postgresql-14
```

서비스가 정상적으로 시작되면 대기 서버는 주 서버에 접속하여 WAL 스트리밍을 시작하고 데이터를 동기화합니다.

## 4. 성능 최적화 및 Best Practices

### 4.1. 복제 상태 모니터링

복제가 정상적으로 이루어지고 있는지 주기적으로 확인하는 것은 매우 중요합니다.

**주 서버에서 확인:** `pg_stat_replication` 뷰를 조회하여 대기 서버의 연결 상태와 복제 지연 상태를 확인할 수 있습니다.

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
`sent_lag`, `replay_lag` 등의 값이 지속적으로 크다면 네트워크 문제나 대기 서버의 I/O 병목을 의심해 볼 수 있습니다.

**대기 서버에서 확인:** 로그 파일을 확인하거나 `pg_stat_wal_receiver` 뷰를 통해 WAL 수신 상태를 확인할 수 있습니다.

```sql
-- 대기 서버에서 실행
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

### 4.2. 장애 조치(Failover)와 승격(Promotion)

주 서버에 장애가 발생했을 때, 대기 서버를 새로운 주 서버로 **승격(Promote)**시켜야 합니다.

**수동 장애 조치(Manual Failover):**
가장 간단한 방법은 대기 서버에서 `pg_promote()` 함수를 호출하거나 `pg_ctl promote` 명령을 실행하는 것입니다.

```bash
# 대기 서버에서 실행 (postgres 사용자)
pg_ctl promote -D /var/lib/pgsql/14/data
```

승격이 완료되면 `standby.signal` 파일은 `promote.done` 으로 이름이 변경되고, 대기 서버는 읽기/쓰기가 모두 가능한 주 서버로 전환됩니다. 이후 기존 주 서버가 복구되면, 이제는 새로운 주 서버의 대기 서버로 재구성해야 합니다.

**자동 장애 조치(Automatic Failover):**
프로덕션 환경에서는 수동 개입을 최소화하기 위해 자동 장애 조치 솔루션을 도입하는 것이 좋습니다. [Patroni](https://patroni.readthedocs.io/ "Patroni 공식 문서"){:target="_blank"}, [repmgr](https://repmgr.org/ "repmgr 공식 문서"){:target="_blank"} 과 같은 오픈소스 도구들이 널리 사용됩니다. 이러한 도구들은 주 서버의 상태를 지속적으로 모니터링하고, 장애 감지 시 자동으로 대기 서버를 승격시키고 애플리케이션의 연결 정보를 업데이트하는 복잡한 과정을 자동화해줍니다.

### 4.3. 동기 복제 설정

데이터 무손실이 매우 중요한 경우 동기 복제를 설정할 수 있습니다.

**주 서버 `postgresql.conf` 수정:**

```ini
# 최소 1개의 대기 서버에 동기적으로 커밋하도록 설정
synchronous_commit = on
synchronous_standby_names = '1 (standby_1)' # '1'은 동기 적용할 서버 수, 'standby_1'은 대기 서버의 application_name
```

**대기 서버 `postgresql.auto.conf` 수정:**

`primary_conninfo`에 `application_name`을 명시해야 합니다.

```ini
primary_conninfo = '... application_name=standby_1'
```

이렇게 설정하면 주 서버는 `standby_1` 이라는 이름을 가진 대기 서버에 WAL이 안전하게 기록된 것을 확인한 후에야 클라이언트에 커밋 완료를 응답합니다. 이는 데이터 정합성을 보장하지만 쓰기 지연 시간을 증가시킬 수 있음을 반드시 인지해야 합니다.

## 5. 결론

**PostgreSQL 스트리밍 복제**는 프로덕션 데이터베이스의 안정성과 확장성을 확보하기 위한 강력하고 필수적인 기능입니다. 본 가이드에서 다룬 내용을 바탕으로 주/대기 서버를 구성하면, 예기치 않은 장애 상황에서도 데이터 손실을 최소화하고 신속하게 서비스를 복구할 수 있는 **고가용성 환경**을 구축할 수 있습니다. 또한, 읽기 쿼리를 대기 서버로 분산하여 **데이터베이스 부하를 효과적으로 관리**하고 전체 시스템의 응답성을 향상시킬 수 있습니다.

단순히 복제를 설정하는 것에서 그치지 않고, `pg_stat_replication` 등을 활용한 지속적인 **모니터링**과 Patroni와 같은 **자동 장애 조치 솔루션** 도입을 함께 고려하여 더욱 견고하고 신뢰성 높은 데이터 인프라를 완성하시길 바랍니다.

### 참고문헌
- [PostgreSQL 14 Documentation: Chapter 27. High Availability, Load Balancing, and Replication](https://www.postgresql.org/docs/14/high-availability.html "PostgreSQL 14 공식 문서"){:target="_blank"}
- [PostgreSQL 14 Documentation: pg_basebackup](https://www.postgresql.org/docs/14/app-pgbasebackup.html "pg_basebackup 공식 문서"){:target="_blank"}
- [PostgreSQL 14 Documentation: The pg_hba.conf File](https://www.postgresql.org/docs/14/auth-pg-hba-conf.html "pg_hba.conf 공식 문서"){:target="_blank"}
- [Patroni: A Template for PostgreSQL High Availability with ZooKeeper, etcd or Consul](https://patroni.readthedocs.io/ "Patroni 공식 문서"){:target="_blank"}