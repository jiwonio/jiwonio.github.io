---
layout: post
title: 使用 Amazon EKS 和 AWS Load Balancer Controller 构建生产级 Kubernetes Ingress 完全指南
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
description: 本文深入探讨在 AWS EKS 环境中为高效管理外部流量而安装和配置‘AWS Load Balancer Controller’的方法。全面掌握如何构建生产级
  Kubernetes Ingress，并精通 SSL/TLS 应用、健康检查、高级路由等实战最佳实践。
image: /uploads/production-kubernetes-ingress-with-aws-eks-and-alb-controller/thumbnail.webp
lang: zh
translation_key: production-kubernetes-ingress-with-aws-eks-and-alb-controller
permalink: /zh/posts/production-kubernetes-ingress-with-aws-eks-and-alb-controller/
post_type: deep-dive
---
在使用 Amazon EKS (Elastic Kubernetes Service) 运营 Kubernetes 集群时，最重要的挑战之一是如何稳定、高效地将外部流量路由到集群内部的服务。虽然 Kubernetes 提供了 `NodePort` 或 `LoadBalancer` 类型的服务，但它们在满足生产环境的复杂需求方面存在明显的局限性。例如，每当部署一个 `LoadBalancer` 类型的服务时，都会创建一个新的 ELB (Elastic Load Balancer)，这不仅增加了成本负担，而且难以应用精细的 L7 路由规则（如基于路径、基于主机的路由）。

为了解决这些问题，Kubernetes 提供了 **Ingress** 对象。Ingress 是将集群外部的 HTTP/HTTPS 请求连接到集群内部服务的规则集合，而实际执行这些规则的就是 **Ingress Controller**。特别是在 AWS 环境中，**AWS Load Balancer Controller** 与 EKS 的集成最为完善，它能够原生利用 AWS 的 Application Load Balancer (ALB) 或 Network Load Balancer (NLB)。通过使用该控制器，我们可以通过单个 ALB 暴露多个服务，并以 Kubernetes 原生的方式声明式地管理 SSL/TLS 证书、高级流量路由、WAF 集成等强大功能。

本文面向经验丰富的工程师，将从 A 到 Z 深入探讨在生产环境中，**结合 Amazon EKS 和 AWS Load Balancer Controller 构建稳定且经济高效的 Ingress 系统**的全部过程。我们不仅会介绍控制器的安装，还将详细讲解 IAM 角色设置、利用必要的注解（Annotation）进行高级配置，以及应对实际工作中可能遇到的问题的解决方案和最佳实践。

<!--more-->
![使用 Amazon EKS 和 AWS Load Balancer Controller 构建生产级 Kubernetes Ingress 完全指南](/uploads/production-kubernetes-ingress-with-aws-eks-and-alb-controller/thumbnail.webp "使用 Amazon EKS 和 AWS Load Balancer Controller 构建生产级 Kubernetes Ingress 完全指南")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI 生成的图像</small>
</p>
-----

## 背景与问题定义

在 Kubernetes 集群中，向外部暴露正在运行的应用程序的基本方法是将 `Service` 对象设置为 `LoadBalancer` 类型。在这种情况下，云提供商（如 AWS、GCP）会为该服务配置一个外部负载均衡器。

然而，这种方式有几个严重的缺点。

1.  **成本问题：** 每创建一个 `LoadBalancer` 类型的 `Service`，就会创建一个独立的负载均衡器（在 AWS 中是 Classic 或 Network Load Balancer）。在运行成百上千个微服务的环境中，负载均衡器的成本可能会呈指数级增长。
2.  **功能限制：** `Service` 类型的负载均衡器基本上工作在 L4（传输层）。因此，它不直接支持像根据主机名或 URL 路径分流的 L7（应用层）路由、SSL/TLS 卸载、基于 HTTP 头的路由等高级功能。
3.  **管理复杂性：** 每个服务都需要单独管理外部 IP 地址和 DNS 记录，这增加了运维的复杂性。

**Kubernetes Ingress** 正是为解决这些问题而设计的 API 对象。Ingress 定义了 L7 虚拟主机和基于路径的路由规则，而实际执行这些规则的 **Ingress Controller** 会共享单个负载均衡器，将流量分发到多个后端服务。

在 AWS 环境中，**AWS Load Balancer Controller** 扮演了这个角色，并与 AWS 强大的 Application Load Balancer (ALB) 直接集成。通过这种方式，我们可以降低成本，并最大限度地利用 AWS 的托管服务，构建稳定且可扩展的架构。

## 核心架构与原理

AWS Load Balancer Controller 是一个以 Pod 形式在 Kubernetes 集群内部运行的控制器。其核心职责是持续监控（`watch`）Kubernetes API 服务器，检测 `Ingress` 对象的创建、修改和删除事件，并相应地自动创建和管理 AWS ALB 资源。

整体的流量流向和架构如下：

1.  **用户请求：** 用户通过 Web 浏览器向 `example.com` 等域名发送请求。
2.  **DNS 查询：** Route 53 等 DNS 服务将域名解析为由 AWS Load Balancer Controller 创建的 **ALB 的 DNS 名称**。
3.  **ALB 接收：** 请求到达 ALB。ALB 执行 SSL/TLS 终止，并检查请求的主机名（`Host` 头）和路径（`Path`）。
4.  **应用路由规则：** ALB 根据 Ingress Controller 设置的监听器规则（Listener Rules），将请求转发到适当的**目标组（Target Group）**。
5.  **目标组与 Pod：** 目标组包含处理请求的后端 Pod 的 IP 地址列表。ALB 将流量转发到其中一个 Pod。此时，根据 **Target Type** 的设置（`ip` 或 `instance`），行为方式会有所不同。
    *   `ip` 模式（推荐）：ALB 不经过 EKS Worker Node，直接将流量路由到 Pod 的 IP。性能更优，并且可以对 Pod 级别应用安全组。
    *   `instance` 模式：ALB 将流量发送到节点的 `NodePort`，然后由节点的 `kube-proxy` 再次将流量转发到相应的 Pod。
6.  **响应：** Pod 处理完请求并返回响应后，流量按相反的路径返回给用户。

在整个过程中，开发人员只需定义 `Ingress` YAML 文件并执行 `kubectl apply` 即可。AWS Load Balancer Controller 会自动管理其余复杂的 AWS 资源（如 ALB、Target Group、Listener、Rules 等）的生命周期。

## 实践代码与配置深度解析

现在，我们将逐步在实际的 EKS 集群上安装 AWS Load Balancer Controller，并为一个示例应用程序配置 Ingress。

### 第 1 步：准备工作

开始之前，请确保已安装并配置好以下工具：

*   AWS CLI：用于访问您的 AWS 账户。
*   `kubectl`：用于与 Kubernetes 集群进行交互。
*   `eksctl`：用于轻松创建和管理 EKS 集群的官方 CLI 工具。
*   `helm`：Kubernetes 包管理器，用于安装控制器。

### 第 2 步：创建 IAM OIDC 提供商

控制器需要 IAM 权限才能调用 AWS API 来管理 ALB。我们将使用 IAM 角色并将其与 Kubernetes 服务账户关联（IRSA, IAM Roles for Service Accounts），以安全地授予权限。为此，我们首先需要在集群上创建一个 IAM OIDC 身份提供商。

```bash
# 请将 <YOUR_CLUSTER_NAME> 替换为您的实际 EKS 集群名称。
eksctl utils associate-iam-oidc-provider \
    --region=ap-northeast-2 \
    --cluster=<YOUR_CLUSTER_NAME> \
    --approve
```

### 第 3 步：为控制器创建 IAM 策略和服务账户

下载并创建定义了 AWS Load Balancer Controller 所需权限的 IAM 策略。

```bash
# 下载 IAM 策略
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json

# 创建 IAM 策略
aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam-policy.json
```

现在，使用 `eksctl` 创建一个关联了该 IAM 策略的 Kubernetes 服务账户。此命令会通过 CloudFormation 堆栈创建一个 IAM 角色，并将其与 Kubernetes 服务账户关联。

```bash
# 请将 <YOUR_AWS_ACCOUNT_ID> 和 <YOUR_CLUSTER_NAME> 替换为实际值。
eksctl create iamserviceaccount \
  --cluster=<YOUR_CLUSTER_NAME> \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name "AmazonEKSLoadBalancerControllerRole" \
  --attach-policy-arn=arn:aws:iam::<YOUR_AWS_ACCOUNT_ID>:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve
```

### 第 4 步：使用 Helm 安装 AWS Load Balancer Controller

使用 Helm chart 安装控制器是最简单且推荐的方法。

```bash
# 添加 Helm 仓库
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks

# 安装 Helm chart
# [🚨 注意] 请务必确认 clusterName, serviceAccount.name, serviceAccount.create 的值。
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=<YOUR_CLUSTER_NAME> \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=ap-northeast-2 \
  --set vpcId=<YOUR_VPC_ID>
```

安装完成后，请确认控制器的 Pod 是否正常运行。

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

### 第 5 步：部署示例应用和 Ingress

现在，我们来部署一个简单的 Web 应用程序（例如 `game-2048`）进行测试，并创建 `Ingress` 资源来连接外部流量。

#### 5.1. 部署示例应用

创建名为 `deployment-2048.yaml` 的文件，内容如下。该 YAML 定义了一个 Deployment 和一个 `ClusterIP` 类型的 Service。

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

将文件应用到集群中。

```bash
kubectl apply -f deployment-2048.yaml
```

#### 5.2. 创建 Ingress 资源

现在是最关键的一步：定义 `Ingress` 资源。下面的 `ingress-2048.yaml` 文件是一个示例，它将所有发往 `game.your-domain.com` 的流量路由到 `service-2048`，并使用预先在 AWS Certificate Manager (ACM) 中颁发的 SSL 证书来启用 HTTPS。

```yaml
# ingress-2048.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-2048
  annotations:
    # [🔥 重要] 将 Ingress Class 指定为 'alb'，以便由 AWS Load Balancer Controller 处理。
    kubernetes.io/ingress.class: alb
    
    # [🔥 重要] 指定 ALB 的方案 (scheme)。要暴露到外部，请使用 'internet-facing'。
    alb.ingress.kubernetes.io/scheme: internet-facing
    
    # [🔥 重要] 强烈建议将 Target Type 设置为 'ip'。
    alb.ingress.kubernetes.io/target-type: ip
    
    # [SSL/TLS] 指定从 ACM 颁发的证书的 ARN。
    alb.ingress.kubernetes.io/certificate-arn: <YOUR_ACM_CERTIFICATE_ARN>
    
    # [SSL/TLS] 设置监听 HTTP(80) 和 HTTPS(443) 端口。
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    
    # [SSL/TLS] 将所有传入的 HTTP 请求重定向到 HTTPS。
    alb.ingress.kubernetes.io/actions.ssl-redirect: '{"Type": "redirect", "RedirectConfig": { "Protocol": "HTTPS", "Port": "443", "StatusCode": "HTTP_301"}}'
    
    # [Health Check] 指定 ALB 对 Pod 执行健康检查的路径。
    # alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  rules:
    - host: game.your-domain.com # [🚨 注意] 请更改为您实际拥有的域名。
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

应用该 YAML 文件。

```bash
kubectl apply -f ingress-2048.yaml
```

几分钟后，执行 `kubectl get ingress ingress-2048` 命令，您将在 `ADDRESS` 字段看到已创建的 ALB 的 DNS 地址。将此地址作为 CNAME 记录添加到您的域名（`game.your-domain.com`）中，稍等片刻，您就可以通过 HTTPS 访问您的应用程序了。

## 性能优化与最佳实践

这里有一些在生产环境中稳定运行 AWS Load Balancer Controller 的技巧和最佳实践。

1.  **使用 `ip` 模式的 Target Type：** `ip` 模式直接将流量转发到 Pod，消除了经过 `kube-proxy` 的额外一跳（hop），从而减少了网络延迟并提高了性能。此外，它还允许您直接为 Pod 应用安全组（Security Groups for Pods），实现更精细的网络安全策略。
2.  **通过 Ingress Grouping 优化成本：** 您可以将多个 `Ingress` 资源分组，让它们共享同一个 ALB。通过使用 `alb.ingress.kubernetes.io/group.name` 注解将多个 Ingress 绑定到一个逻辑组，控制器将只为该组创建一个 ALB，从而显著降低成本。
3.  **设置准确的健康检查路径：** 使用 `alb.ingress.kubernetes.io/healthcheck-path` 注解指定一个能够准确反映应用程序状态的 API 端点（例如 `/health`、`/status`）。这样可以确保不健康的 Pod 被迅速从目标组中移除，从而提高服务稳定性。
4.  **利用子网自动发现标签：** 默认情况下，控制器会将 ALB 部署到具有特定标签（`kubernetes.io/cluster/<cluster-name>: owned` 和 `kubernetes.io/role/elb: 1` 或 `kubernetes.io/role/internal-elb: 1`）的子网中。如果使用 `eksctl` 创建集群，这些标签会自动应用于公有和私有子网。如果您的基础设施是使用 Terraform 等工具手动管理的，请确保正确设置这些标签，以便控制器能准确找到部署 ALB 的子网。
5.  **定期检查控制器日志：** 控制器 Pod 的日志对于调试 `Ingress` 配置错误或 AWS API 调用失败等问题至关重要。通过 `kubectl logs -n kube-system deploy/aws-load-balancer-controller` 命令检查日志，可以帮助您提前发现并解决潜在问题。

## 结论

到目前为止，我们详细探讨了如何在 Amazon EKS 环境中使用 AWS Load Balancer Controller 来构建生产级的 Ingress 系统。该控制器完美结合了 Kubernetes 的声明式 API 和 AWS 强大的 ALB，使开发人员和运维人员无需直接管理复杂的 AWS 基础设施，仅通过 YAML 文件就能实现精密的 L7 流量路由。

它不仅仅是简单地将服务暴露到外部，更通过**成本优化、SSL/TLS 自动化、高级路由以及与 AWS 生态系统的紧密集成**等优势，使您的微服务架构更加健壮和可扩展。将本指南中讨论的配置和最佳实践应用到您的实际工作中，您的 EKS 集群必将达到更高水平的稳定性和效率。

### 参考资料

*   [AWS Load Balancer Controller 官方文档](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.7/ "AWS Load Balancer Controller Documentation"){:target="_blank"}
*   [Amazon EKS 最佳实践指南 - 网络](https://docs.aws.amazon.com/eks/latest/best-practices/ingress.html "Amazon EKS Best Practices Guide for Networking"){:target="_blank"}
*   [AWS 博客：介绍 AWS Load Balancer Controller](https://aws.amazon.com/ko/blogs/containers/introducing-aws-load-balancer-controller/ "Introducing AWS Load Balancer Controller Blog Post"){:target="_blank"}
*   [AWS Load Balancer Controller 注解参考](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.7/guide/ingress/annotations/ "Official Annotation Reference"){:target="_blank"}