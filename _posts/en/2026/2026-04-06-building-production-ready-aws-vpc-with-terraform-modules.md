---
layout: post
title: Building a Production-Ready AWS VPC with Terraform Modules
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
description: Learn how to build a scalable, reusable, production-level AWS VPC network
  using Terraform. This guide provides key know-how for efficiently managing complex
  cloud infrastructure through Terraform modularization strategies and practical HCL
  code based on IaC principles.
image: /uploads/building-production-ready-aws-vpc-with-terraform-modules/thumbnail.webp
lang: en
translation_key: building-production-ready-aws-vpc-with-terraform-modules
permalink: /en/posts/building-production-ready-aws-vpc-with-terraform-modules/
---
When operating cloud infrastructure, the battle against "repetition" is unavoidable. The need to build similar yet subtly different network environments across multiple stages like development, staging, and production is a challenge every server engineer faces. While manually configuring VPCs, subnets, and routing tables in the AWS console might seem intuitive at first, the potential for error grows exponentially as the scale increases. Tracking change history or reproducing an identical environment becomes nearly impossible.

This is where **IaC (Infrastructure as Code)** comes to the rescue, with **Terraform** at its core. Terraform allows you to define infrastructure as code, version control it, and provision it in an automated fashion. However, simply dumping all your resources into one giant `.tf` file only leads to another management nightmare. As code becomes long and complex, readability suffers, and reusing specific parts becomes difficult. The true value of IaC shines through **'modularization'**. A well-designed Terraform module, much like a well-written function in a programming language, abstracts complex infrastructure components into concise, reusable forms.

In this post, we will take a deep dive into building a complete **VPC (Virtual Private Cloud)**, the foundation of all AWS infrastructure, as a **Terraform module**. We will go beyond simply listing resources to implement a high-availability architecture required for production environments as code. We will also present practical code and best practices on how to design it as a reusable module. Through this article, you will break free from the shackles of manual work and acquire the core competency to build stable, scalable cloud infrastructure.

<!--more-->
![Building a Production-Ready AWS VPC with Terraform Modules](/uploads/building-production-ready-aws-vpc-with-terraform-modules/thumbnail.webp "Building a Production-Ready AWS VPC with Terraform Modules")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## Background and Problem Definition: Why is VPC Modularization Essential?

The first step to deploying an application in a cloud environment is always to configure the network infrastructure, the VPC. A production-grade VPC isn't just about allocating a network range; it must satisfy complex requirements such as:

*   **High Availability:** Resources must be distributed across multiple Availability Zones (AZs) to prepare for failures.
*   **Security:** **Public Subnets**, which communicate directly with the internet, must be separated from **Private Subnets** for internal services and databases.
*   **Network Connectivity:** A **NAT Gateway** must be configured to allow resources in private subnets to communicate with the outside world (e.g., package repositories).
*   **Routing Policies:** Sophisticated **Route Tables** are needed to control the traffic flow for each subnet.

If you manage these components manually or with copy-pasted Terraform code for each environment (dev, staging, prod), you'll face problems like outages due to minor configuration differences or difficulty in applying common security policies universally. **Terraform modularization** is the clear solution to these issues. By encapsulating all the logic for creating a VPC into a single, independent 'module', you can configure your infrastructure by simply calling this module with the necessary parameters (e.g., VPC CIDR, number of subnets) for each environment.

This approach offers the following benefits:

1.  **Reusability:** A single, well-crafted VPC module can be used to quickly deploy consistent networks across multiple projects and environments.
2.  **Maintainability:** When the VPC network structure needs to be changed, you only need to modify the module code, and the changes can be applied to all environments using it at once.
3.  **Readability:** The root Terraform code becomes very concise, like `module "production_vpc" {...}`, making it easy to grasp the overall infrastructure architecture.

Now, let's define a production-grade VPC architecture and walk through the step-by-step process of implementing it as a reusable Terraform module.

## Core Architecture and Principles: Production VPC and Terraform Module Structure

The VPC we will build follows a standard production structure capable of supporting a typical 3-Tier architecture.

*   **VPC:** A private IP address space with a `/16` block.
*   **Availability Zones (AZs):** Resources distributed across at least two AZs.
*   **Public Subnets:** One per AZ. Connected to an Internet Gateway, allowing two-way communication with the internet. (e.g., Web Servers, Bastion Hosts, ALB/NLB).
*   **Private Subnets:** One per AZ. Only outbound communication to the internet is allowed through a NAT Gateway. (e.g., Application Servers, DBs).
*   **Internet Gateway (IGW):** Manages communication between the VPC and the internet.
*   **NAT Gateway:** One placed in the public subnet of each AZ. Serves as a gateway for resources in private subnets to access the internet. Created per AZ for high availability.
*   **Route Tables:** Separate route tables for public and private subnets to control traffic.

The directory structure for the Terraform module to implement this architecture is as follows:

```
.
├── main.tf         # Root file that calls the module to create the actual infrastructure
├── variables.tf    # Defines variables for the root module
├── terraform.tfvars  # Assigns actual values to variables (e.g., staging environment values)
└── modules/
    └── vpc/
        ├── main.tf         # Core resource definitions for the VPC module
        ├── variables.tf    # Defines input variables for the VPC module
        └── outputs.tf      # Defines the output values the module will return after creation
```

*   `modules/vpc/`: The reusable module responsible for creating the VPC.
*   Root directory (`.`): The top-level location of the project that 'calls' this module to create a VPC for a specific environment (e.g., 'staging').

This structure follows the Separation of Concerns principle, allowing for effective management of infrastructure code complexity.

## Deep Dive into Practical Code/Configuration

Let's now write the actual code to complete our VPC module.

### 1. Defining VPC Module Variables (`modules/vpc/variables.tf`)

For a module to be reusable, it must be able to receive configuration values from the outside. The `variables.tf` file acts as the specification for these input values.

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

### 2. Writing the Core VPC Module Logic (`modules/vpc/main.tf`)

This file contains all the AWS resource definitions that make up the VPC. The key is to use Terraform's built-in functions like `for_each` to dynamically create AZs and subnets.

```hcl
# modules/vpc/main.tf

# 1. Create VPC
resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# 2. Create Internet Gateway and attach to VPC
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# 3. Create Public Subnets (one per AZ)
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

# 4. Create Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  for_each   = aws_subnet.public
  depends_on = [aws_internet_gateway.this]
  vpc        = true
  
  tags = {
    Name = "${var.project_name}-nat-eip-${each.key}"
  }
}

# 5. Create NAT Gateway (one per Public Subnet in each AZ)
resource "aws_nat_gateway" "this" {
  for_each      = aws_subnet.public
  allocation_id = aws_eip.nat[each.key].id
  subnet_id     = each.value.id

  tags = {
    Name = "${var.project_name}-nat-gw-${each.value.availability_zone}"
  }
  depends_on = [aws_internet_gateway.this]
}

# 6. Create Private Subnets (one per AZ)
resource "aws_subnet" "private" {
  for_each          = { for i, cidr in var.private_subnet_cidr_blocks : i => cidr }
  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = var.availability_zones[each.key]

  tags = {
    Name = "${var.project_name}-private-subnet-${var.availability_zones[each.key]}"
  }
}

# 7. Create Public Route Table and set up IGW route
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

# 8. Create Private Route Tables and set up NAT Gateway routes
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

# 9. Associate subnets with route tables
resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  for_each       = aws_subnet.private
  subnet_id      = each.value.id
  # Associate with the Private Route Table in the same AZ as the Private Subnet
  route_table_id = aws_route_table.private[index(var.availability_zones, each.value.availability_zone)].id
}
```

### 3. Defining Module Outputs (`modules/vpc/outputs.tf`)

Important information, like the IDs of the resources created by the module, is needed when creating other resources (e.g., EC2 instances, RDS). You can expose these values to the outside world using `outputs.tf`.

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

### 4. Calling the Module from the Root Directory

Now it's time to deploy our well-crafted VPC module to an actual environment. Let's configure the files in the root directory.

#### Root Variable Definitions (`variables.tf`)

```hcl
# ./variables.tf

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}
```

#### Defining Staging Environment Values (`terraform.tfvars`)

```hcl
# ./terraform.tfvars

aws_region = "ap-northeast-2"
```

#### Root Module Configuration (`main.tf`)

In this file, we set up the `provider` and use a `module` block to call `modules/vpc`.

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

# Call the VPC module for the 'staging' environment
module "staging_vpc" {
  source = "./modules/vpc" # Module path

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

# Example of using module outputs in other resources
# e.g., Create a security group in the Staging VPC's private subnet
resource "aws_security_group" "rds_sg" {
  name        = "staging-rds-sg"
  description = "Allow inbound traffic for RDS"
  vpc_id      = module.staging_vpc.vpc_id # Using the module output!

  # ... security group rules
}
```

Now, by running `terraform init`, `terraform plan`, and `terraform apply` in your terminal, a high-availability VPC for the `staging` environment will be perfectly created through code. If you need a `production` environment, you just need to add a `module "production_vpc" {...}` block and change the parameters. This is the power of modularization.

## Optimization and Best Practices

Beyond just making the code work, let's look at some additional best practices for stable operation in a production environment.

### 1. Using a Remote State Backend

The `terraform.tfstate` file is a crucial file that records the current state of your infrastructure. By default, it's created locally, but if you're collaborating with team members or running it in a CI/CD pipeline, you must store it in a **remote backend**. The standard practice is to use a combination of AWS S3 and DynamoDB to implement state file storage and locking.

```hcl
# backend.tf (add to the root directory)

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

### 2. Variable Validation

To prevent users of the module from entering incorrect values, you can add `validation` rules within the `variable` block. For example, you can verify that the number of subnets matches the number of availability zones.

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

### 3. Module Versioning

When sharing modules across a team or organization, it's a good practice to use a Git repository and specify versions using **tags**. This prevents changes to the module from having unintended impacts on other projects.

```hcl
# Example of calling a versioned module in the root main.tf

module "production_vpc" {
  # Use a Git address instead of source = "./modules/vpc"
  source = "git::https://github.com/my-org/terraform-aws-vpc.git?ref=v1.2.0"

  # ... variables
}
```

## Conclusion

So far, we have walked through the entire process of building a reusable and scalable **Terraform module** for the VPC, the core of AWS infrastructure. We've seen through practical code how to solve the inefficiency and risks of manual setup using the powerful paradigms of IaC and modularization.

The VPC module we covered today is just the beginning. By applying the same principles, you can create modules for various infrastructure components like Security Groups, EC2 Auto Scaling Groups, RDS databases, and EKS clusters. When these modules come together to form a well-designed 'infrastructure library', you will be able to provision infrastructure for applications with any complex requirements in a fast, stable, and consistent manner. Infrastructure will no longer be a bottleneck but a solid foundation that accelerates the speed of your business.

### References
- [Terraform Modules Documentation](https://developer.hashicorp.com/terraform/language/modules "Terraform Modules Documentation"){:target="_blank"}
- [Terraform AWS Provider - VPC Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc "Terraform AWS VPC Resource Documentation"){:target="_blank"}
- [Terraform S3 Backend Documentation](https://developer.hashicorp.com/terraform/language/settings/backends/s3 "Terraform S3 Backend Documentation"){:target="_blank"}
- [What is Amazon VPC?](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html "What is Amazon VPC?"){:target="_blank"}