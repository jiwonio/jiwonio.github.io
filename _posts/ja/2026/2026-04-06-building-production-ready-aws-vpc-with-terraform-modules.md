---
layout: post
title: Terraformモジュールで実現する、本番環境レベルのAWS VPC完全構築
slug: building-production-ready-aws-vpc-with-terraform-modules
date: 2026-04-06 16:44:10 +0900
categories:
- DevOps
- Cloud
tags:
- Terraform
- AWS
- VPC
- IaC
- Module
- DevOps
description: Terraformを使い、スケーラブルで再利用可能な本番環境レベルのAWS VPCネットワークを構築する方法を解説します。本ガイドでは、IaCの原則に基づいたTerraformモジュール化戦略と実践的なHCLコードを通じて、複雑なクラウドインフラを効率的に管理するための核心的なノウハウを提供します。
image: /uploads/building-production-ready-aws-vpc-with-terraform-modules/thumbnail.webp
lang: ja
translation_key: building-production-ready-aws-vpc-with-terraform-modules
post_type: deep-dive
permalink: /ja/posts/building-production-ready-aws-vpc-with-terraform-modules/
ai_generated: true
updated: 2026-04-06 16:44:10 +0900
---
クラウドインフラを運用していると、「繰り返し」との戦いは避けられません。開発、ステージング、本番など、複数の環境にまたがって、似ているようで微妙に異なるネットワーク環境を構築しなければならない状況は、すべてのサーバーエンジニアの宿命とも言えます。AWSコンソールで手作業でVPC、サブネット、ルートテーブルをクリックして構成するやり方は、最初は直感的かもしれませんが、規模が大きくなるほどミスの可能性が指数関数的に増加し、変更履歴の追跡や同じ環境の再現はほぼ不可能に近くなります。

これらの問題を解決するために登場したのが**IaC (Infrastructure as Code)**、そしてその中心にあるのが**Terraform**です。Terraformを使えば、インフラをコードとして定義し、バージョン管理し、自動化された方法でプロビジョニングできます。しかし、単にすべてのリソースを一つの巨大な`.tf`ファイルに詰め込むだけでは、また別の管理上の悲劇を生むだけです。コードが長くなり複雑になると可読性が低下し、特定の部分だけを再利用することが難しくなるからです。真のIaCの価値は、**「モジュール化」**によって輝きを放ちます。よく設計されたTerraformモジュールは、プログラミング言語における優れた関数のように、複雑なインフラコンポーネントを抽象化し、簡潔で再利用可能な形にしてくれます。

本稿では、すべてのAWSインフラの基盤となる**VPC (Virtual Private Cloud)**を、**Terraformモジュール**として完璧に構築する方法を深く掘り下げていきます。単にリソースを羅列するレベルを超え、本番環境で求められる高可用性アーキテクチャをコードで実装し、それをどのように再利用可能なモジュールとして設計するかについて、実践的なコードとベストプラクティスを提示します。この記事を通じて、皆さんは手作業の足枷から解放され、安定的でスケーラブルなクラウドインフラを構築するための核心的な能力を身につけることができるでしょう。

<!--more-->
![Terraformモジュールで実現する、本番環境レベルのAWS VPC完全構築](/uploads/building-production-ready-aws-vpc-with-terraform-modules/thumbnail.webp "Terraformモジュールで実現する、本番環境レベルのAWS VPC完全構築")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 背景と課題：なぜVPCのモジュール化が必須なのか？

クラウド環境でアプリケーションをデプロイするための最初のステップは、常にネットワークインフラ、すなわちVPCの構成です。本番環境向けのVPCは、単にネットワーク帯域を割り当てるだけでなく、以下のような複雑な要件を満たす必要があります。

*   **高可用性 (High Availability):** 複数のアベイラビリティーゾーン(AZ)にまたがってリソースを分散配置し、障害に備える必要があります。
*   **セキュリティ (Security):** 外部インターネットと直接通信する**Public Subnet**と、内部サービスやデータベースのための**Private Subnet**を分離する必要があります。
*   **ネットワーク接続性:** Private Subnetのリソースが外部（例：パッケージリポジトリ）と通信できるよう、**NAT Gateway**を構成する必要があります。
*   **ルーティングポリシー:** 各サブネットのトラフィックフローを制御するため、精巧な**Route Table**の設定が必要です。

これらの構成要素を各環境（dev, staging, prod）ごとに手動で、あるいはコピー＆ペースト方式のTerraformコードで管理すると、些細な設定の違いによる障害が発生したり、共通のセキュリティポリシーを一括で適用することが難しくなったりする問題が発生します。**Terraformのモジュール化**は、これらの問題に対する明快な答えです。VPC作成のためのすべてのロジックを一つの独立した「モジュール」としてカプセル化し、各環境ではこのモジュールを必要なパラメータ（例：VPC CIDR、サブネット数など）だけを渡して呼び出す形でインフラを構成します。

これにより、以下のようなメリットが得られます。

1.  **再利用性 (Reusability):** よく作られたVPCモジュール一つで、複数のプロジェクトや環境に一貫したネットワークを迅速にデプロイできます。
2.  **保守性 (Maintainability):** VPCネットワーク構造の変更が必要な場合、モジュールコードを修正するだけで、それを使用するすべての環境に一括で変更を適用できます。
3.  **可読性 (Readability):** ルート(root)のTerraformコードは`module "production_vpc" {...}`のように非常に簡潔になり、インフラ全体の構造を容易に把握できます。

これから、本番環境レベルのVPCアーキテクチャを定義し、それを再利用可能なTerraformモジュールとして実装するプロセスを段階的に見ていきましょう。

## コアアーキテクチャと原則：本番VPCとTerraformモジュールの構造

私たちが構築するVPCは、一般的な3-Tierアーキテクチャをサポートできる、標準的な本番環境の構成に従います。

*   **VPC:** `/16`帯域のプライベートIPアドレス空間
*   **アベイラビリティーゾーン (AZs):** 最低2つ以上のAZにまたがってリソースを分散
*   **Public Subnets:** 各AZに1つずつ配置。Internet Gatewayと接続され、外部インターネットとの双方向通信が可能です。（例: Web Server, Bastion Host, ALB/NLB）
*   **Private Subnets:** 各AZに1つずつ配置。NAT Gatewayを介して外部へのアウトバウンド通信のみが許可されます。（例: Application Server, DB）
*   **Internet Gateway (IGW):** VPCとインターネット間の通信を担います。
*   **NAT Gateway:** 各AZのPublic Subnetに1つずつ配置。Private Subnetのリソースが外部インターネットにアクセスするための経路の役割を果たします。高可用性のためにAZごとに作成します。
*   **Route Tables:** Public, Privateサブネット用に個別のルートテーブルを作成し、トラフィックを制御します。

このアーキテクチャを実装するためのTerraformモジュールのディレクトリ構造は以下の通りです。

```
.
├── main.tf         # モジュールを呼び出して実際のインフラを生成するルートファイル
├── variables.tf    # ルートモジュールで使用する変数を定義
├── terraform.tfvars  # 変数に実際の値を割り当て（例：ステージング環境の値）
└── modules/
    └── vpc/
        ├── main.tf         # VPCモジュールのコアリソースを定義
        ├── variables.tf    # VPCモジュールが受け取る入力変数を定義
        └── outputs.tf      # モジュールが生成後に返す結果値を定義
```

*   `modules/vpc/`: VPCの作成を担当する再利用可能なモジュールです。
*   ルートディレクトリ (`.`) : このモジュールを「呼び出し」、特定の環境（例：「ステージング」）のVPCを作成するプロジェクトの最上位の場所です。

このような構造は、関心の分離(Separation of Concerns)の原則に従い、インフラコードの複雑さを効果的に管理するのに役立ちます。

## 実践的なコード/設定の深掘り

それでは、実際にコードを書きながらVPCモジュールを完成させていきましょう。

### 1. VPCモジュールの変数定義 (`modules/vpc/variables.tf`)

モジュールが再利用可能であるためには、外部から構成値を注入できる必要があります。`variables.tf`ファイルは、これらの入力値の仕様書の役割を果たします。

```hcl
# modules/vpc/variables.tf

variable "project_name" {
  description = "The name of the project. Used for tagging resources."
  type        = string
}

variable "vpc_cidr_block" {
  description = "The CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "A list of availability zones to use."
  type        = list(string)
}

variable "public_subnet_cidr_blocks" {
  description = "A list of CIDR blocks for public subnets."
  type        = list(string)
}

variable "private_subnet_cidr_blocks" {
  description = "A list of CIDR blocks for private subnets."
  type        = list(string)
}
```

### 2. VPCモジュールのコアロジック作成 (`modules/vpc/main.tf`)

このファイルに、VPCを構成するすべてのAWSリソースの定義が含まれます。`for_each`のようなTerraformの組み込み関数を活用し、AZとサブネットを動的に生成することが核心です。

```hcl
# modules/vpc/main.tf

# 1. VPCの作成
resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# 2. Internet Gatewayの作成とVPCへのアタッチ
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# 3. Public Subnetの作成（AZごとに1つ）
resource "aws_subnet" "public" {
  for_each          = { for i, cidr in var.public_subnet_cidr_blocks : i => cidr }
  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = var.availability_zones[each.key]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-${var.availability_zones[each.key]}"
  }
}

# 4. NAT Gateway用のElastic IPの作成
resource "aws_eip" "nat" {
  for_each   = aws_subnet.public
  depends_on = [aws_internet_gateway.this]
  vpc        = true
  
  tags = {
    Name = "${var.project_name}-nat-eip-${each.key}"
  }
}

# 5. NAT Gatewayの作成（AZごとのPublic Subnetに1つ）
resource "aws_nat_gateway" "this" {
  for_each      = aws_subnet.public
  allocation_id = aws_eip.nat[each.key].id
  subnet_id     = each.value.id

  tags = {
    Name = "${var.project_name}-nat-gw-${each.value.availability_zone}"
  }
  depends_on = [aws_internet_gateway.this]
}

# 6. Private Subnetの作成（AZごとに1つ）
resource "aws_subnet" "private" {
  for_each          = { for i, cidr in var.private_subnet_cidr_blocks : i => cidr }
  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = var.availability_zones[each.key]

  tags = {
    Name = "${var.project_name}-private-subnet-${var.availability_zones[each.key]}"
  }
}

# 7. Public Route Tableの作成とIGWへのルーティング設定
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# 8. Private Route Tableの作成とNAT Gatewayへのルーティング設定
resource "aws_route_table" "private" {
  for_each = aws_nat_gateway.this
  vpc_id   = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = each.value.id
  }

  tags = {
    Name = "${var.project_name}-private-rt-${aws_subnet.public[each.key].availability_zone}"
  }
}

# 9. サブネットとルートテーブルの関連付け
resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  for_each       = aws_subnet.private
  subnet_id      = each.value.id
  # Private Subnetが属するAZと同じAZのPrivate Route Tableに関連付け
  route_table_id = aws_route_table.private[index(var.availability_zones, each.value.availability_zone)].id
}
```

### 3. モジュールの出力値定義 (`modules/vpc/outputs.tf`)

モジュールが作成したリソースのIDなどの重要な情報は、他のリソース（例：EC2インスタンス、RDS）を作成する際に必要となります。`outputs.tf`を介してこれらの値を外部に公開できます。

```hcl
# modules/vpc/outputs.tf

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = [for s in aws_subnet.public : s.id]
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value       = [for s in aws_subnet.private : s.id]
}
```

### 4. ルートディレクトリからのモジュール呼び出し

これで、よく設計されたVPCモジュールを実際の環境にデプロイする準備ができました。ルートディレクトリのファイルを設定します。

#### ルート変数の定義 (`variables.tf`)

```hcl
# ./variables.tf

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}
```

#### ステージング環境の値の定義 (`terraform.tfvars`)

```hcl
# ./terraform.tfvars

aws_region = "ap-northeast-2"
```

#### ルートモジュールの構成 (`main.tf`)

このファイルで`provider`を設定し、`module`ブロックを使って`modules/vpc`を呼び出します。

```hcl
# ./main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 'staging'環境のためのVPCモジュール呼び出し
module "staging_vpc" {
  source = "./modules/vpc" # モジュールのパス

  project_name      = "my-app-staging"
  vpc_cidr_block    = "10.10.0.0/16"
  availability_zones = ["ap-northeast-2a", "ap-northeast-2c"]
  
  public_subnet_cidr_blocks = [
    "10.10.1.0/24",
    "10.10.2.0/24"
  ]
  private_subnet_cidr_blocks = [
    "10.10.101.0/24",
    "10.10.102.0/24"
  ]
}

# モジュールの出力値を他のリソースで使用する例
# 例：Staging VPCのprivate subnetにセキュリティグループを作成
resource "aws_security_group" "rds_sg" {
  name        = "staging-rds-sg"
  description = "Allow inbound traffic for RDS"
  vpc_id      = module.staging_vpc.vpc_id # モジュールの出力値を使用！

  # ... security group rules
}
```

これで、ターミナルで`terraform init`、`terraform plan`、`terraform apply`を実行すれば、`staging`環境のための高可用性VPCがコードによって完璧に作成されます。もし`production`環境が必要なら、`module "production_vpc" {...}`ブロックを追加し、パラメータを変更するだけです。これこそがモジュール化の強力さです。

## パフォーマンス最適化とベストプラクティス

コードが動作するだけでなく、本番環境で安定して運用するための追加のベストプラクティスをいくつか見てみましょう。

### 1. リモートステートバックエンドの使用

`terraform.tfstate`ファイルは、インフラの現在の状態を記録する非常に重要なファイルです。デフォルトではローカルに作成されますが、チームで協業したり、CI/CDパイプラインで実行したりするには、**リモートストレージ**に保存する必要があります。AWS S3とDynamoDBを組み合わせて、ステートファイルの保存とロック(Locking)機能を実装するのが標準的な方法です。

```hcl
# backend.tf (ルートディレクトリに追加)

terraform {
  backend "s3" {
    bucket         = "my-terraform-state-bucket-unique-name"
    key            = "staging/vpc/terraform.tfstate"
    region         = "ap-northeast-2"
    dynamodb_table = "my-terraform-lock-table"
    encrypt        = true
  }
}
```

### 2. 変数のバリデーション

モジュールのユーザーが誤った値を入力するのを防ぐため、`variable`ブロック内に`validation`ルールを追加できます。例えば、サブネットの数とアベイラビリティーゾーンの数が一致するかどうかを検証できます。

```hcl
# modules/vpc/variables.tf

variable "public_subnet_cidr_blocks" {
  description = "A list of CIDR blocks for public subnets."
  type        = list(string)

  validation {
    condition     = length(var.public_subnet_cidr_blocks) == length(var.availability_zones)
    error_message = "The number of public subnet CIDRs must match the number of availability zones."
  }
}
```

### 3. モジュールのバージョン管理

チームや組織全体でモジュールを共有する場合、Gitリポジトリを活用し、**タグ(Tag)**によってバージョンを明記することをお勧めします。これにより、モジュールの変更が他のプロジェクトに予期せぬ影響を与えるのを防ぐことができます。

```hcl
# ルートのmain.tfでバージョン指定されたモジュールを呼び出す例

module "production_vpc" {
  # source = "./modules/vpc" の代わりにGitアドレスを使用
  source = "git::https://github.com/my-org/terraform-aws-vpc.git?ref=v1.2.0"

  # ... variables
}
```

## 結論

これまで、私たちはAWSインフラの核心であるVPCを、再利用可能でスケーラブルな**Terraformモジュール**として構築する全過程を見てきました。手動設定の非効率性とリスクを、IaCとモジュール化という強力なパラダイムで解決する方法を、実践的なコードを通じて確認しました。

本日取り上げたVPCモジュール化は始まりに過ぎません。これと同じ原則を適用して、Security Group、EC2 Auto Scaling Group、RDSデータベース、EKSクラスターなど、様々なインフラコンポーネントをモジュール化できます。これらのモジュールが集まって、よく設計された「インフラライブラリ」が構築されれば、どんなに複雑な要件のアプリケーションであっても、迅速かつ安定的で、一貫した方法でインフラをプロビジョニングできるようになるでしょう。もはやインフラはボトルネックではなく、ビジネスのスピードを加速させる強固な基盤となるのです。

### 参考資料
- [Terraform Modules公式ドキュメント](https://developer.hashicorp.com/terraform/language/modules "Terraform Modules Documentation"){:target="_blank"}
- [Terraform AWS Provider - VPCリソース](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc "Terraform AWS VPC Resource Documentation"){:target="_blank"}
- [Terraform S3 Backend公式ドキュメント](https://developer.hashicorp.com/terraform/language/settings/backends/s3 "Terraform S3 Backend Documentation"){:target="_blank"}
- [Amazon VPC とは?](https://docs.aws.amazon.com/ja_jp/vpc/latest/userguide/what-is-amazon-vpc.html "What is Amazon VPC?"){:target="_blank"}
---