---
layout: post
title: Mastering Production-Ready Kubernetes Ingress with Amazon EKS and AWS Load
  Balancer Controller
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
description: This post provides an in-depth guide on installing and configuring the
  AWS Load Balancer Controller for efficient external traffic management in an AWS
  EKS environment. Master the art of building a production-grade Kubernetes Ingress,
  including SSL/TLS termination, health checks, advanced routing, and real-world best
  practices.
image: /uploads/production-kubernetes-ingress-with-aws-eks-and-alb-controller/thumbnail.webp
lang: en
translation_key: production-kubernetes-ingress-with-aws-eks-and-alb-controller
permalink: /en/posts/production-kubernetes-ingress-with-aws-eks-and-alb-controller/
post_type: deep-dive
---
When operating a Kubernetes cluster using Amazon EKS (Elastic Kubernetes Service), one of the most critical challenges is routing external traffic to services inside the cluster reliably and efficiently. While Kubernetes provides `NodePort` or `LoadBalancer` type services, they have clear limitations in meeting the complex demands of a production environment. For example, every time a `LoadBalancer` service is deployed, a new ELB (Elastic Load Balancer) is created, increasing costs. It's also difficult to apply fine-grained L7 routing rules (path-based, host-based routing).

To solve these problems, Kubernetes offers an object called **Ingress**. An Ingress is a collection of rules that allow inbound connections to reach cluster services, and the component that actually fulfills these rules is the **Ingress Controller**. In the AWS environment, the **AWS Load Balancer Controller** integrates most seamlessly with EKS, allowing you to natively leverage AWS's Application Load Balancer (ALB) or Network Load Balancer (NLB). Using this controller, you can expose multiple services through a single ALB and declare powerful features like SSL/TLS certificate management, advanced traffic routing, and WAF integration in a Kubernetes-native way.

This post, aimed at experienced engineers, will cover the entire process of building a stable and cost-effective ingress system by integrating **Amazon EKS with the AWS Load Balancer Controller** in a production environment, from A to Z. We'll go beyond simple controller installation to delve into IAM role setup, advanced configurations using essential annotations, and detailed solutions and best practices for problems you might encounter in the field.

<!--more-->
![Mastering Production-Ready Kubernetes Ingress with Amazon EKS and AWS Load Balancer Controller](/uploads/production-kubernetes-ingress-with-aws-eks-and-alb-controller/thumbnail.webp "Mastering Production-Ready Kubernetes Ingress with Amazon EKS and AWS Load Balancer Controller")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## Background and Problem Definition

The basic way to expose an application running in a Kubernetes cluster is to set the `Service` object to the `LoadBalancer` type. In this case, the cloud provider (AWS, GCP, etc.) provisions an external load balancer for that service.

However, this approach has several significant drawbacks.

1.  **Cost Issues:** Each time a `LoadBalancer` type `Service` is created, a separate load balancer (Classic or Network Load Balancer in AWS) is also created. In an environment running tens or hundreds of microservices, load balancer costs can increase exponentially.
2.  **Functional Limitations:** A `Service` type load balancer primarily operates at the L4 (Transport Layer) level. Therefore, it does not directly support advanced features like L7 (Application Layer) routing based on hostname or URL path, SSL/TLS Offloading, or HTTP header-based routing.
3.  **Management Complexity:** Each service requires individual management of its external IP address and DNS records, which increases operational complexity.

**Kubernetes Ingress** is an API object designed to solve these problems. Ingress defines L7 virtual hosting and path-based routing rules, and the **Ingress Controller** that actually executes these rules shares a single load balancer to direct traffic to multiple backend services.

In the AWS environment, the **AWS Load Balancer Controller** performs this role, integrating directly with AWS's powerful Application Load Balancer (ALB). This allows us to reduce costs and build a stable, scalable architecture by leveraging AWS's managed services to the fullest.

## Core Architecture and Principles

The AWS Load Balancer Controller is a controller that runs as a Pod within the Kubernetes cluster. Its core role is to continuously `watch` the Kubernetes API server, detect create, update, and delete events for `Ingress` objects, and automatically create and manage AWS ALB resources accordingly.

The overall traffic flow and architecture are as follows:

1.  **User Request:** A user sends a request to a domain like `example.com` through a web browser.
2.  **DNS Lookup:** A DNS service like Route 53 resolves the domain name to the **ALB's DNS name** created by the AWS Load Balancer Controller.
3.  **ALB Reception:** The request reaches the ALB. The ALB performs SSL/TLS Termination and checks the request's hostname (`Host` header) and path (`Path`).
4.  **Routing Rule Application:** The ALB forwards the request to the appropriate **Target Group** based on the Listener Rules configured by the ingress controller.
5.  **Target Group and Pods:** The Target Group contains a list of IP addresses of the backend Pods that will handle the request. The ALB forwards the traffic to one of these Pods. The behavior differs based on the **Target Type** setting (`ip` or `instance`).
    *   `ip` mode (Recommended): The ALB routes traffic directly to the Pod's IP without passing through the EKS Worker Node. This offers better performance and allows for the application of security groups at the Pod level.
    *   `instance` mode: The ALB sends traffic to the Node's `NodePort`, and the Node's `kube-proxy` then forwards the traffic to the corresponding Pod.
6.  **Response:** After the Pod processes the request and returns a response, the traffic is delivered back to the user in reverse order.

Throughout this entire process, the developer only needs to define an `Ingress` YAML file and run `kubectl apply`. The AWS Load Balancer Controller automatically manages the lifecycle of the complex underlying AWS resources (ALB, Target Groups, Listeners, Rules, etc.).

## Deep Dive into Practical Application Code/Configuration

Now, let's walk through the steps to install the AWS Load Balancer Controller on an actual EKS cluster and configure an ingress for a sample application.

### Step 1: Prerequisites

Before you begin, ensure you have the following tools installed and configured:

*   AWS CLI: Required for accessing your AWS account.
*   `kubectl`: Required for interacting with your Kubernetes cluster.
*   `eksctl`: The official CLI tool for easily creating and managing EKS clusters.
*   `helm`: The Kubernetes package manager, used for installing the controller.

### Step 2: Create an IAM OIDC Provider

The controller needs IAM permissions to call AWS APIs to manage ALBs. We will use an IAM role and associate it with a Kubernetes service account (IRSA, IAM Roles for Service Accounts) to grant permissions securely. To do this, we first need to create an IAM OIDC identity provider for the cluster.

```bash
# Replace <YOUR_CLUSTER_NAME> with your actual EKS cluster name.
eksctl utils associate-iam-oidc-provider \
    --region=ap-northeast-2 \
    --cluster=<YOUR_CLUSTER_NAME> \
    --approve
```

### Step 3: Create IAM Policy and Service Account for the Controller

Download and create an IAM policy that defines the permissions required by the AWS Load Balancer Controller.

```bash
# Download the IAM policy
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json

# Create the IAM policy
aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam-policy.json
```

Now, use `eksctl` to create a Kubernetes service account with the IAM policy attached. This command creates an IAM role via a CloudFormation stack and associates it with the Kubernetes service account.

```bash
# Replace <YOUR_AWS_ACCOUNT_ID> and <YOUR_CLUSTER_NAME> with your actual values.
eksctl create iamserviceaccount \
  --cluster=<YOUR_CLUSTER_NAME> \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name "AmazonEKSLoadBalancerControllerRole" \
  --attach-policy-arn=arn:aws:iam::<YOUR_AWS_ACCOUNT_ID>:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve
```

### Step 4: Install AWS Load Balancer Controller using Helm

Using a Helm chart is the easiest and recommended way to install the controller.

```bash
# Add the EKS Helm repository
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks

# Install the Helm chart
# [🚨 CAUTION] Be sure to verify the clusterName, serviceAccount.name, and serviceAccount.create values.
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=<YOUR_CLUSTER_NAME> \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=ap-northeast-2 \
  --set vpcId=<YOUR_VPC_ID>
```

Once the installation is complete, verify that the controller Pod is running correctly.

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

### Step 5: Deploy a Sample Application and Ingress

Now, let's deploy a simple web application (e.g., `game-2048`) for testing and create an `Ingress` resource to route external traffic to it.

#### 5.1. Deploy the Sample Application

Create a file named `deployment-2048.yaml` with the following content. This YAML defines a Deployment and a `ClusterIP` type Service.

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

Apply the file to your cluster.

```bash
kubectl apply -f deployment-2048.yaml
```

#### 5.2. Create the Ingress Resource

Now for the most important part: defining the `Ingress` resource. The `ingress-2048.yaml` file below is an example that routes traffic for `game.your-domain.com` to `service-2048` and applies an SSL certificate pre-issued from AWS Certificate Manager (ACM) to enable HTTPS.

```yaml
# ingress-2048.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-2048
  annotations:
    # [🔥 IMPORTANT] Specify 'alb' as the Ingress Class to be handled by the AWS Load Balancer Controller.
    kubernetes.io/ingress.class: alb
    
    # [🔥 IMPORTANT] Specify the ALB's scheme. Use 'internet-facing' for external exposure.
    alb.ingress.kubernetes.io/scheme: internet-facing
    
    # [🔥 IMPORTANT] It is highly recommended to set the Target Type to 'ip'.
    alb.ingress.kubernetes.io/target-type: ip
    
    # [SSL/TLS] Specify the ARN of the certificate issued from ACM.
    alb.ingress.kubernetes.io/certificate-arn: <YOUR_ACM_CERTIFICATE_ARN>
    
    # [SSL/TLS] Set up listeners for HTTP (80) and HTTPS (443) ports.
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    
    # [SSL/TLS] Redirect all incoming HTTP requests to HTTPS.
    alb.ingress.kubernetes.io/actions.ssl-redirect: '{"Type": "redirect", "RedirectConfig": { "Protocol": "HTTPS", "Port": "443", "StatusCode": "HTTP_301"}}'
    
    # [Health Check] Specify the path for the ALB to perform health checks on the Pod.
    # alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  rules:
    - host: game.your-domain.com # [🚨 CAUTION] Change this to a domain you actually own.
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

Apply the YAML file.

```bash
kubectl apply -f ingress-2048.yaml
```

After a few minutes, run the command `kubectl get ingress ingress-2048`. The `ADDRESS` field will show the DNS address of the created ALB. Register this address as a CNAME record for your domain (`game.your-domain.com`), and shortly after, you will be able to access your application via HTTPS.

## Performance Optimization and Best Practices

Here are some tips and best practices for running the AWS Load Balancer Controller reliably in a production environment.

1.  **Use `ip` Mode for Target Type:** `ip` mode forwards traffic directly to the Pods, eliminating the extra hop through `kube-proxy`, which reduces network latency and improves performance. It also allows you to apply Security Groups for Pods directly, enabling more granular network security policies.
2.  **Optimize Costs with Ingress Grouping:** You can group multiple `Ingress` resources to share the same ALB. By using the `alb.ingress.kubernetes.io/group.name` annotation to bundle several ingresses into a single logical group, the controller will create only one ALB for that group, significantly reducing costs.
3.  **Set an Accurate Health Check Path:** Use the `alb.ingress.kubernetes.io/healthcheck-path` annotation to specify an API endpoint (e.g., `/health`, `/status`) that can accurately reflect your application's health. This ensures that unhealthy Pods are quickly removed from the target group, improving service stability.
4.  **Utilize Subnet Auto-discovery Tags:** By default, the controller deploys ALBs to subnets with specific tags (`kubernetes.io/cluster/<cluster-name>: owned` and `kubernetes.io/role/elb: 1` or `kubernetes.io/role/internal-elb: 1`). When you create a cluster with `eksctl`, these tags are automatically applied to your Public and Private subnets. If you manage your infrastructure with tools like Terraform, you must set these tags correctly so the controller can find the right subnets for ALB placement.
5.  **Periodically Check Controller Logs:** The controller Pod's logs are crucial for debugging issues like `Ingress` configuration errors or failed AWS API calls. Use the `kubectl logs -n kube-system deploy/aws-load-balancer-controller` command to check the logs, allowing you to identify and resolve potential problems proactively.

## Conclusion

We have now explored in detail how to build a production-grade ingress system using the AWS Load Balancer Controller in an Amazon EKS environment. This controller perfectly combines Kubernetes's declarative API with AWS's powerful ALB, enabling developers and operators to implement sophisticated L7 traffic routing with just a YAML file, without needing to manage complex AWS infrastructure directly.

Beyond simply exposing services, it makes your microservice architecture more robust and scalable through **cost optimization, SSL/TLS automation, advanced routing, and tight integration with the AWS ecosystem**. By applying the configurations and best practices covered in this guide to your work, your EKS cluster will achieve a higher level of stability and efficiency.

### References

*   [AWS Load Balancer Controller Official Documentation](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.7/ "AWS Load Balancer Controller Documentation"){:target="_blank"}
*   [Amazon EKS Best Practices Guide - Networking](https://docs.aws.amazon.com/eks/latest/best-practices/ingress.html "Amazon EKS Best Practices Guide for Networking"){:target="_blank"}
*   [Introducing the AWS Load Balancer Controller for Kubernetes](https://aws.amazon.com/ko/blogs/containers/introducing-aws-load-balancer-controller/ "Introducing AWS Load Balancer Controller Blog Post"){:target="_blank"}
*   [AWS Load Balancer Controller Annotations](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.7/guide/ingress/annotations/ "Official Annotation Reference"){:target="_blank"}
---