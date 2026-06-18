---
layout: post
title: 从入门到精通：使用 AWS Lambda 与 API Gateway 构建高性能无服务器 REST API
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
description: 本实践指南将指导您如何使用 AWS Lambda 和 API Gateway 构建可扩展、经济高效的高性能无服务器 REST API，摆脱传统服务器管理的复杂性。内容涵盖基于
  Python 的实践代码、AWS SAM 模板以及性能优化技巧。
image: /uploads/building-serverless-rest-api-with-aws-lambda-api-gateway/thumbnail.webp
lang: zh
translation_key: building-serverless-rest-api-with-aws-lambda-api-gateway
permalink: /zh/posts/building-serverless-rest-api-with-aws-lambda-api-gateway/
---
在传统的 Web 应用程序开发中，服务器的预置、扩展、补丁和维护是影响开发者生产力的主要障碍之一。每当流量激增时，开发者不得不手动增加服务器，反之，在服务器空闲时，又不得不为空置资源支付成本，效率极低。以 **AWS Lambda** 和 **API Gateway** 为代表的无服务器（Serverless）架构从根本上改变了这一模式。

无服务器计算是一种云计算模型，它让开发者无需管理服务器，只需专注于业务逻辑。代码仅在事件触发时执行，并且按使用量付费，因此非常经济。特别是，在构建处理 HTTP 请求的 **REST API** 时，**API Gateway** 和 **Lambda** 的组合能发挥出巨大的协同效应，让您轻松实现一个具备自动扩展性和高可用性的强大后端。本文将面向经验丰富的工程师，超越理论，深入探讨在实际工作中构建无服务器 REST API 的全过程。

<!--more-->
![使用 AWS Lambda 和 API Gateway 构建高性能无服务器 REST API](/uploads/building-serverless-rest-api-with-aws-lambda-api-gateway/thumbnail.webp "使用 AWS Lambda 和 API Gateway 构建高性能无服务器 REST API")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI 生成的图像</small>
</p>
-----

## 无服务器 API 的核心架构与原理

无服务器 REST API 的核心是 **AWS API Gateway** 和 **AWS Lambda**。理解这两者之间的交互是掌握整个架构的关键。

-   **AWS API Gateway**：扮演着接收所有来自客户端（Web、移动应用等）HTTP 请求的“网关”角色。API Gateway 提供请求路由、认证授权、请求/响应转换、速率限制（Throttling）、缓存等 API 管理所需的各种功能。
-   **AWS Lambda**：是执行实际业务逻辑的计算服务。它处理从 API Gateway 传来的请求（事件），并将结果返回给 API Gateway。Lambda 函数在隔离的容器环境中运行，AWS 会根据请求数量自动管理其伸缩。

### 请求处理流程

1.  **客户端请求**：用户通过网页浏览器或移动应用向 API 端点（例如 `https://api.example.com/posts`）发送 HTTP 请求（GET、POST 等）。
2.  **API Gateway 接收**：API Gateway 接收该请求，并根据配置的路由规则决定调用哪个 Lambda 函数。在此过程中，可以根据需要执行 API 密钥验证、IAM 权限检查或 JWT 令牌验证等。
3.  **触发 Lambda 函数**：API Gateway 将 HTTP 请求信息转换为 JSON 格式的“事件”对象，并异步调用（invoke）目标 Lambda 函数。
4.  **执行业务逻辑**：Lambda 函数解析传入的事件对象，提取请求参数、标头、正文等，并执行已定义的业务逻辑（例如，查询数据库、处理数据）。
5.  **返回响应**：逻辑执行完成后，Lambda 函数按照 API Gateway 能理解的特定 JSON 格式，将包含 HTTP 状态码、标头和正文的响应返回。
6.  **响应客户端**：API Gateway 将从 Lambda 收到的响应转换为实际的 HTTP 响应，并最终发送给客户端。

这种结构的最大优点是每个组件都可以独立扩展和管理。当没有流量时，几乎不产生任何费用；而当流量激增至每秒数千个请求时，AWS 会自动扩展 Lambda 执行环境，以稳定地处理请求。

## 实战应用：使用 AWS SAM 构建基于 IaC 的 API

虽然在控制台中手动配置 Lambda 函数和 API Gateway 对于简单测试很方便，但在生产环境中，这种方式在可复现性、版本控制和协作方面存在明显局限。因此，采用“基础设施即代码”（**IaC, Infrastructure as Code**）的方法至关重要。为此，AWS 提供了 **SAM（Serverless Application Model）**。SAM 是一个基于 CloudFormation 的开源框架，简化了无服务器应用程序的定义。

### 1. 项目结构

首先，创建如下的基本项目结构。

```
sam-rest-api-project/
├── src/
│   ├── __init__.py
│   ├── app.py          # Lambda 处理程序逻辑
│   └── requirements.txt  # Python 依赖项
└── template.yaml       # SAM 模板文件
```

### 2. 编写 AWS SAM 模板 (`template.yaml`)

`template.yaml` 文件定义了我们无服务器应用程序的所有资源（Lambda 函数、API Gateway、IAM 角色等）。

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
  #  定义 Lambda 函数
  # ------------------------------------------------------------#
  MyApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: app.lambda_handler
      Policies:
        # 在此处添加必要的 IAM 策略，例如数据库访问权限
        - AmazonDynamoDBReadOnlyAccess
      Events:
        # 定义与 API Gateway 的集成部分
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
  #  定义 API Gateway（可隐式创建，也可显式定义）
  # ------------------------------------------------------------#
  # 当在 AWS::Serverless::Function 的 Events 属性中使用 'Api' 类型时，
  # SAM 会自动创建 API Gateway 并与 Lambda 集成。
  # 如果需要更复杂的配置（如 CORS、授权方等），
  # 可以显式定义 AWS::Serverless::Api 资源。

Outputs:
  MyApiEndpoint:
    Description: "API Gateway endpoint URL for Prod stage"
    Value: !Sub "https://execute-api.${AWS::Region}.amazonaws.com/Prod/"
```

**核心要点:**

*   `Transform: AWS::Serverless-2016-10-31`: 声明此文件为 SAM 模板。
*   `Resources.MyApiFunction`: 使用 `AWS::Serverless::Function` 类型定义一个 Lambda 函数。
*   `CodeUri`: 指定 Lambda 函数源代码所在的路径。
*   `Handler`: 以 `文件名.函数名` 的格式指定请求到达时要执行的函数。
*   `Events`: 定义触发此函数的事件。`Type: Api` 表示 API Gateway 事件，通过 `Path` 和 `Method` 将特定的端点和 HTTP 方法与 Lambda 函数关联起来。

### 3. 编写 Lambda 处理程序代码 (`src/app.py`)

现在，我们来编写包含实际业务逻辑的 Python 代码。

```python
import json
import boto3
from decimal import Decimal

# 用于 DynamoDB Decimal 类型 JSON 序列化的辅助类
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Posts') # 实际的 DynamoDB 表名

def lambda_handler(event, context):
    """
    用于 API Gateway 代理集成的主处理程序
    """
    print(f"Received event: {json.dumps(event)}")
    
    http_method = event.get('httpMethod')
    path = event.get('path')
    
    try:
        if http_method == 'GET' and '/posts/' in path:
            # 查询单个帖子：/posts/{postId}
            post_id = event['pathParameters']['postId']
            response = table.get_item(Key={'postId': post_id})
            item = response.get('Item')
            if not item:
                return create_response(404, {'message': 'Post not found'})
            return create_response(200, item)
            
        elif http_method == 'GET' and path == '/posts':
            # 查询所有帖子列表
            response = table.scan()
            return create_response(200, response.get('Items', []))

        elif http_method == 'POST' and path == '/posts':
            # 创建新帖子
            body = json.loads(event.get('body', '{}'))
            # 实际上，输入验证逻辑是必不可少的。
            table.put_item(Item=body)
            return create_response(201, {'message': 'Post created successfully', 'item': body})
            
        else:
            return create_response(400, {'message': 'Unsupported route or method'})

    except Exception as e:
        print(f"Error: {e}")
        return create_response(500, {'message': 'Internal server error'})


def create_response(status_code, body):
    """
    创建 API Gateway 所需格式的响应对象的辅助函数
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*' # CORS 配置
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

```

### 4. 构建和部署

使用 SAM CLI 构建应用程序并将其部署到 AWS。

```bash
# 1. 安装依赖包并构建
# 将 requirements.txt 中指定的库与代码一起打包。
sam build

# 2. 部署打包好的应用程序
# 使用 --guided 选项，它会在首次部署时引导您完成必要的配置（如堆栈名称、区域等）。
sam deploy --guided
```

成功部署后，`Outputs` 中定义的 API 端点 URL 将会显示出来。现在，您可以使用 `curl` 或 Postman 等工具来测试 API。

## 性能优化与最佳实践

为了在生产环境中稳定地运行无服务器 API，必须考虑以下几个关键点。

### 1. 缓解冷启动（Cold Start）

当 Lambda 函数长时间未被调用时，为了提高资源效率，AWS 会终止其执行环境（容器）。当再次调用该函数时，准备新的执行环境（下载代码、初始化运行时、初始化全局变量等）会产生额外的延迟，这被称为**冷启动**。

*   **Provisioned Concurrency (预置并发)**：此功能可以使指定数量的 Lambda 执行环境始终保持“热”状态，从而消除冷启动。它适用于对响应延迟非常敏感的核心 API，但会产生额外费用。
*   **Lambda SnapStart (仅限 Java)**：对于 Java 运行时，此功能会创建一个初始化完成的执行环境快照。当函数被调用时，它能从快照中快速恢复，将启动时间最多缩短 10 倍。
*   **代码优化**：最小化函数包的大小，并在处理程序函数之外（全局作用域）执行耗时的操作，如导入库或初始化数据库连接，这样这些操作在冷启动时只执行一次。

### 2. 数据库连接管理

无服务器环境中的最大陷阱之一是数据库连接管理。由于每次调用 Lambda 都可能创建一个新的执行环境，如果每次都建立新的数据库连接，可能会给数据库带来巨大负载，甚至超出连接数限制。

*   **在处理程序外部初始化连接**：将数据库连接对象声明为全局变量，以便在 Lambda 执行环境被重用时，可以继续使用现有的连接。
*   **使用 RDS Proxy**：如果您使用 Amazon RDS，最理想的解决方案是使用 **RDS Proxy**。RDS Proxy 位于 Lambda 函数和数据库之间，能有效地管理和共享连接池，从而安全地应对 Lambda 的并发扩展。

### 3. 安全性：最小权限原则

分配给 Lambda 函数的 IAM 执行角色（Execution Role）必须遵循**最小权限原则**。例如，对于一个只从特定 DynamoDB 表中读取数据的函数，不应授予 `dynamodb:*` 这样的通配符权限。应在 `template.yaml` 的 `Policies` 部分明确授予所需的特定操作权限（例如 `dynamodb:GetItem`、`dynamodb:Scan`）。

### 4. 监控与日志记录

*   **Amazon CloudWatch**：Lambda 函数会自动将执行日志发送到 CloudWatch Logs。通过 `print()` 语句或日志库输出的所有内容都会记录在这里，这对于错误调试和行为分析至关重要。此外，您还可以通过 CloudWatch Metrics 监控调用次数、错误率、执行时间等指标，并设置告警。
*   **AWS X-Ray**：作为一个分布式追踪系统，X-Ray 非常有助于可视化从 API Gateway 开始，到 Lambda 函数，再到该函数调用的其他 AWS 服务（如 DynamoDB、S3）的整个请求流程，并识别性能瓶颈。

## 总结

基于 AWS Lambda 和 API Gateway 的无服务器架构已不再是未来的技术，而是构建现代 Web 服务的标准方法之一。它使开发者能够摆脱服务器管理的负担，专注于创造业务价值的代码。其基于使用量的合理成本模型和自动扩展能力，使其成为从初创公司到大型企业等各种规模组织都极具吸引力的选择。

当然，理解并克服无服务器架构固有的特性（如冷启动或状态管理的复杂性）是必要的。但正如我们今天所见，通过利用 AWS SAM 等 IaC 工具，并遵循数据库连接管理、安全性、监控等最佳实践，您将能够成功构建和运营比任何其他架构都更稳健、更高效的高性能 REST API。

### 参考资料
- [AWS Lambda 开发人员指南](https://docs.aws.amazon.com/ko_kr/lambda/latest/dg/welcome.html "AWS Lambda 官方文档"){:target="_blank"}
- [Amazon API Gateway 开发人员指南](https://docs.aws.amazon.com/ko_kr/apigateway/latest/developerguide/welcome.html "Amazon API Gateway 官方文档"){:target="_blank"}
- [AWS SAM（无服务器应用程序模型）开发人员指南](https://docs.aws.amazon.com/ko_kr/serverless-application-model/latest/developerguide/what-is-sam.html "AWS SAM 官方文档"){:target="_blank"}
- [管理 AWS Lambda 函数的数据库连接](https://aws.amazon.com/ko/blogs/compute/database-connection-management-for-serverless-applications/ "AWS 官方博客"){:target="_blank"}