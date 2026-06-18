---
layout: post
title: Amazon EKS와 AWS Load Balancer Controller를 활용한 프로덕션 레벨 쿠버네티스 인그레스 완벽 구축
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
description: AWS EKS 환경에서 외부 트래픽을 효율적으로 관리하기 위한 'AWS Load Balancer Controller' 설치
  및 설정 방법을 심층적으로 다룹니다. 프로덕션 레벨의 쿠버네티스 인그레스(Ingress)를 구축하고, SSL/TLS 적용, 헬스 체크, 고급 라우팅
  등 실무 Best Practice를 완벽하게 마스터하세요.
image: /uploads/production-kubernetes-ingress-with-aws-eks-and-alb-controller/thumbnail.webp
---
Amazon EKS(Elastic Kubernetes Service)를 사용하여 쿠버네티스 클러스터를 운영할 때 가장 중요한 과제 중 하나는 외부 트래픽을 클러스터 내부의 서비스로 안정적이고 효율적으로 라우팅하는 것입니다. 쿠버네티스는 `NodePort`나 `LoadBalancer` 타입의 서비스를 제공하지만, 이는 프로덕션 환경의 복잡한 요구사항을 모두 충족시키기에는 한계가 명확합니다. 예를 들어, `LoadBalancer` 타입 서비스를 배포할 때마다 새로운 ELB(Elastic Load Balancer)가 생성되어 비용 부담이 커지고, 세밀한 L7 라우팅 규칙(경로 기반, 호스트 기반 라우팅)을 적용하기도 어렵습니다.

이러한 문제를 해결하기 위해 쿠버네티스는 **인그레스(Ingress)** 라는 오브젝트를 제공합니다. 인그레스는 클러스터 외부의 HTTP/HTTPS 요청을 클러스터 내부 서비스로 연결하는 규칙의 집합이며, 이 규칙을 실제로 이행하는 것이 바로 **인그레스 컨트롤러(Ingress Controller)** 입니다. 특히 AWS 환경에서는 **AWS Load Balancer Controller**가 EKS와 가장 완벽하게 통합되어 AWS의 Application Load Balancer(ALB)나 Network Load Balancer(NLB)를 네이티브하게 활용할 수 있게 해줍니다. 이 컨트롤러를 사용하면 단일 ALB를 통해 여러 서비스를 노출하고, SSL/TLS 인증서 관리, 고급 트래픽 라우팅, WAF 통합 등 강력한 기능을 쿠버네티스 네이티브 방식으로 선언할 수 있습니다.

본 포스트에서는 숙련된 엔지니어를 위해, 프로덕션 환경에서 **Amazon EKS와 AWS Load Balancer Controller를 연동하여 안정적이고 비용 효율적인 인그레스 시스템을 구축**하는 모든 과정을 A부터 Z까지 심도 있게 다룹니다. 단순히 컨트롤러를 설치하는 것을 넘어, IAM 역할 설정, 필수 어노테이션(Annotation)을 활용한 고급 설정, 그리고 실무에서 마주할 수 있는 문제에 대한 해결책과 Best Practice까지 상세하게 살펴보겠습니다.

<!--more-->
![Amazon EKS와 AWS Load Balancer Controller를 활용한 프로덕션 레벨 쿠버네티스 인그레스 완벽 구축](/uploads/production-kubernetes-ingress-with-aws-eks-and-alb-controller/thumbnail.webp "Amazon EKS와 AWS Load Balancer Controller를 활용한 프로덕션 레벨 쿠버네티스 인그레스 완벽 구축")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 도입 배경 및 문제 정의

쿠버네티스 클러스터에서 실행 중인 애플리케이션을 외부에 노출하는 기본적인 방법은 `Service` 오브젝트를 `LoadBalancer` 타입으로 설정하는 것입니다. 이 경우, 클라우드 제공업체(AWS, GCP 등)는 해당 서비스를 위해 외부 로드 밸런서를 프로비저닝합니다.

하지만 이 방식은 몇 가지 심각한 단점을 가집니다.

1.  **비용 문제:** `LoadBalancer` 타입의 `Service`가 하나 생성될 때마다 별도의 로드 밸런서(AWS의 경우 Classic 또는 Network Load Balancer)가 생성됩니다. 수십, 수백 개의 마이크로서비스를 운영하는 환경에서는 로드 밸런서 비용이 기하급수적으로 증가할 수 있습니다.
2.  **기능적 한계:** `Service` 타입의 로드 밸런서는 기본적으로 L4(Transport Layer) 수준에서 동작합니다. 따라서 호스트 이름이나 URL 경로에 따라 트래픽을 분기하는 L7(Application Layer) 라우팅, SSL/TLS Offloading, HTTP 헤더 기반 라우팅과 같은 고급 기능을 직접 지원하지 않습니다.
3.  **관리의 복잡성:** 각 서비스마다 외부 IP 주소와 DNS 레코드를 개별적으로 관리해야 하므로 운영 복잡성이 증가합니다.

**쿠버네티스 인그레스(Ingress)**는 이러한 문제를 해결하기 위해 설계된 API 오브젝트입니다. 인그레스는 L7 가상 호스팅 및 경로 기반 라우팅 규칙을 정의하며, 이러한 규칙을 실제로 수행하는 **인그레스 컨트롤러**가 단일 로드 밸런서를 공유하여 여러 백엔드 서비스로 트래픽을 전달합니다.

AWS 환경에서는 **AWS Load Balancer Controller**가 이 역할을 수행하며, AWS의 강력한 Application Load Balancer(ALB)와 직접 통합됩니다. 이를 통해 우리는 비용을 절감하고, AWS의 관리형 서비스를 최대한 활용하여 안정적이고 확장 가능한 아키텍처를 구축할 수 있습니다.

## 핵심 아키텍처 및 원리

AWS Load Balancer Controller는 쿠버네티스 클러스터 내에서 Pod 형태로 실행되는 컨트롤러입니다. 이 컨트롤러의 핵심 역할은 쿠버네티스 API 서버를 지속적으로 감시(`watch`)하다가 `Ingress` 오브젝트의 생성, 수정, 삭제 이벤트를 감지하고, 그에 맞춰 AWS ALB 리소스를 자동으로 생성 및 관리하는 것입니다.

전체적인 트래픽 흐름과 아키텍처는 다음과 같습니다.

1.  **사용자 요청:** 사용자가 웹 브라우저를 통해 `example.com`과 같은 도메인으로 요청을 보냅니다.
2.  **DNS 조회:** Route 53과 같은 DNS 서비스가 도메인 이름을 AWS Load Balancer Controller가 생성한 **ALB의 DNS 이름**으로 해석합니다.
3.  **ALB 수신:** 요청은 ALB에 도달합니다. ALB는 SSL/TLS Termination을 수행하고, 요청의 호스트 이름(`Host` 헤더)과 경로(`Path`)를 확인합니다.
4.  **라우팅 규칙 적용:** ALB는 인그레스 컨트롤러에 의해 설정된 리스너 규칙(Listener Rules)에 따라 요청을 적절한 **대상 그룹(Target Group)**으로 전달합니다.
5.  **대상 그룹 및 Pod:** 대상 그룹은 요청을 처리할 백엔드 Pod들의 IP 주소 목록을 가지고 있습니다. ALB는 이 중 하나의 Pod로 트래픽을 전달합니다. 이때 **Target Type** 설정(`ip` 또는 `instance`)에 따라 동작 방식이 달라집니다.
    *   `ip` 모드 (권장): ALB가 EKS Worker Node를 거치지 않고 Pod의 IP로 직접 트래픽을 라우팅합니다. 성능이 우수하고 Pod 레벨의 보안 그룹 적용이 가능합니다.
    *   `instance` 모드: ALB가 트래픽을 Node의 `NodePort`로 보내면, Node의 `kube-proxy`가 다시 해당 Pod로 트래픽을 전달합니다.
6.  **응답:** Pod가 요청을 처리한 후 응답을 반환하면, 트래픽은 역순으로 사용자에게 전달됩니다.

이 모든 과정에서 개발자는 단지 `Ingress` YAML 파일을 정의하고 `kubectl apply`를 실행하기만 하면 됩니다. AWS Load Balancer Controller가 나머지 복잡한 AWS 리소스(ALB, Target Group, Listener, Rules 등)의 생명 주기를 자동으로 관리해주는 것입니다.

## 실무 적용 코드/설정 딥다이브

이제 실제 EKS 클러스터에 AWS Load Balancer Controller를 설치하고, 샘플 애플리케이션에 대한 인그레스를 설정하는 과정을 단계별로 진행하겠습니다.

### 1단계: 사전 준비 사항

시작하기 전에 다음 도구들이 설치 및 구성되어 있어야 합니다.

*   AWS CLI: AWS 계정 접근을 위해 필요합니다.
*   `kubectl`: 쿠버네티스 클러스터와 상호작용하기 위해 필요합니다.
*   `eksctl`: EKS 클러스터를 쉽게 생성하고 관리하기 위한 공식 CLI 도구입니다.
*   `helm`: 쿠버네티스 패키지 매니저로, 컨트롤러 설치에 사용됩니다.

### 2단계: IAM OIDC 공급자 생성

컨트롤러가 AWS API를 호출하여 ALB를 관리하려면 IAM 권한이 필요합니다. 우리는 IAM 역할을 사용하고 쿠버네티스 서비스 어카운트와 연결(IRSA, IAM Roles for Service Accounts)하여 안전하게 권한을 부여할 것입니다. 이를 위해 먼저 클러스터에 IAM OIDC 자격 증명 공급자를 생성해야 합니다.

```bash
# <YOUR_CLUSTER_NAME>을 실제 EKS 클러스터 이름으로 변경하세요.
eksctl utils associate-iam-oidc-provider \
    --region=ap-northeast-2 \
    --cluster=<YOUR_CLUSTER_NAME> \
    --approve
```

### 3단계: 컨트롤러를 위한 IAM 정책 및 서비스 어카운트 생성

AWS Load Balancer Controller가 필요로 하는 권한을 정의한 IAM 정책을 다운로드하고 생성합니다.

```bash
# IAM 정책 다운로드
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json

# IAM 정책 생성
aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam-policy.json
```

이제 `eksctl`을 사용하여 IAM 정책이 연결된 쿠버네티스 서비스 어카운트를 생성합니다. 이 명령은 CloudFormation 스택을 통해 IAM 역할을 생성하고, 이를 쿠버네티스 서비스 어카운트와 연결해줍니다.

```bash
# <YOUR_AWS_ACCOUNT_ID>와 <YOUR_CLUSTER_NAME>을 실제 값으로 변경하세요.
eksctl create iamserviceaccount \
  --cluster=<YOUR_CLUSTER_NAME> \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name "AmazonEKSLoadBalancerControllerRole" \
  --attach-policy-arn=arn:aws:iam::<YOUR_AWS_ACCOUNT_ID>:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve
```

### 4단계: Helm을 이용한 AWS Load Balancer Controller 설치

Helm 차트를 사용하여 컨트롤러를 설치하는 것이 가장 간편하고 권장되는 방법입니다.

```bash
# Helm 리포지토리 추가
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks

# Helm 차트 설치
# [🚨 주의] clusterName, serviceAccount.name, serviceAccount.create 값을 반드시 확인하세요.
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=<YOUR_CLUSTER_NAME> \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=ap-northeast-2 \
  --set vpcId=<YOUR_VPC_ID>
```

설치가 완료되면 컨트롤러 Pod가 정상적으로 실행 중인지 확인합니다.

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

### 5단계: 샘플 애플리케이션 및 인그레스 배포

이제 테스트를 위한 간단한 웹 애플리케이션(예: `game-2048`)을 배포하고, `Ingress` 리소스를 생성하여 외부 트래픽을 연결해보겠습니다.

#### 5.1. 샘플 애플리케이션 배포

아래 내용으로 `deployment-2048.yaml` 파일을 작성합니다. 이 YAML은 Deployment와 `ClusterIP` 타입의 Service를 정의합니다.

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

파일을 클러스터에 적용합니다.

```bash
kubectl apply -f deployment-2048.yaml
```

#### 5.2. 인그레스 리소스 생성

이제 가장 중요한 `Ingress` 리소스를 정의합니다. 아래 `ingress-2048.yaml` 파일은 `game.your-domain.com`으로 들어오는 트래픽을 `service-2048`로 라우팅하고, AWS Certificate Manager(ACM)에 미리 발급받은 SSL 인증서를 사용하여 HTTPS를 적용하는 예시입니다.

```yaml
# ingress-2048.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-2048
  annotations:
    # [🔥 중요] Ingress Class를 'alb'로 지정하여 AWS Load Balancer Controller가 처리하도록 합니다.
    kubernetes.io/ingress.class: alb
    
    # [🔥 중요] ALB의 스킴을 지정합니다. 외부에 노출하려면 'internet-facing'을 사용합니다.
    alb.ingress.kubernetes.io/scheme: internet-facing
    
    # [🔥 중요] Target Type을 'ip'로 설정하는 것을 적극 권장합니다.
    alb.ingress.kubernetes.io/target-type: ip
    
    # [SSL/TLS] ACM에서 발급받은 인증서의 ARN을 지정합니다.
    alb.ingress.kubernetes.io/certificate-arn: <YOUR_ACM_CERTIFICATE_ARN>
    
    # [SSL/TLS] HTTP(80)와 HTTPS(443) 포트를 리스닝하도록 설정합니다.
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    
    # [SSL/TLS] HTTP로 들어온 모든 요청을 HTTPS로 리디렉션합니다.
    alb.ingress.kubernetes.io/actions.ssl-redirect: '{"Type": "redirect", "RedirectConfig": { "Protocol": "HTTPS", "Port": "443", "StatusCode": "HTTP_301"}}'
    
    # [Health Check] ALB가 Pod의 헬스 체크를 수행할 경로를 지정합니다.
    # alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  rules:
    - host: game.your-domain.com # [🚨 주의] 실제 소유한 도메인으로 변경하세요.
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

YAML 파일을 적용합니다.

```bash
kubectl apply -f ingress-2048.yaml
```

몇 분 후, `kubectl get ingress ingress-2048` 명령을 실행하면 `ADDRESS` 필드에 생성된 ALB의 DNS 주소가 나타납니다. 이 주소를 여러분의 도메인(`game.your-domain.com`)에 CNAME 레코드로 등록하면, 잠시 후 HTTPS를 통해 애플리케이션에 접속할 수 있습니다.

## 성능 최적화 및 Best Practices

프로덕션 환경에서 AWS Load Balancer Controller를 안정적으로 운영하기 위한 몇 가지 팁과 모범 사례입니다.

1.  **Target Type은 `ip` 모드를 사용하세요:** `ip` 모드는 Pod에 직접 트래픽을 전달하여 `kube-proxy`를 거치는 추가 홉(hop)을 제거하므로 네트워크 지연 시간을 줄이고 성능을 향상시킵니다. 또한 Pod에 직접 보안 그룹(Security Groups for Pods)을 적용할 수 있어 더욱 세분화된 네트워크 보안 정책 구현이 가능합니다.
2.  **Ingress Grouping으로 비용을 최적화하세요:** 여러 `Ingress` 리소스가 동일한 ALB를 공유하도록 그룹화할 수 있습니다. `alb.ingress.kubernetes.io/group.name` 어노테이션을 사용하여 여러 인그레스를 하나의 논리적 그룹으로 묶으면, 컨트롤러는 해당 그룹에 대해 단 하나의 ALB만 생성하여 비용을 크게 절감할 수 있습니다.
3.  **정확한 헬스 체크 경로를 설정하세요:** `alb.ingress.kubernetes.io/healthcheck-path` 어노테이션을 사용하여 애플리케이션의 상태를 정확하게 확인할 수 있는 API 엔드포인트(예: `/health`, `/status`)를 지정하세요. 이를 통해 비정상적인 Pod가 대상 그룹에서 신속하게 제외되어 서비스 안정성을 높일 수 있습니다.
4.  **Subnet Auto-discovery 태그를 활용하세요:** 컨트롤러는 기본적으로 특정 태그(`kubernetes.io/cluster/<cluster-name>: owned`와 `kubernetes.io/role/elb: 1` 또는 `kubernetes.io/role/internal-elb: 1`)가 지정된 서브넷에 ALB를 배포합니다. `eksctl`로 클러스터를 생성하면 이 태그들이 자동으로 Public 및 Private 서브넷에 적용됩니다. 인프라를 Terraform 등으로 직접 관리하는 경우, 이 태그들을 올바르게 설정해야 컨트롤러가 ALB를 배치할 서브넷을 정확히 찾을 수 있습니다.
5.  **컨트롤러 로그를 주기적으로 확인하세요:** 컨트롤러 Pod의 로그는 `Ingress` 설정 오류나 AWS API 호출 실패 등의 문제를 디버깅하는 데 매우 중요합니다. `kubectl logs -n kube-system deploy/aws-load-balancer-controller` 명령을 통해 로그를 확인하여 잠재적인 문제를 사전에 파악하고 해결할 수 있습니다.

## 결론

지금까지 Amazon EKS 환경에서 AWS Load Balancer Controller를 사용하여 프로덕션 레벨의 인그레스 시스템을 구축하는 방법을 상세히 알아보았습니다. 이 컨트롤러는 쿠버네티스의 선언적 API와 AWS의 강력한 ALB를 완벽하게 결합하여, 개발자와 운영자가 복잡한 AWS 인프라를 직접 관리할 필요 없이 YAML 파일만으로 정교한 L7 트래픽 라우팅을 구현할 수 있도록 해줍니다.

단순히 서비스를 외부에 노출하는 것을 넘어, **비용 최적화, SSL/TLS 자동화, 고급 라우팅, 그리고 AWS 생태계와의 긴밀한 통합**이라는 장점을 통해 마이크로서비스 아키텍처를 더욱 견고하고 확장 가능하게 만들어 줍니다. 본 가이드에서 다룬 설정과 Best Practice를 현업에 적용한다면, 여러분의 EKS 클러스터는 한 단계 더 높은 수준의 안정성과 효율성을 갖추게 될 것입니다.

### 참고문헌

*   [AWS Load Balancer Controller 공식 문서](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.7/ "AWS Load Balancer Controller Documentation"){:target="_blank"}
*   [Amazon EKS 모범 사례 가이드 - 네트워킹](https://aws.github.io/aws-eks-best-practices/networking/ingress/ "Amazon EKS Best Practices Guide for Networking"){:target="_blank"}
*   [AWS의 쿠버네티스 인그레스 컨트롤러 소개](https://aws.amazon.com/ko/blogs/containers/introducing-aws-load-balancer-controller/ "Introducing AWS Load Balancer Controller Blog Post"){:target="_blank"}
*   [AWS Load Balancer Controller Annotations](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.7/guide/ingress/annotations/ "Official Annotation Reference"){:target="_blank"}