---
layout: post
title: "쿠버네티스 환경을 위한 Fluentd 기반 프로덕션 레벨 중앙 로깅 시스템 완벽 구축 가이드"
slug: "building-production-level-centralized-logging-system-with-fluentd-on-kubernetes"
date: 2026-05-04 10:03:05 +0900
categories: [DevOps, Cloud]
tags: [Kubernetes, Fluentd, Elasticsearch, Kibana, Logging, EFK, Observability]
description: "프로덕션 쿠버네티스 클러스터에서 발생하는 대규모 로그를 효율적으로 수집, 처리, 분석하기 위해 Fluentd, Elasticsearch, Kibana (EFK) 스택을 활용한 중앙 로깅 시스템 구축 방법을 심도 있게 다룹니다. 실무 중심의 설정과 최적화 팁을 확인하세요."
---

마이크로서비스 아키텍처(MSA)가 보편화되면서 쿠버네티스는 컨테이너 오케스트레이션의 표준으로 자리 잡았습니다. 수많은 컨테이너가 동적으로 생성되고 사라지는 쿠버네티스 환경에서, 분산된 애플리케이션 로그를 추적하고 문제를 해결하는 것은 기존의 방식으로는 거의 불가능에 가깝습니다. 각 파드(Pod)에 접속하여 `kubectl logs` 명령어로 로그를 확인하는 것은 임시방편일 뿐, 실시간 장애 대응과 근본 원인 분석에는 한계가 명확합니다.

이러한 문제를 해결하기 위해 **중앙 로깅 시스템(Centralized Logging System)** 구축은 선택이 아닌 필수가 되었습니다. 중앙 로깅 시스템은 클러스터 전체에서 발생하는 모든 로그를 단일 위치로 수집, 정제, 저장하여 개발자와 운영자가 손쉽게 검색하고 시각화할 수 있도록 지원합니다. 본 포스트에서는 CNCF(Cloud Native Computing Foundation)의 졸업 프로젝트이자 강력한 로그 수집기인 **Fluentd**를 중심으로, **Elasticsearch**, **Kibana**를 조합한 **EFK(Elasticsearch, Fluentd, Kibana) 스택**을 활용하여 프로덕션 레벨의 쿠버네티스 중앙 로깅 시스템을 구축하는 모든 과정을 심도 있게 다룹니다.

<!--more-->
![쿠버네티스 환경을 위한 Fluentd 기반 프로덕션 레벨 중앙 로깅 시스템 완벽 구축 가이드](/uploads/building-production-level-centralized-logging-system-with-fluentd-on-kubernetes/thumbnail.webp "쿠버네티스 환경을 위한 Fluentd 기반 프로덕션 레벨 중앙 로깅 시스템 완벽 구축 가이드")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 도입 배경 및 문제 정의: 왜 쿠버네티스에는 중앙 로깅이 필수적인가?

쿠버네티스 환경에서의 로깅은 다음과 같은 복잡성과 어려움을 가지고 있습니다.

1.  **로그의 비영속성(Ephemeral Nature):** 파드는 언제든지 재시작되거나 다른 노드로 스케줄링될 수 있습니다. 파드가 사라지면 해당 컨테이너의 로그 또한 함께 사라져 장애 분석에 필요한 중요한 정보를 영원히 잃게 됩니다.
2.  **분산된 로그 위치:** 수백, 수천 개의 파드에서 생성되는 로그는 클러스터 내의 여러 노드에 분산되어 저장됩니다. 특정 트랜잭션과 관련된 로그를 찾기 위해 여러 파드와 노드를 넘나들며 추적하는 것은 엄청난 시간과 노력을 소모합니다.
3.  **다양한 로그 형식:** 각 애플리케이션이나 시스템 컴포넌트는 저마다 다른 형식으로 로그를 출력합니다. 이 비정형 데이터를 그대로 수집하면 검색과 분석의 효율이 크게 떨어집니다.
4.  **컨텍스트 정보의 부재:** 단순히 로그 메시지만으로는 부족합니다. 해당 로그가 어떤 `네임스페이스`, `파드`, `컨테이너`에서 발생했는지와 같은 쿠버네티스 메타데이터 정보가 함께 있어야만 정확한 문제 파악이 가능합니다.

**EFK 스택**은 이러한 문제들을 해결하기 위한 검증된 솔루션입니다. **Fluentd**는 각 노드에서 로그를 수집하고 쿠버네티스 메타데이터를 첨부하여 정제한 뒤, **Elasticsearch**로 안정적으로 전송하는 역할을 합니다. **Elasticsearch**는 대규모 로그 데이터를 빠르게 검색하고 분석할 수 있도록 인덱싱하여 저장하며, **Kibana**는 저장된 데이터를 사용자가 직관적으로 탐색하고 대시보드를 통해 시각화할 수 있는 강력한 웹 UI를 제공합니다.

## 핵심 아키텍처 및 원리: EFK 스택은 쿠버네티스에서 어떻게 동작하는가?

쿠버네티스 환경에서 EFK 스택의 일반적인 로그 파이프라인은 다음과 같은 흐름으로 구성됩니다.

1.  **로그 생성 (Application Pods):** 애플리케이션은 표준 출력(`stdout`)이나 표준 에러(`stderr`)로 로그를 출력합니다. 컨테이너 런타임(Docker, containerd 등)은 이 로그들을 잡아 각 노드의 특정 디렉토리(예: `/var/log/containers/`)에 파일 형태로 저장합니다.
2.  **로그 수집 (Fluentd DaemonSet):** **Fluentd**는 **데몬셋(DaemonSet)** 형태로 클러스터의 모든 노드에 배포됩니다. 각 노드에 배포된 Fluentd 파드는 호스트의 로그 디렉토리를 볼륨 마운트하여 컨테이너 로그 파일들을 실시간으로 감시(`tail`)합니다.
3.  **로그 처리 및 강화 (Fluentd Filter Plugins):** Fluentd는 수집한 로그를 파싱하여 비정형 텍스트를 JSON과 같은 구조화된 데이터로 변환합니다. 특히 `fluent-plugin-kubernetes_metadata_filter` 플러그인을 사용하여 로그 파일 이름으로부터 `pod_name`, `namespace`, `container_name`, `labels` 등의 쿠버네티스 메타데이터를 추출하고 로그에 동적으로 추가합니다.
4.  **로그 전송 (Fluentd Output Plugins):** 풍부한 메타데이터가 추가된 정제된 로그는 Fluentd의 버퍼링 메커니즘을 통해 안정적으로 **Elasticsearch** 클러스터로 전송됩니다. 네트워크 문제나 Elasticsearch 장애 시 로그 유실을 방지하기 위해 재시도 로직이 동작합니다.
5.  **저장 및 인덱싱 (Elasticsearch):** Elasticsearch는 전송받은 로그 데이터를 인덱싱하여 저장합니다. 이를 통해 수십억 건의 로그 데이터 속에서도 밀리초 단위의 빠른 전문(Full-text) 검색이 가능해집니다.
6.  **시각화 및 분석 (Kibana):** 사용자는 웹 브라우저를 통해 **Kibana**에 접속하여 Elasticsearch에 저장된 로그를 검색, 필터링하고 시각화 대시보드를 구성하여 클러스터의 상태를 한눈에 파악할 수 있습니다.

이러한 아키텍처는 각 컴포넌트의 역할을 명확히 분리하여 확장성과 안정성을 높이고, 개발자가 로깅 인프라를 신경 쓰지 않고 애플리케이션 개발에만 집중할 수 있는 환경을 제공합니다.

## 실무 적용 코드/설정 딥다이브

이제 실제 쿠버네티스 클러스터에 EFK 스택을 구축하는 과정을 단계별로 살펴보겠습니다. 여기서는 편의상 `logging` 네임스페이스에 모든 리소스를 배포하는 것을 가정합니다.

### 1단계: Elasticsearch 및 Kibana 배포

프로덕션 환경에서는 Elasticsearch 클러스터의 안정적인 운영을 위해 [Elastic Cloud on Kubernetes (ECK) Operator](https://www.elastic.co/guide/en/cloud-on-k8s/current/index.html "Elastic Cloud on Kubernetes 공식 문서"){:target="_blank"}나 Helm 차트를 사용하는 것이 일반적입니다. 여기서는 기본적인 이해를 돕기 위해 간단한 StatefulSet과 Deployment 매니페스트를 사용합니다.

#### Elasticsearch StatefulSet

안정적인 데이터 저장을 위해 `PersistentVolumeClaim`을 사용하는 `StatefulSet`으로 Elasticsearch를 배포합니다.

```yaml
# elasticsearch-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 1 # 프로덕션 환경에서는 3 이상을 권장합니다.
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
          value: single-node # 단일 노드 설정. 클러스터 구성 시 변경 필요
        - name: ES_JAVA_OPTS
          value: "-Xms1g -Xmx1g" # requests.memory와 일치시키는 것이 좋습니다.
        - name: xpack.security.enabled
          value: "false" # 데모 목적으로 보안 기능 비활성화
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "gp2" # 사용하는 스토리지 클래스로 변경
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
  type: LoadBalancer # 외부 접근을 위해 LoadBalancer 또는 Ingress 사용
  selector:
    app: kibana
  ports:
  - port: 5601
    targetPort: 5601
```

### 2단계: Fluentd DaemonSet 배포

Fluentd가 각 노드의 로그를 수집하고 쿠버네티스 API에 접근하여 메타데이터를 가져올 수 있도록 `ServiceAccount`, `ClusterRole`, `ClusterRoleBinding`을 먼저 설정해야 합니다.

#### RBAC 설정

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

#### Fluentd ConfigMap 및 DaemonSet

Fluentd의 동작을 정의하는 설정 파일을 `ConfigMap`으로 생성하고, 이를 참조하는 `DaemonSet`을 배포합니다.

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

모든 리소스를 배포한 후, 잠시 기다리면 Kibana 서비스의 외부 IP를 통해 대시보드에 접속할 수 있습니다. `Discover` 탭으로 이동하여 `fluentd-*` 패턴으로 인덱스를 생성하면 클러스터의 모든 로그가 실시간으로 수집되는 것을 확인할 수 있습니다.

## 성능 최적화 및 Best Practices

프로덕션 환경에서 EFK 스택을 안정적으로 운영하기 위해서는 몇 가지 추가적인 고려사항이 필요합니다.

### 1. Elasticsearch 인덱스 생명주기 관리 (ILM)

로그 데이터는 시간이 지남에 따라 기하급수적으로 증가하여 스토리지 비용과 검색 성능 저하를 유발합니다. Elasticsearch의 **ILM(Index Lifecycle Management)** 기능을 사용하면 인덱스를 자동으로 관리할 수 있습니다.

-   **Hot Phase:** 데이터가 활발하게 인덱싱되고 검색되는 단계입니다. 고성능 스토리지를 사용합니다.
-   **Warm Phase:** 데이터 쓰기는 없지만 여전히 검색이 필요한 단계입니다. 인덱스를 축소(shrink)하고 저렴한 스토리지로 이전할 수 있습니다.
-   **Cold/Frozen Phase:** 거의 검색되지 않는 오래된 데이터입니다. 검색 가능 상태를 유지하면서 스토리지 사용량을 최소화합니다.
-   **Delete Phase:** 보존 기간이 지난 데이터는 자동으로 삭제하여 저장 공간을 확보합니다.

예를 들어, 30일이 지난 로그는 자동으로 삭제하는 ILM 정책을 Kibana Dev Tools에서 설정할 수 있습니다.

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

### 2. Fluentd 버퍼링 전략

위 `fluentd.conf` 예시에서도 사용했지만, Fluentd의 **버퍼링(buffering)**은 로그 파이프라인의 안정성을 보장하는 핵심 기능입니다. 네트워크 문제나 Elasticsearch의 일시적인 장애 상황에서 로그가 유실되는 것을 방지합니다.

-   `@type memory`: 메모리에 로그를 버퍼링합니다. 빠르지만 Fluentd 파드가 재시작되면 버퍼링된 데이터가 유실될 위험이 있습니다.
-   `@type file`: 파일 시스템에 로그를 버퍼링합니다. 파드가 재시작되어도 데이터가 보존되므로 프로덕션 환경에서는 **파일 기반 버퍼링**을 사용하는 것이 강력히 권장됩니다. `path`에 `PersistentVolume`을 마운트하여 사용하면 더욱 안정적입니다.
-   `retry_type exponential_backoff`, `retry_forever true` 등의 옵션을 조합하여 Elasticsearch가 복구될 때까지 안정적으로 재시도를 수행하도록 설정해야 합니다.

### 3. 애플리케이션 레벨의 구조화된 로깅 (Structured Logging)

Fluentd의 파싱 필터는 강력하지만, 복잡한 정규 표현식(regex)은 CPU 사용량을 높이고 처리 성능을 저하시킬 수 있습니다. 가장 좋은 방법은 처음부터 애플리케이션에서 **JSON 형식과 같은 구조화된 로그**를 출력하는 것입니다.

**Bad (Unstructured):**
`INFO: User 'admin' logged in successfully from IP 192.168.1.10`

**Good (Structured JSON):**
`{"level": "info", "message": "User login successful", "user": "admin", "source_ip": "192.168.1.10"}`

구조화된 로그를 사용하면 Fluentd는 복잡한 파싱 과정 없이 데이터를 바로 Elasticsearch로 전송할 수 있으며, Kibana에서도 `user:admin`과 같이 필드 기반의 정확하고 빠른 검색이 가능해집니다.

## 결론

지금까지 쿠버네티스 환경에서 **Fluentd, Elasticsearch, Kibana (EFK) 스택**을 활용하여 프로덕션 레벨의 중앙 로깅 시스템을 구축하는 방법을 아키텍처부터 실무 설정, 최적화 팁까지 상세하게 살펴보았습니다. 안정적인 중앙 로깅 시스템은 복잡한 마이크로서비스 환경의 **관측 가능성(Observability)**을 확보하고, 신속한 장애 대응과 서비스 품질 향상을 위한 필수적인 기반 인프라입니다.

본문에서 제시된 설정은 EFK 스택 구축의 시작점입니다. 실제 운영 환경에서는 각 컴포넌트의 리소스 사용량 모니터링, 보안 설정 강화(TLS, 인증/인가), 대규모 트래픽을 위한 Fluentd Aggregator 레이어 추가 등 비즈니스 요구사항과 워크로드 특성에 맞게 아키텍처를 지속적으로 고도화해나가야 합니다. 이 가이드가 여러분의 쿠버네티스 클러스터에 강력한 로깅 시스템을 구축하는 데 훌륭한 밑거름이 되기를 바랍니다.

### 참고문헌
- [Fluentd 공식 문서](https://docs.fluentd.org/ "Fluentd Documentation"){:target="_blank"}
- [Elasticsearch 공식 가이드](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html "Elasticsearch Reference"){:target="_blank"}
- [Kibana 공식 가이드](https://www.elastic.co/guide/en/kibana/current/index.html "Kibana Guide"){:target="_blank"}
- [Kubernetes Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/ "Kubernetes Logging Documentation"){:target="_blank"}