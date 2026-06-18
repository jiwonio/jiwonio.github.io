---
layout: post
title: AWS LambdaとAPI Gatewayを活用した高性能サーバーレスREST API構築のすべて
slug: building-serverless-rest-api-with-aws-lambda-api-gateway
date: 2026-04-06 15:48:16 +0900
categories:
- Cloud
- Backend
tags:
- AWS
- Lambda
- API Gateway
- Serverless
- REST API
- Python
- IaC
- SAM
description: 従来のサーバー管理の複雑さから解放され、AWS LambdaとAPI Gatewayを使用して、スケーラブルでコスト効率の高い高性能サーバーレスREST
  APIを構築するための実践ガイドです。Pythonベースの実践コード、AWS SAMテンプレート、パフォーマンス最適化のヒントまで、すべてを解説します。
image: /uploads/building-serverless-rest-api-with-aws-lambda-api-gateway/thumbnail.webp
lang: ja
translation_key: building-serverless-rest-api-with-aws-lambda-api-gateway
permalink: /ja/posts/building-serverless-rest-api-with-aws-lambda-api-gateway/
---
従来のWebアプリケーション開発において、サーバーのプロビジョニング、スケーリング、パッチ適用、メンテナンスは開発者の生産性を阻害する主な要因の一つでした。トラフィックが急増するたびに手動でサーバーを増設したり、逆にアイドル状態のサーバーコストをそのまま支払い続けなければならない非効率性を受け入れる必要がありました。**AWS Lambda**と**API Gateway**を筆頭とするサーバーレス（Serverless）アーキテクチャは、このようなパラダイムを根本から変えました。

サーバーレスコンピューティングは、開発者がサーバーを直接管理する必要なく、ビジネスロジックにのみ集中できるようにするクラウドコンピューティングモデルです。コードはイベントによってトリガーされたときにのみ実行され、使用した分だけ料金を支払うため、非常に経済的です。特に、HTTPリクエストを処理する**REST API**を構築する際、**API Gateway**と**Lambda**の組み合わせは絶大なシナジーを発揮し、自動スケーラビリティと高可用性を標準で備えた強力なバックエンドを容易に実現できます。本記事では、熟練したエンジニア向けに、理論だけでなく、実務ですぐに適用できるサーバーレスREST API構築の全プロセスを深く掘り下げて解説します。

<!--more-->
![AWS LambdaとAPI Gatewayを活用した高性能サーバーレスREST API構築のすべて](/uploads/building-serverless-rest-api-with-aws-lambda-api-gateway/thumbnail.webp "AWS LambdaとAPI Gatewayを活用した高性能サーバーレスREST API構築のすべて")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI生成画像</small>
</p>
-----

## サーバーレスAPIのコアアーキテクチャと原理

サーバーレスREST APIの中心には**AWS API Gateway**と**AWS Lambda**があります。この二つの相互作用を理解することが、アーキテクチャ全体を把握する鍵となります。

-   **AWS API Gateway**：クライアント（Web、モバイルアプリなど）から入ってくるすべてのHTTPリクエストを受け取る「ゲートウェイ」の役割を果たします。API Gatewayは、リクエストのルーティング、認証・認可、リクエスト/レスポンスの変換、レート制限（スロットリング）、キャッシングなど、API管理に必要なさまざまな機能を提供します。
-   **AWS Lambda**：実際のビジネスロジックを実行するコンピューティングサービスです。API Gatewayから渡されたリクエスト（イベント）を処理し、その結果を再びAPI Gatewayに返します。Lambda関数は隔離されたコンテナ環境で実行され、リクエスト数に応じてAWSが自動的にスケールイン/アウトを管理します。

### リクエスト処理フロー

1.  **クライアントリクエスト**：ユーザーがWebブラウザやモバイルアプリからAPIエンドポイント（例: `https://api.example.com/posts`）にHTTPリクエスト（GET、POSTなど）を送信します。
2.  **API Gatewayでの受信**：API Gatewayが該当リクエストを受信します。設定されたルーティングルールに従って、どのLambda関数を呼び出すかを決定します。この過程で、必要に応じてAPIキーの検証、IAM権限の確認、JWTトークンの検証などを行うことができます。
3.  **Lambda関数のトリガー**：API GatewayはHTTPリクエスト情報をJSON形式の「イベント」オブジェクトに変換し、対象のLambda関数を非同期的に呼び出し（invoke）ます。
4.  **ビジネスロジックの実行**：Lambda関数は渡されたイベントオブジェクトをパースして、リクエストパラメータ、ヘッダー、ボディなどを抽出し、定義されたビジネスロジック（例: データベース照会、データ加工）を実行します。
5.  **レスポンスの返却**：ロジックの実行が完了すると、Lambda関数はAPI Gatewayが理解できる特定のJSON形式に合わせて、HTTPステータスコード、ヘッダー、ボディを含んだレスポンスを返却します。
6.  **クライアントへの応答**：API GatewayはLambdaから受け取ったレスポンスを実際のHTTPレスポンスに変換し、最終的にクライアントに送信します。

この構造の最大の利点は、各コンポーネントが独立して拡張・管理される点です。トラフィックがゼロの時はコストがほとんど発生せず、秒間数千のリクエストが殺到しても、AWSが自動的にLambdaの実行環境を拡張して安定的にリクエストを処理します。

## 実践編：AWS SAMを活用したIaCベースのAPI構築

コンソールから手動でLambda関数とAPI Gatewayを設定するのは、簡単なテストには有用ですが、本番環境では再現性、バージョン管理、共同作業の困難さという明確な限界があります。そのため、インフラをコードとして管理する**IaC (Infrastructure as Code)**のアプローチが必須であり、AWSではそのために**SAM (Serverless Application Model)**を提供しています。SAMはCloudFormationをベースに、サーバーレスアプリケーションの定義を簡素化したオープンソースのフレームワークです。

### 1. プロジェクト構造

まず、以下のような基本的なプロジェクト構造を作成します。

```
sam-rest-api-project/
├── src/
│   ├── __init__.py
│   ├── app.py          # Lambdaハンドラロジック
│   └── requirements.txt  # Pythonの依存関係
└── template.yaml       # SAMテンプレートファイル
```

### 2. AWS SAMテンプレート（`template.yaml`）の作成

`template.yaml`ファイルは、私たちのサーバーレスアプリケーションのすべてのリソース（Lambda関数、API Gateway、IAMロールなど）を定義します。

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: >
  A sample serverless REST API project with AWS Lambda and API Gateway

Globals:
  Function:
    Timeout: 10
    MemorySize: 256
    Runtime: python3.9
    Architectures:
      - x86_64

Resources:
  # ------------------------------------------------------------#
  #  Lambda Function Definition
  # ------------------------------------------------------------#
  MyApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: app.lambda_handler
      Policies:
        # Add necessary IAM policies here, e.g., for database access
        - AmazonDynamoDBReadOnlyAccess
      Events:
        # This section defines the integration with API Gateway
        GetPost:
          Type: Api
          Properties:
            Path: /posts/{postId}
            Method: get
        CreatePost:
          Type: Api
          Properties:
            Path: /posts
            Method: post
        ListPosts:
          Type: Api
          Properties:
            Path: /posts
            Method: get

  # ------------------------------------------------------------#
  #  API Gateway Definition (implicitly created, but can be explicit)
  # ------------------------------------------------------------#
  # When using the 'Api' event type in AWS::Serverless::Function's Events property,
  # SAM automatically creates an API Gateway and integrates it with Lambda.
  # For more complex configurations (CORS, Authorizers, etc.),
  # you can explicitly define an AWS::Serverless::Api resource.

Outputs:
  MyApiEndpoint:
    Description: "API Gateway endpoint URL for Prod stage"
    Value: !Sub "https://execute-api.${AWS::Region}.amazonaws.com/Prod/"
```

**キーポイント：**

*   `Transform: AWS::Serverless-2016-10-31`: このファイルがSAMテンプレートであることを明示します。
*   `Resources.MyApiFunction`: `AWS::Serverless::Function`タイプでLambda関数を定義します。
*   `CodeUri`: Lambda関数のソースコードが配置されているパスを指定します。
*   `Handler`: リクエストがあった際に実行される関数を`ファイル名.関数名`の形式で指定します。
*   `Events`: この関数をトリガーするイベントを定義します。`Type: Api`はAPI Gatewayイベントを意味し、`Path`と`Method`で特定のエンドポイントとHTTPメソッドをLambda関数に紐付けます。

### 3. Lambdaハンドラコード（`src/app.py`）の作成

次に、実際のビジネスロジックを記述するPythonコードを作成します。

```python
import json
import boto3
from decimal import Decimal

# DynamoDBのDecimal型をJSONシリアライズするためのヘルパークラス
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Posts') # 実際のDynamoDBテーブル名

def lambda_handler(event, context):
    """
    API Gatewayプロキシ統合のためのメインハンドラ
    """
    print(f"Received event: {json.dumps(event)}")
    
    http_method = event.get('httpMethod')
    path = event.get('path')
    
    try:
        if http_method == 'GET' and '/posts/' in path:
            # 個別投稿の取得: /posts/{postId}
            post_id = event['pathParameters']['postId']
            response = table.get_item(Key={'postId': post_id})
            item = response.get('Item')
            if not item:
                return create_response(404, {'message': 'Post not found'})
            return create_response(200, item)
            
        elif http_method == 'GET' and path == '/posts':
            # 投稿一覧の取得
            response = table.scan()
            return create_response(200, response.get('Items', []))

        elif http_method == 'POST' and path == '/posts':
            # 新規投稿の作成
            body = json.loads(event.get('body', '{}'))
            # 実際には入力値の検証（バリデーション）ロジックが必須です。
            table.put_item(Item=body)
            return create_response(201, {'message': 'Post created successfully', 'item': body})
            
        else:
            return create_response(400, {'message': 'Unsupported route or method'})

    except Exception as e:
        print(f"Error: {e}")
        return create_response(500, {'message': 'Internal server error'})


def create_response(status_code, body):
    """
    API Gatewayが要求する形式でレスポンスオブジェクトを生成するヘルパー関数
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*' # CORS設定
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

```

### 4. ビルドとデプロイ

SAM CLIを使用してアプリケーションをビルドし、AWSにデプロイします。

```bash
# 1. 依存パッケージのインストールとビルド
# requirements.txtに記載されたライブラリをコードと共にパッケージングします。
sam build

# 2. パッケージングされたアプリケーションのデプロイ
# --guidedオプションを使用すると、初回デプロイ時に必要な設定（スタック名、リージョンなど）を対話形式で進められます。
sam deploy --guided
```

デプロイが正常に完了すると、`Outputs`で定義したAPIエンドポイントのURLが出力されます。これで、`curl`やPostmanのようなツールを使ってAPIをテストできます。

## パフォーマンス最適化とベストプラクティス

本番環境でサーバーレスAPIを安定して運用するためには、いくつかの主要な事項を必ず考慮する必要があります。

### 1. コールドスタートの緩和

Lambda関数がしばらく呼び出されないと、AWSはリソース効率化のためにその実行環境（コンテナ）を終了させます。その後再び呼び出しが発生すると、新しい実行環境の準備（コードのダウンロード、ランタイムの初期化、グローバル変数の初期化など）に追加の時間がかかります。これを**コールドスタート**と呼びます。

*   **Provisioned Concurrency (プロビジョニングされた同時実行)**：特定の数のLambda実行環境を常に「ウォーム」状態に保ち、コールドスタートをなくす機能です。レスポンス遅延に非常に敏感なコアAPIに適用できますが、追加コストが発生します。
*   **Lambda SnapStart (Java専用)**：Javaランタイムの場合、初期化が完了した実行環境のスナップショットを作成しておき、呼び出し時にスナップショットから高速に復元することで、起動時間を最大10倍短縮する機能です。
*   **コードの最適化**：関数パッケージのサイズを最小限に抑え、ハンドラ関数の外部（グローバルスコープ）でライブラリのインポートやデータベース接続の初期化など、時間のかかる処理を行うことで、コールドスタート時に一度だけ実行されるように構成します。

### 2. データベースコネクション管理

サーバーレス環境における最大の落とし穴の一つが、データベースコネクションの管理です。Lambdaは呼び出しごとに新しい実行環境が生成される可能性があるため、毎回新しいDBコネクションを確立するコードは、DBに過大な負荷をかけたり、コネクション制限を超えたりする原因となります。

*   **ハンドラ外部でのコネクション初期化**：DBコネクションオブジェクトをグローバル変数として宣言し、Lambdaの実行環境が再利用される際に既存のコネクションを継続して使用するようにします。
*   **RDS Proxyの使用**：Amazon RDSを使用している場合、**RDS Proxy**を使用することが最も理想的な解決策です。RDS ProxyはLambda関数とデータベースの間に位置し、コネクションプールを効率的に管理・共有してくれるため、Lambdaの同時実行数の拡大にも安全に対応できます。

### 3. セキュリティ：最小権限の原則

Lambda関数に割り当てられるIAM実行ロール（Execution Role）は、必ず**最小限の権限**のみを持つべきです。例えば、DynamoDBの特定のテーブルを読み取るだけの関数に`dynamodb:*`のようなワイルドカード権限を与えるべきではありません。`template.yaml`の`Policies`セクションで、必要な特定の操作（例：`dynamodb:GetItem`, `dynamodb:Scan`）に対する権限のみを明示的に付与する必要があります。

### 4. モニタリングとロギング

*   **Amazon CloudWatch**：Lambda関数は実行ログを自動的にCloudWatch Logsに送信します。`print()`文やロギングライブラリを介して出力された内容はすべてここに記録されるため、エラーのデバッグや動作分析に不可欠です。また、CloudWatch Metricsを通じて呼び出し数、エラー率、実行時間などのメトリクスを監視し、アラームを設定することができます。
*   **AWS X-Ray**：分散トレーシングシステムであり、API Gatewayから始まり、Lambda関数、そしてその関数が呼び出す他のAWSサービス（例：DynamoDB、S3）までのリクエスト全体の流れを可視化し、パフォーマンスのボトルネックを特定するのに非常に有用です。

## 結論

AWS LambdaとAPI Gatewayをベースとしたサーバーレスアーキテクチャは、もはや未来の技術ではなく、現代的なWebサービスを構築するための標準的な方法論の一つとして確立されました。サーバー管理の負担から解放され、ビジネス価値を生み出すコードにのみ集中できるようになり、使用量ベースの合理的な料金モデルと自動スケーラビリティは、スタートアップから大企業まで、あらゆる規模の組織にとって魅力的な選択肢です。

もちろん、コールドスタートやステート管理の難しさといったサーバーレス特有の特性を理解し、克服する努力は必要です。しかし、今日見てきたように、AWS SAMのようなIaCツールを活用し、データベースコネクション管理、セキュリティ、モニタリングといったベストプラクティスに適切に従えば、他のどのアーキテクチャよりも堅牢で効率的な高性能REST APIを成功裏に構築・運用できるでしょう。

### 参考資料
- [AWS Lambda デベロッパーガイド](https://docs.aws.amazon.com/ko_kr/lambda/latest/dg/welcome.html "AWS Lambda 公式ドキュメント"){:target="_blank"}
- [Amazon API Gateway デベロッパーガイド](https://docs.aws.amazon.com/ko_kr/apigateway/latest/developerguide/welcome.html "Amazon API Gateway 公式ドキュメント"){:target="_blank"}
- [AWS SAM (サーバーレスアプリケーションモデル) デベロッパーガイド](https://docs.aws.amazon.com/ko_kr/serverless-application-model/latest/developerguide/what-is-sam.html "AWS SAM 公式ドキュメント"){:target="_blank"}
- [AWS Lambda 関数でのデータベース接続管理](https://aws.amazon.com/ko/blogs/compute/database-connection-management-for-serverless-applications/ "AWS 公式ブログ"){:target="_blank"}