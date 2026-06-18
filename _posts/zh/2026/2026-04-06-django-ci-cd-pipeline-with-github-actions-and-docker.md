---
layout: post
title: 使用 GitHub Actions 与 Docker 构建 Django 应用 CI/CD 流水线完整指南
slug: django-ci-cd-pipeline-with-github-actions-and-docker
date: 2026-04-06 15:26:09 +0900
categories:
- DevOps
- Backend
tags:
- GitHub Actions
- Django
- CI/CD
- Docker
- AWS
- ECR
- EC2
meta: 面向经验丰富的开发者，一份基于 GitHub Actions 的 Django CI/CD 流水线实战指南。本文将通过详细的 YAML 代码示例，讲解从自动化测试、构建
  Docker 镜像、推送到 AWS ECR，直至部署到 EC2 的完整流程。
image: /uploads/django-ci-cd-pipeline-with-github-actions-and-docker/thumbnail.webp
lang: zh
translation_key: django-ci-cd-pipeline-with-github-actions-and-docker
description: 面向经验丰富的开发者，一份基于 GitHub Actions 的 Django CI/CD 流水线实战指南。本文将通过详细的 YAML 代码示例，讲解从自动化测试、构建
  Docker 镜像、推送到 AWS ECR，直至部署到 EC2 的完整流程。
permalink: /zh/posts/django-ci-cd-pipeline-with-github-actions-and-docker/
---
手动部署的时代已经一去不复返。修改代码后通过 FTP 上传文件，或者 SSH 登录服务器执行 `git pull` 并重启服务的流程，不仅容易引发失误，还是拖慢整个开发周期的罪魁祸首。尤其是在协作环境中，追踪谁在何时部署了哪个版本的代码变得异常困难，这给服务的稳定运营带来了巨大障碍。为了解决这些问题，构建 **CI/CD（持续集成/持续部署）** 流水线如今已不再是可选项，而是必需品。

本篇文章将深入探讨如何结合最广泛使用的 Web 框架之一 **Django** 与已成为 Git 托管服务标准的 GitHub **GitHub Actions**，构建一个从测试、Docker 镜像构建，到部署至 AWS ECR (Elastic Container Registry) 和 EC2 (Elastic Compute Cloud) 的全自动化 CI/CD 流水线。本文不仅仅是“Hello, World!”级别的教程，而是一份包含安全、性能优化、环境分离等高级策略的实战指南，可立即应用于实际生产环境。

<!--more-->
![使用 GitHub Actions 与 Docker 构建 Django 应用 CI/CD 流水线完整指南](/uploads/django-ci-cd-pipeline-with-github-actions-and-docker/thumbnail.webp "使用 GitHub Actions 与 Docker 构建 Django 应用 CI/CD 流水线完整指南")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; 由 Imagen 4.0 AI 生成</small>
</p>
-----

## 1. 引言：为何 Django 项目需要 GitHub Actions CI/CD？

随着 Django 项目规模的扩大和团队成员的增加，保持代码的一致性和部署的稳定性变得至关重要。每当开发者向 `main` 分支推送代码时，自动执行测试，并只有在测试通过后才自动构建和部署的环境，是最大化开发生产力、最小化人为错误的核心要素。

**GitHub Actions** 是 GitHub 仓库内置的工作流自动化工具，其最大优势在于无需构建独立的 CI/CD 服务器，仅通过 YAML 文件即可轻松定义流水线。此外，它与 Docker 的无缝集成为应用程序的运行环境提供了容器化标准，从根本上解决了“在我电脑上明明是好的……”这类顽固问题。

本文中我们将构建的流水线整体流程如下：
1.  **触发 (Trigger)**：开发者向 `main` 分支推送 (Push) 或合并 (Merge) 代码。
2.  **测试 (Test)**：GitHub Actions 工作流启动，执行 Django 项目的单元测试和代码风格检查 (Linting)。
3.  **构建 (Build)**：测试成功后，基于 `Dockerfile` 构建包含 Django 应用程序的 Docker 镜像。
4.  **推送 (Push)**：将构建好的镜像连同版本标签一起推送到 AWS ECR（私有 Docker 镜像仓库）。
5.  **部署 (Deploy)**：通过 SSH 连接到生产环境的 AWS EC2 实例，从 ECR 拉取最新镜像并运行新容器，以近乎零停机的方式完成部署。

## 2. 核心架构：GitHub Actions 工作流设计

一个高效的 CI/CD 流水线由多个逻辑上分离的阶段 (Job) 组成。我们将把工作流设计为三个主要的 Job：`Test`、`Build & Push` 和 `Deploy`。

-   **`test` Job**：验证代码正确性的阶段。如果此阶段失败，后续的构建和部署 Job 将不会执行，从而防止包含错误的代码被部署。
-   **`build-and-push` Job**：仅在 `test` Job 成功时执行。将 Django 应用程序打包成 Docker 镜像，并为版本控制推送到 ECR。
-   **`deploy` Job**：仅在 `build-and-push` Job 成功时执行。连接到实际的生产服务器，部署新版本的应用程序。

这种结构使每个阶段的职责清晰明了，并在出现问题时能快速定位失败的环节。

### GitHub Actions 的主要概念

在编写工作流 YAML 文件之前，需要理解几个核心概念。
-   **Workflow (工作流)**：位于 `.github/workflows/` 目录下的 YAML 文件所定义的整个自动化过程。
-   **Event (事件)**：触发工作流执行的特定活动。（例如：`push`、`pull_request`）
-   **Job (作业)**：一个工作流由一个或多个 Job 组成，每个 Job 都在独立的虚拟环境 (Runner) 中运行。
-   **Step (步骤)**：构成 Job 的单个任务单元。可以执行 shell 命令或使用预制的 Action。
-   **Action (动作)**：封装了工作流中可重复使用的复杂任务的可复用代码。（例如：`actions/checkout@v3`、`aws-actions/configure-aws-credentials@v2`）

## 3. 实战应用：深入 Django CI/CD 工作流 YAML

现在，让我们开始编写实际的工作流文件。在项目根目录下创建 `.github/workflows/main.yml` 文件，并分步填充以下内容。

### 3.1. 定义基础工作流及触发器配置

```yaml
# .github/workflows/main.yml

name: Django CI/CD

on:
  push:
    branches: [ "main" ] # 仅在 main 分支发生 push 事件时运行

env:
  AWS_REGION: ap-northeast-2 # 使用的 AWS 区域
  ECR_REPOSITORY: my-django-app # 创建的 ECR 仓库名称
```
-   `name`: 指定工作流的名称，会显示在 GitHub UI 中。
-   `on.push.branches`: 设置当 `main` 分支发生 `push` 事件时触发此工作流。
-   `env`: 定义可在整个工作流中使用的环境变量。

### 3.2. 实现测试 (Test) Job

作为第一个 Job，我们运行 Django 项目的测试代码来验证代码的稳定性。

```yaml
# .github/workflows/main.yml (续)

jobs:
  test:
    name: Test Django Project
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: |
          python manage.py test
```
-   `runs-on: ubuntu-latest`: 表示此 Job 将在最新版的 Ubuntu 虚拟环境中运行。
-   `actions/checkout@v3`: 一个将仓库代码拉取到 Runner 的 Action。
-   `actions/setup-python@v4`: 设置指定版本的 Python 环境。
-   `Install dependencies` 和 `Run tests`: 使用 `pip` 安装依赖包，并执行 Django 内置的 `test` 命令。

### 3.3. 构建并推送至 ECR (Build & Push) Job

当 `test` Job 成功完成后，我们将构建 Docker 镜像并将其推送到 AWS ECR。此步骤需要 AWS 凭证，因此必须使用 GitHub Secrets。

**[前期准备]**
1.  在 AWS IAM 中为 GitHub Actions 创建一个用户，并授予 `AmazonEC2ContainerRegistryFullAccess` 权限。
2.  为该用户生成 **Access Key ID** 和 **Secret Access Key**。
3.  在 GitHub 仓库的 `Settings > Secrets and variables > Actions` 菜单中，将上面生成的密钥分别注册为 `AWS_ACCESS_KEY_ID` 和 `AWS_SECRET_ACCESS_KEY`。

{% raw %}
```yaml
# .github/workflows/main.yml (续)

  build-and-push:
    name: Build and Push to ECR
    runs-on: ubuntu-latest
    needs: test # 仅在 'test' Job 成功后运行

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Set image tag
        id: image-tag
        run: echo "IMAGE_TAG=$(date +%Y%m%d%H%M%S)" >> $GITHUB_ENV

      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ env.IMAGE_TAG }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -f Dockerfile .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
```
{% endraw %}
-   `needs: test`: 声明此 Job 依赖于 `test` Job。
-   `aws-actions/configure-aws-credentials@v2`: 使用存储在 GitHub Secrets 中的 AWS 密钥来配置 Runner 环境的 AWS 身份验证。
-   `aws-actions/amazon-ecr-login@v1`: 使 Docker 客户端登录到 ECR。
-   `Set image tag`: 基于当前时间创建一个唯一的镜像标签，并注册到 `GITHUB_ENV` 中。
-   `docker build` 和 `docker push`: 使用 `Dockerfile` 构建镜像，并结合 ECR 仓库地址和生成的标签将其推送到 ECR。

### 3.4. 自动部署至 EC2 服务器 (Deploy) Job

最后，我们在 EC2 实例上运行推送到 ECR 的最新镜像，完成部署。这里我们采用通过 SSH 执行远程命令的方式。

**[前期准备]**
1.  创建用于 SSH 连接 EC2 实例的密钥对。
2.  将私钥（`pem` 文件内容）以 `EC2_SSH_PRIVATE_KEY` 为名注册到 GitHub Secrets 中。
3.  将 EC2 实例的公网 IP 地址或域名注册为 `EC2_HOST`，将 SSH 用户名（如 `ubuntu`、`ec2-user`）注册为 `EC2_USERNAME`。
4.  在 EC2 实例上预先安装 Docker 和 Docker Compose。
5.  为 EC2 实例附加一个 IAM Role，使其能够从 ECR 拉取镜像。（需要 `AmazonEC2ContainerRegistryReadOnly` 权限）

{% raw %}
```yaml
# .github/workflows/main.yml (续)

  deploy:
    name: Deploy to EC2
    runs-on: ubuntu-latest
    needs: build-and-push # 仅在 'build-and-push' Job 成功后运行

    steps:
      - name: Get image tag
        id: image-tag
        # 获取前一个 Job 中创建的标签的一种简便方法。
        # 实际上，使用 Artifact 或工作流输出 (outputs) 是更规范的做法。
        # 这里为了简单起见，我们用相同的逻辑重新生成标签。
        run: echo "IMAGE_TAG=$(date +%Y%m%d%H%M%S)" >> $GITHUB_ENV
        
      - name: Deploy to EC2 instance
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_PRIVATE_KEY }}
          script: |
            # 登录 ECR
            aws ecr get-login-password --region ${{ env.AWS_REGION }} | docker login --username AWS --password-stdin ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ env.AWS_REGION }}.amazonaws.com

            # 设置 DOCKER_IMAGE 环境变量，以便在 docker-compose.yml 中使用
            export DOCKER_IMAGE=${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ env.AWS_REGION }}.amazonaws.com/${{ env.ECR_REPOSITORY }}:${{ env.IMAGE_TAG }}
            
            # 停止并删除现有容器（如果存在）
            if [ $(docker ps -q -f name=my-django-container) ]; then
              docker-compose -f /home/ubuntu/my-django-app/docker-compose.yml down
            fi

            # 拉取最新镜像
            docker pull $DOCKER_IMAGE

            # 切换到 docker-compose.yml 所在目录并运行
            cd /home/ubuntu/my-django-app
            docker-compose up -d
```
{% endraw %}
-   `appleboy/ssh-action@master`: 一个非常有用的 Action，可以通过 SSH 在远程服务器上执行脚本。
-   `script`: 将在 EC2 实例上执行的 shell 脚本。它自动化了登录 ECR、拉取最新镜像，以及通过 `docker-compose up -d` 在后台运行容器的整个过程。请注意，`AWS_ACCOUNT_ID` 也需要注册为 Secret。

## 4. 性能优化及最佳实践

### 通过依赖项缓存缩短构建时间
每次工作流运行时都执行 `pip install` 是低效的。通过使用 `actions/cache` 来保存和恢复 `pip` 缓存，可以显著缩短构建时间。

**`test` Job 修改示例:**
{% raw %}
```yaml
      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
```
{% endraw %}
如果 `requirements.txt` 文件的内容没有改变，工作流将直接使用缓存的依赖项。

### 环境分离（Staging vs. Production）
在实际运营环境中，按分支分离部署环境是更安全的做法，例如 `main` 分支用于生产部署，`develop` 分支用于预发布（Staging）部署。可以利用 GitHub Actions 的 `if` 条件和 `environments` 功能来实现这一点。

```yaml
on:
  push:
    branches: [ "main", "develop" ]

...
jobs:
...
  deploy-to-staging:
    if: github.ref == 'refs/heads/develop'
    name: Deploy to Staging
    # ... 预发布服务器部署逻辑 ...
    
  deploy-to-production:
    if: github.ref == 'refs/heads/main'
    name: Deploy to Production
    needs: build-and-push
    environment: production # 使用 GitHub Environment 功能
    # ... 生产服务器部署逻辑 ...
```
使用 GitHub `environment` 功能可以增加部署前的审批流程，或为特定环境设置专属的 Secret，从而实现更精细化的管理。

## 5. 结论：通过自动化流水线最大化开发生产力

至此，我们详细探讨了如何利用 GitHub Actions 和 Docker 为 Django 应用程序构建一个涵盖测试、构建、部署全过程的自动化 CI/CD 流水线。一个精心设计的流水线能带来以下显而易见的优势：

-   **快速交付**：代码变更可以在几分钟内反映到生产环境。
-   **提升稳定性**：自动化测试在部署前保证了代码质量，避免了手动操作带来的失误。
-   **改善开发者体验**：开发者可以从部署的繁琐中解放出来，专注于核心业务逻辑的开发。
-   **增强可见性**：通过 GitHub Actions UI，可以一目了然地掌握所有部署历史、成功与否的状态。

希望您能以本指南中提供的 YAML 代码和策略为基础，为您的 Django 项目构建出最优的 CI/CD 流水线，从而同时实现开发效率和服务稳定性的双赢。

### 参考资料
- [GitHub Actions 官方文档](https://docs.github.com/en/actions "GitHub Actions Documentation"){:target="_blank"}
- [AWS ECR(Elastic Container Registry) 用户指南](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html "Amazon ECR User Guide"){:target="_blank"}
- [Django 测试官方文档](https://docs.djangoproject.com/en/stable/topics/testing/ "Django Testing Documentation"){:target="_blank"}
- [appleboy/ssh-action GitHub 仓库](https://github.com/appleboy/ssh-action "ssh-action on GitHub"){:target="_blank"}