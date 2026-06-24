---
layout: post
title: Building a High-Performance Serverless REST API with AWS Lambda and API Gateway
  - From A to Z
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
description: A practical guide to building a scalable, cost-effective, and high-performance
  serverless REST API using AWS Lambda and API Gateway, without the complexities of
  traditional server management. It covers everything from Python-based hands-on code
  and AWS SAM templates to performance optimization tips.
image: /uploads/building-serverless-rest-api-with-aws-lambda-api-gateway/thumbnail.webp
lang: en
translation_key: building-serverless-rest-api-with-aws-lambda-api-gateway
permalink: /en/posts/building-serverless-rest-api-with-aws-lambda-api-gateway/
post_type: deep-dive
---
In traditional web application development, server provisioning, scaling, patching, and maintenance have been major factors hindering developer productivity. Developers had to endure the inefficiency of manually adding servers whenever traffic surged or, conversely, paying for idle servers. The serverless architecture, led by **AWS Lambda** and **API Gateway**, has fundamentally changed this paradigm.

Serverless computing is a cloud computing model that allows developers to focus solely on business logic without needing to manage servers directly. Code runs only when triggered by an event, and you pay only for what you use, making it highly cost-effective. In particular, when building a **REST API** to handle HTTP requests, the combination of **API Gateway** and **Lambda** creates immense synergy, enabling the easy implementation of a powerful backend with built-in auto-scaling and high availability. This article moves beyond theory for experienced engineers, providing an in-depth look at the entire process of building a serverless REST API that can be immediately applied in practice.

<!--more-->
![Building a High-Performance Serverless REST API with AWS Lambda and API Gateway - From A to Z](/uploads/building-serverless-rest-api-with-aws-lambda-api-gateway/thumbnail.webp "Building a High-Performance Serverless REST API with AWS Lambda and API Gateway - From A to Z")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## Core Architecture and Principles of Serverless APIs

At the heart of a serverless REST API are **AWS API Gateway** and **AWS Lambda**. Understanding their interaction is key to grasping the entire architecture.

-   **AWS API Gateway**: Acts as the 'gateway' that receives all incoming HTTP requests from clients (web, mobile apps, etc.). API Gateway provides various features necessary for API management, such as request routing, authentication and authorization, request/response transformation, throttling, and caching.
-   **AWS Lambda**: The computing service that executes the actual business logic. It processes the request (event) received from API Gateway and returns the result back to API Gateway. Lambda functions run in an isolated container environment, and AWS automatically manages scaling in and out based on the number of requests.

### Request Processing Flow

1.  **Client Request**: A user sends an HTTP request (e.g., GET, POST) from a web browser or mobile app to an API endpoint (e.g., `https://api.example.com/posts`).
2.  **API Gateway Reception**: API Gateway receives the request. It determines which Lambda function to invoke based on configured routing rules. During this process, it can perform tasks like API key validation, IAM permission checks, or JWT token verification if necessary.
3.  **Lambda Function Trigger**: API Gateway transforms the HTTP request information into a JSON 'event' object and invokes the target Lambda function asynchronously.
4.  **Business Logic Execution**: The Lambda function parses the received event object to extract request parameters, headers, and the body, then executes the defined business logic (e.g., querying a database, processing data).
5.  **Response Return**: Once the logic execution is complete, the Lambda function returns a response in a specific JSON format that API Gateway understands, containing the HTTP status code, headers, and body.
6.  **Client Response**: API Gateway transforms the response received from Lambda into an actual HTTP response and sends it to the client.

The biggest advantage of this architecture is that each component is scaled and managed independently. When traffic is zero, there is almost no cost, but even if thousands of requests per second flood in, AWS automatically scales the Lambda execution environment to handle them reliably.

## Practical Application: Building an IaC-based API with AWS SAM

Manually configuring Lambda functions and API Gateway in the console is useful for simple tests, but it has clear limitations in a production environment, such as difficulties with reproducibility, version control, and collaboration. Therefore, an **IaC (Infrastructure as Code)** approach is essential. AWS provides the **SAM (Serverless Application Model)** for this purpose. SAM is an open-source framework based on CloudFormation that simplifies the definition of serverless applications.

### 1. Project Structure

First, let's create the following basic project structure.

```
sam-rest-api-project/
├── src/
│   ├── __init__.py
│   ├── app.py          # Lambda handler logic
│   └── requirements.txt  # Python dependencies
└── template.yaml       # SAM template file
```

### 2. Writing the AWS SAM Template (`template.yaml`)

The `template.yaml` file defines all the resources for our serverless application (Lambda function, API Gateway, IAM roles, etc.).

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
        # Add necessary IAM policies here, such as for database access
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
  #  API Gateway Definition (Implicitly created, but can be explicitly defined)
  # ------------------------------------------------------------#
  # When using the 'Api' type in the Events property of AWS::Serverless::Function,
  # SAM automatically creates an API Gateway and integrates it with Lambda.
  # For more complex configurations (e.g., CORS, Authorizers),
  # you can explicitly define an AWS::Serverless::Api resource.

Outputs:
  MyApiEndpoint:
    Description: "API Gateway endpoint URL for Prod stage"
    Value: !Sub "https://execute-api.${AWS::Region}.amazonaws.com/Prod/"
```

**Key Points:**

*   `Transform: AWS::Serverless-2016-10-31`: Specifies that this file is a SAM template.
*   `Resources.MyApiFunction`: Defines a Lambda function with the type `AWS::Serverless::Function`.
*   `CodeUri`: Specifies the path to the Lambda function's source code.
*   `Handler`: Specifies the function to be executed when a request is received, in the format `filename.function_name`.
*   `Events`: Defines the event that will trigger this function. `Type: Api` signifies an API Gateway event, linking the Lambda function to a specific endpoint and HTTP method via `Path` and `Method`.

### 3. Writing the Lambda Handler Code (`src/app.py`)

Now, let's write the Python code that will contain our business logic.

```python
import json
import boto3
from decimal import Decimal

# Helper class to serialize DynamoDB's Decimal type into JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Posts') # Your actual DynamoDB table name

def lambda_handler(event, context):
    """
    Main handler for API Gateway proxy integration
    """
    print(f"Received event: {json.dumps(event)}")
    
    http_method = event.get('httpMethod')
    path = event.get('path')
    
    try:
        if http_method == 'GET' and '/posts/' in path:
            # Get a single post: /posts/{postId}
            post_id = event['pathParameters']['postId']
            response = table.get_item(Key={'postId': post_id})
            item = response.get('Item')
            if not item:
                return create_response(404, {'message': 'Post not found'})
            return create_response(200, item)
            
        elif http_method == 'GET' and path == '/posts':
            # Get all posts
            response = table.scan()
            return create_response(200, response.get('Items', []))

        elif http_method == 'POST' and path == '/posts':
            # Create a new post
            body = json.loads(event.get('body', '{}'))
            # In a real application, input validation logic is essential.
            table.put_item(Item=body)
            return create_response(201, {'message': 'Post created successfully', 'item': body})
            
        else:
            return create_response(400, {'message': 'Unsupported route or method'})

    except Exception as e:
        print(f"Error: {e}")
        return create_response(500, {'message': 'Internal server error'})


def create_response(status_code, body):
    """
    Helper function to create a response object in the format API Gateway expects
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*' # CORS settings
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
```

### 4. Build and Deploy

We'll use the SAM CLI to build and deploy the application to AWS.

```bash
# 1. Install dependencies and build
# Packages libraries specified in requirements.txt with the code.
sam build

# 2. Deploy the packaged application
# The --guided option will prompt you for the necessary settings (stack name, region, etc.) on the first deployment.
sam deploy --guided
```

Once the deployment is successfully completed, the API endpoint URL defined in `Outputs` will be displayed. You can now test the API using tools like `curl` or Postman.

## Performance Optimization and Best Practices

To operate a serverless API reliably in a production environment, several key points must be considered.

### 1. Mitigating Cold Starts

If a Lambda function is not invoked for a while, AWS terminates its execution environment (container) for resource efficiency. When a subsequent invocation occurs, additional time is required to prepare a new environment (downloading code, initializing the runtime, initializing global variables, etc.). This is known as a **cold start**.

*   **Provisioned Concurrency**: A feature that keeps a specified number of Lambda execution environments in a 'warm' state, eliminating cold starts. It can be applied to critical APIs that are highly sensitive to response latency, but it incurs additional costs.
*   **Lambda SnapStart (for Java)**: For Java runtimes, this feature creates a snapshot of the initialized execution environment and restores from it upon invocation, reducing startup times by up to 10x.
*   **Code Optimization**: Minimize the function package size. Perform time-consuming tasks like importing libraries or initializing database connections outside the handler function (in the global scope) so they are executed only once during a cold start.

### 2. Database Connection Management

One of the biggest pitfalls in a serverless environment is database connection management. Since a new execution environment can be created for each Lambda invocation, code that establishes a new DB connection every time can put a huge load on the database or exceed connection limits.

*   **Initialize Connections Outside the Handler**: Declare the DB connection object as a global variable so that existing connections can be reused when the Lambda execution environment is reused.
*   **Use RDS Proxy**: If you are using Amazon RDS, the ideal solution is to use **RDS Proxy**. RDS Proxy sits between your Lambda functions and the database, efficiently managing and sharing a pool of connections, which allows it to safely handle Lambda's concurrent scaling.

### 3. Security: The Principle of Least Privilege

The IAM execution role assigned to a Lambda function must have only the **minimum necessary permissions**. For example, a function that only reads from a specific DynamoDB table should not be granted a wildcard permission like `dynamodb:*`. You should explicitly grant only the required specific actions (e.g., `dynamodb:GetItem`, `dynamodb:Scan`) in the `Policies` section of your `template.yaml`.

### 4. Monitoring and Logging

*   **Amazon CloudWatch**: Lambda functions automatically send execution logs to CloudWatch Logs. Everything output via `print()` statements or logging libraries is recorded here, making it essential for error debugging and behavior analysis. You can also monitor metrics such as invocation count, error rate, and execution duration through CloudWatch Metrics and set up alarms.
*   **AWS X-Ray**: A distributed tracing system that is extremely useful for visualizing the entire flow of a request, from API Gateway through the Lambda function to other AWS services it calls (e.g., DynamoDB, S3), and for identifying performance bottlenecks.

## Conclusion

A serverless architecture based on AWS Lambda and API Gateway is no longer a technology of the future but has become one of the standard methodologies for building modern web services. It relieves the burden of server management, allowing developers to focus solely on code that creates business value. Its usage-based, reasonable cost model and automatic scalability make it an attractive option for organizations of all sizes, from startups to large enterprises.

Of course, it requires an effort to understand and overcome the unique characteristics of serverless, such as cold starts and the challenges of state management. However, as we've seen today, by leveraging IaC tools like AWS SAM and following best practices for database connection management, security, and monitoring, you can successfully build and operate a high-performance REST API that is more robust and efficient than almost any other architecture.

### References
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/ko_kr/lambda/latest/dg/welcome.html "Official AWS Lambda Documentation"){:target="_blank"}
- [Amazon API Gateway Developer Guide](https://docs.aws.amazon.com/ko_kr/apigateway/latest/developerguide/welcome.html "Official Amazon API Gateway Documentation"){:target="_blank"}
- [AWS SAM (Serverless Application Model) Developer Guide](https://docs.aws.amazon.com/ko_kr/serverless-application-model/latest/developerguide/what-is-sam.html "Official AWS SAM Documentation"){:target="_blank"}
- [Database connection management for serverless applications](https://docs.aws.amazon.com/lambda/latest/dg/services-rds.html "Official AWS Blog"){:target="_blank"}