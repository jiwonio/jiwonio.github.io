---
layout: post
title: Ubuntu 22.04 LTS 스왑 메모리 설정하기
tags:
- ubuntu
image: /uploads/ubuntu22-swap-memory/thumbnail.webp
lang: ko
translation_key: ubuntu22-swap-memory
slug: ubuntu22-swap-memory
description: Ubuntu 22.04 LTS에서 스왑 파일을 만들고 재부팅 후에도 유지하는 방법과, 크기·swappiness 선택 기준,
  프로덕션에서 피해야 할 함정을 정리합니다.
post_type: deep-dive
categories:
- DevOps
updated: 2026-07-13 12:00:00 +0900
---
AWS EC2 프리티어나 저사양 자체 호스팅 서버에서 대용량 패키지를 설치하다 보면 RAM 부족으로 서버가 멈추거나 OOM으로 프로세스가 죽는 경우가 있습니다. 인스턴스 타입을 올리기 전에 **스왑 파일**로 디스크 일부를 비상 메모리로 쓰면, 설치·빌드 중 순간 피크를 넘기는 데 도움이 됩니다. 이 글은 Ubuntu 22.04 LTS 기준으로 설정 절차와 함께 **언제 쓰고, 언제 쓰면 안 되는지**를 정리합니다.

<!--more-->

![Random Access Memory](/uploads/ubuntu22-swap-memory/ram.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@akshar_dave" title="Content copyright holder" target="_blank">Akshar Dave🌻</a></small>
</p>

-----

## 스왑이 하는 일

**스왑 메모리**는 물리 디스크(또는 스왑 파티션/파일)의 일부를 휘발성 메모리처럼 쓰는 기법입니다. 커널이 당장 쓰지 않는 페이지를 디스크로 내리고, 필요할 때 다시 올립니다. [Laravel](https://laravel.com/ "Laravel"){:target="_blank"}·[NestJS](https://nestjs.com/ "NestJS"){:target="_blank"} 같은 큰 패키지 설치나 `npm`/`composer` 의존성 해석처럼 **짧은 시간 동안 메모리 피크**가 생기는 작업에서, 물리 RAM만으로는 부족한 순간을 메울 수 있습니다.

다만 디스크 I/O는 RAM보다 훨씬 느립니다. 스왑이 **상시 풀가동**되는 상태라면 서비스 지연이 커지므로, 스왑은 “여유 버퍼”이지 “RAM 대체재”가 아닙니다.

[Google Compute Engine](https://cloud.google.com/products/compute "Google Compute Engine"){:target="_blank"}, [Amazon EC2](https://aws.amazon.com/ko/ec2/ "Amazon EC2"){:target="_blank"} 등에서 메모리를 늘리려면 보통 인스턴스를 중지하고 타입을 바꿔야 합니다. 예기치 않은 OOM으로 재부팅이 반복되면 그 시간 동안 장애가 이어지므로, **개발·토이·저사양 테스트 노드**에서는 스왑을 미리 켜 두는 편이 안전합니다. 상용 프로덕션은 보통 오토스케일·적정 인스턴스 사이징으로 해결하는 쪽이 맞습니다.

Windows에도 **가상 메모리(페이지 파일)** 라는 이름으로 같은 개념이 있습니다.

![Windows 11 virtual memory](/uploads/ubuntu22-swap-memory/windows11-virtual-memory.png)

<p style="text-align:center;color:gray;"><small>윈도우의 가상 메모리</small></p>

## 크기 선택 기준

정답 공식은 환경마다 다르지만, 실무에서 자주 쓰는 출발점은 다음과 같습니다.

| 물리 RAM | 권장 스왑(시작점) | 비고 |
| --- | --- | --- |
| 1–2 GB (t2/t3.micro 급) | 2–4 GB | 패키지 설치·가벼운 빌드용 버퍼 |
| 4 GB | 2–4 GB | hibernate가 필요 없으면 RAM의 0.5–1배 |
| 8 GB 이상 | 1–2 GB 또는 생략 | 개발 노트북이 아니면 최소만 |

- **디스크 여유**가 부족하면 스왑을 크게 잡지 마세요. SSD 수명·용량 모두 비용입니다.
- `fallocate`가 실패하거나 파일시스템 제약이 있으면 `dd`로 생성할 수 있습니다(아래 대안).
- 이 글 예시는 **4GB 스왑 파일** (`/swapfile`) 기준입니다. 필요에 맞게 숫자만 바꾸면 됩니다.

## 스왑 파일 설정 단계

### 1. 현재 스왑 확인

```shell
sudo free -m
sudo swapon --show
```

![Check swap memory](/uploads/ubuntu22-swap-memory/check-swap-memory.png)

`free -m`의 Swap 행이 모두 0이면 스왑이 없거나 비활성 상태입니다.

### 2. 기존 스왑이 있으면 끄기

이미 스왑 파티션/파일이 켜져 있고 크기를 바꾸려는 경우에만 실행합니다.

```shell
sudo swapoff -a
```

### 3. 스왑 파일 생성

```shell
# 4G 크기 스왑 파일
sudo fallocate -l 4G /swapfile
```

`fallocate`가 지원되지 않거나 오류가 나면:

```shell
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
```

### 4. 권한·포맷·활성화

스왑 파일은 **루트만 읽기/쓰기**여야 합니다. 권한이 넓으면 보안 경고 대상입니다.

```shell
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo swapon --show
sudo free -m
```

![Make swapfile](/uploads/ubuntu22-swap-memory/make-swapfile.png)

### 5. 재부팅 후에도 유지 (`/etc/fstab`)

```shell
# 중복 추가를 피하려면 먼저 검색
grep -n swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

예전 글에서 쓰던 `defaults` 형태도 동작하는 경우가 많지만, Ubuntu 문서·관례상 스왑에는 `none swap sw 0 0` 형식을 쓰는 편이 명확합니다.

![Swap setup for rebooting](/uploads/ubuntu22-swap-memory/swap-setup-for-rebooting.png)

### 6. 확인

```shell
sudo free -m
sudo swapon --show
```

![Complete make swapfile](/uploads/ubuntu22-swap-memory/complete-make-swapfile.png)

## swappiness와 성능

커널 파라미터 `vm.swappiness`는 메모리 압박이 있을 때 스왑을 얼마나 공격적으로 쓸지 조절합니다(0–100). 기본값은 배포판마다 다르지만 Ubuntu 서버에서는 보통 60 근처입니다.

- **DB·지연에 민감한 서비스**: 10–30 정도로 낮춰 스왑 의존을 줄이는 경우가 많습니다.
- **저사양 빌드 전용 노드**: 기본값을 유지해도 무방한 경우가 많습니다.

임시 적용:

```shell
sudo sysctl vm.swappiness=20
```

영구 적용 예 (`/etc/sysctl.d/99-swap.conf`):

```shell
echo 'vm.swappiness=20' | sudo tee /etc/sysctl.d/99-swap.conf
sudo sysctl --system
```

값을 낮춘다고 OOM이 사라지지는 않습니다. RAM 자체가 부족하면 프로세스가 죽거나 극단적으로 느려질 수 있습니다.

## 프로덕션에서 주의할 점

- **상시 스왑 thrashing**은 장애입니다. `vmstat 1`, `iostat`, 모니터링으로 `si`/`so`가 지속되는지 보세요.
- **루트 볼륨이 가득 찬 상태**에서 큰 스왑 파일을 만들면 배포·로그 적재가 함께 실패합니다.
- **암호화·규정**이 있는 환경에서는 스왑에 메모리 내용이 남을 수 있으므로 정책에 맞게 암호화 스왑 등을 검토하세요.
- 컨테이너 오케스트레이션 노드에서는 노드 차원 스왑 정책이 플랫폼 권장과 다를 수 있습니다. 클러스터 가이드를 우선하세요.

## 스왑 비활성화

더 이상 필요 없으면 아래 순서로 정리합니다.

```shell
sudo swapoff -v /swapfile
sudo sed -i.bak '/swapfile/d' /etc/fstab
sudo rm /swapfile
sudo free -m
```

`/etc/fstab` 편집 후에는 **오타로 부팅 실패**할 수 있으니, 클라우드 콘솔 시리얼/복구 수단을 확인한 뒤 재부팅하세요.

## 참고문헌

- 위키피디아: [가상 메모리](https://en.wikipedia.org/wiki/Virtual_memory "가상 메모리"){:target="_blank"}
- 위키피디아: [메모리 관리 기법 - 페이징](https://en.wikipedia.org/wiki/Memory_paging "메모리 관리 기법 - 페이징"){:target="_blank"}
- Ubuntu Server 문서: [Swap](https://documentation.ubuntu.com/server/how-to/system-tuning/swap-faq/ "Ubuntu swap FAQ"){:target="_blank"}
