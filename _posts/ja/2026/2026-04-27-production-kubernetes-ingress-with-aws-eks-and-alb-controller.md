---
layout: post
title: Amazon EKSとAWS Load Balancer Controllerを活用した本番レベルのKubernetes Ingress完全構築ガイド
slug: production-kubernetes-ingress-with-aws-eks-and-alb-controller
date: 2026-04-27 09:59:32 +0900
categories:
- Cloud
- DevOps
tags:
- AWS
- EKS
- Kubernetes
- Ingress
- ALB
- Load Balancer
- DevOps
description: AWS EKS環境で外部トラフィックを効率的に管理するための「AWS Load Balancer Controller」のインストールおよび設定方法を深掘りします。本番レベルのKubernetes
  Ingressを構築し、SSL/TLS適用、ヘルスチェック、高度なルーティングなど、実務のベストプラクティスを完全にマスターしましょう。
image: /uploads/production-kubernetes-ingress-with-aws-eks-and-alb-controller/thumbnail.webp
lang: ja
translation_key: production-kubernetes-ingress-with-aws-eks-and-alb-controller
permalink: /ja/posts/production-kubernetes-ingress-with-aws-eks-and-alb-controller/
---
Amazon EKS (Elastic Kubernetes Service) を使用してKubernetesクラスターを運用する際、最も重要な課題の一つは、外部トラフィックをクラスター内部のサービスへ安定的かつ効率的にルーティングすることです。Kubernetesは`NodePort`や`LoadBalancer`タイプのサービスを提供しますが、これらは本番環境の複雑な要件をすべて満たすには限界が明確です。例えば、`LoadBalancer`タイプのサービスをデプロイするたびに新しいELB (Elastic Load Balancer) が作成されてコスト負担が大きくなり、詳細なL7ルーティングルール（パスベース、ホストベースのルーティング）を適用することも困難です。

これらの問題を解決するため、Kubernetesは**Ingress（イングレス）**というオブジェクトを提供します。Ingressはクラスター外部のHTTP/HTTPSリクエストをクラスター内部のサービスに接続するルールの集合であり、このルールを実際に履行するのが**Ingress Controller（イングレスコントローラー）**です。特にAWS環境では、**AWS Load Balancer Controller**がEKSと最も完全に統合されており、AWSのApplication Load Balancer (ALB) やNetwork Load Balancer (NLB) をネイティブに活用できます。このコントローラーを使用すると、単一のALBを通じて複数のサービスを公開し、SSL/TLS証明書の管理、高度なトラフィックルーティング、WAF統合などの強力な機能をKubernetesネイティブな方法で宣言できます。

本稿では、経験豊富なエンジニア向けに、本番環境で**Amazon EKSとAWS Load Balancer Controllerを連携させ、安定的でコスト効率の高いIngressシステムを構築する**全プロセスをAからZまで深く掘り下げます。単にコントローラーをインストールするだけでなく、IAMロールの設定、必須のアノテーション（Annotation）を活用した高度な設定、そして実務で直面しうる問題への解決策とベストプラクティスまで詳細に見ていきます。

<!--more-->
![Amazon EKSとAWS Load Balancer Controllerを活用した本番レベルのKubernetes Ingress完全構築ガイド](/uploads/production-kubernetes-ingress-with-aws-eks-and-alb-controller/thumbnail.webp "Amazon EKSとAWS Load Balancer Controllerを活用した本番レベルのKubernetes Ingress完全構築ガイド")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI生成画像</small>
</p>
-----

## 背景と課題

Kubernetesクラスターで実行中のアプリケーションを外部に公開する基本的な方法は、`Service`オブジェクトを`LoadBalancer`タイプに設定することです。この場合、クラウドプロバイダー（AWS, GCPなど）は、そのサービスのために外部ロードバランサーをプロビジョニングします。

しかし、この方式にはいくつかの深刻な欠点があります。

1.  **コスト問題:** `LoadBalancer`タイプの`Service`が一つ作成されるたびに、個別のロードバランサー（AWSの場合はClassicまたはNetwork Load Balancer）が作成されます。数十、数百のマイクロサービスを運用する環境では、ロードバランサーのコストが指数関数的に増加する可能性があります。
2.  **機能的な限界:** `Service`タイプのロードバランサーは、基本的にL4（トランスポート層）レベルで動作します。そのため、ホスト名やURLパスに基づいてトラフィックを分岐させるL7（アプリケーション層）ルーティング、SSL/TLSオフロード、HTTPヘッダーベースのルーティングといった高度な機能を直接サポートしていません。
3.  **管理の複雑性:** 各サービスごとに外部IPアドレスとDNSレコードを個別に管理する必要があるため、運用の複雑性が増大します。

**Kubernetes Ingress**は、これらの問題を解決するために設計されたAPIオブジェクトです。IngressはL7の仮想ホスティングおよびパスベースのルーティングルールを定義し、これらのルールを実際に実行する**Ingressコントローラー**が単一のロードバランサーを共有して複数のバックエンドサービスにトラフィックを転送します。

AWS環境では、**AWS Load Balancer Controller**がこの役割を担い、AWSの強力なApplication Load Balancer (ALB) と直接統合されます。これにより、コストを削減し、AWSのマネージドサービスを最大限に活用して、安定的でスケーラブルなアーキテクチャを構築できます。

## 中核となるアーキテクチャと原則

AWS Load Balancer Controllerは、Kubernetesクラスター内でPodとして実行されるコントローラーです。このコントローラーの主な役割は、Kubernetes APIサーバーを継続的に監視（`watch`）し、`Ingress`オブジェクトの作成、変更、削除イベントを検知して、それに応じてAWS ALBリソースを自動的に作成・管理することです。

全体的なトラフィックフローとアーキテクチャは以下の通りです。

1.  **ユーザーリクエスト:** ユーザーがウェブブラウザを通じて`example.com`のようなドメインにリクエストを送信します。
2.  **DNS解決:** Route 53などのDNSサービスが、ドメイン名をAWS Load Balancer Controllerが作成した**ALBのDNS名**に解決します。
3.  **ALBでの受信:** リクエストはALBに到達します。ALBはSSL/TLS Terminationを行い、リクエストのホスト名（`Host`ヘッダー）とパス（`Path`）を確認します。
4.  **ルーティングルールの適用:** ALBは、Ingressコントローラーによって設定されたリスナールール（Listener Rules）に従い、リクエストを適切な**ターゲットグループ（Target Group）**に転送します。
5.  **ターゲットグループとPod:** ターゲットグループは、リクエストを処理するバックエンドPodのIPアドレスリストを保持しています。ALBはこの中の一つのPodにトラフィックを転送します。このとき、**Target Type**の設定（`ip`または`instance`）によって動作方式が変わります。
    *   `ip`モード（推奨）: ALBがEKSワーカーノードを経由せず、PodのIPに直接トラフィックをルーティングします。パフォーマンスに優れ、Podレベルのセキュリティグループ適用が可能です。
    *   `instance`モード: ALBがトラフィックをノードの`NodePort`に送信し、ノードの`kube-proxy`が再び該当のPodにトラフィックを転送します。
6.  **レスポンス:** Podがリクエストを処理してレスポンスを返すと、トラフィックは逆の順序でユーザーに返されます。

この全てのプロセスにおいて、開発者は単に`Ingress`のYAMLファイルを定義し、`kubectl apply`を実行するだけです。AWS Load Balancer Controllerが、残りの複雑なAWSリソース（ALB, Target Group, Listener, Rulesなど）のライフサイクルを自動的に管理してくれるのです。

## 実践的なコード/設定の深掘り

それでは、実際にEKSクラスターにAWS Load Balancer Controllerをインストールし、サンプルアプリケーションに対するIngressを設定するプロセスを段階的に進めていきます。

### ステップ1: 事前準備

始める前に、以下のツールがインストールされ、設定されている必要があります。

*   AWS CLI: AWSアカウントへのアクセスのために必要です。
*   `kubectl`: Kubernetesクラスターとの対話のために必要です。
*   `eksctl`: EKSクラスターを容易に作成・管理するための公式CLIツールです。
*   `helm`: Kubernetesのパッケージマネージャーで、コントローラーのインストールに使用します。

### ステップ2: IAM OIDCプロバイダーの作成

コントローラーがAWS APIを呼び出してALBを管理するためには、IAM権限が必要です。私たちはIAMロールを使用し、Kubernetesサービスアカウントと連携（IRSA, IAM Roles for Service Accounts）させることで、安全に権限を付与します。そのために、まずクラスターにIAM OIDC IDプロバイダーを作成する必要があります。

```bash
# <YOUR_CLUSTER_NAME>を実際のEKSクラスター名に置き換えてください。
eksctl utils associate-iam-oidc-provider \
    --region=ap-northeast-2 \
    --cluster=<YOUR_CLUSTER_NAME> \
    --approve
```

### ステップ3: コントローラー用のIAMポリシーとサービスアカウントの作成

AWS Load Balancer Controllerが必要とする権限を定義したIAMポリシーをダウンロードし、作成します。

```bash
# IAMポリシーのダウンロード
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json

# IAMポリシーの作成
aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam-policy.json
```

次に、`eksctl`を使用して、IAMポリシーがアタッチされたKubernetesサービスアカウントを作成します。このコマンドはCloudFormationスタックを通じてIAMロールを作成し、それをKubernetesサービスアカウントに紐付けます。

```bash
# <YOUR_AWS_ACCOUNT_ID>と<YOUR_CLUSTER_NAME>を実際の値に置き換えてください。
eksctl create iamserviceaccount \
  --cluster=<YOUR_CLUSTER_NAME> \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name "AmazonEKSLoadBalancerControllerRole" \
  --attach-policy-arn=arn:aws:iam::<YOUR_AWS_ACCOUNT_ID>:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve
```

### ステップ4: Helmを使用したAWS Load Balancer Controllerのインストール

Helmチャートを使用してコントローラーをインストールするのが、最も簡単で推奨される方法です。

```bash
# Helmリポジトリの追加
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks

# Helmチャートのインストール
# [🚨 注意] clusterName, serviceAccount.name, serviceAccount.createの値を必ず確認してください。
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=<YOUR_CLUSTER_NAME> \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=ap-northeast-2 \
  --set vpcId=<YOUR_VPC_ID>
```

インストールが完了したら、コントローラーのPodが正常に実行中であることを確認します。

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

### ステップ5: サンプルアプリケーションとIngressのデプロイ

次に、テスト用の簡単なウェブアプリケーション（例: `game-2048`）をデプロイし、`Ingress`リソースを作成して外部トラフィックを接続してみましょう。

#### 5.1. サンプルアプリケーションのデプロイ

以下の内容で`deployment-2048.yaml`ファイルを作成します。このYAMLはDeploymentと`ClusterIP`タイプのServiceを定義します。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deployment-2048
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: app-2048
  template:
    metadata:
      labels:
        app.kubernetes.io/name: app-2048
    spec:
      containers:
      - image: public.ecr.aws/l6m2t8p7/docker-2048:latest
        name: app-2048
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: service-2048
spec:
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
  type: ClusterIP
  selector:
    app.kubernetes.io/name: app-2048
```

ファイルをクラスターに適用します。

```bash
kubectl apply -f deployment-2048.yaml
```

#### 5.2. Ingressリソースの作成

次に、最も重要な`Ingress`リソースを定義します。以下の`ingress-2048.yaml`ファイルは、`game.your-domain.com`へのトラフィックを`service-2048`にルーティングし、AWS Certificate Manager (ACM)で事前に発行されたSSL証明書を使用してHTTPSを適用する例です。

```yaml
# ingress-2048.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-2048
  annotations:
    # [🔥 重要] Ingress Classを'alb'に指定し、AWS Load Balancer Controllerが処理するようにします。
    kubernetes.io/ingress.class: alb
    
    # [🔥 重要] ALBのスキームを指定します。外部に公開するには'internet-facing'を使用します。
    alb.ingress.kubernetes.io/scheme: internet-facing
    
    # [🔥 重要] Target Typeを'ip'に設定することを強く推奨します。
    alb.ingress.kubernetes.io/target-type: ip
    
    # [SSL/TLS] ACMで発行された証明書のARNを指定します。
    alb.ingress.kubernetes.io/certificate-arn: <YOUR_ACM_CERTIFICATE_ARN>
    
    # [SSL/TLS] HTTP(80)とHTTPS(443)ポートをリッスンするように設定します。
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    
    # [SSL/TLS] HTTPで入ってきたすべてのリクエストをHTTPSにリダイレクトします。
    alb.ingress.kubernetes.io/actions.ssl-redirect: '{"Type": "redirect", "RedirectConfig": { "Protocol": "HTTPS", "Port": "443", "StatusCode": "HTTP_301"}}'
    
    # [Health Check] ALBがPodのヘルスチェックを実行するパスを指定します。
    # alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  rules:
    - host: game.your-domain.com # [🚨 注意] 実際に所有しているドメインに変更してください。
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: service-2048
                port:
                  number: 80
```

YAMLファイルを適用します。

```bash
kubectl apply -f ingress-2048.yaml
```

数分後、`kubectl get ingress ingress-2048`コマンドを実行すると、`ADDRESS`フィールドに作成されたALBのDNSアドレスが表示されます。このアドレスをあなたのドメイン（`game.your-domain.com`）にCNAMEレコードとして登録すれば、しばらくしてHTTPS経由でアプリケーションにアクセスできるようになります。

## パフォーマンス最適化とベストプラクティス

本番環境でAWS Load Balancer Controllerを安定して運用するためのヒントとベストプラクティスをいくつか紹介します。

1.  **Target Typeは`ip`モードを使用する:** `ip`モードはPodに直接トラフィックを転送するため、`kube-proxy`を経由する余分なホップ（hop）を排除し、ネットワーク遅延を削減してパフォーマンスを向上させます。また、Podに直接セキュリティグループ（Security Groups for Pods）を適用できるため、より詳細なネットワークセキュリティポリシーの実装が可能です。
2.  **Ingress Groupingでコストを最適化する:** 複数の`Ingress`リソースが同じALBを共有するようにグループ化できます。`alb.ingress.kubernetes.io/group.name`アノテーションを使用して複数のIngressを一つの論理的なグループにまとめることで、コントローラーはそのグループに対して単一のALBのみを作成し、コストを大幅に削減できます。
3.  **正確なヘルスチェックパスを設定する:** `alb.ingress.kubernetes.io/healthcheck-path`アノテーションを使用して、アプリケーションの状態を正確に確認できるAPIエンドポイント（例: `/health`, `/status`）を指定してください。これにより、異常なPodがターゲットグループから迅速に除外され、サービスの安定性が向上します。
4.  **Subnet Auto-discoveryタグを活用する:** コントローラーはデフォルトで、特定のタグ（`kubernetes.io/cluster/<cluster-name>: owned`と`kubernetes.io/role/elb: 1`または`kubernetes.io/role/internal-elb: 1`）が付けられたサブネットにALBをデプロイします。`eksctl`でクラスターを作成すると、これらのタグは自動的にPublicおよびPrivateサブネットに適用されます。インフラをTerraformなどで直接管理している場合は、これらのタグを正しく設定しないと、コントローラーがALBを配置するサブネットを正確に見つけられません。
5.  **コントローラーのログを定期的に確認する:** コントローラーPodのログは、`Ingress`の設定エラーやAWS API呼び出しの失敗などの問題をデバッグする上で非常に重要です。`kubectl logs -n kube-system deploy/aws-load-balancer-controller`コマンドでログを確認し、潜在的な問題を事前に把握して解決できます。

## 結論

ここまで、Amazon EKS環境でAWS Load Balancer Controllerを使用して本番レベルのIngressシステムを構築する方法を詳しく見てきました。このコントローラーは、Kubernetesの宣言的APIとAWSの強力なALBを完全に組み合わせることで、開発者や運用者が複雑なAWSインフラを直接管理することなく、YAMLファイルだけで高度なL7トラフィックルーティングを実装できるようにします。

単にサービスを外部に公開するだけでなく、**コスト最適化、SSL/TLSの自動化、高度なルーティング、そしてAWSエコシステムとの緊密な統合**といった利点を通じて、マイクロサービスアーキテクチャをより堅牢でスケーラブルなものにします。本ガイドで扱った設定とベストプラクティスを現場で適用すれば、あなたのEKSクラスターは一段と高いレベルの安定性と効率性を備えることになるでしょう。

### 参考資料

*   [AWS Load Balancer Controller公式ドキュメント](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.7/ "AWS Load Balancer Controller Documentation"){:target="_blank"}
*   [Amazon EKS ベストプラクティスガイド - ネットワーキング](https://aws.github.io/aws-eks-best-practices/networking/ingress/ "Amazon EKS Best Practices Guide for Networking"){:target="_blank"}
*   [Introducing the AWS Load Balancer Controller](https://aws.amazon.com/blogs/containers/introducing-aws-load-balancer-controller/ "Introducing AWS Load Balancer Controller Blog Post"){:target="_blank"}
*   [AWS Load Balancer Controller Annotations](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.7/guide/ingress/annotations/ "Official Annotation Reference"){:target="_blank"}