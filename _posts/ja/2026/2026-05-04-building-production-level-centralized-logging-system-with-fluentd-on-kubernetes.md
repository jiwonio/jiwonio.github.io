---
layout: post
title: Kubernetes環境のためのFluentdベースの本番レベル中央集権ログシステム構築完全ガイド
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
description: 本番環境のKubernetesクラスタで発生する大規模ログを効率的に収集、処理、分析するため、Fluentd、Elasticsearch、
  Kibana（EFK）スタックを活用した中央集権ログシステムの構築方法を深く掘り下げます。実践的な設定と最適化のヒントを紹介します。
image: /uploads/building-production-level-centralized-logging-system-with-fluentd-on-kubernetes/thumbnail.webp
lang: ja
translation_key: building-production-level-centralized-logging-system-with-fluentd-on-kubernetes
permalink: /ja/posts/building-production-level-centralized-logging-system-with-fluentd-on-kubernetes/
post_type: deep-dive
ai_generated: true
updated: 2026-05-04 10:03:05 +0900
---
マイクロサービスアーキテクチャ（MSA）が一般化するにつれて、Kubernetesはコンテナオーケストレーションの標準としての地位を確立しました。数多くのコンテナが動的に生成・消滅するKubernetes環境において、分散したアプリケーションログを追跡し、問題を解決することは、従来の方法ではほとんど不可能です。各Podに接続して`kubectl logs`コマンドでログを確認するのは一時しのぎに過ぎず、リアルタイムの障害対応や根本原因の分析には明らかな限界があります。

これらの問題を解決するために、**中央集権ログシステム（Centralized Logging System）**の構築は選択肢ではなく必須となりました。中央集権ログシステムは、クラスタ全体で発生するすべてのログを単一の場所に収集、整形、保存し、開発者と運用者が容易に検索・可視化できるように支援します。本稿では、CNCF（Cloud Native Computing Foundation）の卒業プロジェクトであり、強力なログコレクターである**Fluentd**を中心に、**Elasticsearch**、**Kibana**を組み合わせた**EFK（Elasticsearch, Fluentd, Kibana）スタック**を活用し、本番レベルのKubernetes中央集権ログシステムを構築する全プロセスを深く掘り下げて解説します。

<!--more-->
![Kubernetes環境のためのFluentdベースの本番レベル中央集権ログシステム構築完全ガイド](/uploads/building-production-level-centralized-logging-system-with-fluentd-on-kubernetes/thumbnail.webp "Kubernetes環境のためのFluentdベースの本番レベル中央集権ログシステム構築完全ガイド")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI生成画像</small>
</p>
-----

## 導入背景と問題定義：なぜKubernetesには中央集権ログが必要不可欠なのか？

Kubernetes環境におけるロギングは、以下のような複雑さと困難さを伴います。

1.  **ログの非永続性（Ephemeral Nature）:** Podはいつでも再起動されたり、他のノードにスケジューリングされたりする可能性があります。Podが消えると、該当コンテナのログも一緒に消え、障害分析に必要な重要な情報を永遠に失ってしまいます。
2.  **分散したログの場所:** 数百、数千のPodから生成されるログは、クラスタ内の複数のノードに分散して保存されます。特定のトランザクションに関連するログを見つけるために、複数のPodやノードを横断して追跡するのは、膨大な時間と労力を消費します。
3.  **多様なログ形式:** 各アプリケーションやシステムコンポーネントは、それぞれ異なる形式でログを出力します。この非構造化データをそのまま収集すると、検索と分析の効率が大幅に低下します。
4.  **コンテキスト情報の欠如:** 単なるログメッセージだけでは不十分です。そのログがどの`ネームスペース`、`Pod`、`コンテナ`で発生したかといったKubernetesのメタデータ情報が伴って初めて、正確な問題把握が可能になります。

**EFKスタック**は、これらの問題を解決するための実績あるソリューションです。**Fluentd**は各ノードでログを収集し、Kubernetesメタデータを付与して整形した後、**Elasticsearch**へ安定的に転送する役割を担います。**Elasticsearch**は大規模なログデータを迅速に検索・分析できるようインデックス化して保存し、**Kibana**は保存されたデータをユーザーが直感的に探索し、ダッシュボードを通じて可視化できる強力なウェブUIを提供します。

## コアアーキテクチャと原理：EFKスタックはKubernetesでどのように動作するのか？

Kubernetes環境におけるEFKスタックの一般的なログパイプラインは、次のようなフローで構成されます。

1.  **ログ生成（Application Pods）:** アプリケーションは標準出力（`stdout`）や標準エラー（`stderr`）にログを出力します。コンテナランタイム（Docker, containerdなど）はこれらのログをキャッチし、各ノードの特定のディレクトリ（例: `/var/log/containers/`）にファイル形式で保存します。
2.  **ログ収集（Fluentd DaemonSet）:** **Fluentd**は**DaemonSet**としてクラスタの全ノードにデプロイされます。各ノードにデプロイされたFluentd Podは、ホストのログディレクトリをボリュームマウントし、コンテナログファイルをリアルタイムで監視（`tail`）します。
3.  **ログ処理と強化（Fluentd Filter Plugins）:** Fluentdは収集したログをパースし、非構造化テキストをJSONのような構造化データに変換します。特に`fluent-plugin-kubernetes_metadata_filter`プラグインを使用し、ログファイル名から`pod_name`、`namespace`、`container_name`、`labels`などのKubernetesメタデータを抽出し、ログに動的に追加します。
4.  **ログ転送（Fluentd Output Plugins）:** 豊富なメタデータが追加された整形済みのログは、Fluentdのバッファリングメカニズムを通じて安定的に**Elasticsearch**クラスタに転送されます。ネットワーク問題やElasticsearchの障害時にログの損失を防ぐため、リトライロジックが動作します。
5.  **保存とインデックス作成（Elasticsearch）:** Elasticsearchは転送されたログデータをインデックス化して保存します。これにより、数十億件のログデータの中からでもミリ秒単位の高速な全文検索が可能になります。
6.  **可視化と分析（Kibana）:** ユーザーはウェブブラウザを通じて**Kibana**にアクセスし、Elasticsearchに保存されたログを検索、フィルタリングし、可視化ダッシュボードを構成してクラスタの状態を一目で把握できます。

このようなアーキテクチャは、各コンポーネントの役割を明確に分離することで拡張性と安定性を高め、開発者がロギングインフラを気にすることなくアプリケーション開発に集中できる環境を提供します。

## 実践的コード/設定のディープダイブ

それでは、実際のKubernetesクラスタにEFKスタックを構築するプロセスをステップバイステップで見ていきましょう。ここでは便宜上、`logging`ネームスペースにすべてのリソースをデプロイすることを前提とします。

### ステップ1：ElasticsearchとKibanaのデプロイ

本番環境では、Elasticsearchクラスタの安定した運用のため、[Elastic Cloud on Kubernetes (ECK) Operator](https://www.elastic.co/guide/en/cloud-on-k8s/current/index.html "Elastic Cloud on Kubernetes公式ドキュメント"){:target="_blank"}やHelmチャートを使用するのが一般的です。ここでは基本的な理解を助けるため、シンプルなStatefulSetとDeploymentマニフェストを使用します。

#### Elasticsearch StatefulSet

安定したデータ保存のため、`PersistentVolumeClaim`を使用する`StatefulSet`でElasticsearchをデプロイします。

```yaml
# elasticsearch-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 1 # 本番環境では3以上を推奨します。
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
          value: single-node # シングルノード設定。クラスタ構成時には変更が必要です。
        - name: ES_JAVA_OPTS
          value: "-Xms1g -Xmx1g" # requests.memoryと一致させることをお勧めします。
        - name: xpack.security.enabled
          value: "false" # デモ目的でセキュリティ機能を無効化
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "gp2" # 使用するストレージクラスに変更してください
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
  type: LoadBalancer # 外部アクセスのためにLoadBalancerまたはIngressを使用します
  selector:
    app: kibana
  ports:
  - port: 5601
    targetPort: 5601
```

### ステップ2：Fluentd DaemonSetのデプロイ

Fluentdが各ノードのログを収集し、Kubernetes APIにアクセスしてメタデータを取得できるよう、まず`ServiceAccount`、`ClusterRole`、`ClusterRoleBinding`を設定する必要があります。

#### RBAC設定

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

#### Fluentd ConfigMapとDaemonSet

Fluentdの動作を定義する設定ファイルを`ConfigMap`として作成し、それを参照する`DaemonSet`をデプロイします。

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

すべてのリソースをデプロイした後、しばらく待つとKibanaサービスの外部IPを通じてダッシュボードにアクセスできます。`Discover`タブに移動し、`fluentd-*`パターンでインデックスを作成すれば、クラスタのすべてのログがリアルタイムで収集されていることを確認できます。

## パフォーマンス最適化とベストプラクティス

本番環境でEFKスタックを安定して運用するためには、いくつかの追加的な考慮事項が必要です。

### 1. Elasticsearchインデックスライフサイクル管理（ILM）

ログデータは時間の経過とともに指数関数的に増加し、ストレージコストと検索パフォーマンスの低下を引き起こします。Elasticsearchの**ILM（Index Lifecycle Management）**機能を使用すると、インデックスを自動的に管理できます。

-   **Hot Phase:** データが活発にインデックス化され、検索される段階です。高性能なストレージを使用します。
-   **Warm Phase:** データの書き込みはありませんが、まだ検索が必要な段階です。インデックスを縮小（shrink）し、より安価なストレージに移行できます。
-   **Cold/Frozen Phase:** ほとんど検索されない古いデータです。検索可能な状態を維持しつつ、ストレージ使用量を最小限に抑えます。
-   **Delete Phase:** 保存期間が過ぎたデータは自動的に削除し、ストレージスペースを確保します。

例えば、30日経過したログを自動的に削除するILMポリシーをKibana Dev Toolsで設定できます。

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

### 2. Fluentdのバッファリング戦略

上記の`fluentd.conf`の例でも使用しましたが、Fluentdの**バッファリング（buffering）**は、ログパイプラインの安定性を保証するコア機能です。ネットワークの問題やElasticsearchの一時的な障害状況でログが失われるのを防ぎます。

-   `@type memory`: メモリにログをバッファリングします。高速ですが、Fluentd Podが再起動するとバッファリングされたデータが失われるリスクがあります。
-   `@type file`: ファイルシステムにログをバッファリングします。Podが再起動してもデータが保持されるため、本番環境では**ファイルベースのバッファリング**を使用することが強く推奨されます。`path`に`PersistentVolume`をマウントして使用すると、さらに安定性が増します。
-   `retry_type exponential_backoff`、`retry_forever true`などのオプションを組み合わせ、Elasticsearchが復旧するまで安定的にリトライを実行するように設定する必要があります。

### 3. アプリケーションレベルの構造化ロギング（Structured Logging）

Fluentdのパースフィルターは強力ですが、複雑な正規表現（regex）はCPU使用率を高め、処理性能を低下させる可能性があります。最善の方法は、最初からアプリケーションで**JSON形式のような構造化ログ**を出力することです。

**悪い例（非構造化）：**
`INFO: User 'admin' logged in successfully from IP 192.168.1.10`

**良い例（構造化JSON）：**
`{"level": "info", "message": "User login successful", "user": "admin", "source_ip": "192.168.1.10"}`

構造化ログを使用すると、Fluentdは複雑なパース処理なしにデータを直接Elasticsearchに転送でき、Kibanaでも`user:admin`のようにフィールドベースの正確で高速な検索が可能になります。

## 結論

ここまで、Kubernetes環境で**Fluentd、Elasticsearch、Kibana（EFK）スタック**を活用し、本番レベルの中央集権ログシステムを構築する方法を、アーキテクチャから実践的な設定、最適化のヒントまで詳細に見てきました。安定した中央集権ログシステムは、複雑なマイクロサービス環境の**可観測性（Observability）**を確保し、迅速な障害対応とサービス品質向上のための必須の基盤インフラです。

本文で提示された設定は、EFKスタック構築の出発点です。実際の運用環境では、各コンポーネントのリソース使用量の監視、セキュリティ設定の強化（TLS、認証/認可）、大規模トラフィックのためのFluentd Aggregatorレイヤーの追加など、ビジネス要件とワークロードの特性に合わせてアーキテクチャを継続的に高度化していく必要があります。このガイドが、皆さんのKubernetesクラスタに強力なロギングシステムを構築する上で、素晴らしい土台となることを願っています。

### 参考文献
- [Fluentd 公式ドキュメント](https://docs.fluentd.org/ "Fluentd Documentation"){:target="_blank"}
- [Elasticsearch 公式ガイド](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html "Elasticsearch Reference"){:target="_blank"}
- [Kibana 公式ガイド](https://www.elastic.co/guide/en/kibana/current/index.html "Kibana Guide"){:target="_blank"}
- [Kubernetes Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/ "Kubernetes Logging Documentation"){:target="_blank"}