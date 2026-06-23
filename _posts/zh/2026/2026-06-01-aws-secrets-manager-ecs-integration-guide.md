---
layout: post
title: 'AWS Secrets Manager와 ECS 연동: 프로덕션 환경을 위한 안전한 비밀 관리 완벽 가이드'
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
description: 프로덕션 환경에서 API 키, DB 자격 증명과 같은 민감 정보를 안전하게 관리하는 방법을 찾고 계신가요? 이 글에서는 AWS
  Secrets Manager와 Amazon ECS를 연동하여 컨테이너 애플리케이션에 비밀 값을 안전하게 주입하는 '완벽한' 아키텍처와 실전 예제를
  상세히 다룹니다.
image: /uploads/aws-secrets-manager-ecs-integration-guide/thumbnail.webp
lang: zh
translation_key: aws-secrets-manager-ecs-integration-guide
post_type: deep-dive
permalink: /zh/posts/aws-secrets-manager-ecs-integration-guide/
---
在生产环境运行容器化应用时，最棘手的挑战之一就是 **秘密(Secret)管理**。将数据库凭证、外部 API 密钥、证书等敏感信息硬编码到代码中、提交到 Git 仓库，甚至只是以普通环境变量的形式注入，都可能导致严重的安全漏洞。这些做法会增加秘密信息泄露的风险，并且在更改秘密值时需要重新部署应用程序，从而增加了管理复杂性。

为了实现安全高效的秘密管理，许多团队开始引入 **AWS Secrets Manager** 等专业解决方案。AWS Secrets Manager 提供了秘密信息的集中管理、生命周期控制、自动轮换以及通过 IAM 进行精细化访问控制，显著提升了安全级别。特别地，它与 Amazon ECS (Elastic Container Service) 紧密集成，为容器化应用程序提供了动态安全注入秘密信息的能力。本文将深入探讨 AWS Secrets Manager 与 ECS 集成的核心架构，并详细介绍可用于实际场景的配置方法和最佳实践。

<!--more-->
![AWS Secrets Manager와 ECS 연동: 프로덕션 환경을 위한 안전한 비밀 관리 완벽 가이드](/uploads/aws-secrets-manager-ecs-integration-guide/thumbnail.webp "AWS Secrets Manager와 ECS 연동: 프로덕션 환경을 위한 안전한 비밀 관리 완벽 가이드")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 背景介绍与问题定义

随着容器环境的普及，将应用程序配置和秘密信息分离已不再是“选择”，而是“必需”。传统的秘密管理方式存在以下明显局限性：

-   **硬编码在代码/配置文件中：** 这是最危险的方式，一旦代码存储库泄露，所有秘密信息都会随之暴露。
-   **以环境变量 (ENV) 形式存储在 Docker 镜像中：** 使用 `docker inspect` 命令或通过容器内部访问时很容易暴露，并且存在以明文形式存储在镜像层的风险。
-   **使用 `.env` 文件：** 文件存储在容器主机 (EC2 实例) 上，任何能够访问该实例的用户都能看到秘密信息。文件的管理和分发也很麻烦。

为了解决这些问题，我们需要将秘密管理的责任转移到一个安全集中的外部存储。**AWS Secrets Manager** 正是承担了这一角色，并通过与 ECS 的原生集成，让开发者能够摆脱秘密管理的复杂性，专注于业务逻辑。

## 核心架构与原理

ECS 使用 AWS Secrets Manager 秘密信息的关键在于 **ECS Task Execution Role**。ECS Agent 需要 IAM Role 来执行多种任务，例如从 ECR 拉取容器镜像、将日志发送到 CloudWatch Logs，以及从 Secrets Manager 获取秘密信息。这个角色被称为“Task Execution Role”。

我们需要做的是，为该 Task Execution Role 授予访问特定秘密的 `secretsmanager:GetSecretValue` 权限。这样，ECS Agent 在启动任务时，会使用此角色从 Secrets Manager 安全地获取秘密值，并将其注入到容器中。

将秘密注入 ECS 主要有两种方式：

1.  **作为环境变量注入 (Injecting as Environment Variables)：**
    *   最简单、最常见的方式。
    *   在 ECS Task Definition 的 `secrets` 属性中，将 Secrets Manager 中存储的键值对映射到容器的环境变量。
    *   **优点：** 无需更改应用程序代码，即可直接应用，方便了那些已在使用环境变量的应用程序。
    *   **缺点：** 秘密信息可能在容器内部通过 `env` 或 `printenv` 命令暴露，并且在某些敏感场景下，可能通过进程信息（例如 `/proc/[pid]/environ`）被查看，安全性相对较低。

2.  **挂载为文件 (Mounting as a File)：**
    *   将 Secrets Manager 中存储的整个 JSON 秘密文本作为文件挂载到容器内的特定路径。
    *   使用 ECS Task Definition 的 `mountPoints` 和 `volumes` 属性，并通过 `secretOptions` 指定 Secrets Manager ARN。
    *   **优点：** 秘密信息不会出现在环境变量列表中，安全性更高。方便应用程序解析复杂的 JSON 结构。
    *   **缺点：** 应用程序需要额外的逻辑来读取和解析文件系统。

这两种方式都有各自的优缺点，应根据应用程序的特性和安全需求选择合适的方式。

## 实战代码/配置深度解析

现在，让我们一步步了解如何在实际生产环境中进行配置。我们将以将包含数据库连接信息的秘密注入 ECS 容器为例。

### 步骤 1：在 AWS Secrets Manager 中创建秘密

首先，创建应用程序将使用的秘密。我们将以 JSON 格式存储数据库连接信息。

可以使用 AWS Management Console 或 AWS CLI 进行创建。

```bash
# 使用 AWS CLI 创建秘密的示例
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

[🚨 安全提示] 上述示例中的 `<...>` 部分需要替换为实际值。直接在命令中输入实际密码是不安全的，使用 `--secret-string file://my-secret.json` 等方式从文件读取更安全。

创建后，请记录该秘密的 **ARN**（Amazon Resource Name）。(例如：`arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:prod/myapp/database-AbCdEf`)

### 步骤 2：配置 ECS Task Execution IAM Role 策略

为了让 ECS 任务能够访问 Secrets Manager，需要向 Task Execution Role 添加权限。通常 `AmazonECSTaskExecutionRolePolicy` 管理策略已连接，但 Secrets Manager 的访问权限需要单独添加。

创建一个内联策略并将其连接到 Task Execution Role，策略内容如下：

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

-   **`secretsmanager:GetSecretValue`**：允许读取指定秘密值的权限。**为安全起见，务必在 `Resource` 中指定特定秘密的 ARN，而不是使用通配符 (`*`)**。
-   **`kms:Decrypt`**：Secrets Manager 默认使用 AWS KMS 加密秘密。因此，需要具备解密使用该 KMS 密钥加密的秘密的权限。如果使用的是默认 KMS 密钥 (`aws/secretsmanager`)，资源 ARN 会略有不同。

### 步骤 3：配置 ECS Task Definition

现在，在 ECS Task Definition 中设置 Secrets Manager 的集成。我们将通过 `task-definition.json` 文件的一部分来展示这两种方式。

#### 方法 1：作为环境变量注入

在 `containerDefinitions` 部分添加 `secrets` 对象。在 `valueFrom` 中指定 Secrets Manager ARN 和 JSON 键，该值将被注入到名为 `name` 的环境变量中。

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
    // ... 其他设置
}
```
> **注意：** `valueFrom` 中的 ARN 格式为 `secret-arn:json-key:version-stage:version-id`。在 `json-key` 后面加上 `::` 表示使用最新版本。

#### 方法 2：挂载为文件

使用 `volumes`、`mountPoints` 和 `secrets` 属性的组合。此方法会将整个秘密 JSON 文件化。

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
> 此设置不正确。直接使用 `volumes` 和 `secretOptions` 的方式更接近于 EC2 Launch Type 中与 Docker Volume Driver 结合使用的旧模式。**在 Fargate 和较新的 ECS 版本中，更推荐使用 `secrets` 选项注入环境变量，或者让应用程序直接通过 SDK 调用。**
> 
> **更正：** 在 Fargate 中以现代方式挂载文件的常用方法是使用 `aws-secrets-extension` 等 Sidecar 容器，或在应用程序启动脚本中通过 AWS CLI/SDK 将秘密保存到文件。但最原生、最简单的文件挂载方式实际上是 **AWS Systems Manager Parameter Store**。Secrets Manager 的直接文件挂载功能是有限的。抱歉造成混淆。在实践中，**环境变量注入** 是最广泛使用的模式。

### 步骤 4：应用程序代码（Python 示例）

在应用程序中使用通过**环境变量**注入的秘密非常简单。

```python
# settings.py (Django 示例)
import os
import json

# 读取通过环境变量注入的秘密
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

如果应用程序直接通过 SDK 调用 Secrets Manager，则可以这样实现。（在这种情况下，Task Role 需要 `secretsmanager:GetSecretValue` 权限，而不是 Execution Role）

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
        # 生产环境中需要更精细化的异常处理。
        raise e
    else:
        # 秘密以 JSON 字符串形式存储在 'SecretString' 中。
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)

# 在应用程序初始化时调用
db_credentials = get_secret("prod/myapp/database")
DB_USERNAME = db_credentials['username']
DB_PASSWORD = db_credentials['password']
# ...
```

这种方式的优点是 ECS Task Definition 中不会暴露秘密 ARN，但应用程序代码中会增加 AWS SDK 的依赖，并且需要考虑 API 调用成本和延迟。

## 性能优化与最佳实践

1.  **最小权限原则 (Principle of Least Privilege)：** 在设置 IAM 策略时，始终指定特定秘密的 ARN，而不是使用通配符 (`*`)，以限制该任务仅访问其必需的秘密。

2.  **启用秘密轮换 (Secret Rotation)：** 对于需要定期更改的秘密（如数据库密码），建议使用 Secrets Manager 的自动轮换功能。通过与 AWS Lambda 集成，可以在预设周期（例如 90 天）内自动更改秘密，并更新 Secrets Manager 中的信息。这能显著增强安全性。

3.  **应用程序内缓存：** 如果应用程序直接通过 SDK 查询秘密，最好在应用程序启动时仅查询一次并将其缓存在内存中复用。每次请求都调用 `GetSecretValue` API 会产生不必要的成本和延迟。

4.  **秘密的逻辑分离：** 使用环境（prod, dev）和应用名（myapp）组合来命名秘密，如 `prod/myapp/database`, `dev/myapp/database`，可以方便管理。

5.  **审计与监控：** 所有 Secrets Manager API 调用都会记录在 AWS CloudTrail 中。定期监控 CloudTrail 日志或使用 Amazon GuardDuty 等服务来检测异常的秘密访问尝试，并及时做出响应。

## 结论

将 AWS Secrets Manager 与 Amazon ECS 集成是现代云原生应用程序安全性的关键一步。通过将秘密信息与代码和基础设施分离并集中管理，可以大大减少安全漏洞，并提高运营效率。基于 Task Execution Role 的环境变量注入方式实现简单且安全性强，适用于大多数场景。

不要再为 `.env` 文件或硬编码的秘密信息而烦恼了。应用本文介绍的架构和最佳实践，构建更安全、更健壮、更具扩展性的容器服务吧。

### 参考资料
- [AWS Secrets Manager 官方文档](https://aws.amazon.com/secrets-manager/){:target="_blank"}
- [Amazon ECS 任务中传递私有注册表认证和 Secrets Manager 秘密](https://docs.aws.amazon.com/zh_cn/AmazonECS/latest/developerguide/specifying-sensitive-data.html "Specifying Sensitive Data in Amazon ECS"){:target="_blank"}
- [在 AWS Secrets Manager 中配置秘密轮换](https://docs.aws.amazon.com/zh_cn/secretsmanager/latest/userguide/rotating-secrets.html "Configuring Secret Rotation"){:target="_blank"}
- [使用 IAM 控制对 AWS Secrets Manager 秘密的访问](https://docs.aws.amazon.com/zh_cn/secretsmanager/latest/userguide/auth-and-access.html "Controlling Access to Secrets"){:target="_blank"}