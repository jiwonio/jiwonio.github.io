---
layout: post
title: 'Configuring Swap Memory on Ubuntu 22.04 LTS'
meta: 'Learn to configure swap memory on Ubuntu 22.04 LTS to address RAM shortages on low-spec servers. Perfect for AWS EC2 and self-hosted servers running resource-heavy applications.'
tags:
  - ubuntu
---

When using the free tier of services like **Amazon Web Services EC2** or other self-hosted servers,
you might occasionally run into issues with insufficient RAM when installing large external resources.
This can cause the server to freeze for extended periods and eventually crash.
While this doesn't happen often, it can be quite critical if you're running a personal project
for commercial use and implementing a **Micro Service Architecture** on a server with very limited specifications.
In such situations, **swap memory** can be extremely helpful. In this post, I've written about how to create swap memory and what it is.
This translation was provided by **Microsoft Copilot**.

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">제목과 첫 문단은 영어가 멋있어요.</small>

<img src="/uploads/ubuntu22-swap-memory/ram.jpg" alt="Random Access Memory" />

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@akshar_dave" title="Content copyright holder" target="_blank">Akshar Dave🌻</a></small>
</p>

-----

**스왑 메모리**는 물리 디스크의 일부를 휘발성 메모리인 RAM(이하 메모리) 으로 사용하여 부족한 메모리 용량을 보강해주는 역할을 합니다.
간혹 [Laravel](https://laravel.com/ "Laravel"){:target="_blank"} 이나 [NestJS](https://nestjs.com/ "NestJS"){:target="_blank"} 같은 큰 패키지 덩어리를 인스톨하는 경우에 메모리나 CPU 자원과 같은
즉, 컴퓨터 리소스를 많이 필요로하기 때문에 리소스가 부족한 경우 설치에 실패하는 경우가 있습니다.

[Google Compute Engine](https://cloud.google.com/products/compute "Google Compute Engine"){:target="_blank"}, [Amazon EC2](https://aws.amazon.com/ko/ec2/ "Amazon EC2"){:target="_blank"} 등등 대부분의 가상 머신 서비스에서는 메모리 용량을 추가하려면 인스턴스를 중지한 후에 인스턴스 타입을 변경해야 합니다.
예상하지 못한 상황에서 메모리 부족으로 인한 시스템 오류가 발생하여 재부팅하는 일이 생긴다면, 중지되어 있는 동안 계속해서 손해가 발생하기 때문에 미리 대비해야 할 필요가 있습니다.
이런 경우에 스왑 메모리를 설정해놓으면 임시적으로라도 메모리 부족에 대해서 조금이나마 도움을 받을 수 있습니다.

대부분의 상용서비스 환경에서는 각각의 인프라 관리 기술을 도입해서 위와 같은 상황이 생기는 경우는 잘 없겠습니다만,
개발 테스트나 토이프로젝트와 같은 용도로 사용하는 프리티어 정도의 낮은 사양에서는 스왑 메모리를 설정해두는 게 굉장히 편리하고 도움이 됩니다.

<img src="/uploads/ubuntu22-swap-memory/windows11-virtual-memory.png" alt="Windows 11 virtual memory" />

<p style="text-align:center;color:gray;"><small>윈도우의 가상 메모리</small></p>

스왑 메모리라는 개념은 우분투와 같은 리눅스나 유닉스에만 있는 개념이 아닙니다. 윈도우에도 가상 메모리라는 이름으로 활용되고 있고, 저사양 PC에서 유용하게 활용되고 있습니다.

## 스왑 메모리 설정

1. 스왑 메모리가 설정되어 있는 지 확인
   ```shell
      sudo free -m
      sudo swapon -s
   ```
   <img src="/uploads/ubuntu22-swap-memory/check-swap-memory.png" alt="Check swap memory">
2. 스왑 메모리가 설정되어 있다면 사용 중지
   ```shell
      sudo swapoff -a
   ```
3. 스왑 메모리로 사용 할 swapfile 생성
   ```shell
      # 4G 크기만큼 스왑 파일 생성
      sudo fallocate -l 4G /swapfile
   ```
4. 생성한 swapfile 을 스왑 메모리로 사용하도록 설정
    ```shell
      # 권한 수정
      sudo chmod 600 /swapfile
    
      # 활성화 준비
      sudo mkswap /swapfile
    
      # 활성화
      sudo swapon /swapfile
    ```
    <img src="/uploads/ubuntu22-swap-memory/make-swapfile.png" alt="Make swapfile">
5. 서버 리부팅 후에도 스왑 메모리를 사용할 수 있도록 설정
    ```shell
      # 파일 편집
      sudo nano /etc/fstab 
    
      # 내용 추가
      /swapfile swap swap defaults 0 0
    ```
    <img src="/uploads/ubuntu22-swap-memory/swap-setup-for-rebooting.png" alt="Swap setup for rebooting">
6. 스왑 메모리 설정 완료
   <img src="/uploads/ubuntu22-swap-memory/complete-make-swapfile.png" alt="Complete make swapfile">

## 스왑 메모리 비활성화

스왑 메모리를 더 이상 사용하지 않는 경우 비활성화 합니다.
```shell
# 스왑 비활성화
sudo swapoff -v /swapfile 

# 파일 실행 후 아래 라인 삭제
sudo nano /etc/fstab      
/swapfile swap swap defaults 0 0

# swap 파일 삭제
sudo rm /swapfile 
```

## 참고문헌
- 위키피디아 : [가상 메모리](https://en.wikipedia.org/wiki/Virtual_memory "가상 메모리"){:target="_blank"}
- 위키피디아 : [메모리 관리 기법 - 페이징](https://en.wikipedia.org/wiki/Memory_paging "메모리 관리 기법 - 페이징"){:target="_blank"}