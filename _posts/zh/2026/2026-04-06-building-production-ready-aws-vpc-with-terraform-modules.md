---
layout: post
title: 通过 Terraform 模块化，完美构建生产级 AWS VPC
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
description: 了解如何使用 Terraform 构建可扩展、可复用的生产级 AWS VPC 网络。本指南基于 IaC 原则，通过 Terraform 模块化策略和实用的
  HCL 代码，为您提供高效管理复杂云基础设施的核心技巧。
image: /uploads/building-production-ready-aws-vpc-with-terraform-modules/thumbnail.webp
lang: zh
translation_key: building-production-ready-aws-vpc-with-terraform-modules
permalink: /zh/posts/building-production-ready-aws-vpc-with-terraform-modules/
---
在运营云基础设施时，我们不可避免地要与“重复”作斗争。为开发、预发布、生产等多个环境构建相似但又略有不同的网络环境，是每个服务器工程师的宿命。通过 AWS 控制台手动点击配置 VPC、子网、路由表等方式，初期可能很直观，但随着规模的扩大，出错的可能性会呈指数级增长，追踪变更历史或重现相同环境几乎变得不可能。

为解决这些问题，**IaC (Infrastructure as Code)** 应运而生，而 **Terraform** 正是其核心。通过 Terraform，我们可以将基础设施定义为代码，进行版本控制，并以自动化的方式进行部署。然而，简单地将所有资源堆砌在一个庞大的 `.tf` 文件中，只会引发另一场管理灾难。因为随着代码变长变复杂，可读性会下降，也难以只复用其中特定部分。真正的 IaC 价值在于通过 **“模块化”** 来体现。一个设计良好的 Terraform 模块，就像编程语言中一个优秀的函数，能将复杂的基础设施组件抽象成简洁、可复用的形式。

本文将深入探讨如何使用 **Terraform 模块** 完美构建作为所有 AWS 基础设施基石的 **VPC (Virtual Private Cloud)**。我们将超越简单罗列资源的层面，展示如何用代码实现生产环境所需的高可用性架构，并提供关于如何设计可复用模块的实用代码和最佳实践。通过本文，您将摆脱手动操作的束缚，掌握构建稳定、可扩展的云基础设施的核心能力。

<!--more-->
![通过 Terraform 模块化，完美构建生产级 AWS VPC](/uploads/building-production-ready-aws-vpc-with-terraform-modules/thumbnail.webp "通过 Terraform 模块化，完美构建生产级 AWS VPC")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI 生成的图像</small>
</p>
-----

## 背景与问题定义：为何 VPC 模块化至关重要？

在云环境中部署应用程序的第一步，始终是配置网络基础设施，即 VPC。一个用于生产环境的 VPC 不仅仅是分配一个网络地址段那么简单，它还必须满足以下复杂要求。

*   **高可用性 (High Availability):** 资源需要跨多个可用区 (Availability Zone) 分布，以应对故障。
*   **安全性 (Security):** 需要将与外部互联网直接通信的 **Public Subnet** 和用于内部服务及数据库的 **Private Subnet** 分离开来。
*   **网络连接性:** 需要配置 **NAT Gateway**，以便 Private Subnet 中的资源能够与外部（例如：软件包仓库）通信。
*   **路由策略:** 需要精细的 **Route Table** 设置来控制每个子网的流量走向。

如果为每个环境（dev、staging、prod）都通过手动或复制粘贴 Terraform 代码的方式来管理这些组件，很容易因微小的配置差异导致故障，或者难以统一应用通用的安全策略。**Terraform 模块化** 为这些问题提供了清晰的解决方案。它将创建 VPC 的所有逻辑封装在一个独立的“模块”中，每个环境只需调用此模块并传递必要的参数（如 VPC CIDR、子网数量等）即可配置基础设施。

通过这种方式，可以获得以下好处：

1.  **可复用性 (Reusability):** 一个精心设计的 VPC 模块，可以为多个项目和环境快速部署一致的网络。
2.  **可维护性 (Maintainability):** 当需要更改 VPC 网络结构时，只需修改模块代码，即可将变更统一应用到所有使用该模块的环境中。
3.  **可读性 (Readability):** 根 (root) Terraform 代码会变得非常简洁，如 `module "production_vpc" {...}`，从而可以轻松掌握整个基础设施的结构。

从现在开始，我们将分步探讨如何定义一个生产级的 VPC 架构，并将其实现为一个可复用的 Terraform 模块。

## 核心架构与原理：生产级 VPC 与 Terraform 模块结构

我们将要构建的 VPC 将遵循能够支持典型 3-Tier 架构的标准生产级结构。

*   **VPC:** `/16` 网段的私有 IP 地址空间
*   **可用区 (AZs):** 资源至少分布在 2 个以上的可用区
*   **公有子网 (Public Subnets):** 每个可用区部署一个。与互联网网关连接，可以与外部互联网进行双向通信。（例如：Web 服务器、堡垒机、ALB/NLB）
*   **私有子网 (Private Subnets):** 每个可用区部署一个。只允许通过 NAT 网关向外（outbound）通信。（例如：应用服务器、数据库）
*   **互联网网关 (IGW):** 负责 VPC 与互联网之间的通信。
*   **NAT 网关:** 每个可用区的公有子网中部署一个。作为私有子网中资源访问外部互联网的通道。为实现高可用性，按可用区创建。
*   **路由表 (Route Tables):** 为公有和私有子网创建独立的路由表以控制流量。

为实现此架构，Terraform 模块的目录结构如下：

```
.
├── main.tf         # 调用模块以创建实际基础设施的根文件
├── variables.tf    # 定义根模块中使用的变量
├── terraform.tfvars  # 为变量分配实际值（例如：staging 环境的值）
└── modules/
    └── vpc/
        ├── main.tf         # VPC 模块的核心资源定义
        ├── variables.tf    # VPC 模块接收的输入变量定义
        └── outputs.tf      # 模块创建后返回的结果值定义
```

*   `modules/vpc/`: 负责创建 VPC 的可复用模块。
*   根目录 (`.`) : 调用此模块以创建特定环境（如 'staging'）VPC 的项目顶层位置。

这种结构遵循关注点分离（Separation of Concerns）原则，可以有效地管理基础设施代码的复杂性。

## 实战代码/配置深度解析

现在，我们来通过编写实际代码，完成 VPC 模块的构建。

### 1. 定义 VPC 模块变量 (`modules/vpc/variables.tf`)

为了让模块能够复用，它必须能够从外部注入配置值。`variables.tf` 文件就扮演了这些输入值说明书的角色。

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

### 2. 编写 VPC 模块核心逻辑 (`modules/vpc/main.tf`)

该文件包含了构成 VPC 的所有 AWS 资源的定义。核心在于利用 `for_each` 等 Terraform 内置函数来动态创建可用区和子网。

```hcl
# modules/vpc/main.tf

# 1. 创建 VPC
resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# 2. 创建互联网网关并附加到 VPC
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# 3. 创建公有子网 (每个 AZ 一个)
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

# 4. 为 NAT 网关创建弹性 IP
resource "aws_eip" "nat" {
  for_each   = aws_subnet.public
  depends_on = [aws_internet_gateway.this]
  vpc        = true
  
  tags = {
    Name = "${var.project_name}-nat-eip-${each.key}"
  }
}

# 5. 创建 NAT 网关 (每个 AZ 的公有子网中一个)
resource "aws_nat_gateway" "this" {
  for_each      = aws_subnet.public
  allocation_id = aws_eip.nat[each.key].id
  subnet_id     = each.value.id

  tags = {
    Name = "${var.project_name}-nat-gw-${each.value.availability_zone}"
  }
  depends_on = [aws_internet_gateway.this]
}

# 6. 创建私有子网 (每个 AZ 一个)
resource "aws_subnet" "private" {
  for_each          = { for i, cidr in var.private_subnet_cidr_blocks : i => cidr }
  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = var.availability_zones[each.key]

  tags = {
    Name = "${var.project_name}-private-subnet-${var.availability_zones[each.key]}"
  }
}

# 7. 创建公有路由表并设置 IGW 路由
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

# 8. 创建私有路由表并设置 NAT 网关路由
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

# 9. 将子网与路由表关联
resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  for_each       = aws_subnet.private
  subnet_id      = each.value.id
  # 将私有子网关联到同一 AZ 的私有路由表
  route_table_id = aws_route_table.private[index(var.availability_zones, each.value.availability_zone)].id
}
```

### 3. 定义模块输出值 (`modules/vpc/outputs.tf`)

模块创建的资源 ID 等重要信息，在创建其他资源（如 EC2 实例、RDS）时会需要。通过 `outputs.tf` 可以将这些值暴露给外部。

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

### 4. 在根目录中调用模块

现在，是时候将我们精心制作的 VPC 模块部署到实际环境中了。我们需要配置根目录下的文件。

#### 定义根模块变量 (`variables.tf`)

```hcl
# ./variables.tf

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}
```

#### 定义预发布环境值 (`terraform.tfvars`)

```hcl
# ./terraform.tfvars

aws_region = "ap-northeast-2"
```

#### 配置根模块 (`main.tf`)

在这个文件中，我们配置 `provider`，并使用 `module` 块来调用 `modules/vpc`。

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

# 为 'staging' 环境调用 VPC 模块
module "staging_vpc" {
  source = "./modules/vpc" # 模块路径

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

# 在其他资源中使用模块输出值的示例
# 例如：在 Staging VPC 的私有子网中创建安全组
resource "aws_security_group" "rds_sg" {
  name        = "staging-rds-sg"
  description = "Allow inbound traffic for RDS"
  vpc_id      = module.staging_vpc.vpc_id # 使用模块输出值！

  # ... security group rules
}
```

现在，在终端中依次执行 `terraform init`、`terraform plan` 和 `terraform apply`，一个用于 `staging` 环境的高可用性 VPC 就会通过代码被完美创建。如果需要 `production` 环境，只需添加一个 `module "production_vpc" {...}` 块并修改参数即可。这就是模块化的强大之处。

## 性能优化与最佳实践

除了让代码能够运行，我们还需要了解一些额外的最佳实践，以确保在生产环境中稳定运行。

### 1. 使用远程状态后端 (Remote State Backend)

`terraform.tfstate` 文件是记录基础设施当前状态的极其重要的文件。默认情况下，它在本地创建，但如果要与团队成员协作或在 CI/CD 流水线中运行，就必须将其存储在 **远程存储库** 中。结合使用 AWS S3 和 DynamoDB 来实现状态文件的存储和锁定（Locking）功能，是一种标准做法。

```hcl
# backend.tf (添加到根目录)

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

### 2. 变量验证 (Validation)

为了防止模块使用者输入错误的值，可以在 `variable` 块中添加 `validation` 规则。例如，可以验证子网数量是否与可用区数量一致。

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

### 3. 模块版本控制

在团队或整个组织内共享模块时，推荐使用 Git 仓库并通过 **标签（Tag）** 来指定版本。这样可以防止模块的变更对其他项目造成意想不到的影响。

```hcl
# 根 main.tf 中调用带版本号的模块示例

module "production_vpc" {
  # source 不再是 "./modules/vpc"，而是 Git 地址
  source = "git::https://github.com/my-org/terraform-aws-vpc.git?ref=v1.2.0"

  # ... variables
}
```

## 结论

至此，我们完整地探讨了如何将 AWS 基础设施的核心——VPC，构建成一个可复用、可扩展的 **Terraform 模块** 的全过程。我们通过实用的代码，验证了如何利用 IaC 和模块化这一强大范式，来解决手动配置的低效与风险。

今天所讨论的 VPC 模块化仅仅是一个开始。我们可以应用相同的原则，为安全组（Security Group）、EC2 自动伸缩组（Auto Scaling Group）、RDS 数据库、EKS 集群等各种基础设施组件创建模块。当这些模块汇集在一起，构建出一个设计精良的“基础设施库”时，无论应用程序的需求多么复杂，我们都能快速、稳定、一致地部署其所需的基础设施。届时，基础设施将不再是瓶颈，而是加速业务发展的坚实基础。

### 参考资料
- [Terraform 模块官方文档](https://developer.hashicorp.com/terraform/language/modules "Terraform Modules Documentation"){:target="_blank"}
- [Terraform AWS Provider - VPC 资源](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc "Terraform AWS VPC Resource Documentation"){:target="_blank"}
- [Terraform S3 Backend 官方文档](https://developer.hashicorp.com/terraform/language/settings/backends/s3 "Terraform S3 Backend Documentation"){:target="_blank"}
- [什么是 AWS VPC (Virtual Private Cloud)？](https://docs.aws.amazon.com/ko_kr/vpc/latest/userguide/what-is-amazon-vpc.html "What is Amazon VPC?"){:target="_blank"}