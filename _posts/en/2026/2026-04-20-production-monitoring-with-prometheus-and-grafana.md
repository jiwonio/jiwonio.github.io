---
layout: post
title: 'Production-Grade Web Application Monitoring: A Complete Guide to Building
  with Prometheus and Grafana'
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
description: A complete guide for server engineers and developers on building a real-time
  monitoring system with Prometheus and Grafana. Covers Docker-based setup, custom
  metric instrumentation, PromQL queries, and performance optimization best practices.
image: /uploads/production-monitoring-with-prometheus-and-grafana/thumbnail.webp
lang: en
translation_key: production-monitoring-with-prometheus-and-grafana
permalink: /en/posts/production-monitoring-with-prometheus-and-grafana/
post_type: deep-dive
---
The core of successful web service operation goes beyond simply implementing features; it lies in continuously observing the service's state while it's 'alive' and predicting potential issues. Identifying potential bottlenecks before users experience outages and analyzing resource usage trends to scale infrastructure efficiently are essential skills for any experienced engineer. However, managing the state of numerous servers and applications fragmentally in a distributed microservices architecture is nearly impossible.

To solve these problems, the combination of **Prometheus** and **Grafana** has become the de facto standard in modern DevOps environments. Prometheus collects metrics from systems and applications based on a powerful time-series database (TSDB), and Grafana visualizes this collected data into beautiful and intuitive dashboards. This combination allows us to gain powerful 'observability,' enabling us to grasp the state of a distributed system at a glance from a central point, detect signs of anomalies early, and respond swiftly. This post will provide an in-depth guide on the entire process of building a production-ready Prometheus and Grafana monitoring stack using Docker, and instrumenting and visualizing key business metrics of an application.

<!--more-->
![Production-Grade Web Application Monitoring: A Complete Guide to Building with Prometheus and Grafana](/uploads/production-monitoring-with-prometheus-and-grafana/thumbnail.webp "Production-Grade Web Application Monitoring: A Complete Guide to Building with Prometheus and Grafana")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## Background and Problem Definition: Why is Monitoring Essential?

The phrase "It works on my machine" is meaningless in a production environment. The development environment and the actual service environment differ in numerous variables, such as network latency, traffic load, and resource contention. To provide a stable service, you must be able to answer the following questions in real-time:

-   Are the server's current CPU, memory, and disk usage levels stable?
-   What is the requests per second (RPS), and what is the average response time?
-   What is the error rate as a percentage of total requests?
-   Is the database connection pool sufficiently large?
-   Has the API call latency for a specific feature suddenly spiked?

If we cannot answer these questions, we find ourselves in a 'closing the barn door after the horse has bolted' situation, reacting to failures only after they occur. **Building a monitoring system with Prometheus and Grafana** is the first step towards proactive engineering, preventing such situations and enabling data-driven diagnosis and optimization of system health.

## Core Architecture and Principles

A Prometheus-based monitoring system consists of several key components. Understanding the role of each element and the flow of data is crucial.


> **Note:** The following is a text-based example to explain the architecture instead of an image.

| Component             | Role and Features                                                                                                                                                                             |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Prometheus Server** | The core engine. It periodically **pulls (scrapes)** the HTTP endpoint (`/metrics`) of monitoring targets to collect and store time-series data.                                               |
| **Exporter**          | An agent that collects data from systems that do not directly expose Prometheus metrics (e.g., databases, hardware) and converts it into a format that Prometheus can understand. (Examples: `node_exporter`, `postgres_exporter`) |
| **Client Library**    | A library that helps developers add metric collection logic (instrumentation) directly into their application code. (Examples: `prom-client` for Node.js, `django-prometheus` for Django)          |
| **Grafana**           | A tool that queries data stored in the Prometheus server using **PromQL (Prometheus Query Language)** and visualizes it into user-friendly graphs and dashboards.                                  |
| **Alertmanager**      | Responsible for sending alerts to various channels like email and Slack when specific conditions defined by alerting rules in Prometheus are met.                                               |

Prometheus's most significant feature is its **pull-based architecture**. Unlike a push-based model where monitoring targets push data to the server, the Prometheus server actively visits targets to fetch data. This has the advantage that Prometheus can directly verify the health of the targets, and all monitoring targets can be managed centrally from a single configuration file.

## Practical Application Code/Configuration Deep Dive

Now, let's use Docker Compose to build a complete monitoring stack in a local environment and instrument a simple Node.js application.

### 1. Project Structure

Create the following directory structure.

```
monitoring-stack/
├── docker-compose.yml
├── prometheus/
│   └── prometheus.yml
└── app/
    ├── index.js
    └── package.json
```

### 2. Docker Compose Configuration (`docker-compose.yml`)

We will define Prometheus, Grafana, and `node_exporter` for system metric collection as services.

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

### 3. Prometheus Configuration (`prometheus/prometheus.yml`)

This is the core configuration file that defines which targets Prometheus will scrape.

```yaml
global:
  scrape_interval: 15s # Default scrape interval

scrape_configs:
  - job_name: 'prometheus'
    # Monitor Prometheus itself
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    # Access via container name through Docker's internal network
    static_configs:
      - targets: ['node_exporter:9100']

  - job_name: 'web_app'
    # Monitor the web application we will create
    static_configs:
      - targets: ['web_app:8080']
```

### 4. Node.js Application Instrumentation (`app/`)

We'll create a simple Express server that exposes custom metrics using the `prom-client` library.

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

// Create a Prometheus metric registry
const register = new client.Registry();
client.collectDefaultMetrics({ register }); // Collect default Node.js metrics

// 1. Counter: A cumulative value (e.g., total number of HTTP requests)
const httpRequestCounter = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'path', 'status_code'],
  registers: [register],
});

// 2. Gauge: A value representing the current state (e.g., number of active users)
const activeUsersGauge = new client.Gauge({
  name: 'active_users',
  help: 'Number of active users',
  registers: [register],
});

// 3. Histogram: Records the distribution of observed values in buckets (e.g., HTTP request latency)
const httpRequestDurationMicroseconds = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'path', 'status_code'],
  buckets: [0.1, 0.5, 1, 1.5], // Buckets for 0.1s, 0.5s, 1s, 1.5s
  registers: [register],
});

app.use((req, res, next) => {
  // Start a timer to measure the end of the response
  res.locals.startEpoch = Date.now();
  next();
});

app.get('/', (req, res) => {
  setTimeout(() => {
    // Calculate the response time
    const responseTimeInMs = Date.now() - res.locals.startEpoch;
    httpRequestDurationMicroseconds
      .labels(req.method, req.path, 200)
      .observe(responseTimeInMs / 1000); // Convert to seconds
    
    httpRequestCounter.labels(req.method, req.path, 200).inc();
    res.send('Hello World!');
  }, Math.random() * 1000); // Random delay between 0 and 1 second
});

// The /metrics endpoint to expose metrics
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// Logic to simulate fluctuating active user counts
setInterval(() => {
  const activeUsers = Math.round(Math.random() * 100);
  activeUsersGauge.set(activeUsers);
}, 5000);

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`);
});
```

### 5. Running and Verifying the Stack

In the project's root directory (`monitoring-stack/`), run the following command.

```bash
docker-compose up -d
```

-   **Prometheus UI:** Navigate to `http://localhost:9090` in your browser and go to 'Status' > 'Targets'. You should see three targets (`prometheus`, `node_exporter`, `web_app`) with an 'UP' status.
-   **Grafana UI:** Navigate to `http://localhost:3000`. (Default ID/PW: `admin`/`admin`).
    1.  **Add Data Source:** Go to the gear icon (Configuration) in the left menu > Data Sources > Add data source > Select Prometheus.
    2.  Enter `http://prometheus:9090` for the URL and click Save & Test. (This uses the Docker internal network).
    3.  **Create Dashboard:** Go to the plus icon (Create) in the left menu > Dashboard > Add new panel.
    4.  Select Prometheus as the 'Data source' and enter the following PromQL queries to visualize the data.
        -   **Requests Per Second (RPS):** `rate(http_requests_total[1m])`
        -   **P95 Response Time:** `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
        -   **Active Users:** `active_users`

## Performance Optimization and Best Practices

To operate Prometheus reliably in a production environment, several important factors must be considered.

### 1. **Managing Label Cardinality**

The factor that most significantly impacts Prometheus performance is **cardinality**. This refers to the number of unique time series generated by the combination of a metric name and its labels. Using data with unique values, such as `user_id` or `request_id`, as labels can cause an exponential increase in time series data, potentially exhausting Prometheus's memory and CPU.

-   **Bad:** `http_requests_total{user_id="123", path="/api/data"}`
-   **Good:** `http_requests_total{path="/api/data"}`

**Label values must be a limited set (enum).**

### 2. **Leveraging Recording Rules**

Complex and heavy PromQL queries are a major cause of slow dashboard loading times. A **Recording Rule** is a feature that pre-computes the results of frequently used, complex queries and saves them as a new time series. This allows dashboards to query the lighter, pre-calculated metrics, resulting in much faster rendering.

For example, you can pre-calculate the per-instance CPU usage aggregated over five minutes.

```yaml
# rules.yml
groups:
- name: cpu_rules
  rules:
  - record: instance:node_cpu_usage:rate5m
    expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance) * 100)
```

### 3. **Grafana Dashboard Provisioning (Dashboard as Code)**

Manually creating and managing Grafana dashboards through the UI is inefficient and makes it difficult to track change history. Grafana supports a **provisioning** feature that automatically loads data sources and dashboards (as JSON models) via YAML configuration files.

By managing dashboard JSON files in Git and mounting them as a volume in the Grafana container, you can manage dashboards as code (Dashboard as Code), which is highly advantageous for collaboration and version control.

## Conclusion

So far, we have explored how to build a powerful and scalable system for monitoring web applications and system infrastructure using Prometheus and Grafana. The key takeaway is that it's not just about installing the tools, but about the process of **defining what to measure (Instrumentation)** and processing the collected data into **meaningful information (Visualization & Alerting)**.

Building on the stack we created today, you can progressively expand the scope of your observability by adding `postgres_exporter` to monitor detailed database metrics or by integrating `Alertmanager` to set up specific alert rules, such as '5xx error rate exceeds 5% for 5 minutes'. This culture of understanding and improving system health based on data will become the strongest foundation for a stable and successful service.

### References
- [Prometheus Official Documentation](https://prometheus.io/docs/introduction/overview/){:target="_blank"}
- [Grafana Official Documentation](https://grafana.com/docs/grafana/latest/){:target="_blank"}
- [Node.js prom-client Library](https://github.com/siimon/prom-client){:target="_blank"}
- [Google SRE Book - Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/){:target="_blank"}
---