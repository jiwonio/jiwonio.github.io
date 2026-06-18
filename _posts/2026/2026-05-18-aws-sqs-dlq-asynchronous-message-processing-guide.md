---
layout: post
title: AWS SQS와 데드 레터 큐(DLQ)를 활용한 안정적인 비동기 메시지 처리 시스템 구축 완벽 가이드
slug: aws-sqs-dlq-asynchronous-message-processing-guide
date: 2026-05-18 10:09:30 +0900
categories:
- Cloud
- Backend
tags:
- AWS
- SQS
- DLQ
- Message Queue
- Asynchronous
- Terraform
- Python
- Architecture
description: 프로덕션 환경에서 AWS SQS와 데드 레터 큐(DLQ)를 활용하여 안정적이고 확장 가능한 비동기 메시지 처리 시스템을 구축하는
  방법을 심층적으로 다룹니다. Python(boto3) 코드 예제, Terraform 설정, 성능 최적화, 모니터링 Best Practice를 포함한
  실무 가이드입니다.
image: /uploads/aws-sqs-dlq-asynchronous-message-processing-guide/thumbnail.webp
lang: ko
translation_key: aws-sqs-dlq-asynchronous-message-processing-guide
---
현대의 웹 애플리케이션은 사용자에게 빠른 응답 속도를 제공하면서도, 백그라운드에서는 이메일 발송, 데이터 집계, 이미지 처리 등 시간이 오래 걸리는 작업을 안정적으로 처리해야 하는 과제를 안고 있습니다. 사용자의 요청을 동기적으로 모두 처리하려 한다면, 응답 시간이 길어져 사용자 경험을 해치고 시스템 전체의 성능 저하로 이어질 수 있습니다. 이러한 문제를 해결하기 위한 핵심 아키텍처 패턴이 바로 **비동기 메시지 처리**입니다.

이 글에서는 AWS의 완전 관리형 메시지 큐 서비스인 **Amazon Simple Queue Service (SQS)**를 활용하여 이러한 비동기 처리 시스템을 구축하는 방법을 심층적으로 다룹니다. 특히, 예기치 못한 오류로 인해 처리되지 못한 메시지를 안전하게 격리하고 분석할 수 있는 **데드 레터 큐(Dead-Letter Queue, DLQ)**의 구성과 운영 전략에 초점을 맞춥니다. 단순히 SQS의 기본 개념을 넘어, 프로덕션 환경에서 즉시 적용 가능한 Terraform 코드, Python(boto3) 기반의 실제 처리 로직, 성능 최적화 기법 및 모니터링 Best Practice까지 총망라하여 안정적인 시스템을 구축하는 완벽한 가이드를 제공하겠습니다.

<!--more-->
![AWS SQS와 데드 레터 큐(DLQ)를 활용한 안정적인 비동기 메시지 처리 시스템 구축 완벽 가이드](/uploads/aws-sqs-dlq-asynchronous-message-processing-guide/thumbnail.webp "AWS SQS와 데드 레터 큐(DLQ)를 활용한 안정적인 비동기 메시지 처리 시스템 구축 완벽 가이드")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 1. 도입 배경 및 문제 정의: 왜 메시지 큐가 필요한가?

사용자 요청에 대한 응답으로 이메일을 발송하는 웹 애플리케이션을 가정해 보겠습니다.

**동기 처리 방식의 문제점:**
1.  **느린 응답 속도:** SMTP 서버와의 통신 지연이나 네트워크 문제 발생 시, 사용자는 이메일 발송이 완료될 때까지 계속 기다려야 합니다. 이는 매우 나쁜 사용자 경험을 초래합니다.
2.  **강한 결합(Tight Coupling):** 웹 서버와 이메일 발송 모듈이 직접적으로 연결되어 있습니다. 만약 이메일 발송 서버에 장애가 발생하면, 웹 서버의 회원가입 기능 전체가 마비될 수 있습니다.
3.  **확장성의 한계:** 이메일 발송 요청이 폭주할 경우, 웹 서버의 부하가 급증하여 전체 서비스가 불안정해질 수 있습니다. 이메일 발송 로직만을 독립적으로 확장하기 어렵습니다.

**비동기 메시지 처리와 SQS의 역할:**
이러한 문제를 해결하기 위해 웹 서버(Producer)와 이메일 발송 워커(Consumer) 사이에 **메시지 큐(Message Queue)**를 도입할 수 있습니다.

-   **Producer (생산자):** 웹 서버는 이메일 발송에 필요한 최소한의 정보(수신자 이메일, 제목, 내용 등)를 담은 **메시지**를 생성하여 SQS 큐에 넣고 즉시 사용자에게 '요청이 접수되었습니다'와 같은 빠른 응답을 보냅니다.
-   **Queue (큐):** SQS는 Producer가 보낸 메시지를 안전하고 안정적으로 저장합니다.
-   **Consumer (소비자):** 별도의 워커 프로세스는 큐를 주기적으로 확인하여 처리할 메시지가 있으면 가져와 실제 이메일 발송 작업을 수행합니다.

이 구조를 통해 웹 서버와 이메일 발송 로직이 **느슨하게 결합(Loose Coupling)**되어 서로의 장애에 영향을 받지 않게 되며, 각 컴포넌트를 독립적으로 확장할 수 있어 전체 시스템의 안정성과 확장성이 크게 향상됩니다.

## 2. 핵심 아키텍처 및 원리

안정적인 비동기 처리 시스템을 구축하기 위해 SQS의 핵심 개념과 특히 데드 레터 큐(DLQ)의 동작 원리를 정확히 이해해야 합니다.

### SQS 기본 구성 요소

| 용어                 | 설명                                                                                                                                                                                            |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **표준 큐 (Standard Queue)** | 기본 큐 유형. 최소 한 번 이상 전달(At-Least-Once Delivery)을 보장하며, 메시지 순서는 보장되지 않습니다. 최고의 처리량을 제공하여 대부분의 시나리오에 적합합니다.                                |
| **FIFO 큐**            | 선입선출(First-In, First-Out)을 보장하고, 정확히 한 번만 처리(Exactly-Once Processing)를 지원합니다. 처리량에 제한이 있어 순서 보장이 필수적인 경우에 사용합니다. (예: 금융 거래) |
| **가시성 제한 시간 (Visibility Timeout)** | Consumer가 큐에서 메시지를 수신하면, 이 메시지는 다른 Consumer에게 보이지 않게 됩니다. 이 숨겨진 상태를 유지하는 시간을 의미합니다. Consumer가 이 시간 내에 처리를 완료하고 메시지를 삭제하지 않으면, 메시지는 다시 큐에 나타나 다른 Consumer가 처리할 수 있게 됩니다. |
| **폴링 (Polling)**     | Consumer가 큐에 새 메시지가 있는지 확인하는 동작입니다. `Short Polling`과 `Long Polling` 두 가지 방식이 있습니다.                                                                                    |

### 데드 레터 큐 (Dead-Letter Queue, DLQ) 아키텍처

Consumer가 메시지를 처리하는 과정에서 반복적으로 실패하는 경우가 발생할 수 있습니다. 예를 들어, 잘못된 형식의 메시지, 버그로 인한 예외 발생, 외부 API의 일시적 장애 등이 원인일 수 있습니다. 이런 '독이 든 메시지(Poison Pill)'가 계속 큐에 남아있으면, Consumer는 동일한 메시지를 계속 가져와 처리하려 시도하며 리소스를 낭비하고 정상적인 다른 메시지들의 처리를 방해하게 됩니다.

이 문제를 해결하기 위해 **데드 레터 큐(DLQ)**를 사용합니다.

1.  **원본 큐 (Source Queue):** Producer가 메시지를 보내는 주 큐입니다.
2.  **재시도 정책 (Redrive Policy):** 원본 큐에 설정하는 정책입니다. 메시지 처리가 특정 횟수(`maxReceiveCount`) 이상 실패하면, 해당 메시지를 DLQ로 자동으로 이동시키도록 정의합니다.
3.  **데드 레터 큐 (DLQ):** 처리 실패한 메시지들이 최종적으로 모이는 별도의 SQS 큐입니다.

이 아키텍처를 통해 실패한 메시지를 원본 큐에서 즉시 격리하여 전체 시스템의 안정성을 확보하고, 개발자는 DLQ에 쌓인 메시지를 분석하여 문제의 원인을 파악하고 해결할 수 있습니다.

## 3. 실무 적용 코드/설정 딥다이브

이제 Terraform을 사용하여 SQS 큐와 DLQ 인프라를 코드로 정의하고, Python(boto3)을 이용해 Producer와 Consumer를 구현해 보겠습니다.

### 3.1. Terraform을 이용한 SQS 및 DLQ 프로비저닝

IaC(Infrastructure as Code) 도구인 Terraform을 사용하면 인프라를 재사용 가능하고 버전 관리가 가능한 코드로 관리할 수 있습니다.

먼저, 처리 실패한 메시지를 보관할 DLQ(`my-app-dlq`)를 정의합니다.

```terraform
# a_dlq.tf

resource "aws_sqs_queue" "my_app_dlq" {
  name = "my-app-production-dlq"

  # DLQ에 쌓인 메시지를 최대 14일간 보관
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
```

이제 원본 큐(`my-app-queue`)를 정의하고, 위에서 생성한 DLQ를 연결하는 재시도 정책(`redrive_policy`)을 설정합니다.

```terraform
# b_main_queue.tf

resource "aws_sqs_queue" "my_app_queue" {
  name = "my-app-production-queue"

  # 메시지 처리를 위한 가시성 제한 시간 (30초)
  visibility_timeout_seconds = 30

  # Long Polling 활성화 (20초)
  # Consumer가 메시지를 요청했을 때 큐가 비어있으면 최대 20초까지 대기
  receive_wait_time_seconds = 20

  # 재시도 정책 설정
  redrive_policy = jsonencode({
    # 실패한 메시지는 my_app_dlq.arn으로 지정된 DLQ로 이동
    deadLetterTargetArn = aws_sqs_queue.my_app_dlq.arn
    # Consumer가 메시지를 5번 수신(처리 시도)하고도 삭제되지 않으면 실패로 간주
    maxReceiveCount     = 5
  })

  tags = {
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
```

위 설정에서 `maxReceiveCount`를 5로 설정했기 때문에, Consumer가 어떤 메시지를 5번 가져가서 처리하려 했지만 `visibility_timeout_seconds` 내에 성공적으로 삭제하지 못하면, SQS는 해당 메시지를 자동으로 `my-app-production-dlq`로 이동시킵니다.

### 3.2. Python (boto3)을 이용한 Producer 구현

사용자 요청을 받아 SQS에 메시지를 보내는 Producer 코드입니다.

```python
# producer.py
import boto3
import json
import uuid

# SQS 클라이언트 생성
sqs = boto3.client('sqs', region_name='ap-northeast-2')

# Terraform에서 생성한 SQS 큐 URL
# 실제 환경에서는 환경 변수나 Parameter Store에서 가져오는 것을 권장합니다.
QUEUE_URL = 'https://sqs.ap-northeast-2.amazonaws.com/123456789012/my-app-production-queue'

def send_email_task(recipient_email, subject, body):
    """이메일 발송 작업을 SQS 큐에 추가합니다."""
    
    message_body = {
        'recipient_email': recipient_email,
        'subject': subject,
        'body': body
    }

    try:
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message_body),
            MessageAttributes={
                'type': {
                    'DataType': 'String',
                    'StringValue': 'email'
                }
            },
            # FIFO 큐 사용 시 필요한 파라미터. 표준 큐에서는 불필요.
            # MessageDeduplicationId=str(uuid.uuid4()),
            # MessageGroupId='email_group'
        )
        print(f"Message sent successfully. MessageId: {response['MessageId']}")
        return response['MessageId']
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

if __name__ == '__main__':
    # 정상적인 이메일 발송 작업 요청
    send_email_task(
        recipient_email='user1@example.com',
        subject='Welcome to our service!',
        body='Thank you for signing up.'
    )
    
    # [🚨 테스트용] 고의로 오류를 유발하는 잘못된 형식의 메시지 전송
    # 이 메시지는 Consumer에서 처리 실패 후最终적으로 DLQ로 이동하게 됩니다.
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody='{"invalid_json": "this will cause a parsing error"' # Missing closing brace
    )
    print("Sent a malformed message to test DLQ.")
```

### 3.3. Python (boto3)을 이용한 Consumer 구현

SQS 큐에서 메시지를 주기적으로 가져와 처리하는 Consumer(워커) 코드입니다.

```python
# consumer.py
import boto3
import json
import time

sqs = boto3.client('sqs', region_name='ap-northeast-2')
QUEUE_URL = 'https://sqs.ap-northeast-2.amazonaws.com/123456789012/my-app-production-queue'

def process_email_message(message):
    """실제 이메일 발송 로직을 수행합니다."""
    try:
        # [🚨 중요] 메시지 본문 파싱
        # 여기서 JSON 파싱 에러 등이 발생하면 예외 처리되어 메시지가 삭제되지 않음
        task_data = json.loads(message['Body'])
        
        recipient = task_data['recipient_email']
        subject = task_data['subject']
        
        print(f"Sending email to {recipient} with subject '{subject}'...")
        # 여기에 실제 이메일 발송 로직 (e.g., a call to AWS SES or an SMTP library)
        time.sleep(2) # 이메일 발송에 2초가 걸린다고 가정
        print("Email sent successfully.")

        return True # 처리 성공
    
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse message body: {message['Body']}. Error: {e}")
        return False # 처리 실패
    except KeyError as e:
        print(f"[ERROR] Missing key in message body: {e}. Body: {message['Body']}")
        return False # 처리 실패
    except Exception as e:
        print(f"An unexpected error occurred while sending email: {e}")
        return False # 처리 실패


def main_loop():
    """메인 워커 루프: SQS 큐를 계속 폴링하며 메시지를 처리합니다."""
    print("Worker started. Waiting for messages...")
    while True:
        try:
            # Long Polling을 사용하여 메시지를 수신합니다.
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=10, # 한 번에 최대 10개의 메시지를 가져옴
                WaitTimeSeconds=20, # Long Polling 대기 시간
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )

            if 'Messages' in response:
                messages = response['Messages']
                print(f"Received {len(messages)} messages.")
                
                for message in messages:
                    # 메시지 처리 시도
                    is_successful = process_email_message(message)
                    
                    # [🚨 매우 중요] 처리가 성공한 경우에만 큐에서 메시지를 삭제합니다.
                    if is_successful:
                        sqs.delete_message(
                            QueueUrl=QUEUE_URL,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        print(f"Message {message['MessageId']} deleted.")
            else:
                print("No messages in queue. Waiting...")

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")
            time.sleep(5) # 예기치 못한 에러 발생 시 잠시 대기 후 재시도

if __name__ == '__main__':
    main_loop()

```

위 Consumer 코드의 핵심은, **`process_email_message` 함수가 `True`를 반환할 때(즉, 처리가 성공했을 때)만 `sqs.delete_message`를 호출한다는 점**입니다. 만약 처리 중 예외가 발생하여 `False`를 반환하면 메시지는 삭제되지 않고, `visibility_timeout`이 지난 후 다시 큐에 나타나 다른 Consumer가 처리할 수 있게 됩니다. 이 과정이 `maxReceiveCount` 횟수만큼 반복되면 메시지는 DLQ로 이동합니다.

## 4. 성능 최적화 및 Best Practices

### 4.1. Long Polling 적극 활용
`receive_wait_time_seconds`를 1초 이상(최대 20초)으로 설정하여 **Long Polling**을 활성화하는 것은 필수입니다.
-   **비용 절감:** 큐가 비어있을 때 불필요한 `ReceiveMessage` API 호출(빈 응답)을 줄여 비용을 크게 절감할 수 있습니다.
-   **성능 향상:** 메시지가 큐에 도착하는 즉시 Consumer가 수신할 확률이 높아져 전체 처리 지연 시간을 줄입니다.

### 4.2. 배치(Batch) 작업으로 처리량 극대화
단일 메시지를 처리하는 `send_message`, `delete_message` 대신 배치 API를 사용하면 네트워크 오버헤드를 줄이고 처리량을 높일 수 있습니다.
-   `send_message_batch`: 최대 10개의 메시지를 한 번의 API 호출로 전송합니다.
-   `delete_message_batch`: 최대 10개의 메시지를 한 번의 API 호출로 삭제합니다.

대량의 메시지를 처리해야 하는 시스템에서는 배치 작업 사용 여부가 전체 성능에 큰 영향을 미칩니다.

### 4.3. Consumer의 멱등성(Idempotency) 보장
SQS 표준 큐는 '최소 한 번 이상' 전달을 보장하므로, 네트워크 문제 등으로 인해 드물게 동일한 메시지가 두 번 이상 전달될 수 있습니다. 따라서 Consumer 로직은 동일한 메시지를 여러 번 처리하더라도 결과가 항상 동일하도록, 즉 **멱등성을 갖도록 설계**해야 합니다.
-   **예시:** '주문 생성' 메시지를 처리한다면, DB에 insert 하기 전에 해당 `order_id`가 이미 존재하는지 확인하는 로직을 추가해야 합니다.

### 4.4. CloudWatch를 이용한 필수 모니터링 및 알람 설정
안정적인 운영을 위해 다음 CloudWatch 지표를 반드시 모니터링해야 합니다.

| 지표명                        | 의미 및 모니터링 목적                                                                                                        | 권장 알람 설정                                                                                                    |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `ApproximateAgeOfOldestMessage` (원본 큐) | 큐에 있는 가장 오래된 메시지의 연령. 이 값이 계속 증가하면 Consumer의 처리 속도가 Producer의 생성 속도를 따라가지 못하고 있다는 신호입니다. | 특정 임계값(예: 300초)을 초과하면 알람을 발생시켜 Consumer 확장 또는 성능 점검을 유도합니다. |
| `ApproximateNumberOfMessagesVisible` (DLQ) | **DLQ**에 쌓인 메시지 수. 이 값이 0보다 커지면 시스템에 처리하지 못하는 메시지가 발생했다는 의미이므로 즉시 확인이 필요합니다. | 1 이상일 때 즉시 개발팀/운영팀 Slack 채널 등으로 알람을 보내도록 설정합니다.                                      |

**[🚨 보안 주의]** 아래 코드의 Slack Webhook URL은 반드시 실제 값으로 교체해야 합니다.
```yaml
# 예시: Serverless Framework를 이용한 DLQ 알람 설정
functions:
  myConsumer:
    # ...
    alarms:
      - name: high-dlq-messages-alarm
        namespace: "AWS/SQS"
        metric: ApproximateNumberOfMessagesVisible
        threshold: 0
        statistic: Sum
        period: 60
        evaluationPeriods: 1
        comparisonOperator: GreaterThanThreshold
        # DLQ 이름으로 Dimension 설정
        dimensions:
          QueueName: my-app-production-dlq
        # 알람 발생 시 SNS 토픽으로 알림 전송
        actions:
          - arn:aws:sns:ap-northeast-2:123456789012:slack-notification-topic
```

### 4.5. DLQ 메시지 재처리(Redrive) 전략
DLQ에 쌓인 메시지는 버그 수정이나 의존성 서비스 복구 후 다시 처리해야 할 수 있습니다. AWS 콘솔에서는 'Start DLQ redrive' 기능을 제공하여 DLQ의 메시지를 원본 큐로 다시 보낼 수 있습니다. 이 프로세스를 자동화하거나 정기적으로 처리하는 스크립트를 마련해두는 것이 좋습니다.

## 5. 결론

AWS SQS와 데드 레터 큐(DLQ)를 활용하면, 동기 처리 방식의 한계를 극복하고 확장 가능하며 장애에 강한 **안정적인 비동기 메시지 처리 시스템**을 구축할 수 있습니다. 시스템의 각 컴포넌트를 분리(decoupling)함으로써, 한 부분의 장애가 전체 시스템의 중단으로 이어지는 것을 방지하고, 트래픽 변화에 유연하게 대처할 수 있는 탄력적인 아키텍처를 구현할 수 있습니다.

이 글에서 다룬 핵심 사항들을 다시 한번 정리하면 다음과 같습니다.
-   **느슨한 결합:** SQS를 통해 Producer와 Consumer를 분리하여 시스템의 안정성과 확장성을 확보합니다.
-   **실패 격리:** DLQ와 재시도 정책을 구성하여 처리 실패 메시지를 자동으로 격리하고, 시스템의 메인 흐름을 보호합니다.
-   **IaC 기반 관리:** Terraform을 사용하여 인프라를 코드로 관리함으로써 일관성과 재현성을 보장합니다.
-   **안정적인 Consumer 구현:** 메시지 처리 성공 시에만 큐에서 삭제하고, 예외 처리를 철저히 하여 메시지 유실을 방지합니다.
-   **성능 최적화와 모니터링:** Long Polling과 배치 처리를 통해 성능을 최적화하고, CloudWatch를 통해 큐의 상태를 지속적으로 모니터링하여 잠재적인 문제를 사전에 감지합니다.

단순히 기능을 구현하는 것을 넘어, 위와 같은 프로덕션 레벨의 고려사항들을 적용함으로써 어떠한 상황에서도 신뢰할 수 있는 백엔드 시스템을 만들어나갈 수 있을 것입니다.

### 참고문헌
- [AWS SQS 개발자 안내서 (공식 문서)](https://docs.aws.amazon.com/ko_kr/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html){:target="_blank"}
- [Amazon SQS 데드 레터 큐 사용 (공식 문서)](https://docs.aws.amazon.com/ko_kr/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html){:target="_blank"}
- [Boto3 SQS 클라이언트 문서](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html){:target="_blank"}
- [Terraform AWS SQS Queue 리소스 문서](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue){:target="_blank"}