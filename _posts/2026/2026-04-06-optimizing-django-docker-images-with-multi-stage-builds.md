---
layout: post
title: 'Optimizing Django Docker Images with Multi-Stage Builds'
meta: 'This post explains how to significantly reduce the size of a Django Docker image using multi-stage builds. We will walk through creating an efficient Dockerfile that separates the build environment from the final production environment, resulting in a smaller, more secure image.'
tags:
  - tech
  - docker
  - django
  - python
---

Docker has become an essential tool for modern application deployment, but unoptimized images can lead to slower deployments, increased storage costs, and potential security vulnerabilities. One of the most effective techniques for creating lean, production-ready images is the multi-stage build. This approach allows you to use one container for building and compiling your application, and a separate, clean container for the final runtime, copying only the necessary artifacts. This post was generated with the assistance of **Gemini 3.0**.



<small style="color:lightgray;text-decoration:line-through;font-style: italic;">[Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"} 에도 발행하고 있어요.</small>

![Docker containers on a cargo ship](/uploads/docker/optimizing-django-docker.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/photos/blue-and-red-cargo-ship-on-sea-during-daytime-T7o_T9oFvRw" title="Content copyright holder" target="_blank">frank mckenna</a></small>
</p>

-----

숙련된 서버 엔지니어와 개발자에게 **컨테이너화(Containerization)** 기술은 이제 선택이 아닌 필수가 되었습니다. 특히 **Docker**는 애플리케이션의 개발, 배포, 실행을 단순화하는 강력한 도구로 자리 잡았습니다. 하지만 편리함 속에서 우리는 종종 Docker 이미지의 크기가 불필요하게 커지는 문제를 간과하곤 합니다.

이 포스트에서는 **Python Django** 애플리케이션을 예시로, `Dockerfile`에서 **멀티스테이지 빌드(Multi-stage builds)** 기법을 사용하여 최종 이미지의 크기를 획기적으로 줄이고 보안을 강화하는 방법을 상세히 다루겠습니다.

### Docker 이미지 크기가 중요한 이유

프로덕션 환경에서 Docker 이미지가 작을수록 여러 가지 이점이 있습니다.

1.  **빠른 배포**: 이미지 크기가 작을수록 레지스트리에서 이미지를 PULL하는 시간이 단축되어 배포 속도가 향상됩니다. 이는 오토스케일링(Auto-scaling) 환경에서 특히 중요합니다.
2.  **비용 절감**: 컨테이너 레지스트리(Docker Hub, AWS ECR 등)는 보통 저장 용량에 따라 비용을 청구합니다. 작은 이미지는 저장 비용을 절감하는 데 도움이 됩니다.
3.  **보안 강화**: 최종 이미지에 빌드에만 필요했던 컴파일러, 라이브러리, 개발용 의존성 패키지 등이 포함되지 않으므로 공격 표면(Attack Surface)이 줄어듭니다.

### 멀티스테이지 빌드란 무엇일까요?

**멀티스테이지 빌드**는 하나의 `Dockerfile` 내에서 여러 개의 `FROM` 명령어를 사용하여 여러 빌드 단계를 정의하는 기능입니다. 각 `FROM` 명령어는 새로운 빌드 단계를 시작하며, 이전 단계의 결과물을 선택적으로 다음 단계로 복사할 수 있습니다.

이를 통해, 첫 번째 단계에서는 소스 코드를 컴파일하고 의존성을 설치하는 등 '빌드'에 필요한 모든 도구를 사용하고, 마지막 단계에서는 빌드 결과물(실행 파일, 라이브러리 등)만을 깨끗한 베이스 이미지에 복사하여 최종 이미지를 생성할 수 있습니다.

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem auto 0;max-width:100%;">
    <div>
        <img src="/uploads/docker/single-stage-build.png" alt="싱글스테이지 빌드 개념도" />
    </div>
    <div>
        <img src="/uploads/docker/multi-stage-build.png" alt="멀티스테이지 빌드 개념도" />
    </div>
</div>
<p style="text-align:center;color:gray;"><small>싱글스테이지 빌드(좌)와 멀티스테이지 빌드(우)의 개념적 차이</small></p>

### 일반적인 Django Dockerfile의 문제점

먼저 최적화되지 않은 일반적인 `Dockerfile`을 살펴보겠습니다.

```dockerfile
# Dockerfile.naive

# 1. 베이스 이미지 선택
FROM python:3.11

# 2. 시스템 패키지 및 빌드 도구 설치
# psycopg2-binary 같은 패키지는 컴파일을 위해 gcc 등이 필요할 수 있음
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사
COPY . .

# 6. 애플리케이션 실행
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
```

이 `Dockerfile`은 정상적으로 동작하지만 몇 가지 문제가 있습니다. 가장 큰 문제는 `build-essential`과 같은 **빌드용 시스템 패키지**가 최종 이미지에 그대로 남는다는 점입니다. Python 패키지를 설치한 후에는 더 이상 필요 없지만, 이미지의 용량을 차지하고 잠재적인 보안 위협이 될 수 있습니다.

### 멀티스테이지 빌드를 활용한 최적화

이제 멀티스테이지 빌드를 적용하여 `Dockerfile`을 개선해 보겠습니다.

```dockerfile
# Dockerfile.optimized

# =================================================================
# 1단계: 빌더 (Builder) 스테이지
# 의존성을 설치하고 빌드하는 역할
# =================================================================
FROM python:3.11-slim as builder

# 시스템 패키지 및 빌드 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 가상 환경 생성
RUN python -m venv /opt/venv

# 가상 환경의 pip를 사용하도록 PATH 설정
ENV PATH="/opt/venv/bin:$PATH"

# 의존성 설치 (가상 환경 내부에)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =================================================================
# 2단계: 최종 (Final) 스테이지
# 실제 프로덕션에서 실행될 경량 이미지
# =================================================================
FROM python:3.11-slim

# 보안을 위해 non-root 유저 생성 및 사용
RUN useradd --create-home appuser
WORKDIR /home/appuser/app
USER appuser

# 빌더 스테이지에서 생성된 가상 환경만 복사
# 빌드에 사용된 시스템 패키지(build-essential 등)는 복사되지 않음
COPY --from=builder /opt/venv /opt/venv

# PATH 설정
ENV PATH="/opt/venv/bin:$PATH"

# 애플리케이션 소스 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]

```

개선된 `Dockerfile`의 핵심은 다음과 같습니다.

1.  **빌더 스테이지 (`as builder`)**: `python:3.11-slim` 이미지를 기반으로 `build-essential` 등 빌드에 필요한 모든 도구를 설치합니다. 그리고 파이썬 의존성을 `/opt/venv`라는 가상 환경 내에 설치합니다.
2.  **최종 스테이지**: 다시 한번 깨끗한 `python:3.11-slim` 이미지에서 시작합니다. 여기서는 `build-essential`을 설치하지 않습니다.
3.  **`COPY --from=builder`**: 가장 중요한 부분입니다. 빌더 스테이지에서 생성된 가상 환경(`- /opt/venv`)만을 `COPY` 명령어를 통해 가져옵니다. 이렇게 하면 빌드용 도구들은 제외하고, **순수하게 실행에 필요한 Python 패키지들만** 최종 이미지에 포함시킬 수 있습니다.
4.  **Non-root 유저 사용**: 보안 모범 사례에 따라 `root`가 아닌 일반 사용자(`appuser`) 권한으로 애플리케이션을 실행하도록 설정했습니다.

### 이미지 크기 비교 및 결론

두 `Dockerfile`로 이미지를 빌드하고 크기를 비교하면 그 차이를 명확하게 확인할 수 있습니다.

```bash
# Naive Dockerfile 빌드
docker build -t django-naive -f Dockerfile.naive .

# Optimized Dockerfile 빌드
docker build -t django-optimized -f Dockerfile.optimized .

# 이미지 크기 확인
docker images | grep django-
```

프로젝트의 의존성에 따라 다르지만, 일반적으로 `build-essential`과 같은 패키지들이 차지하는 용량이 수백 MB에 달하기 때문에, 멀티스테이지 빌드를 사용한 이미지(`django-optimized`)는 그렇지 않은 이미지(`django-naive`)에 비해 **30% ~ 50% 이상 크기가 감소**하는 효과를 볼 수 있습니다.

이처럼 멀티스테이지 빌드는 Docker 이미지를 **더 작고, 더 안전하며, 더 빠르게** 만드는 매우 효과적인 전략입니다. 프로덕션 환경을 위한 컨테이너를 만든다면 반드시 도입을 고려해야 할 필수 기술이라고 할 수 있습니다.

### 참고문헌
- [Docker 공식 문서 - Multi-stage builds](https://docs.docker.com/build/building/multi-stage/ "Official Docker Documentation on Multi-stage builds"){:target="_blank"}
- [TestDriven.io - Dockerizing Django with Postgres, Gunicorn, and Nginx](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/ "A practical tutorial on Dockerizing Django"){:target="_blank"}
