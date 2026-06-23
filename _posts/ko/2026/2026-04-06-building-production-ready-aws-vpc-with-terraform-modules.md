---
layout: post
title: 프로덕션 레벨 AWS VPC, Terraform 모듈화로 완벽하게 구축하기
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
description: Terraform을 사용하여 확장 가능하고 재사용 가능한 프로덕션 레벨의 AWS VPC 네트워크를 구축하는 방법을 알아보세요.
  본 가이드는 IaC 원칙에 기반한 Terraform 모듈화 전략과 실용적인 HCL 코드를 통해 복잡한 클라우드 인프라를 효율적으로 관리하는 핵심
  노하우를 제공합니다.
image: /uploads/building-production-ready-aws-vpc-with-terraform-modules/thumbnail.webp
lang: ko
translation_key: building-production-ready-aws-vpc-with-terraform-modules
post_type: deep-dive
---
클라우드 인프라를 운영하다 보면 '반복'과의 싸움을 피할 수 없습니다. 개발, 스테이징, 프로덕션 등 여러 환경에 걸쳐 유사하지만 미묘하게 다른 네트워크 환경을 구축해야 하는 상황은 모든 서버 엔지니어의 숙명과도 같습니다. AWS 콘솔에서 수작업으로 VPC, 서브넷, 라우팅 테이블을 클릭하며 구성하는 방식은 초기에는 직관적일 수 있지만, 규모가 커질수록 실수의 가능성이 기하급수적으로 증가하며, 변경 이력을 추적하거나 동일한 환경을 재현하는 것은 거의 불가능에 가깝습니다.

이러한 문제를 해결하기 위해 등장한 것이 바로 **IaC(Infrastructure as Code)**, 그리고 그 중심에는 **Terraform**이 있습니다. Terraform을 사용하면 인프라를 코드로 정의하고 버전 관리하며, 자동화된 방식으로 프로비저닝할 수 있습니다. 하지만 단순히 모든 리소스를 하나의 거대한 `.tf` 파일에 쏟아붓는 것은 또 다른 관리의 비극을 낳을 뿐입니다. 코드가 길어지고 복잡해지면 가독성이 떨어지고, 특정 부분만 재사용하기가 어려워지기 때문입니다. 진정한 IaC의 가치는 **'모듈화'**를 통해 빛을 발합니다. 잘 설계된 Terraform 모듈은 마치 프로그래밍 언어의 잘 만든 함수처럼, 복잡한 인프라 구성 요소를 추상화하여 간결하고 재사용 가능한 형태로 만들어 줍니다.

본 포스트에서는 모든 AWS 인프라의 근간이 되는 **VPC(Virtual Private Cloud)**를 **Terraform 모듈**로 완벽하게 구축하는 방법을 심도 있게 다룰 것입니다. 단순히 리소스를 나열하는 수준을 넘어, 프로덕션 환경에서 요구되는 고가용성 아키텍처를 코드로 구현하고, 이를 어떻게 재사용 가능한 모듈로 설계하는지에 대한 실용적인 코드와 Best Practice를 제시합니다. 이 글을 통해 여러분은 수동 작업의 굴레에서 벗어나 안정적이고 확장 가능한 클라우드 인프라를 구축하는 핵심 역량을 갖추게 될 것입니다.

<!--more-->
![프로덕션 레벨 AWS VPC, Terraform 모듈화로 완벽하게 구축하기](/uploads/building-production-ready-aws-vpc-with-terraform-modules/thumbnail.webp "프로덕션 레벨 AWS VPC, Terraform 모듈화로 완벽하게 구축하기")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 도입 배경 및 문제 정의: 왜 VPC 모듈화가 필수적인가?

클라우드 환경에서 애플리케이션을 배포하기 위한 첫 단계는 언제나 네트워크 인프라, 즉 VPC를 구성하는 것입니다. 프로덕션 환경을 위한 VPC는 단순히 네트워크 대역을 할당하는 것에서 그치지 않고, 다음과 같은 복잡한 요구사항을 만족해야 합니다.

*   **고가용성(High Availability):** 여러 가용 영역(Availability Zone)에 걸쳐 리소스를 분산 배치하여 장애에 대비해야 합니다.
*   **보안(Security):** 외부 인터넷과 직접 통신하는 **Public Subnet**과 내부 서비스 및 데이터베이스를 위한 **Private Subnet**을 분리해야 합니다.
*   **네트워크 연결성:** Private Subnet의 리소스가 외부(예: 패키지 저장소)와 통신할 수 있도록 **NAT Gateway**를 구성해야 합니다.
*   **라우팅 정책:** 각 서브넷의 트래픽 흐름을 제어하기 위한 정교한 **Route Table** 설정이 필요합니다.

이러한 구성 요소를 각 환경(dev, staging, prod)마다 수동으로 혹은 복사-붙여넣기 방식의 Terraform 코드로 관리한다면, 사소한 설정 차이로 인한 장애가 발생하거나, 공통적인 보안 정책을 일괄 적용하기 어려운 문제가 발생합니다. **Terraform 모듈화**는 이러한 문제에 대한 명쾌한 해답입니다. VPC 생성을 위한 모든 로직을 하나의 독립된 '모듈'로 캡슐화하고, 각 환경에서는 이 모듈을 필요한 파라미터(예: VPC CIDR, 서브넷 개수 등)만 전달하여 호출하는 방식으로 인프라를 구성합니다.

이를 통해 다음과 같은 이점을 얻을 수 있습니다.

1.  **재사용성(Reusability):** 잘 만들어진 VPC 모듈 하나로 여러 프로젝트와 환경에 일관된 네트워크를 빠르게 배포할 수 있습니다.
2.  **유지보수성(Maintainability):** VPC 네트워크 구조 변경이 필요할 때, 모듈 코드만 수정하면 이를 사용하는 모든 환경에 일괄적으로 변경 사항을 적용할 수 있습니다.
3.  **가독성(Readability):** 루트(root) Terraform 코드는 `module "production_vpc" {...}`와 같이 매우 간결해져 전체 인프라 구조를 쉽게 파악할 수 있습니다.

이제부터 프로덕션 레벨의 VPC 아키텍처를 정의하고, 이를 재사용 가능한 Terraform 모듈로 구현하는 과정을 단계별로 살펴보겠습니다.

## 핵심 아키텍처 및 원리: 프로덕션 VPC와 Terraform 모듈 구조

우리가 구축할 VPC는 일반적인 3-Tier 아키텍처를 지원할 수 있는 표준적인 프로덕션 구조를 따릅니다.

*   **VPC:** `/16` 대역의 사설 IP 주소 공간
*   **Availability Zones (AZs):** 최소 2개 이상의 AZ에 걸쳐 리소스 분산
*   **Public Subnets:** 각 AZ에 1개씩 배치. Internet Gateway와 연결되어 외부 인터넷과 양방향 통신이 가능합니다. (예: Web Server, Bastion Host, ALB/NLB)
*   **Private Subnets:** 각 AZ에 1개씩 배치. NAT Gateway를 통해 외부로 나가는(outbound) 통신만 허용됩니다. (예: Application Server, DB)
*   **Internet Gateway (IGW):** VPC와 인터넷 간의 통신을 담당합니다.
*   **NAT Gateway:** 각 AZ의 Public Subnet에 1개씩 배치. Private Subnet의 리소스가 외부 인터넷에 접근할 수 있는 통로 역할을 합니다. 고가용성을 위해 AZ별로 생성합니다.
*   **Route Tables:** Public, Private 서브넷을 위한 별도의 라우팅 테이블을 생성하여 트래픽을 제어합니다.

이 아키텍처를 구현하기 위한 Terraform 모듈의 디렉토리 구조는 다음과 같습니다.

```
.
├── main.tf         # 모듈을 호출하여 실제 인프라를 생성하는 루트 파일
├── variables.tf    # 루트 모듈에서 사용할 변수 정의
├── terraform.tfvars  # 변수에 실제 값 할당 (예: staging 환경 값)
└── modules/
    └── vpc/
        ├── main.tf         # VPC 모듈의 핵심 리소스 정의
        ├── variables.tf    # VPC 모듈이 받을 입력 변수 정의
        └── outputs.tf      # 모듈이 생성 후 반환할 결과 값 정의
```

*   `modules/vpc/`: VPC 생성을 책임지는 재사용 가능한 모듈입니다.
*   루트 디렉토리 (`.`) : 이 모듈을 '호출'하여 특정 환경(예: 'staging')의 VPC를 생성하는 프로젝트의 최상위 위치입니다.

이러한 구조는 관심사의 분리(Separation of Concerns) 원칙을 따르며, 인프라 코드의 복잡도를 효과적으로 관리하게 해줍니다.

## 실무 적용 코드/설정 딥다이브

이제 실제 코드를 작성하며 VPC 모듈을 완성해 보겠습니다.

### 1. VPC 모듈 변수 정의 (`modules/vpc/variables.tf`)

모듈이 재사용 가능하려면 외부에서 구성 값을 주입받을 수 있어야 합니다. `variables.tf` 파일은 이러한 입력 값의 명세서 역할을 합니다.

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

### 2. VPC 모듈 핵심 로직 작성 (`modules/vpc/main.tf`)

이 파일에 VPC를 구성하는 모든 AWS 리소스 정의가 들어갑니다. `for_each`와 같은 Terraform 내장 함수를 활용하여 AZ와 서브넷을 동적으로 생성하는 것이 핵심입니다.

```hcl
# modules/vpc/main.tf

# 1. VPC 생성
resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# 2. Internet Gateway 생성 및 VPC에 연결
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# 3. Public Subnets 생성 (AZ별로 하나씩)
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

# 4. NAT Gateway를 위한 Elastic IP 생성
resource "aws_eip" "nat" {
  for_each   = aws_subnet.public
  depends_on = [aws_internet_gateway.this]
  vpc        = true
  
  tags = {
    Name = "${var.project_name}-nat-eip-${each.key}"
  }
}

# 5. NAT Gateway 생성 (AZ별 Public Subnet에 하나씩)
resource "aws_nat_gateway" "this" {
  for_each      = aws_subnet.public
  allocation_id = aws_eip.nat[each.key].id
  subnet_id     = each.value.id

  tags = {
    Name = "${var.project_name}-nat-gw-${each.value.availability_zone}"
  }
  depends_on = [aws_internet_gateway.this]
}

# 6. Private Subnets 생성 (AZ별로 하나씩)
resource "aws_subnet" "private" {
  for_each          = { for i, cidr in var.private_subnet_cidr_blocks : i => cidr }
  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = var.availability_zones[each.key]

  tags = {
    Name = "${var.project_name}-private-subnet-${var.availability_zones[each.key]}"
  }
}

# 7. Public Route Table 생성 및 IGW 라우팅 설정
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

# 8. Private Route Table 생성 및 NAT Gateway 라우팅 설정
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

# 9. 서브넷과 라우팅 테이블 연결
resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  for_each       = aws_subnet.private
  subnet_id      = each.value.id
  # Private Subnet이 속한 AZ와 동일한 AZ의 Private Route Table에 연결
  route_table_id = aws_route_table.private[index(var.availability_zones, each.value.availability_zone)].id
}
```

### 3. 모듈 출력 값 정의 (`modules/vpc/outputs.tf`)

모듈이 생성한 리소스의 ID와 같은 중요한 정보들은 다른 리소스(예: EC2 인스턴스, RDS)를 생성할 때 필요합니다. `outputs.tf`를 통해 이 값들을 외부로 노출시킬 수 있습니다.

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

### 4. 루트 디렉토리에서 모듈 호출하기

이제 잘 만들어진 VPC 모듈을 실제 환경에 배포할 차례입니다. 루트 디렉토리의 파일들을 설정합니다.

#### 루트 변수 정의 (`variables.tf`)

```hcl
# ./variables.tf

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}
```

#### 스테이징 환경 값 정의 (`terraform.tfvars`)

```hcl
# ./terraform.tfvars

aws_region = "ap-northeast-2"
```

#### 루트 모듈 구성 (`main.tf`)

이 파일에서 `provider`를 설정하고, `module` 블록을 사용해 `modules/vpc`를 호출합니다.

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

# 'staging' 환경을 위한 VPC 모듈 호출
module "staging_vpc" {
  source = "./modules/vpc" # 모듈 경로

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

# 모듈의 출력값을 다른 리소스에서 사용하는 예시
# 예: Staging VPC의 private subnet에 보안 그룹 생성
resource "aws_security_group" "rds_sg" {
  name        = "staging-rds-sg"
  description = "Allow inbound traffic for RDS"
  vpc_id      = module.staging_vpc.vpc_id # 모듈 출력값 사용!

  # ... security group rules
}
```

이제 터미널에서 `terraform init`, `terraform plan`, `terraform apply`를 실행하면, `staging` 환경을 위한 고가용성 VPC가 코드를 통해 완벽하게 생성됩니다. 만약 `production` 환경이 필요하다면, `module "production_vpc" {...}` 블록을 추가하고 파라미터만 변경하면 됩니다. 이것이 바로 모듈화의 강력함입니다.

## 성능 최적화 및 Best Practices

코드가 동작하는 것을 넘어, 프로덕션 환경에서 안정적으로 운영하기 위한 몇 가지 추가적인 Best Practice를 알아봅니다.

### 1. 원격 상태 저장소(Remote State Backend) 사용

`terraform.tfstate` 파일은 인프라의 현재 상태를 기록하는 매우 중요한 파일입니다. 기본적으로 로컬에 생성되지만, 팀원과 협업하거나 CI/CD 파이프라인에서 실행하려면 **원격 저장소**에 저장해야 합니다. AWS S3와 DynamoDB를 조합하여 상태 파일 저장 및 잠금(Locking) 기능을 구현하는 것이 표준적인 방법입니다.

```hcl
# backend.tf (루트 디렉토리에 추가)

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

### 2. 변수 유효성 검사(Validation)

모듈 사용자가 잘못된 값을 입력하는 것을 방지하기 위해 `variable` 블록 내에 `validation` 규칙을 추가할 수 있습니다. 예를 들어, 서브넷 개수와 가용 영역 개수가 일치하는지 검증할 수 있습니다.

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

### 3. 모듈 버전 관리

팀이나 조직 전체에서 모듈을 공유할 때는 Git 저장소를 활용하고 **태그(Tag)**를 통해 버전을 명시하는 것이 좋습니다. 이를 통해 모듈의 변경이 다른 프로젝트에 예기치 않은 영향을 미치는 것을 방지할 수 있습니다.

```hcl
# 루트 main.tf 에서 버전이 명시된 모듈 호출 예시

module "production_vpc" {
  # source = "./modules/vpc" 대신 Git 주소 사용
  source = "git::https://github.com/my-org/terraform-aws-vpc.git?ref=v1.2.0"

  # ... variables
}
```

## 결론

지금까지 우리는 AWS 인프라의 핵심인 VPC를 재사용 가능하고 확장성 있는 **Terraform 모듈**로 구축하는 전 과정을 살펴보았습니다. 수동 설정의 비효율성과 위험성을 IaC와 모듈화라는 강력한 패러다임으로 해결하는 방법을 실용적인 코드를 통해 확인했습니다.

오늘 다룬 VPC 모듈화는 시작에 불과합니다. 이와 동일한 원칙을 적용하여 Security Group, EC2 Auto Scaling Group, RDS 데이터베이스, EKS 클러스터 등 다양한 인프라 구성 요소를 모듈로 만들 수 있습니다. 이러한 모듈들이 모여 하나의 잘 설계된 '인프라 라이브러리'를 구축하게 되면, 어떤 복잡한 요구사항의 애플리케이션이라도 빠르고, 안정적이며, 일관된 방식으로 인프라를 프로비저닝할 수 있게 될 것입니다. 더 이상 인프라는 병목 지점이 아니라, 비즈니스의 속도를 가속하는 든든한 기반이 될 것입니다.

### 참고문헌
- [Terraform Modules 공식 문서](https://developer.hashicorp.com/terraform/language/modules "Terraform Modules Documentation"){:target="_blank"}
- [Terraform AWS Provider - VPC 리소스](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc "Terraform AWS VPC Resource Documentation"){:target="_blank"}
- [Terraform S3 Backend 공식 문서](https://developer.hashicorp.com/terraform/language/settings/backends/s3 "Terraform S3 Backend Documentation"){:target="_blank"}
- [AWS VPC(Virtual Private Cloud)란?](https://docs.aws.amazon.com/ko_kr/vpc/latest/userguide/what-is-amazon-vpc.html "What is Amazon VPC?"){:target="_blank"}