---
layout: post
title: A Complete Guide to Building a Production-Level Centralized Logging System
  with Fluentd on Kubernetes
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
description: This in-depth guide covers how to build a centralized logging system
  using the Fluentd, Elasticsearch, and Kibana (EFK) stack to efficiently collect,
  process, and analyze large-scale logs in a production Kubernetes cluster. Discover
  practical configurations and optimization tips.
image: /uploads/building-production-level-centralized-logging-system-with-fluentd-on-kubernetes/thumbnail.webp
lang: en
translation_key: building-production-level-centralized-logging-system-with-fluentd-on-kubernetes
permalink: /en/posts/building-production-level-centralized-logging-system-with-fluentd-on-kubernetes/
---
As Microservices Architecture (MSA) has become commonplace, Kubernetes has established itself as the standard for container orchestration. In a Kubernetes environment where numerous containers are dynamically created and destroyed, tracking distributed application logs and troubleshooting issues is nearly impossible with traditional methods. Accessing each pod and checking logs with the `kubectl logs` command is merely a temporary fix, with clear limitations for real-time incident response and root cause analysis.

To solve these problems, building a **Centralized Logging System** has become not an option, but a necessity. A centralized logging system collects all logs generated across the entire cluster into a single location, refining and storing them so that developers and operators can easily search and visualize them. This post provides an in-depth guide to building a production-level centralized logging system for Kubernetes using the **EFK (Elasticsearch, Fluentd, Kibana) stack**, centered around **Fluentd**, a powerful log collector and a graduated project of the CNCF (Cloud Native Computing Foundation).

<!--more-->
![A Complete Guide to Building a Production-Level Centralized Logging System with Fluentd on Kubernetes](/uploads/building-production-level-centralized-logging-system-with-fluentd-on-kubernetes/thumbnail.webp "A Complete Guide to Building a Production-Level Centralized Logging System with Fluentd on Kubernetes")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## Background and Problem Definition: Why is Centralized Logging Essential for Kubernetes?

Logging in a Kubernetes environment presents the following complexities and challenges:

1.  **Ephemeral Nature of Logs:** Pods can be restarted or rescheduled to different nodes at any time. When a pod disappears, its container logs also disappear, leading to the permanent loss of crucial information needed for failure analysis.
2.  **Distributed Log Locations:** Logs generated from hundreds or thousands of pods are stored across various nodes within the cluster. Tracking logs related to a specific transaction by navigating through multiple pods and nodes consumes an immense amount of time and effort.
3.  **Diverse Log Formats:** Each application or system component outputs logs in its own unique format. Collecting this unstructured data as-is significantly reduces the efficiency of searching and analysis.
4.  **Absence of Contextual Information:** The log message alone is insufficient. Kubernetes metadata, such as which `namespace`, `pod`, or `container` the log originated from, is essential for accurate problem identification.

The **EFK stack** is a proven solution to address these challenges. **Fluentd** collects logs from each node, enriches them by attaching Kubernetes metadata, and reliably forwards them to **Elasticsearch**. **Elasticsearch** indexes and stores large volumes of log data for fast searching and analysis, while **Kibana** provides a powerful web UI for users to intuitively explore the stored data and visualize it through dashboards.

## Core Architecture and Principles: How Does the EFK Stack Work in Kubernetes?

In a Kubernetes environment, the typical log pipeline of an EFK stack follows this flow:

1.  **Log Generation (Application Pods):** Applications write logs to standard output (`stdout`) or standard error (`stderr`). The container runtime (e.g., Docker, containerd) captures these logs and saves them as files in a specific directory on each node (e.g., `/var/log/containers/`).
2.  **Log Collection (Fluentd DaemonSet):** **Fluentd** is deployed as a **DaemonSet** on every node in the cluster. The Fluentd pod on each node volume-mounts the host's log directory and tails the container log files in real-time.
3.  **Log Processing and Enrichment (Fluentd Filter Plugins):** Fluentd parses the collected logs, transforming unstructured text into structured data like JSON. Critically, it uses the `fluent-plugin-kubernetes_metadata_filter` plugin to extract Kubernetes metadata such as `pod_name`, `namespace`, `container_name`, and `labels` from the log file names and dynamically adds it to the log records.
4.  **Log Forwarding (Fluentd Output Plugins):** The refined logs, enriched with metadata, are reliably sent to the **Elasticsearch** cluster through Fluentd's buffering mechanism. Retry logic is activated during network issues or Elasticsearch failures to prevent log loss.
5.  **Storage and Indexing (Elasticsearch):** Elasticsearch indexes and stores the incoming log data. This enables millisecond-fast full-text searches even across billions of log records.
6.  **Visualization and Analysis (Kibana):** Users access **Kibana** through a web browser to search, filter, and create visualization dashboards from the data stored in Elasticsearch, allowing them to grasp the cluster's state at a glance.

This architecture clearly separates the roles of each component, enhancing scalability and reliability, and provides an environment where developers can focus solely on application development without worrying about the logging infrastructure.

## Deep Dive into Practical Application Code/Configuration

Now, let's walk through the steps to build an EFK stack on an actual Kubernetes cluster. For convenience, we will assume all resources are deployed in the `logging` namespace.

### Step 1: Deploying Elasticsearch and Kibana

In a production environment, it is common to use the [Elastic Cloud on Kubernetes (ECK) Operator](https://www.elastic.co/guide/en/cloud-on-k8s/current/index.html "Elastic Cloud on Kubernetes Official Documentation"){:target="_blank"} or a Helm chart for stable operation of the Elasticsearch cluster. Here, we will use simple StatefulSet and Deployment manifests to aid basic understanding.

#### Elasticsearch StatefulSet

We deploy Elasticsearch as a `StatefulSet` using a `PersistentVolumeClaim` for stable data storage.

```yaml
# elasticsearch-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 1 # For production environments, 3 or more replicas are recommended.
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
          value: single-node # Single-node configuration. Needs to be changed for a cluster setup.
        - name: ES_JAVA_OPTS
          value: "-Xms1g -Xmx1g" # It's recommended to match this with requests.memory.
        - name: xpack.security.enabled
          value: "false" # Disable security features for demo purposes.
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "gp2" # Change to your storage class.
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
  type: LoadBalancer # Use LoadBalancer or Ingress for external access.
  selector:
    app: kibana
  ports:
  - port: 5601
    targetPort: 5601
```

### Step 2: Deploying the Fluentd DaemonSet

To allow Fluentd to collect logs from each node and access the Kubernetes API to fetch metadata, we must first set up a `ServiceAccount`, `ClusterRole`, and `ClusterRoleBinding`.

#### RBAC Configuration

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

#### Fluentd ConfigMap and DaemonSet

We create a `ConfigMap` for Fluentd's configuration file and deploy a `DaemonSet` that references it.

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

After deploying all resources, wait a moment and you will be able to access the Kibana dashboard via the external IP of the Kibana service. Navigate to the `Discover` tab and create an index pattern with `fluentd-*` to see all logs from the cluster being collected in real-time.

## Performance Optimization and Best Practices

To operate the EFK stack reliably in a production environment, several additional considerations are necessary.

### 1. Elasticsearch Index Lifecycle Management (ILM)

Log data grows exponentially over time, leading to increased storage costs and degraded search performance. Elasticsearch's **ILM (Index Lifecycle Management)** feature allows you to automate index management.

-   **Hot Phase:** The stage where data is actively being indexed and queried. Uses high-performance storage.
-   **Warm Phase:** Data is no longer being written but is still being queried. You can shrink the index and move it to less expensive storage.
-   **Cold/Frozen Phase:** Older data that is rarely queried. Minimizes storage usage while keeping the data searchable.
-   **Delete Phase:** Data that has passed its retention period is automatically deleted to free up storage space.

For example, you can set an ILM policy in Kibana Dev Tools to automatically delete logs older than 30 days.

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

### 2. Fluentd Buffering Strategy

As used in the `fluentd.conf` example above, Fluentd's **buffering** is a core feature that ensures the reliability of the log pipeline. It prevents log loss during network issues or temporary Elasticsearch outages.

-   `@type memory`: Buffers logs in memory. It's fast, but buffered data may be lost if the Fluentd pod restarts.
-   `@type file`: Buffers logs to the filesystem. Since data is preserved even if the pod restarts, using **file-based buffering** is strongly recommended for production environments. Mounting a `PersistentVolume` to the `path` makes it even more robust.
-   Combine options like `retry_type exponential_backoff` and `retry_forever true` to ensure reliable retries until Elasticsearch recovers.

### 3. Application-Level Structured Logging

While Fluentd's parsing filters are powerful, complex regular expressions (regex) can increase CPU usage and degrade processing performance. The best practice is for applications to output **structured logs, such as in JSON format**, from the beginning.

**Bad (Unstructured):**
`INFO: User 'admin' logged in successfully from IP 192.168.1.10`

**Good (Structured JSON):**
`{"level": "info", "message": "User login successful", "user": "admin", "source_ip": "192.168.1.10"}`

With structured logs, Fluentd can send data directly to Elasticsearch without complex parsing, and in Kibana, you can perform precise and fast field-based searches like `user:admin`.

## Conclusion

We have explored in detail how to build a production-level centralized logging system in a Kubernetes environment using the **Fluentd, Elasticsearch, and Kibana (EFK) stack**, covering everything from architecture to practical configurations and optimization tips. A stable centralized logging system is an essential infrastructure for achieving **observability** in a complex microservices environment, enabling rapid incident response and improving service quality.

The configurations presented in this post are a starting point for building an EFK stack. In a real-world operational environment, you must continuously enhance the architecture to meet business requirements and workload characteristics, including monitoring the resource usage of each component, strengthening security settings (TLS, authentication/authorization), and adding a Fluentd Aggregator layer for high-volume traffic. We hope this guide serves as an excellent foundation for building a powerful logging system in your Kubernetes cluster.

### References
- [Fluentd Official Documentation](https://docs.fluentd.org/ "Fluentd Documentation"){:target="_blank"}
- [Elasticsearch Official Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html "Elasticsearch Reference"){:target="_blank"}
- [Kibana Official Guide](https://www.elastic.co/guide/en/kibana/current/index.html "Kibana Guide"){:target="_blank"}
- [Kubernetes Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/ "Kubernetes Logging Documentation"){:target="_blank"}
---