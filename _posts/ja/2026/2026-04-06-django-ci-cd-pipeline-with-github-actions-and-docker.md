---
layout: post
title: GitHub ActionsとDockerを活用したDjangoアプリケーションCI/CDパイプライン構築完全ガイド
slug: django-ci-cd-pipeline-with-github-actions-and-docker
date: 2026-04-06 15:26:09 +0900
categories:
- DevOps
- Backend
tags:
- GitHub Actions
- Django
- CI/CD
- Docker
- AWS
- ECR
- EC2
meta: 熟練開発者向け、GitHub ActionsによるDjango CI/CDパイプライン構築の実践ガイド。テスト自動化、Dockerイメージビルド、AWS
  ECRへのプッシュ、EC2へのデプロイまで、全プロセスを詳細なYAMLコード例と共に解説します。
image: /uploads/django-ci-cd-pipeline-with-github-actions-and-docker/thumbnail.webp
lang: ja
translation_key: django-ci-cd-pipeline-with-github-actions-and-docker
description: 熟練開発者向け、GitHub ActionsによるDjango CI/CDパイプライン構築の実践ガイド。テスト自動化、Dockerイメージビルド、AWS
  ECRへのプッシュ、EC2へのデプロイまで、全プロセスを詳細なYAMLコード例と共に解説します。
permalink: /ja/posts/django-ci-cd-pipeline-with-github-actions-and-docker/
---
手動デプロイの時代は終わりを告げています。コードを修正した後、FTPでファイルをアップロードしたり、SSHでサーバーに接続して`git pull`を実行しサーバーを再起動するプロセスは、ミスを誘発しやすく、開発サイクル全体を遅くする主な原因です。特に共同作業環境では、誰が、いつ、どのコードをデプロイしたのかを追跡することが難しく、安定したサービス運用において大きな障害となります。このような問題を解決するため、**CI/CD（継続的インテグレーション/継続的デプロイメント）**、すなわち継続的統合・デプロイパイプラインの構築は、もはや選択肢ではなく必須となりました。

本記事では、最も広く使われているWebフレームワークの一つである**Django**と、Gitホスティングサービスの標準となったGitHubの**GitHub Actions**を組み合わせ、テストからDockerイメージのビルド、そしてAWS ECR（Elastic Container Registry）およびEC2（Elastic Compute Cloud）へのデプロイまで続く、完全自動化されたCI/CDパイプラインを構築する方法を深く掘り下げます。単なる「Hello, World!」レベルのチュートリアルを超え、現場で即座に適用可能なセキュリティ、パフォーマンス最適化、環境分離などの高度な戦略まで含んだ実践的なガイドを提示します。

<!--more-->
![GitHub ActionsとDockerを活用したDjangoアプリケーションCI/CDパイプライン構築完全ガイド](/uploads/django-ci-cd-pipeline-with-github-actions-and-docker/thumbnail.webp "GitHub ActionsとDockerを活用したDjangoアプリケーションCI/CDパイプライン構築完全ガイド")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; Imagen 4.0によるAI生成</small>
</p>
-----

## 1. はじめに：なぜDjangoプロジェクトにGitHub ActionsのCI/CDが必要なのか？

Djangoプロジェクトの規模が大きくなり、チームメンバーが増えるほど、コードの一貫性とデプロイの安定性を維持することは非常に重要になります。開発者が`main`ブランチにコードをプッシュするたびに自動的にテストが実行され、テストを通過したコードだけが自動的にビルドおよびデプロイされる環境は、開発の生産性を最大化し、ヒューマンエラーを最小限に抑えるための核心的な要素です。

**GitHub Actions**は、GitHubリポジトリに組み込まれたワークフロー自動化ツールで、別途CI/CDサーバーを構築する必要なく、YAMLファイルを通じて簡単にパイプラインを定義できるという強力な利点があります。また、Dockerとの完璧な統合を通じて、アプリケーションの実行環境をコンテナイメージとして標準化し、「自分のPCでは動いたのに…」といった根深い問題を根本的に解決できます。

この記事で私たちが構築するパイプラインの全体的な流れは以下の通りです。
1.  **トリガー（Trigger）**: 開発者が`main`ブランチにコードをプッシュ（Push）またはマージ（Merge）します。
2.  **テスト（Test）**: GitHub Actionsのワークフローが実行され、Djangoプロジェクトのユニットテストとリンティング（Linting）を行います。
3.  **ビルド（Build）**: テストが成功すると、`Dockerfile`を基にDjangoアプリケーションを含むDockerイメージをビルドします。
4.  **プッシュ（Push）**: ビルドされたイメージをバージョンタグと共にAWS ECR（プライベートDockerイメージレジストリ）にプッシュします。
5.  **デプロイ（Deploy）**: SSHを通じて本番環境であるAWS EC2インスタンスに接続し、ECRから最新のイメージを取得して新しいコンテナを実行し、ほぼ無停止でデプロイを完了します。

## 2. コアアーキテクチャ：GitHub Actionsワークフローの設計

効果的なCI/CDパイプラインは、論理的に分離された複数の段階（Job）で構成されます。私たちは`Test`、`Build & Push`、`Deploy`という3つの主要なJobでワークフローを設計します。

-   **`test` Job**: コードの整合性を検証するステップです。このステップが失敗すると、後続のビルドおよびデプロイJobは実行されず、バグが含まれたコードがデプロイされるのを防ぎます。
-   **`build-and-push` Job**: `test` Jobが成功した場合にのみ実行されます。DjangoアプリケーションをDockerイメージとしてパッケージ化し、バージョン管理のためにECRにプッシュします。
-   **`deploy` Job**: `build-and-push` Jobが成功した場合にのみ実行されます。実際の運用サーバーに接続し、新しいバージョンのアプリケーションをデプロイします。

このような構造は、各ステップの役割を明確にし、問題が発生した際にどのステップで失敗したかを迅速に把握するのに役立ちます。

### GitHub Actionsの主要概念

ワークフローのYAMLファイルを作成する前に、核心的な概念を理解する必要があります。
-   **ワークフロー（Workflow）**: `.github/workflows/`ディレクトリに配置されたYAMLファイルで定義される、自動化されたプロセス全体を指します。
-   **イベント（Event）**: ワークフローの実行を引き起こす特定のアクティビティです。（例：`push`, `pull_request`）
-   **ジョブ（Job）**: 1つのワークフローは1つ以上のJobで構成され、各Jobは独立した仮想環境（Runner）で実行されます。
-   **ステップ（Step）**: Jobを構成する個々の作業単位です。シェルコマンドを実行したり、事前に作成されたActionを使用したりできます。
-   **アクション（Action）**: ワークフローで繰り返し使用される複雑な作業をカプセル化した、再利用可能なコードです。（例：`actions/checkout@v3`, `aws-actions/configure-aws-credentials@v2`）

## 3. 実践：Django CI/CDワークフローYAMLの詳細解説

それでは、実際のワークフローファイルを作成してみましょう。プロジェクトのルートに`.github/workflows/main.yml`ファイルを作成し、以下の内容を段階的に記述していきます。

### 3.1. 基本的なワークフローの定義とトリガー設定

```yaml
# .github/workflows/main.yml

name: Django CI/CD

on:
  push:
    branches: [ "main" ] # mainブランチにpushイベントが発生した時のみ実行

env:
  AWS_REGION: ap-northeast-2 # 使用するAWSリージョン
  ECR_REPOSITORY: my-django-app # 作成したECRリポジトリ名
```
-   `name`: ワークフローの名前を指定します。GitHubのUIに表示されます。
-   `on.push.branches`: `main`ブランチに`push`イベントが発生したときにこのワークフローをトリガーするように設定します。
-   `env`: ワークフロー全体で使用する環境変数を定義します。

### 3.2. テスト（Test）Jobの実装

最初のJobとして、Djangoプロジェクトのテストコードを実行し、コードの安定性を検証します。

```yaml
# .github/workflows/main.yml (続き)

jobs:
  test:
    name: Test Django Project
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: |
          python manage.py test
```
-   `runs-on: ubuntu-latest`: このJobが最新バージョンのUbuntu仮想環境で実行されることを意味します。
-   `actions/checkout@v3`: リポジトリのコードをRunnerにチェックアウトするActionです。
-   `actions/setup-python@v4`: 指定されたバージョンのPython環境を設定します。
-   `Install dependencies` および `Run tests`: `pip`を使用して依存パッケージをインストールし、Djangoの組み込み`test`コマンドを実行します。

### 3.3. ビルドとECRへのプッシュ（Build & Push）Job

`test` Jobが正常に完了すると、Dockerイメージをビルドし、AWS ECRにプッシュします。このステップではAWSの認証情報が必要になるため、GitHub Secretsを活用する必要があります。

**【事前準備】**
1.  AWS IAMでGitHub Actions用のユーザーを作成し、`AmazonEC2ContainerRegistryFullAccess`権限を付与してください。
2.  そのユーザーの**アクセスキーID**と**シークレットアクセスキー**を発行してください。
3.  GitHubリポジトリの`Settings > Secrets and variables > Actions`メニューで、`AWS_ACCESS_KEY_ID`と`AWS_SECRET_ACCESS_KEY`という名前で上記で発行したキーを登録してください。

{% raw %}
```yaml
# .github/workflows/main.yml (続き)

  build-and-push:
    name: Build and Push to ECR
    runs-on: ubuntu-latest
    needs: test # 'test' Jobが成功した場合にのみ実行

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Set image tag
        id: image-tag
        run: echo "IMAGE_TAG=$(date +%Y%m%d%H%M%S)" >> $GITHUB_ENV

      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ env.IMAGE_TAG }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -f Dockerfile .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
```
{% endraw %}
-   `needs: test`: このJobが`test` Jobに依存することを示します。
-   `aws-actions/configure-aws-credentials@v2`: GitHub Secretsに保存されたAWSキーを使用して、Runner環境にAWS認証を設定します。
-   `aws-actions/amazon-ecr-login@v1`: ECRにDockerクライアントをログインさせます。
-   `Set image tag`: 現在時刻を基にユニークなイメージタグを生成し、`GITHUB_ENV`に登録します。
-   `docker build` および `docker push`: `Dockerfile`を使用してイメージをビルドし、ECRリポジトリアドレスと生成されたタグを組み合わせてECRにプッシュします。

### 3.4. EC2サーバーへの自動デプロイ（Deploy）Job

最後に、ECRにプッシュされた最新のイメージをEC2インスタンスで実行し、デプロイを完了します。SSHを介してリモートコマンドを実行する方法を使用します。

**【事前準備】**
1.  EC2インスタンスにSSHで接続する際に使用するキーペアを作成します。
2.  プライベートキー（`.pem`ファイルの内容）を`EC2_SSH_PRIVATE_KEY`という名前でGitHub Secretsに登録します。
3.  EC2インスタンスのパブリックIPアドレスまたはドメインを`EC2_HOST`という名前で、SSHユーザー名（例：`ubuntu`, `ec2-user`）を`EC2_USERNAME`としてSecretsに登録します。
4.  EC2インスタンスにDockerとDocker Composeを事前にインストールしておきます。
5.  EC2インスタンスがECRからイメージをプルできるように、IAMロールをインスタンスにアタッチしてください。（`AmazonEC2ContainerRegistryReadOnly`権限）

{% raw %}
```yaml
# .github/workflows/main.yml (続き)

  deploy:
    name: Deploy to EC2
    runs-on: ubuntu-latest
    needs: build-and-push # 'build-and-push' Jobが成功した場合にのみ実行

    steps:
      - name: Get image tag
        id: image-tag
        # 前のJobで生成したタグを取得するための方策。
        # 実際にはArtifactを使用するか、ワークフローの出力（outputs）を使用する方がより正式です。
        # ここでは簡単にするために同じロジックでタグを再生成します。
        run: echo "IMAGE_TAG=$(date +%Y%m%d%H%M%S)" >> $GITHUB_ENV
        
      - name: Deploy to EC2 instance
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_PRIVATE_KEY }}
          script: |
            # ECRログイン
            aws ecr get-login-password --region ${{ env.AWS_REGION }} | docker login --username AWS --password-stdin ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ env.AWS_REGION }}.amazonaws.com

            # Docker Composeファイルを更新（sedを使用）
            # DOCKER_IMAGE環境変数を設定し、docker-compose.ymlで使用
            export DOCKER_IMAGE=${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ env.AWS_REGION }}.amazonaws.com/${{ env.ECR_REPOSITORY }}:${{ env.IMAGE_TAG }}
            
            # 既存コンテナの停止と削除（存在する場合）
            if [ $(docker ps -q -f name=my-django-container) ]; then
              docker-compose -f /home/ubuntu/my-django-app/docker-compose.yml down
            fi

            # 最新イメージをpull
            docker pull $DOCKER_IMAGE

            # docker-compose.ymlが配置されているディレクトリに移動して実行
            cd /home/ubuntu/my-django-app
            docker-compose up -d
```
{% endraw %}
-   `appleboy/ssh-action@master`: SSH経由でリモートサーバー上でスクリプトを実行してくれる非常に便利なActionです。
-   `script`: EC2インスタンスで実行されるシェルスクリプトです。ECRログイン、最新イメージのプル、`docker-compose up -d`によるコンテナのバックグラウンド実行プロセスを自動化します。`AWS_ACCOUNT_ID`もSecretとして登録する必要があります。

## 4. パフォーマンス最適化とベストプラクティス

### 依存関係のキャッシングによるビルド時間短縮
ワークフローが実行されるたびに`pip install`を実行するのは非効率です。`actions/cache`を使用して`pip`キャッシュを保存および復元すると、ビルド時間を大幅に短縮できます。

**`test` Jobの修正例：**
{% raw %}
```yaml
      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
```
{% endraw %}
`requirements.txt`ファイルの内容が変更されていない場合、キャッシュされた依存関係がそのまま使用されます。

### 環境分離（ステージング vs. 本番）
実際の運用環境では、`main`ブランチは本番デプロイ、`develop`ブランチはステージングデプロイのように、ブランチごとにデプロイ環境を分離することが安全です。GitHub Actionsの`if`条件文と`environments`機能を利用してこれを実装できます。

```yaml
on:
  push:
    branches: [ "main", "develop" ]

...
jobs:
...
  deploy-to-staging:
    if: github.ref == 'refs/heads/develop'
    name: Deploy to Staging
    # ... ステージングサーバーへのデプロイロジック ...
    
  deploy-to-production:
    if: github.ref == 'refs/heads/main'
    name: Deploy to Production
    needs: build-and-push
    environment: production # GitHub Environment機能を使用
    # ... 本番サーバーへのデプロイロジック ...
```
GitHubの`environment`機能を使用すると、デプロイ前の承認プロセスを追加したり、その環境専用のSecretを設定するなど、より高度な管理が可能になります。

## 5. 結論：自動化パイプラインによる開発生産性の最大化

これまで、GitHub ActionsとDockerを活用してDjangoアプリケーションのテスト、ビルド、デプロイの全プロセスを自動化するCI/CDパイプラインを構築する方法を詳しく見てきました。このように適切に構成されたパイプラインは、次のような明確な利点を提供します。

-   **迅速なデプロイ**: コードの変更を数分で本番環境に反映できます。
-   **安定性の向上**: 自動化されたテストがデプロイ前にコードの品質を保証し、手動作業によるミスを防ぎます。
-   **開発者体験の向上**: 開発者はデプロイの負担から解放され、コアビジネスロジックの開発に集中できます。
-   **可視性の確保**: GitHub ActionsのUIを通じて、すべてのデプロイ履歴と成功/失敗の状況を一目で把握できます。

本ガイドで提示したYAMLコードと戦略を基に、皆さんのDjangoプロジェクトに最適なCI/CDパイプラインを構築し、開発生産性とサービス安定性という二兎を追って両方を手に入れることを願っています。

### 参考文献
- [GitHub Actions 公式ドキュメント](https://docs.github.com/en/actions "GitHub Actions Documentation"){:target="_blank"}
- [AWS ECR (Elastic Container Registry) ユーザーガイド](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html "Amazon ECR User Guide"){:target="_blank"}
- [Django テスト公式ドキュメント](https://docs.djangoproject.com/en/stable/topics/testing/ "Django Testing Documentation"){:target="_blank"}
- [appleboy/ssh-action GitHubリポジトリ](https://github.com/appleboy/ssh-action "ssh-action on GitHub"){:target="_blank"}