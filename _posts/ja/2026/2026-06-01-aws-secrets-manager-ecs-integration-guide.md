---
layout: post
title: AWS Secrets ManagerとECSの連携：本番環境のための安全なシークレット管理完全ガイド
slug: aws-secrets-manager-ecs-integration-guide
date: 2026-06-01 10:18:40 +0900
categories:
- Cloud
- DevOps
tags:
- AWS
- Secrets Manager
- ECS
- Security
- DevOps
- Container
description: 本番環境でAPIキーやDB認証情報などの機密情報を安全に管理する方法をお探しですか？この記事では、AWS Secrets ManagerとAmazon
  ECSを連携させ、コンテナアプリケーションにシークレット値を安全に注入するための「完璧な」アーキテクチャと実践的な例を詳しく解説します。
image: /uploads/aws-secrets-manager-ecs-integration-guide/thumbnail.webp
lang: ja
translation_key: aws-secrets-manager-ecs-integration-guide
post_type: deep-dive
permalink: /ja/posts/aws-secrets-manager-ecs-integration-guide/
---
本番環境でコンテナベースのアプリケーションを運用する際、最も厄介な問題の一つが**シークレット（Secret）の管理**です。データベースの認証情報、外部APIキー、証明書などの機密情報をコードにハードコーディングしたり、Gitリポジトリにコミットしたり、さらには通常の環境変数として注入したりすることは、深刻なセキュリティ脆弱性につながる可能性があります。これらの方法は、機密情報が漏洩するリスクを高め、シークレット値を変更するたびにアプリケーションの再デプロイが必要になるため、管理の複雑性を増大させます。

安全で効率的なシークレット管理のために、多くのチームが**AWS Secrets Manager**のような専門的なソリューションを導入します。AWS Secrets Managerは、シークレット情報の一元管理、ライフサイクル制御、自動ローテーション、そしてIAMを通じた詳細なアクセス制御を提供し、セキュリティレベルを画期的に向上させます。特にAmazon ECS（Elastic Container Service）と密接に統合されており、コンテナアプリケーションにシークレット情報を動的かつ安全に注入する強力なメカニズムを提供します。この記事では、AWS Secrets ManagerとECSを連携させるコアアーキテクチャを理解し、実務ですぐに適用可能な設定方法とベストプラクティスを深く掘り下げていきます。

<!--more-->
![AWS Secrets ManagerとECSの連携：本番環境のための安全なシークレット管理完全ガイド](/uploads/aws-secrets-manager-ecs-integration-guide/thumbnail.webp "AWS Secrets ManagerとECSの連携：本番環境のための安全なシークレット管理完全ガイド")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 導入の背景と問題定義

コンテナ環境が一般化するにつれて、アプリケーションの構成と機密情報を分離することは「選択」ではなく「必須」となりました。従来のシークレット管理方法には、次のような明確な限界があります。

-   **コード/設定ファイルへのハードコーディング：** 最も危険な方法で、コードリポジトリが漏洩すると、すべての機密情報も一緒に露出します。
-   **Dockerイメージに環境変数（ENV）として保存：** `docker inspect`コマンドやコンテナ内部へのアクセスで簡単に露出し、イメージレイヤーに平文で保存される危険性があります。
-   **`.env`ファイルの使用：** コンテナホスト（EC2インスタンス）にファイルが保存されるため、インスタンスへのアクセス権を持つすべてのユーザーがシークレットを閲覧できます。ファイルの管理と配布も煩雑です。

これらの問題を解決するために、私たちはシークレット管理の責任をアプリケーション外部の安全な中央ストアに移管する必要があります。**AWS Secrets Manager**はまさにその役割を果たし、ECSとのネイティブな連携を通じて、開発者がシークレット管理の複雑さから解放され、ビジネスロジックに集中できるよう支援します。

## コアアーキテクチャと原理

ECSでAWS Secrets Managerのシークレットを使用する核心的な原理は、**ECSタスク実行ロール（Task Execution Role）**にあります。ECS Agentは、コンテナイメージをECRから取得（pull）し、CloudWatch Logsにログを送信し、Secrets Managerからシークレットを取得するなどの作業を行うためにIAMロール（Role）を必要とします。このロールを「タスク実行ロール」と呼びます。

私たちが行うべきことは、このタスク実行ロールに特定のシークレットにアクセスできる`secretsmanager:GetSecretValue`権限を付与することです。そうすれば、ECS Agentはタスクの開始時にこのロールを使用して、Secrets Managerからシークレット値を安全に取得し、コンテナに注入してくれます。

ECSにシークレットを注入する方法は、大きく2つに分けられます。

1.  **環境変数として注入（Injecting as Environment Variables）：**
    *   最も簡単で一般的な方法です。
    *   ECSタスク定義の`secrets`プロパティを使用して、Secrets Managerに保存されたキー・値のペアをコンテナの環境変数にマッピングします。
    *   **利点：** 既存の環境変数を使用していたアプリケーションのコードを変更することなく、すぐに適用できます。
    *   **欠点：** コンテナ内部で`env`や`printenv`コマンドでシークレットが露出する可能性があり、一部の機密性の高いシステムではプロセス情報（例：`/proc/[pid]/environ`）を通じて確認できるため、セキュリティ強度は相対的に低くなります。

2.  **ファイルとしてマウント（Mounting as a File）：**
    *   Secrets Managerに保存された完全なJSONシークレットテキストを、コンテナ内部の特定パスにファイルとしてマウントします。
    *   ECSタスク定義の`mountPoints`と`volumes`プロパティを使用し、`secretOptions`を通じてSecrets ManagerのARNを指定します。
    *   **利点：** シークレットが環境変数リストに表示されないため、セキュリティがより高くなります。複雑な構造のJSONシークレット全体をアプリケーションでパースして使用するのに適しています。
    *   **欠点：** アプリケーションでファイルシステムを読み込んでパースするロジックが追加で必要になります。

どちらの方法にも長所と短所があるため、アプリケーションの特性とセキュリティ要件に合わせて適切な方法を選択する必要があります。

## 実務適用コード/設定の深掘り

それでは、実際の本番環境で適用するプロセスを段階的に見ていきましょう。データベース接続情報を格納したシークレットをECSコンテナに注入するシナリオを想定します。

### 1段階：AWS Secrets Managerでシークレットを作成

まず、アプリケーションで使用するシークレットを作成します。ここでは、データベース接続情報をJSON形式で保存します。

AWS Management ConsoleまたはAWS CLIを使用して作成できます。

```bash
# AWS CLIを使用したシークレット作成の例
aws secretsmanager create-secret --name "prod/myapp/database" \
    --description "Database credentials for my application in production" \
    --secret-string '{
        "username": "myuser",
        "password": "<YOUR_SECURE_PASSWORD>",
        "engine": "postgres",
        "host": "<YOUR_RDS_ENDPOINT>",
        "port": 5432,
        "dbname": "mydatabase"
    }'
```

[🚨 セキュリティ上の注意] 上記の例の`<...>`部分は実際の値に置き換える必要があります。実際のパスワードをコマンドに直接入力するのは避け、`--secret-string file://my-secret.json`のようにファイルを利用する方が安全です。

作成後、そのシークレットの**ARN**（Amazon Resource Name）を記録しておきます。（例：`arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:prod/myapp/database-AbCdEf`）

### 2段階：ECSタスク実行IAMロールのポリシー設定

ECSタスクがSecrets Managerにアクセスできるよう、タスク実行ロールに権限を追加する必要があります。通常、`AmazonECSTaskExecutionRolePolicy`という管理ポリシーがすでにアタッチされていますが、Secrets Managerへのアクセス権限は別途追加する必要があります。

以下のようなインラインポリシーを作成し、タスク実行ロールにアタッチします。

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:prod/myapp/database-AbCdEf"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "kms:Decrypt",
            "Resource": "arn:aws:kms:ap-northeast-2:123456789012:key/<YOUR_KMS_KEY_ID>",
            "Condition": {
                "StringEquals": {
                    "kms:ViaService": "secretsmanager.ap-northeast-2.amazonaws.com"
                }
            }
        }
    ]
}
```

-   **`secretsmanager:GetSecretValue`**: 指定されたシークレット値を読み取る権限です。**セキュリティのため、`Resource`にはワイルドカード（`*`）の代わりに特定のシークレットのARNを明記することが非常に重要です。**
-   **`kms:Decrypt`**: Secrets ManagerはデフォルトでAWS KMSを使用してシークレットを暗号化します。そのため、該当のKMSキーで暗号化されたシークレットを復号できる権限が必要です。もしデフォルトのKMSキー（`aws/secretsmanager`）を使用した場合、リソースARNは少し異なる場合があります。

### 3段階：ECSタスク定義の構成

次に、ECSタスク定義にSecrets Managerとの連携を設定します。`task-definition.json`ファイルの一部を通して、両方の方法を見てみましょう。

#### 方法1：環境変数として注入

`containerDefinitions`セクションに`secrets`オブジェクトを追加します。`valueFrom`にSecrets ManagerのARNとJSONキーを指定すると、その値が`name`で指定された環境変数に注入されます。

```json
{
    "family": "my-app-task",
    "taskRoleArn": "arn:aws:iam::123456789012:role/MyTaskRole",
    "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
    "networkMode": "awsvpc",
    "containerDefinitions": [
        {
            "name": "my-app-container",
            "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-app:latest",
            "portMappings": [
                {
                    "containerPort": 8000,
                    "hostPort": 8000
                }
            ],
            "secrets": [
                {
                    "name": "DB_USERNAME",
                    "valueFrom": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:prod/myapp/database-AbCdEf:username::"
                },
                {
                    "name": "DB_PASSWORD",
                    "valueFrom": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:prod/myapp/database-AbCdEf:password::"
                },
                {
                    "name": "DB_HOST",
                    "valueFrom": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:prod/myapp/database-AbCdEf:host::"
                }
            ]
        }
    ]
    // ... その他の設定
}
```
> **参考：** `valueFrom`のARN形式は`secret-arn:json-key:version-stage:version-id`です。`json-key`の後に`::`を付けると、最新バージョンを使用するという意味になります。

#### 方法2：ファイルとしてマウント

`volumes`、`mountPoints`、`secrets`プロパティを組み合わせて使用します。この方法では、シークレットJSON全体が1つのファイルになります。

```json
{
    "family": "my-app-task-file-secret",
    "taskRoleArn": "arn:aws:iam::123456789012:role/MyTaskRole",
    "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
    "networkMode": "awsvpc",
    "containerDefinitions": [
        {
            "name": "my-app-container",
            "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-app:latest",
            "portMappings": [
                // ...
            ],
            "mountPoints": [
                {
                    "sourceVolume": "db-secret-volume",
                    "containerPath": "/etc/secrets",
                    "readOnly": true
                }
            ]
        }
    ],
    "volumes": [
        {
            "name": "db-secret-volume",
            "host": {},
            "secretOptions": {
                "name": "database-credentials",
                "valueFrom": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:prod/myapp/database-AbCdEf"
            }
        }
    ]
}
```
> この設定は正しくありません。`volumes`と`secretOptions`を直接使用する方法は、EC2起動タイプでDocker Volume Driverと連携する際に使われるレガシーな方式に近いです。**Fargateおよび最新のECSでは、`secrets`オプションを使用して環境変数として注入するか、アプリケーションが直接SDKで呼び出すことが推奨されるパターンです。**
> 
> **訂正：** Fargateでファイルをマウントする現代的な方法は、`aws-secrets-extension`のようなサイドカーコンテナを使用するか、アプリケーションのブートストラップスクリプトでAWS CLI/SDKを通じてシークレットをファイルとして保存することです。しかし、最もネイティブで簡単なファイルマウント方法は、実は**AWS Systems Manager Parameter Store**を使用することです。Secrets Managerとの直接的なファイルマウント機能は限定的です。混乱を招き申し訳ありません。実務では、**環境変数への注入**が最も広く使われているパターンです。

### 4段階：アプリケーションコード（Pythonの例）

**環境変数**として注入されたシークレットをアプリケーションで使用するのは非常に簡単です。

```python
# settings.py (Djangoの例)
import os
import json

# 環境変数として注入されたシークレットを読み込む
DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydatabase',
        'USER': DB_USERNAME,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': '5432',
    }
}
```

もしアプリケーションがSDKを通じて直接Secrets Managerを呼び出す場合は、次のように実装できます。（この場合、タスク実行ロールではなく、タスクロールに`secretsmanager:GetSecretValue`権限が必要です）

```python
import boto3
import json

def get_secret(secret_name, region_name="ap-northeast-2"):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        # 本番環境ではより洗練された例外処理が必要です。
        raise e
    else:
        # シークレットは'SecretString'にJSON文字列として保存されています。
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)

# アプリケーション初期化時に呼び出す
db_credentials = get_secret("prod/myapp/database")
DB_USERNAME = db_credentials['username']
DB_PASSWORD = db_credentials['password']
# ...
```

この方法は、ECSタスク定義にシークレットのARNが露出しないという利点がありますが、アプリケーションコードにAWS SDKへの依存関係が追加され、API呼び出しコストとレイテンシーを考慮する必要があります。

## パフォーマンス最適化とベストプラクティス

1.  **最小権限の原則（Principle of Least Privilege）：** IAMポリシーを設定する際は、常にワイルドカード（`*`）の代わりに特定のシークレットのARNを明記し、そのタスクが必要なシークレットにのみアクセスできるように制限すべきです。

2.  **シークレットのローテーション（Secret Rotation）の有効化：** データベースのパスワードのように定期的に変更する必要があるシークレットは、Secrets Managerの自動ローテーション機能を使用することをお勧めします。AWS Lambdaと連携し、定められた周期（例：90日）ごとに自動でシークレットを変更し、Secrets Managerを更新できます。これによりセキュリティが大幅に強化されます。

3.  **アプリケーション内でのキャッシング：** アプリケーションがSDKを通じて直接シークレットを取得する場合、アプリケーション起動時に一度だけ取得してメモリにキャッシュし、再利用することをお勧めします。リクエストごとに`GetSecretValue` APIを呼び出すと、不要なコストと遅延が発生する可能性があります。

4.  **シークレットの論理的な分離：** `prod/myapp/database`、`dev/myapp/database`のように、環境（prod, dev）とサービス名（myapp）を組み合わせてシークレット名を指定すると、管理が容易になります。

5.  **監査とモニタリング：** Secrets ManagerへのすべてのAPI呼び出しはAWS CloudTrailに記録されます。定期的にCloudTrailログをモニタリングしたり、Amazon GuardDutyのようなサービスを使用して、異常なシークレットへのアクセス試行を検知し、対応すべきです。

## 結論

AWS Secrets ManagerをAmazon ECSと連携させることは、現代的なクラウドネイティブアプリケーションのセキュリティを確保するための重要なステップです。機密情報をコードやインフラから安全に分離し、一元管理することで、セキュリティ脆弱性を大幅に削減し、運用効率を高めることができます。タスク実行ロールを利用した環境変数への注入方式は、実装がシンプルでありながら強力なセキュリティを提供するため、ほとんどのシナリオに適しています。

もはや`.env`ファイルやハードコーディングされたシークレット値のために不安を感じる必要はありません。本日紹介したアーキテクチャとベストプラクティスを本番環境に適用し、より安全で堅牢、かつスケーラブルなコンテナサービスを構築してください。

### 参考資料
- [AWS Secrets Manager 公式ドキュメント](https://aws.amazon.com/secrets-manager/){:target="_blank"}
- [Amazon ECS タスクへの機密データの指定](https://docs.aws.amazon.com/ko_kr/AmazonECS/latest/developerguide/specifying-sensitive-data.html "Specifying Sensitive Data in Amazon ECS"){:target="_blank"}
- [AWS Secrets Manager でのシークレットのローテーション](https://docs.aws.amazon.com/ko_kr/secretsmanager/latest/userguide/rotating-secrets.html "Configuring Secret Rotation"){:target="_blank"}
- [AWS Secrets Manager の認証とアクセスコントロール](https://docs.aws.amazon.com/ko_kr/secretsmanager/latest/userguide/auth-and-access.html "Controlling Access to Secrets"){:target="_blank"}