---
layout: post
title: DataGripからAmazon RDSに接続する際のドライバーエラーのトラブルシューティング
meta: Learn how to resolve driver errors when connecting Amazon RDS to JetBrains DataGrip.
  This guide covers common issues and practical solutions for seamless database management.
tags:
- mysql
image: /uploads/datagrip-driver-error/thumbnail.webp
lang: ja
translation_key: datagrip-driver-error
slug: datagrip-driver-error
description: JetBrains DataGripをAmazon RDSに接続する際のドライバーエラーを解決する方法を学びます。このガイドでは、シームレスなデータベース管理のための一般的な問題と実用的な解決策について説明します。
permalink: /ja/posts/datagrip-driver-error/
---
JetBrainsは、リレーショナルデータベースとNoSQLデータベースの両方を扱うためのクロスプラットフォームツールである**DataGrip**を提供しています。
このツールは、MySQL、Oracle Database、PostgreSQL、SQLite、MongoDB、Redisなど、幅広いデータベースをサポートしています。
また、Amazon Redshiftのようなクラウドベースのデータベースに簡単に接続するためのオプションも提供しています。
最近、**AIアシスタント**プラグインが追加され、クエリの作成がさらに便利で効率的になりました。
この機能は、開発者がデータを扱う際の生産性を向上させるのに役立ちます。
この記事では、JetBrains DataGripを使用して**Amazon RDS**に接続する際に発生する可能性のある**ドライバーエラー**について説明し、それを解決するための方法を探ります。

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">[Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"}でも公開しています。</small>

![Cloud Databases](/uploads/datagrip-driver-error/cloud-database.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/avnsuresh-19928520" title="Content copyright holder" target="_blank">Suresh anchan</a></small>
</p>

-----

データベース接続は、アプリケーションの開発および運用において非常に重要なステップの一つです。
特に、**クラウド環境**でデータベースを使用する場合、接続設定の過程での詳細事項と発生しうるエラーをよく理解することが不可欠です。
**Amazon RDS**は、クラウド環境で頻繁に使用されるマネージドデータベースサービスであり、その安定性と柔軟性から多くの開発者や企業に好まれています。
しかし、Amazon RDSを**JetBrains DataGrip**のようなデータベース管理ツールに接続する際に、時折予期せぬ問題が発生することがあります。

この記事を通じて、同様の問題を経験した開発者が効果的に問題を解決し、より安定してAmazon RDSとDataGripを連携できるようになることを目指しています。
データベース接続の過程で経験する小さなエラー一つでも、開発プロセスに大きな影響を与える可能性があるため、問題の根本原因を特定し、適切な解決策を見つけることが重要です。
それでは、本文でこれらの問題を解決するための具体的な手順を順を追って見ていきましょう。

### ドライバーエラー

```
DBMS: MySQL (no ver.)
Case sensitivity: plain=mixed, delimited=exact
NotAfter: Wed Jun 01 12:00:00 UTC 2022.
```

![MySQL connection failed](/uploads/datagrip-driver-error/failed.png)

<p style="text-align:center;color:gray;"><small>Amazon RDS接続時のドライバーエラー</small></p>

MySQLドライバーが正常に接続できず、継続的に接続失敗が表示されます。
詳細なエラーメッセージを確認するには、DataGripのログメッセージを確認する必要があります。

### DataGripのログを確認する

```shell
# DataGripのログファイル
vi ~/AppData/Local/JetBrains/DataGrip{{ VERSION }}/log/idea.log
```

![SSL Handshake exception error](/uploads/datagrip-driver-error/ssl-handshake-exception-error.png)
<p style="text-align:center;color:gray;"><small>SSLHandshakeException エラー</small></p>

![Communications line failure](/uploads/datagrip-driver-error/communications-link-failure.png)
<p style="text-align:center;color:gray;"><small>Communications link failure</small></p>

DataGripのログファイル内で `Connecting to: jdbc:mysql://{HOST}:3306` で検索するか、接続を試みたホストアドレスを検索して、どのようなエラーが発生したかを確認できます。
`javax.net.ssl.SSLHandshakeException` または `[08S01] Communications link failure` のような通信エラーが確認されました。

**TLS** 通信の過程で問題があるものと思われ、個人的な見解では、Amazon RDSインスタンスの設定中に**ストレージの暗号化**が有効になっている場合に問題が発生するようです。

<h3 style="word-wrap: break-word;">1. javax.net.ssl.SSLHandshakeException</h3>

このエラーは通常、SSL/TLS設定に関連しており、クライアントとサーバー間の認証問題で発生します。

解決方法：
1. JDBCドライバーの更新：
    - JetBrains DataGripで使用しているMySQL JDBCドライバーを最新バージョンに更新します。最新のドライバーはSSL/TLSプロトコルに関連する多くの問題を解決します。

2. TLSバージョンの確認：
    - Amazon RDSインスタンスがサポートするTLSバージョンとJDBCドライバーが使用するTLSバージョンが一致する必要があります。
    - Amazon RDSコンソールで**インスタンス設定（TLSバージョン）**を確認し、必要であれば低いバージョン（例：TLS 1.2）に変更します。

3. SSL証明書の設定：
    - Amazon RDSはデフォルトでSSL証明書を使用します。
    - RDSコンソールで提供されるAWS証明書をダウンロードし、DataGripの接続設定でその証明書を追加します。<br/>
      例：MySQL接続URLに `?useSSL=true&requireSSL=true` を追加。

4. SSL接続の無効化：
   - 接続設定の「Advanced」でuseSSLの値をFALSEに変更します
     ![useSSL false](/uploads/datagrip-driver-error/usessl-false.png)

### 2. [08S01] Communications link failure

このエラーは、ネットワーク接続の問題によりクライアントがAmazon RDSインスタンスにアクセスできない場合に発生します。

解決方法：
1. RDSセキュリティグループ設定の確認：
   - Amazon RDSのセキュリティグループで、接続を試みるクライアントのIPアドレスが許可されているか確認します。<br/>
     例：セキュリティグループで3306ポートを開き、クライアントのパブリックIPアドレスを追加します。

2. VPCサブネットの確認：
   - Amazon RDSがパブリックアクセスを許可していない場合、同じVPCからのみ接続が可能です。<br/>
     Amazon RDSインスタンスが正しいサブネットとルーティング設定を使用しているか確認します。

3. DNSおよびホストの確認：
   - 接続URLで使用したRDSホスト名が正しいか確認します。<br/>
     例：<span style="word-wrap: break-word;">jdbc:mysql://your-instance-name.region.rds.amazonaws.com:3306.</span>

セキュアな接続を無効にする方法や、ストレージの暗号化を無効化する簡単な方法もありますが、
暗号化を設定しないことは基本的に推奨されないため、お勧めしません。
別の方法として、**Amazon Aurora MySQL**や**MariaDB**のドライバーを使用する方法もあるようです。
しかし、正しいドライバーを使用することが安定した運用に繋がるため、推奨される方法を使用することが望ましいです。

### 接続成功

<div style="display:flex;flex-direction:row;justify-content:center;">
   <img src="/uploads/datagrip-driver-error/dbms-connection.png" alt="DBMS connection">
</div>
<p style="text-align:center;color:gray;"><small>データベース接続成功</small></p>

### 参考文献

- [Amazon RDS](https://aws.amazon.com/rds/ "Amazon RDS"){:target="_blank"} - [MySQL Community 5.7.38](https://dev.mysql.com/doc/refman/5.7/en/ "MySQL 5.7"){:target="_blank"}
- DataGrip Log : [https://intellij-support.jetbrains.com/hc/en-us/community/posts/10252570443282-Datagrip-cannot-access-containerized-database](https://stackoverflow.com/questions/22544754/failed-to-build-gem-native-extension-installing-compass "Datagrip-cannot-access-containerized-database"){:target="_blank"}
- DataGrip DB Connection Error : [https://youtrack.jetbrains.com/issue/DBE-13313/Cant-connect-to-remote-MySQL-since-last-version-of-IntelliJ#focus=Comments-27-4921748.0-0](https://youtrack.jetbrains.com/issue/DBE-13313/Cant-connect-to-remote-MySQL-since-last-version-of-IntelliJ#focus=Comments-27-4921748.0-0 "DataGrip DB Connection Error"){:target="_blank"}