---
layout: post
title: 本番環境向けWebアプリケーション監視：PrometheusとGrafanaによる完全構築ガイド
slug: production-monitoring-with-prometheus-and-grafana
date: 2026-04-20 15:00:01 +0900
categories:
- DevOps
- Backend
tags:
- Prometheus
- Grafana
- Monitoring
- Observability
- Docker
- DevOps
description: サーバーエンジニアと開発者のための、PrometheusとGrafanaを活用したリアルタイム監視システム構築完全ガイド。Dockerベースの設定、カスタムメトリクスの計測、PromQLクエリ、パフォーマンス最適化のベストプラクティスを解説します。
image: /uploads/production-monitoring-with-prometheus-and-grafana/thumbnail.webp
lang: ja
translation_key: production-monitoring-with-prometheus-and-grafana
permalink: /ja/posts/production-monitoring-with-prometheus-and-grafana/
post_type: deep-dive
---
成功するWebサービスの運営の核心は、単に機能を実装すること以上に、サービスが「生きている」間にどのような状態にあるかを継続的に観察し、問題を予測することにあります。ユーザーがサービス障害を経験する前に潜在的なボトルネックを特定し、リソース使用量の推移を分析してインフラを効率的に拡張することは、すべての熟練したエンジニアにとって必須の能力です。しかし、分散したマイクロサービスアーキテクチャ環境で、数多くのサーバーとアプリケーションの状態を断片的に管理することは、ほとんど不可能に近いでしょう。

このような問題を解決するために、現代のDevOps環境では**Prometheus**と**Grafana**の組み合わせが事実上の標準（De facto standard）として定着しています。Prometheusは強力な時系列データベース（TSDB）を基盤にシステムとアプリケーションのメトリクスを収集し、Grafanaは収集されたデータを視覚的に美しく直感的なダッシュボードで表現します。この組み合わせを通じて、私たちは分散システムの状況を中央で一目で把握し、異常の兆候を早期に発見して迅速に対応できる強力な「可観測性（Observability）」を確保することができます。本記事では、Dockerを活用して本番環境に即時適用可能なPrometheusおよびGrafana監視スタックを構築し、アプリケーションの主要なビジネスメトリクスを直接計測して可視化する全プロセスを深く掘り下げていきます。

<!--more-->
![本番環境向けWebアプリケーション監視：PrometheusとGrafanaによる完全構築ガイド](/uploads/production-monitoring-with-prometheus-and-grafana/thumbnail.webp "本番環境向けWebアプリケーション監視：PrometheusとGrafanaによる完全構築ガイド")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI生成画像</small>
</p>
-----

## 導入背景と問題定義：なぜ監視が必須なのか？

「私のPCではちゃんと動くのですが」という言葉は、本番環境では何の意味も持ちません。開発環境と実際のサービス環境は、ネットワークの遅延、トラフィックの負荷、リソースの競合など、数多くの変数で異なるためです。安定したサービスを提供するためには、次のような質問にリアルタイムで答えられる必要があります。

-   現在のサーバーのCPU、メモリ、ディスク使用量は安定的か？
-   秒間処理リクエスト数（RPS）はどれくらいで、平均応答時間はどの程度か？
-   全リクエスト中のエラー率は何パーセントか？
-   データベースのコネクションプ-ルは十分に確保されているか？
-   特定の機能のAPI呼び出し遅延時間が急増していないか？

これらの質問に答えられなければ、私たちは障害が発生した後に事後対応をする「後の祭り」状態に陥ってしまいます。**PrometheusとGrafanaを活用した監視システムの構築**は、このような状況を未然に防ぎ、データに基づいてシステムの健全性を診断し最適化する、プロアクティブエンジニアリングの第一歩です。

## 主要アーキテクチャと原理

Prometheusベースの監視システムは、いくつかの主要コンポーネントで構成されています。各要素の役割とデータの流れを理解することが重要です。


> **注釈:** 上記は画像の代わりにテキストでアーキテクチャを説明するための例です。

| コンポーネント          | 役割と特徴                                                                                                                              |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Prometheus Server**   | 中核となるエンジン。周期的に監視対象（Target）のHTTPエンドポイント（`_/_metrics_`）を**Pull（スクレイプ）**し、時系列データ（Time-Series Data）を収集・保存します。 |
| **Exporter**            | データベース、ハードウェアなど、Prometheusメトリクスを直接公開しないシステムのデータを収集し、Prometheusが理解できるフォーマットに変換するエージェントです。（例：`node_exporter`、`postgres_exporter`） |
| **Client Library**      | 開発者が作成したアプリケーションコード内に、直接メトリクス収集ロジックを追加（計装、Instrumentation）するのを助けるライブラリです。（例：`prom-client` for Node.js、`django-prometheus` for Django） |
| **Grafana**             | Prometheusサーバーに保存されたデータを**PromQL（Prometheus Query Language）**を通じて照会し、ユーザーフレンドリーなグラフやダッシュボードで可視化するツールです。 |
| **Alertmanager**        | Prometheusに定義されたルール（Alerting Rule）に基づき、特定の条件が満たされるとメール、Slackなど様々なチャネルに警告を送信する役割を担います。 |

Prometheusの最大の特徴は**Pullベースのアーキテクチャ**です。監視対象がデータをサーバーにプッシュ（Push）する方式とは異なり、Prometheusサーバーが能動的に対象を訪れてデータを取得します。これにより、監視対象の状態をPrometheusが直接確認でき、設定ファイル一つで全体の監視対象を中央で管理できるという利点があります。

## 実務適用コード/設定ディープダイブ

それでは、Docker Composeを使用してローカル環境に完全な監視スタックを構築し、簡単なNode.jsアプリケーションを直接計装してみましょう。

### 1. プロジェクト構造

以下のようなディレクトリ構造を作成します。

```
monitoring-stack/
├── docker-compose.yml
├── prometheus/
│   └── prometheus.yml
└── app/
    ├── index.js
    └── package.json
```

### 2. Docker Compose設定 (`docker-compose.yml`)

Prometheus、Grafana、そしてシステムメトリクス収集のための`node_exporter`をサービスとして定義します。

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.44.0
    container_name: prometheus
    volumes:
      - ./prometheus:/etc/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:9.5.1
    container_name: grafana
    ports:
      - "3000:3000"
    restart: unless-stopped
    depends_on:
      - prometheus

  node_exporter:
    image: prom/node-exporter:v1.6.0
    container_name: node_exporter
    ports:
      - "9100:9100"
    restart: unless-stopped

  app:
    build: ./app
    container_name: web_app
    ports:
      - "8080:8080"
    restart: unless-stopped
```

### 3. Prometheus設定 (`prometheus/prometheus.yml`)

Prometheusがどの対象をスクレイプするかを定義する、中核となる設定ファイルです。

```yaml
global:
  scrape_interval: 15s # デフォルトのスクレイプ間隔

scrape_configs:
  - job_name: 'prometheus'
    # Prometheus自身を監視
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    # Docker内部ネットワークを通じてコンテナ名でアクセス
    static_configs:
      - targets: ['node_exporter:9100']

  - job_name: 'web_app'
    # 我々が作成するWebアプリケーションを監視
    static_configs:
      - targets: ['web_app:8080']
```

### 4. Node.jsアプリケーションの計装 (`app/`)

`prom-client`ライブラリを使用して、カスタムメトリクスを公開する簡単なExpressサーバーを作成します。

**`app/package.json`**
```json
{
  "name": "monitored-app",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "prom-client": "^14.2.0"
  }
}
```

**`app/Dockerfile`**
```dockerfile
FROM node:18-alpine
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 8080
CMD [ "npm", "start" ]
```

**`app/index.js`**
```javascript
const express = require('express');
const client = require('prom-client');
const app = express();
const port = 8080;

// Prometheusメトリクスレジストリを作成
const register = new client.Registry();
client.collectDefaultMetrics({ register }); // デフォルトのNode.jsメトリクスを収集

// 1. Counter: 累積する値（例：総HTTPリクエスト数）
const httpRequestCounter = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'path', 'status_code'],
  registers: [register],
});

// 2. Gauge: 現在の状態を表す値（例：現在のアクティブユーザー数）
const activeUsersGauge = new client.Gauge({
  name: 'active_users',
  help: 'Number of active users',
  registers: [register],
});

// 3. Histogram: 観測値の分布をバケットで記録（例：HTTPリクエストの遅延時間）
const httpRequestDurationMicroseconds = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'path', 'status_code'],
  buckets: [0.1, 0.5, 1, 1.5], // 0.1秒、0.5秒、1秒、1.5秒以下で区分
  registers: [register],
});

app.use((req, res, next) => {
  // レスポンスが終了する時点を測定するためのタイマーを開始
  res.locals.startEpoch = Date.now();
  next();
});

app.get('/', (req, res) => {
  setTimeout(() => {
    // 応答遅延時間を計算
    const responseTimeInMs = Date.now() - res.locals.startEpoch;
    httpRequestDurationMicroseconds
      .labels(req.method, req.path, 200)
      .observe(responseTimeInMs / 1000); // 秒単位に変換
    
    httpRequestCounter.labels(req.method, req.path, 200).inc();
    res.send('Hello World!');
  }, Math.random() * 1000); // 0～1秒間のランダムな遅延
});

// メトリクスを公開する /metrics エンドポイント
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// 仮想的にアクティブユーザー数を変動させるロジック
setInterval(() => {
  const activeUsers = Math.round(Math.random() * 100);
  activeUsersGauge.set(activeUsers);
}, 5000);

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`);
});
```

### 5. スタックの実行と確認

プロジェクトの最上位ディレクトリ（`monitoring-stack/`）で以下のコマンドを実行します。

```bash
docker-compose up -d
```

-   **Prometheus UI:** ブラウザで `http://localhost:9090` にアクセスし、「Status」>「Targets」メニューに移動すると、`prometheus`、`node_exporter`、`web_app`の3つのターゲットが「UP」状態であることを確認できます。
-   **Grafana UI:** `http://localhost:3000` にアクセスします。（デフォルトID/PW: `admin`/`admin`）。
    1.  **データソースの追加:** 左側メニューの歯車アイコン（Configuration）> Data Sources > Add data source > Prometheusを選択。
    2.  URLに `http://prometheus:9090` を入力し、Save & Test をクリック。（Docker内部ネットワークを使用）
    3.  **ダッシュボードの作成:** 左側メニューのプラスアイコン（Create）> Dashboard > Add new panel。
    4.  「Data source」でPrometheusを選択し、以下のようなPromQLクエリを入力してデータを可視化します。
        -   **秒間リクエスト数（RPS）:** `rate(http_requests_total[1m])`
        -   **P95応答時間:** `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
        -   **アクティブユーザー数:** `active_users`

## パフォーマンス最適化とベストプラクティス

本番環境でPrometheusを安定して運用するためには、いくつかの重要な事項を考慮する必要があります。

### 1. **ラベルカーディナリティ（Label Cardinality）の管理**

Prometheusのパフォーマンスに最も大きな影響を与える要素は**カーディナリティ**です。これは、メトリクス名とラベルの組み合わせによって生成されるユニークな時系列データの数を意味します。`user_id`や`request_id`のようにユニークな値を持つデータをラベルとして使用すると、時系列データが指数関数的に増加し、PrometheusのメモリとCPUを枯渇させる可能性があります。

-   **悪い例:** `http_requests_total{user_id="123", path="/api/data"}`
-   **良い例:** `http_requests_total{path="/api/data"}`

**ラベルの値は、必ず限定された集合（enum）でなければなりません。**

### 2. **レコーディングルール（Recording Rules）の活用**

複雑で重いPromQLクエリは、ダッシュボードの読み込み速度を低下させる主犯です。**レコーディングルール**は、頻繁に使用される複雑なクエリの結果を事前に計算し、新しい時系列データとして保存する機能です。これにより、ダッシュボードは軽量化された事前計算済みのメトリクスを照会するため、はるかに高速にレンダリングされます。

例えば、分単位で集計されたインスタンス別のCPU使用率を事前に計算することができます。

```yaml
# rules.yml
groups:
- name: cpu_rules
  rules:
  - record: instance:node_cpu_usage:rate5m
    expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance) * 100)
```

### 3. **Grafanaダッシュボードのプロビジョニング（Dashboard as Code）**

GrafanaダッシュボードをUIで手動で作成・管理するのは非効率的であり、変更履歴を追跡することが困難です。Grafanaは、YAML設定ファイルを通じてデータソースとダッシュボード（JSONモデル）を自動的にロードする**プロビジョニング**機能をサポートしています。

ダッシュボードのJSONファイルをGitで管理し、Grafanaコンテナにボリュームとしてマウントすれば、ダッシュボードをコードとして管理（Dashboard as Code）でき、協業やバージョン管理に非常に有利です。

## 結論

ここまで、PrometheusとGrafanaを活用して、Webアプリケーションとシステムインフラを監視するための強力で拡張可能なシステムを構築する方法を見てきました。核心は、単にツールをインストールすること以上に、**何を測定するかを定義（Instrumentation）**し、収集したデータを**意味のある情報（Visualization & Alerting）**に加工するプロセスにあります。

今日構築したスタックを基に、`postgres_exporter`を追加してデータベースの詳細な指標を監視したり、`Alertmanager`を連携させて「5分間の5xxエラー率が5%以上」のような具体的なアラートルールを設定するなど、可観測性の範囲を段階的に拡張していくことができます。このようにデータに基づいてシステムの状態を理解し改善する文化は、安定的で成功したサービスの最も強固な基盤となるでしょう。

### 参考資料
- [Prometheus公式ドキュメント](https://prometheus.io/docs/introduction/overview/){:target="_blank"}
- [Grafana公式ドキュメント](https://grafana.com/docs/grafana/latest/){:target="_blank"}
- [Node.js prom-clientライブラリ](https://github.com/siimon/prom-client){:target="_blank"}
- [Google SRE Book - Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/){:target="_blank"}