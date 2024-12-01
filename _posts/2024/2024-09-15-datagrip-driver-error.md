---
layout: post
title: 'Troubleshooting Driver Errors When Connecting DataGrip to Amazon RDS'
meta: 'Learn how to resolve driver errors when connecting Amazon RDS to JetBrains DataGrip. This guide covers common issues and practical solutions for seamless database management.'
tags:
  - mysql
---

JetBrains offers **DataGrip**, a cross-platform tool for working with both relational and NoSQL databases.
This tool supports a wide range of databases, including MySQL, Oracle Database, PostgreSQL, SQLite, MongoDB, and Redis.
It also provides options to easily connect to cloud-based databases like Amazon Redshift.
Recently, an **AI Assistant** plugin has been added, making it even more convenient and efficient to write queries.
This feature helps developers enhance their productivity when working with data.
In this article, we will discuss **driver errors** that may occur when connecting to **Amazon RDS** using JetBrains DataGrip and explore solutions to resolve them.
This translation was provided with the assistance of **ChatGPT**.

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">제목과 첫 문단은 영어가 멋있어요.</small>

<img src="/uploads/datagrip-driver-error/cloud-database.jpg" alt="Cloud Databases" />

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/avnsuresh-19928520" title="Content copyright holder" target="_blank">Suresh anchan</a></small>
</p>

-----

데이터베이스 연결은 애플리케이션 개발 및 운영에서 매우 중요한 단계 중 하나입니다.
특히, **클라우드 환경**에서 데이터베이스를 사용한다면 연결 설정 과정에서의 세부적인 사항과 발생할 수 있는 오류를 잘 이해하는 것이 필수적입니다.
**Amazon RDS**는 클라우드 환경에서 자주 사용되는 관리형 데이터베이스 서비스로, 안정성과 유연성 덕분에 많은 개발자와 기업이 선호하고 있습니다.
하지만 Amazon RDS를 **JetBrains DataGrip**과 같은 데이터베이스 관리 도구에 연결할 때, 간혹 예상치 못한 문제가 발생할 수 있습니다.

이 글을 통해 비슷한 문제를 경험한 개발자들이 효과적으로 문제를 해결하고, 보다 안정적으로 Amazon RDS와 DataGrip을 연동할 수 있도록 돕고자 합니다.
데이터베이스 연결 과정에서 겪는 작은 오류 하나도 개발 프로세스에 큰 영향을 미칠 수 있기 때문에 문제의 근본 원인을 파악하고 적절한 해결책을 찾는 것이 중요합니다.
이제 본문에서 이러한 문제를 해결하기 위한 구체적인 단계들을 차례대로 알아보겠습니다.

## 드라이버 에러

```
DBMS: MySQL (no ver.)
Case sensitivity: plain=mixed, delimited=exact
NotAfter: Wed Jun 01 12:00:00 UTC 2022.
```

<div style="display:grid;">
   <img src="/uploads/datagrip-driver-error/failed.png" alt="MySQL connection failed" style="justify-self:center;">
</div>

<p style="text-align:center;color:gray;"><small>Amazon RDS 연결 시, 드라이버 에러</small></p>

MySQL 드라이버를 정상적으로 연결하지 못해서 지속적으로 연결 실패가 뜹니다.
자세한 에러 메시지를 확인하기 위해서는 DataGrip 로그 메시지를 확인해야 합니다.

## DataGrip 로그 확인

```shell
# DataGrip 로그 파일
vi ~/AppData/Local/JetBrains/DataGrip{{ VERSION }}/log/idea.log
```

<img src="/uploads/datagrip-driver-error/ssl-handshake-exception-error.png" alt="SSL Handshake exception error">
<p style="text-align:center;color:gray;"><small>SSLHandshakeException error</small></p>

<img src="/uploads/datagrip-driver-error/communications-link-failure.png" alt="Communications line failure">
<p style="text-align:center;color:gray;"><small>Communications link failure</small></p>

DataGrip 로그 파일 내에서 `Connecting to: jdbc:mysql://{HOST}:3306` 으로 검색하거나 연결을 시도한 Host 주소를 검색해서 어떤 에러가 발생했는 지 확인할 수 있습니다.
`javax.net.ssl.SSLHandshakeException` 또는 `[08S01] Communications link failure` 같은 통신 오류가 확인되었습니다.

**TLS** 통신 과정에서 문제가 있는 것으로 보이고, 개인적인 생각으로는 Amazon RDS 인스턴스 설정 중에 **스토리지 암호화** 값이 활성화되어 있는 경우에 문제가 생기는 것으로 보입니다.

## 1. javax.net.ssl.SSLHandshakeException

이 오류는 보통 SSL/TLS 설정과 관련이 있으며, 클라이언트와 서버 간의 인증 문제에서 발생합니다.

해결 방법:
1. JDBC 드라이버 업데이트:
    - JetBrains DataGrip에서 사용하는 MySQL JDBC 드라이버를 최신 버전으로 업데이트합니다. 최신 드라이버는 SSL/TLS 프로토콜과 관련된 많은 문제를 해결합니다.

2. TLS 버전 확인:
    - Amazon RDS 인스턴스가 지원하는 TLS 버전과 JDBC 드라이버가 사용하는 TLS 버전이 일치해야 합니다.
    - Amazon RDS 콘솔에서 **인스턴스 설정(TLS 버전)**을 확인하고 필요하다면 낮은 버전(예: TLS 1.2)으로 변경합니다.

3. SSL 인증서 설정:
    - Amazon RDS는 기본적으로 SSL 인증서를 사용합니다.
    - RDS 콘솔에서 제공하는 AWS 인증서를 다운로드하고, DataGrip 연결 설정에서 해당 인증서를 추가합니다.<br/>
      예: MySQL 연결 URL에 ?useSSL=true&requireSSL=true 추가.

4. SSL 연결 해제:
   - 연결 설정 중 Advanced 에서 useSSL 값을 FALSE 으로 변경
     <img src="/uploads/datagrip-driver-error/usessl-false.png" alt="useSSL false">

## 2. [08S01] Communications link failure

이 오류는 네트워크 연결 문제로 인해 클라이언트가 Amazon RDS 인스턴스에 접근할 수 없을 때 발생합니다.

해결 방법:
1. RDS 보안 그룹 설정 확인:
   - Amazon RDS의 보안 그룹에 연결을 시도하는 클라이언트의 IP 주소가 허용되어 있는지 확인합니다.<br/>
     예: 보안 그룹에서 3306 포트를 열고 클라이언트의 공인 IP 주소를 추가합니다.

2. VPC 서브넷 확인:
   - Amazon RDS가 퍼블릭 액세스를 허용하지 않는 경우, 동일한 VPC에서만 연결이 가능합니다.<br/>
     Amazon RDS 인스턴스가 올바른 서브넷 및 라우팅 설정을 사용하는지 확인합니다.

3. DNS 및 호스트 확인:
   - 연결 URL에서 사용한 RDS 호스트 이름이 올바른지 확인합니다.<br/>
     예: jdbc:mysql://your-instance-name.region.rds.amazonaws.com:3306.

보안 연결을 해제하는 방법이나 스토리지 암호화를 비활성화하는 쉬운 방법도 있겠습니다만,
암호화를 설정하는 않는 것은 기본적으로 권장되는 사항이 아니기 때문에 추천하지는 않습니다.
또 다른 방법으로 **Amazon Aurora MySQL**, **MariaDB** 드라이버를 사용하는 방법도 있는 것 같습니다.
하지만 올바른 드라이버를 사용하는 것이 안정적인 운영에 도움이 되기 때문에 권장되는 방법을 사용하는 것이 좋습니다.

## 연결 성공

<div style="display:flex;flex-direction:row;justify-content:center;">
   <img src="/uploads/datagrip-driver-error/dbms-connection.png" alt="DBMS connection">
</div>
<p style="text-align:center;color:gray;"><small>데이터베이스 연결 성공</small></p>

## 참고문헌

- [Amazon RDS](https://aws.amazon.com/rds/ "Amazon RDS"){:target="_blank"} - [MySQL Community 5.7.38](https://dev.mysql.com/doc/refman/5.7/en/ "MySQL 5.7"){:target="_blank"}
- DataGrip Log : [https://intellij-support.jetbrains.com/hc/en-us/community/posts/10252570443282-Datagrip-cannot-access-containerized-database](https://stackoverflow.com/questions/22544754/failed-to-build-gem-native-extension-installing-compass "Datagrip-cannot-access-containerized-database"){:target="_blank"}
- DataGrip DB Connection Error : [https://youtrack.jetbrains.com/issue/DBE-13313/Cant-connect-to-remote-MySQL-since-last-version-of-IntelliJ#focus=Comments-27-4921748.0-0](https://youtrack.jetbrains.com/issue/DBE-13313/Cant-connect-to-remote-MySQL-since-last-version-of-IntelliJ#focus=Comments-27-4921748.0-0 "DataGrip DB Connection Error"){:target="_blank"}