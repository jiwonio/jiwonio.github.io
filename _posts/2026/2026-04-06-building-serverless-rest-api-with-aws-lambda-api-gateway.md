---
layout: post
title: AWS Lambda와 API Gateway를 활용한 고성능 서버리스 REST API 구축 A to Z
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
description: 전통적인 서버 관리의 복잡성 없이, AWS Lambda와 API Gateway를 사용하여 확장 가능하고 비용 효율적인 고성능
  서버리스 REST API를 구축하는 실전 가이드입니다. Python 기반 실습 코드와 AWS SAM 템플릿, 성능 최적화 팁까지 모든 것을 다룹니다.
image: /uploads/building-serverless-rest-api-with-aws-lambda-api-gateway/thumbnail.webp
lang: ko
translation_key: building-serverless-rest-api-with-aws-lambda-api-gateway
---
전통적인 웹 애플리케이션 개발에서 서버 프로비저닝, 스케일링, 패치 및 유지보수는 개발자의 생산성을 저해하는 주요 요인 중 하나였습니다. 트래픽이 급증할 때마다 수동으로 서버를 증설하거나, 반대로 유휴 상태의 서버 비용을 그대로 지불해야 하는 비효율을 감수해야만 했죠. **AWS Lambda**와 **API Gateway**를 필두로 한 서버리스(Serverless) 아키텍처는 이러한 패러다임을 근본적으로 바꾸었습니다.

서버리스 컴퓨팅은 개발자가 서버를 직접 관리할 필요 없이 비즈니스 로직에만 집중할 수 있게 해주는 클라우드 컴퓨팅 모델입니다. 코드는 이벤트에 의해 트리거될 때만 실행되며, 사용한 만큼만 비용을 지불하므로 매우 경제적입니다. 특히, HTTP 요청을 처리하는 **REST API**를 구축할 때 **API Gateway**와 **Lambda**의 조합은 엄청난 시너지를 발휘하여, 자동 확장성과 고가용성을 기본으로 갖춘 강력한 백엔드를 손쉽게 구현할 수 있게 합니다. 이 글에서는 숙련된 엔지니어를 위해 이론을 넘어, 실무에서 바로 적용 가능한 서버리스 REST API 구축의 모든 과정을 심도 있게 다룹니다.

<!--more-->
![AWS Lambda와 API Gateway를 활용한 고성능 서버리스 REST API 구축 A to Z](/uploads/building-serverless-rest-api-with-aws-lambda-api-gateway/thumbnail.webp "AWS Lambda와 API Gateway를 활용한 고성능 서버리스 REST API 구축 A to Z")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 서버리스 API의 핵심 아키텍처 및 원리

서버리스 REST API의 중심에는 **AWS API Gateway**와 **AWS Lambda**가 있습니다. 이 둘의 상호작용을 이해하는 것이 전체 아키텍처 파악의 핵심입니다.

-   **AWS API Gateway**: 클라이언트(웹, 모바일 앱 등)로부터 들어오는 모든 HTTP 요청을 받는 '관문(Gateway)' 역할을 수행합니다. API Gateway는 요청 라우팅, 인증 및 권한 부여, 요청/응답 변환, 속도 제한(Throttling), 캐싱 등 API 관리에 필요한 다양한 기능을 제공합니다.
-   **AWS Lambda**: 실제 비즈니스 로직을 수행하는 컴퓨팅 서비스입니다. API Gateway로부터 전달받은 요청(이벤트)을 처리하고 그 결과를 다시 API Gateway로 반환합니다. Lambda 함수는 격리된 컨테이너 환경에서 실행되며, 요청 수에 따라 AWS가 자동으로 스케일 인/아웃을 관리합니다.

### 요청 처리 흐름

1.  **클라이언트 요청**: 사용자가 웹 브라우저나 모바일 앱에서 API 엔드포인트(예: `https://api.example.com/posts`)로 HTTP 요청(GET, POST 등)을 보냅니다.
2.  **API Gateway 수신**: API Gateway가 해당 요청을 수신합니다. 설정된 라우팅 규칙에 따라 어떤 Lambda 함수를 호출할지 결정합니다. 이 과정에서 필요한 경우 API 키 검증이나 IAM 권한 확인, JWT 토큰 검증 등을 수행할 수 있습니다.
3.  **Lambda 함수 트리거**: API Gateway는 HTTP 요청 정보를 JSON 형태의 '이벤트' 객체로 변환하여 대상 Lambda 함수를 비동기적으로 호출(invoke)합니다.
4.  **비즈니스 로직 실행**: Lambda 함수는 전달받은 이벤트 객체를 파싱하여 요청 파라미터, 헤더, 본문 등을 추출하고 정의된 비즈니스 로직(예: 데이터베이스 조회, 데이터 가공)을 실행합니다.
5.  **응답 반환**: 로직 실행이 완료되면, Lambda 함수는 API Gateway가 이해할 수 있는 특정 JSON 형식에 맞춰 HTTP 상태 코드, 헤더, 본문을 담아 응답을 반환합니다.
6.  **클라이언트 응답**: API Gateway는 Lambda로부터 받은 응답을 실제 HTTP 응답으로 변환하여 최종적으로 클라이언트에게 전송합니다.

이 구조의 가장 큰 장점은 각 구성 요소가 독립적으로 확장되고 관리된다는 점입니다. 트래픽이 0일 때는 비용이 거의 발생하지 않다가, 초당 수천 개의 요청이 몰려와도 AWS가 자동으로 Lambda 실행 환경을 확장하여 안정적으로 요청을 처리합니다.

## 실무 적용: AWS SAM을 활용한 IaC 기반 API 구축

콘솔에서 수동으로 Lambda 함수와 API Gateway를 설정하는 것은 간단한 테스트에는 유용하지만, 프로덕션 환경에서는 재현성, 버전 관리, 협업의 어려움이라는 명백한 한계가 있습니다. 따라서 인프라를 코드로 관리하는 **IaC (Infrastructure as Code)** 접근 방식이 필수적이며, AWS에서는 이를 위해 **SAM (Serverless Application Model)**을 제공합니다. SAM은 CloudFormation을 기반으로 서버리스 애플리케이션 정의를 단순화한 오픈소스 프레임워크입니다.

### 1. 프로젝트 구조

먼저, 다음과 같은 기본 프로젝트 구조를 생성합니다.

```
sam-rest-api-project/
├── src/
│   ├── __init__.py
│   ├── app.py          # Lambda 핸들러 로직
│   └── requirements.txt  # Python 의존성
└── template.yaml       # SAM 템플릿 파일
```

### 2. AWS SAM 템플릿 (`template.yaml`) 작성

`template.yaml` 파일은 우리 서버리스 애플리케이션의 모든 리소스(Lambda 함수, API Gateway, IAM 역할 등)를 정의합니다.

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
  #  Lambda 함수 정의
  # ------------------------------------------------------------#
  MyApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: app.lambda_handler
      Policies:
        # 데이터베이스 접근 등 필요한 IAM 정책을 여기에 추가
        - AmazonDynamoDBReadOnlyAccess
      Events:
        # API Gateway와의 연동을 정의하는 부분
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
  #  API Gateway 정의 (암시적으로 생성되지만 명시적 정의도 가능)
  # ------------------------------------------------------------#
  # AWS::Serverless::Function의 Events 속성에서 'Api' 타입을 사용하면
  # SAM이 자동으로 API Gateway를 생성하고 Lambda와 통합해줍니다.
  # 더 복잡한 설정(CORS, Authorizers 등)이 필요하면
  # AWS::Serverless::Api 리소스를 명시적으로 정의할 수 있습니다.

Outputs:
  MyApiEndpoint:
    Description: "API Gateway endpoint URL for Prod stage"
    Value: !Sub "https://execute-api.${AWS::Region}.amazonaws.com/Prod/"
```

**핵심 포인트:**

*   `Transform: AWS::Serverless-2016-10-31`: 이 파일이 SAM 템플릿임을 명시합니다.
*   `Resources.MyApiFunction`: `AWS::Serverless::Function` 타입으로 Lambda 함수를 정의합니다.
*   `CodeUri`: Lambda 함수의 소스 코드가 위치한 경로를 지정합니다.
*   `Handler`: 요청이 들어왔을 때 실행될 함수를 `파일이름.함수이름` 형식으로 지정합니다.
*   `Events`: 이 함수를 트리거할 이벤트를 정의합니다. `Type: Api`는 API Gateway 이벤트를 의미하며, `Path`와 `Method`로 특정 엔드포인트와 HTTP 메서드를 Lambda 함수와 연결합니다.

### 3. Lambda 핸들러 코드 (`src/app.py`) 작성

이제 실제 비즈니스 로직을 담을 Python 코드를 작성합니다.

```python
import json
import boto3
from decimal import Decimal

# DynamoDB Decimal 타입 JSON 직렬화를 위한 Helper 클래스
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Posts') # 실제 DynamoDB 테이블 이름

def lambda_handler(event, context):
    """
    API Gateway 프록시 통합을 위한 메인 핸들러
    """
    print(f"Received event: {json.dumps(event)}")
    
    http_method = event.get('httpMethod')
    path = event.get('path')
    
    try:
        if http_method == 'GET' and '/posts/' in path:
            # 단일 게시물 조회: /posts/{postId}
            post_id = event['pathParameters']['postId']
            response = table.get_item(Key={'postId': post_id})
            item = response.get('Item')
            if not item:
                return create_response(404, {'message': 'Post not found'})
            return create_response(200, item)
            
        elif http_method == 'GET' and path == '/posts':
            # 전체 게시물 목록 조회
            response = table.scan()
            return create_response(200, response.get('Items', []))

        elif http_method == 'POST' and path == '/posts':
            # 새 게시물 생성
            body = json.loads(event.get('body', '{}'))
            # 실제로는 입력값 검증(validation) 로직이 필수입니다.
            table.put_item(Item=body)
            return create_response(201, {'message': 'Post created successfully', 'item': body})
            
        else:
            return create_response(400, {'message': 'Unsupported route or method'})

    except Exception as e:
        print(f"Error: {e}")
        return create_response(500, {'message': 'Internal server error'})


def create_response(status_code, body):
    """
    API Gateway가 요구하는 형식으로 응답 객체를 생성하는 헬퍼 함수
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*' # CORS 설정
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

```

### 4. 빌드 및 배포

SAM CLI를 사용하여 애플리케이션을 빌드하고 AWS에 배포합니다.

```bash
# 1. 의존성 패키지 설치 및 빌드
# requirements.txt에 명시된 라이브러리를 코드와 함께 패키징합니다.
sam build

# 2. 패키징된 애플리케이션 배포
# --guided 옵션을 사용하면 최초 배포 시 필요한 설정(스택 이름, 리전 등)을 안내해줍니다.
sam deploy --guided
```

배포가 성공적으로 완료되면 `Outputs`에 정의한 API 엔드포인트 URL이 출력됩니다. 이제 `curl`이나 Postman 같은 도구를 사용하여 API를 테스트할 수 있습니다.

## 성능 최적화 및 Best Practices

프로덕션 환경에서 서버리스 API를 안정적으로 운영하기 위해서는 몇 가지 주요 사항을 반드시 고려해야 합니다.

### 1. 콜드 스타트 (Cold Start) 완화

Lambda 함수가 한동안 호출되지 않으면 AWS는 자원 효율을 위해 해당 실행 환경(컨테이너)을 종료합니다. 이후 다시 호출이 발생하면 새로운 실행 환경을 준비(코드 다운로드, 런타임 초기화, 전역 변수 초기화 등)하는 데 추가 시간이 소요되는데, 이를 **콜드 스타트**라고 합니다.

*   **Provisioned Concurrency (프로비저닝된 동시성)**: 특정 수의 Lambda 실행 환경을 항상 '웜(warm)' 상태로 유지하여 콜드 스타트를 제거하는 기능입니다. 응답 지연 시간에 매우 민감한 핵심 API에 적용할 수 있지만 추가 비용이 발생합니다.
*   **Lambda SnapStart (Java 전용)**: Java 런타임의 경우, 초기화가 완료된 실행 환경의 스냅샷을 생성해 두었다가 호출 시 스냅샷에서 빠르게 복원하여 시작 시간을 최대 10배 단축하는 기능입니다.
*   **코드 최적화**: 함수 패키지 크기를 최소화하고, 핸들러 함수 외부(전역 스코프)에서 라이브러리 임포트나 데이터베이스 커넥션 초기화 등 시간 소모적인 작업을 수행하여 콜드 스타트 시 한 번만 실행되도록 구성합니다.

### 2. 데이터베이스 커넥션 관리

서버리스 환경의 가장 큰 함정 중 하나는 데이터베이스 커넥션 관리입니다. Lambda는 호출마다 새로운 실행 환경이 생성될 수 있으므로, 매번 새로운 DB 커넥션을 맺는 코드는 DB에 엄청난 부하를 주거나 커넥션 제한을 초과하게 만들 수 있습니다.

*   **핸들러 외부에서 커넥션 초기화**: DB 커넥션 객체를 전역 변수로 선언하여 Lambda 실행 환경이 재사용될 때 기존 커넥션을 계속 사용하도록 합니다.
*   **RDS Proxy 사용**: Amazon RDS를 사용한다면 **RDS Proxy**를 사용하는 것이 가장 이상적인 해결책입니다. RDS Proxy는 Lambda 함수와 데이터베이스 사이에 위치하여 커넥션 풀을 효율적으로 관리하고 공유해주므로, Lambda의 동시성 확장에도 안전하게 대응할 수 있습니다.

### 3. 보안: 최소 권한 원칙 (Principle of Least Privilege)

Lambda 함수에 할당되는 IAM 실행 역할(Execution Role)은 반드시 **최소한의 권한**만 가져야 합니다. 예를 들어, DynamoDB에서 특정 테이블을 읽기만 하는 함수에게 `dynamodb:*` 같은 와일드카드 권한을 부여해서는 안 됩니다. `template.yaml`의 `Policies` 섹션에서 필요한 특정 작업(예: `dynamodb:GetItem`, `dynamodb:Scan`)에 대한 권한만 명시적으로 부여해야 합니다.

### 4. 모니터링 및 로깅

*   **Amazon CloudWatch**: Lambda 함수는 실행 로그를 자동으로 CloudWatch Logs에 전송합니다. `print()` 문이나 로깅 라이브러리를 통해 출력된 모든 내용은 이곳에 기록되므로, 에러 디버깅과 동작 분석에 필수적입니다. 또한 CloudWatch Metrics를 통해 호출 수, 에러율, 실행 시간 등의 지표를 모니터링하고 알람을 설정할 수 있습니다.
*   **AWS X-Ray**: 분산 추적 시스템으로, API Gateway에서 시작하여 Lambda 함수, 그리고 그 함수가 호출하는 다른 AWS 서비스(예: DynamoDB, S3)까지 요청의 전체 흐름을 시각화하고 성능 병목 구간을 식별하는 데 매우 유용합니다.

## 결론

AWS Lambda와 API Gateway를 기반으로 한 서버리스 아키텍처는 더 이상 미래의 기술이 아닌, 현대적인 웹 서비스를 구축하는 표준적인 방법론 중 하나로 자리 잡았습니다. 서버 관리의 부담을 덜고 오직 비즈니스 가치를 창출하는 코드에만 집중할 수 있게 해주며, 사용량 기반의 합리적인 비용 모델과 자동 확장성은 스타트업부터 대기업에 이르기까지 모든 규모의 조직에 매력적인 선택지입니다.

물론 콜드 스타트나 상태 관리의 어려움과 같은 서버리스 고유의 특성을 이해하고 극복하는 노력이 필요합니다. 하지만 오늘 살펴본 것처럼 AWS SAM과 같은 IaC 도구를 활용하고, 데이터베이스 커넥션 관리, 보안, 모니터링과 같은 Best Practice를 잘 따른다면, 그 어떤 아키텍처보다 견고하고 효율적인 고성능 REST API를 성공적으로 구축하고 운영할 수 있을 것입니다.

### 참고문헌
- [AWS Lambda 개발자 안내서](https://docs.aws.amazon.com/ko_kr/lambda/latest/dg/welcome.html "AWS Lambda 공식 문서"){:target="_blank"}
- [Amazon API Gateway 개발자 안내서](https://docs.aws.amazon.com/ko_kr/apigateway/latest/developerguide/welcome.html "Amazon API Gateway 공식 문서"){:target="_blank"}
- [AWS SAM (서버리스 애플리케이션 모델) 개발자 안내서](https://docs.aws.amazon.com/ko_kr/serverless-application-model/latest/developerguide/what-is-sam.html "AWS SAM 공식 문서"){:target="_blank"}
- [AWS Lambda 함수의 데이터베이스 연결 관리](https://aws.amazon.com/ko/blogs/compute/database-connection-management-for-serverless-applications/ "AWS 공식 블로그"){:target="_blank"}