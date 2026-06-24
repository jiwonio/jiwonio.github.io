---
layout: post
title: 基于 Fluentd 为 Kubernetes 环境构建生产级中央日志系统的完整指南
slug: building-production-level-centralized-logging-system-with-fluentd-on-kubernetes
date: 2026-05-04 10:03:05 +0900
categories:
- DevOps
- Cloud
tags:
- Kubernetes
- Fluentd
- Elasticsearch
- Kibana
- Logging
- EFK
- Observability
description: 深入探讨如何利用 Fluentd、Elasticsearch 和 Kibana (EFK) 技术栈，在生产 Kubernetes 集群中构建中央日志系统，以高效地收集、处理和分析大规模日志。提供以实践为中心的配置和优化技巧。
image: /uploads/building-production-level-centralized-logging-system-with-fluentd-on-kubernetes/thumbnail.webp
lang: zh
translation_key: building-production-level-centralized-logging-system-with-fluentd-on-kubernetes
permalink: /zh/posts/building-production-level-centralized-logging-system-with-fluentd-on-kubernetes/
post_type: deep-dive
---
随着微服务架构（MSA）的普及，Kubernetes 已成为容器编排的标准。在成千上万个容器动态创建和销毁的 Kubernetes 环境中，使用传统方法追踪和解决分布式应用的日志问题几乎是不可能的。登录到每个 Pod 并使用 `kubectl logs` 命令查看日志只是一种临时措施，对于实时故障响应和根本原因分析存在明显的局限性。

为了解决这些问题，构建**中央日志系统（Centralized Logging System）**已不再是可选项，而是必需品。中央日志系统将整个集群产生的所有日志收集、解析和存储到单一位置，使开发人员和运维人员能够轻松地搜索和可视化数据。本文将以 CNCF（Cloud Native Computing Foundation）的毕业项目、强大的日志收集器 **Fluentd** 为核心，结合 **Elasticsearch** 和 **Kibana**，深入探讨如何利用 **EFK（Elasticsearch, Fluentd, Kibana）技术栈**构建生产级的 Kubernetes 中央日志系统。

<!--more-->
![基于 Fluentd 为 Kubernetes 环境构建生产级中央日志系统的完整指南](/uploads/building-production-level-centralized-logging-system-with-fluentd-on-kubernetes/thumbnail.webp "基于 Fluentd 为 Kubernetes 环境构建生产级中央日志系统的完整指南")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 背景与问题定义：为什么 Kubernetes 必须要有中央日志系统？

在 Kubernetes 环境中，日志记录面临以下复杂性和挑战：

1.  **日志的短暂性（Ephemeral Nature）：** Pod 随时可能重启或被调度到其他节点。当 Pod 消失时，其容器日志也会随之消失，导致用于故障分析的重要信息永久丢失。
2.  **日志位置分散：** 由成百上千个 Pod 生成的日志分散存储在集群内的多个节点上。为了查找与特定事务相关的日志，跨多个 Pod 和节点进行追踪会消耗大量时间和精力。
3.  **日志格式多样：** 每个应用程序或系统组件都以不同的格式输出日志。如果直接收集这些非结构化数据，搜索和分析的效率会大大降低。
4.  **缺乏上下文信息：** 仅有日志消息是不够的。必须附带该日志源自哪个`命名空间`、`Pod`、`容器`等 Kubernetes 元数据信息，才能准确地识别问题。

**EFK 技术栈**是解决这些问题的成熟方案。**Fluentd** 负责从每个节点收集日志，附加 Kubernetes 元数据并进行解析，然后稳定地传输到 **Elasticsearch**。**Elasticsearch** 对大规模日志数据进行索引和存储，以便快速搜索和分析。而 **Kibana** 则提供了一个强大的 Web UI，让用户能够直观地浏览存储的数据，并通过仪表盘进行可视化。

## 核心架构与原理：EFK 技术栈在 Kubernetes 中如何工作？

在 Kubernetes 环境中，EFK 技术栈的典型日志管道遵循以下流程：

1.  **日志生成（Application Pods）：** 应用程序将日志输出到标准输出（`stdout`）或标准错误（`stderr`）。容器运行时（如 Docker、containerd）捕获这些日志，并以文件形式存储在每个节点的特定目录中（例如 `/var/log/containers/`）。
2.  **日志收集（Fluentd DaemonSet）：** **Fluentd** 以 **DaemonSet** 的形式部署到集群中的所有节点上。每个节点上的 Fluentd Pod 通过卷挂载（Volume Mount）访问主机的日志目录，并实时监控（`tail`）容器日志文件。
3.  **日志处理与增强（Fluentd Filter Plugins）：** Fluentd 解析收集到的日志，将非结构化文本转换为 JSON 等结构化数据。特别是通过使用 `fluent-plugin-kubernetes_metadata_filter` 插件，它能从日志文件名中提取 `pod_name`、`namespace`、`container_name`、`labels` 等 Kubernetes 元数据，并动态地添加到日志记录中。
4.  **日志传输（Fluentd Output Plugins）：** 经过丰富元数据增强的结构化日志，通过 Fluentd 的缓冲机制被稳定地发送到 **Elasticsearch** 集群。当网络问题或 Elasticsearch 故障发生时，重试逻辑会启动，以防止日志丢失。
5.  **存储与索引（Elasticsearch）：** Elasticsearch 接收并索引传入的日志数据。这使得在数十亿条日志记录中也能实现毫秒级的快速全文搜索（Full-text search）。
6.  **可视化与分析（Kibana）：** 用户通过 Web 浏览器访问 **Kibana**，可以搜索、筛选存储在 Elasticsearch 中的日志，并构建可视化仪表盘，从而一目了然地掌握集群状态。

这种架构将各组件的职责明确分离，提高了可扩展性和稳定性，为开发人员提供了一个无需关心日志基础设施、可以专注于应用开发的环境。

## 实践代码/配置深度解析

现在，我们来分步了解如何在实际的 Kubernetes 集群中构建 EFK 技术栈。为方便起见，我们假设所有资源都部署在 `logging` 命名空间中。

### 第 1 步：部署 Elasticsearch 和 Kibana

在生产环境中，为了稳定运行 Elasticsearch 集群，通常建议使用 [Elastic Cloud on Kubernetes (ECK) Operator](https://www.elastic.co/guide/en/cloud-on-k8s/current/index.html "Elastic Cloud on Kubernetes 官方文档"){:target="_blank"} 或 Helm Chart。在这里，为了帮助基础理解，我们将使用简单的 StatefulSet 和 Deployment 清单。

#### Elasticsearch StatefulSet

为了实现稳定的数据存储，我们使用带有 `PersistentVolumeClaim` 的 `StatefulSet` 来部署 Elasticsearch。

```yaml
# elasticsearch-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 1 # 生产环境建议设置为 3 或更高
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
        resources:
          limits:
            cpu: 1000m
            memory: 2Gi
          requests:
            cpu: 100m
            memory: 1Gi
        ports:
        - containerPort: 9200
          name: rest
        - containerPort: 9300
          name: inter-node
        volumeMounts:
        - name: data
          mountPath: /usr/share/elasticsearch/data
        env:
        - name: discovery.type
          value: single-node # 单节点设置。在集群配置时需要更改
        - name: ES_JAVA_OPTS
          value: "-Xms1g -Xmx1g" # 建议与 requests.memory 保持一致
        - name: xpack.security.enabled
          value: "false" # 用于演示目的，禁用安全功能
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "gp2" # 替换为您使用的存储类
      resources:
        requests:
          storage: 10Gi
---
# elasticsearch-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch
  namespace: logging
spec:
  selector:
    app: elasticsearch
  ports:
  - port: 9200
    name: rest
```

#### Kibana Deployment

```yaml
# kibana-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
  namespace: logging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kibana
  template:
    metadata:
      labels:
        app: kibana
    spec:
      containers:
      - name: kibana
        image: docker.elastic.co/kibana/kibana:8.5.0
        resources:
          limits:
            cpu: 1000m
            memory: 1Gi
          requests:
            cpu: 100m
            memory: 500Mi
        env:
          - name: ELASTICSEARCH_HOSTS
            value: '["http://elasticsearch.logging:9200"]'
        ports:
        - containerPort: 5601
---
# kibana-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: kibana
  namespace: logging
spec:
  type: LoadBalancer # 使用 LoadBalancer 或 Ingress 进行外部访问
  selector:
    app: kibana
  ports:
  - port: 5601
    targetPort: 5601
```

### 第 2 步：部署 Fluentd DaemonSet

为了让 Fluentd 能够收集每个节点的日志并访问 Kubernetes API 以获取元数据，我们首先需要配置 `ServiceAccount`、`ClusterRole` 和 `ClusterRoleBinding`。

#### RBAC 配置

```yaml
# fluentd-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fluentd
  namespace: logging
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: fluentd
rules:
- apiGroups:
  - ""
  resources:
  - pods
  - namespaces
  verbs:
  - get
  - list
  - watch
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: fluentd
roleRef:
  kind: ClusterRole
  name: fluentd
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: fluentd
  namespace: logging
```

#### Fluentd ConfigMap 和 DaemonSet

我们将定义 Fluentd 行为的配置文件创建为 `ConfigMap`，然后部署一个引用该 ConfigMap 的 `DaemonSet`。

```yaml
# fluentd-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: logging
data:
  fluent.conf: |
    # ======== INPUTS ========
    <source>
      @type tail
      @id in_tail_container_logs
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      read_from_head true
      <parse>
        @type cri
      </parse>
    </source>

    # ======== FILTERS ========
    <filter kubernetes.**>
      @type kubernetes_metadata
      @id filter_kube_metadata
    </filter>

    # ======== OUTPUTS ========
    <match kubernetes.**>
      @type elasticsearch
      @id out_es
      host elasticsearch.logging.svc.cluster.local
      port 9200
      log_level info
      include_tag_key true
      type_name _doc
      logstash_format true
      logstash_prefix fluentd
      logstash_dateformat %Y%m%d
      <buffer>
        @type file
        path /var/log/fluentd-buffers/kubernetes.system.buffer
        flush_mode interval
        retry_type exponential_backoff
        flush_thread_count 2
        flush_interval 5s
        retry_forever true
        retry_max_interval 30
        chunk_limit_size 2M
        queue_limit_length 8
        overflow_action block
      </buffer>
    </match>
```

```yaml
# fluentd-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: logging
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      serviceAccountName: fluentd
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1.15-debian-elasticsearch8-1
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch.logging.svc.cluster.local"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
        resources:
          limits:
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 200Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: config-volume
          mountPath: /fluentd/etc/fluent.conf
          subPath: fluent.conf
      terminationGracePeriodSeconds: 30
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: config-volume
        configMap:
          name: fluentd-config
```

部署完所有资源后，稍等片刻，即可通过 Kibana 服务的外部 IP 访问仪表盘。进入 `Discover` 标签页，使用 `fluentd-*` 模式创建索引，您将能看到集群中的所有日志正在被实时收集。

## 性能优化与最佳实践

为了在生产环境中稳定运行 EFK 技术栈，还需要考虑以下几点：

### 1. Elasticsearch 索引生命周期管理（ILM）

日志数据会随着时间的推移呈指数级增长，导致存储成本增加和搜索性能下降。使用 Elasticsearch 的 **ILM（Index Lifecycle Management）**功能，可以自动管理索引。

-   **Hot Phase：** 数据正在被活跃地索引和搜索的阶段。使用高性能存储。
-   **Warm Phase：** 数据不再写入但仍需搜索的阶段。可以缩小（shrink）索引并迁移到成本较低的存储。
-   **Cold/Frozen Phase：** 几乎不被搜索的旧数据。在保持可搜索状态的同时，最大限度地减少存储使用量。
-   **Delete Phase：** 超过保留期限的数据将被自动删除，以释放存储空间。

例如，您可以在 Kibana Dev Tools 中设置一个 ILM 策略，自动删除超过 30 天的日志。

```json
PUT _ilm/policy/fluentd_policy
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_primary_shard_size": "50gb",
            "max_age": "1d"
          }
        }
      },
      "delete": {
        "min_age": "30d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

### 2. Fluentd 缓冲策略

在上面的 `fluentd.conf` 示例中也已使用，Fluentd 的**缓冲（buffering）**是保障日志管道稳定性的核心功能。它能防止在网络问题或 Elasticsearch 临时故障期间丢失日志。

-   `@type memory`：在内存中缓冲日志。速度快，但如果 Fluentd Pod 重启，缓冲的数据有丢失的风险。
-   `@type file`：在文件系统中缓冲日志。即使 Pod 重启，数据也能保留，因此在生产环境中强烈建议使用**基于文件的缓冲**。如果将 `PersistentVolume` 挂载到 `path` 目录，则更为稳定。
-   应结合使用 `retry_type exponential_backoff`、`retry_forever true` 等选项，以确保在 Elasticsearch 恢复之前能够稳定地执行重试。

### 3. 应用层面的结构化日志（Structured Logging）

虽然 Fluentd 的解析过滤器功能强大，但复杂的正则表达式（regex）会增加 CPU 使用率并降低处理性能。最好的方法是从一开始就在应用程序中输出**JSON 格式等结构化日志**。

**不佳（非结构化）：**
`INFO: User 'admin' logged in successfully from IP 192.168.1.10`

**良好（结构化 JSON）：**
`{"level": "info", "message": "User login successful", "user": "admin", "source_ip": "192.168.1.10"}`

使用结构化日志，Fluentd 无需复杂的解析过程即可将数据直接发送到 Elasticsearch，而在 Kibana 中也可以进行如 `user:admin` 这样基于字段的精确、快速搜索。

## 结论

到目前为止，我们详细探讨了如何在 Kubernetes 环境中利用 **Fluentd、Elasticsearch、Kibana（EFK）技术栈**构建生产级的中央日志系统，内容涵盖了从架构、实践配置到优化技巧的方方面面。一个稳定的中央日志系统是保障复杂微服务环境**可观测性（Observability）**、实现快速故障响应和提升服务质量的关键基础设施。

本文中提供的配置是构建 EFK 技术栈的起点。在实际生产环境中，您需要持续优化架构，以满足业务需求和工作负载的特性，例如监控各组件的资源使用情况、加强安全配置（TLS、认证/授权）、为大规模流量增加 Fluentd 聚合层等。希望本指南能为在您的 Kubernetes 集群中构建强大的日志系统奠定坚实的基础。

### 参考资料
- [Fluentd 官方文档](https://docs.fluentd.org/ "Fluentd Documentation"){:target="_blank"}
- [Elasticsearch 官方指南](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html "Elasticsearch Reference"){:target="_blank"}
- [Kibana 官方指南](https://www.elastic.co/guide/en/kibana/current/index.html "Kibana Guide"){:target="_blank"}
- [Kubernetes 日志架构](https://kubernetes.io/docs/concepts/cluster-administration/logging/ "Kubernetes Logging Documentation"){:target="_blank"}