---
layout: post
title: AWS EC2 Ubuntu 초기 설정 가이드
tags:
- AWS
image: /uploads/ubuntu22-default-setting/thumbnail.webp
lang: ko
translation_key: ubuntu22-default-setting
slug: ubuntu22-default-setting
description: AWS EC2 Ubuntu 22.04 LTS 프리티어 인스턴스의 보안 그룹·SSH·패키지 업데이트·로케일·타임존 초기 설정과, 자주 나는 실수(포트 과개방, HISTFILESIZE 오타 등)를 정리합니다.
post_type: deep-dive
categories:
- DevOps
updated: 2026-07-13 12:00:00 +0900
---
AWS EC2 프리티어로 개발·테스트 환경을 만들 때 **Ubuntu 22.04 LTS** 인스턴스의 초기 설정이 중요합니다. Route 53, ELB, RDS 같은 서비스는 다루지 않고, 키 페어, 방화벽, 스토리지 등 필수 구성만 단계별로 설명합니다. 초기에 올바르게 설정해 두면 이후 트러블슈팅 시간을 크게 줄일 수 있습니다.

<!--more-->

![Ubuntu Server](/uploads/ubuntu22-default-setting/ubuntu.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@6heinz3r" title="Content copyright holder" target="_blank">Gabriel Heinzer</a></small>
</p>

-----

## 이 가이드의 범위

다루지 않는 것: Route 53, ALB/ELB, RDS, 다중 AZ 등 본격 프로덕션 토폴로지.
다루는 것: **한 대의 EC2 Ubuntu 22.04** 를 개발·테스트 용도로 쓰기 위한 최소 안전 설정.

프리티어 `t2.micro` / `t3.micro` 급에서도 동일합니다. 보안 그룹 이름은 콘솔 기본값(`launch-wizard-*`)일 수 있으나, **22/80/3306을 0.0.0.0/0에 장기간 열어 두는 구성은 권장하지 않습니다.**

## 생성 전 체크리스트

1. 키 페어 `.pem` 권한을 로컬에서 `400` 수준으로 제한했는지
2. 보안 그룹 인바운드: SSH(22)는 **본인 IP** 또는 VPN/bastion 대역만
3. 루트 볼륨 크기: 로그·Docker 이미지를 쓸 계획이면 8GB 기본보다 여유 있게
4. 퍼블릭 IP/Elastic IP 필요 여부

[Amazon EC2](https://aws.amazon.com/ec2/ "Amazon EC2"){:target="_blank"}에서 개발 또는 테스트 환경을 설정할 때는 인스턴스를 올바르게 구성하는 것이 중요합니다. 이 가이드는 Ubuntu 22.04 LTS 초기 설정 단계를 안내합니다.
비용 절감을 위해 무료 티어를 사용하는 경우에 특히 유용합니다. Route 53, ELB, RDS 등의 서비스는 다루지 않으며 기본 설정에 중점을 둡니다.

### 1. 서버 기본 설정

<p style="text-align:right;color:gray;"><small>EC2 사양</small></p>

| EC2 설정 항목  | 설정 값                                           |
|------------|------------------------------------------------|
| 이미지(AMI)   | Ubuntu Server 22.04 LTS (HVM), SSD Volume Type |
| 인스턴스 유형    | t2.micro                                       |
| 방화벽(보안 그룹) | launch-wizard-9                                |
| 스토리지(볼륨)   | 1개 - 30GB                                      |
| 키 페어(로그인)  | Key pair file                                  |

![Create EC2 instance](/uploads/ubuntu22-default-setting/create-ec2-Instance.png)
<p style="text-align:center;color:gray;"><small>EC2 사양 설정</small></p>

개발 또는 테스트 용도로는 높은 사양이 필요 없습니다. 무료 티어 모델로 충분합니다. 
launch-wizard-9 보안 그룹은 인스턴스를 생성하면 자동으로 생성되는 기본 설정값으로, 22, 80, 3306과 같은 API 개발에 필요한 포트를 모두에게 열어놓습니다. 
보안을 강화하려면 [OpenVPN](https://openvpn.net/ "OpenVPN"){:target="_blank"} 과 같은 도구를 사용해 IP 주소를 고정하고, 이 IP들만 포트에 접속 가능하도록 설정하는 것이 좋습니다.

![Security group - inbound](/uploads/ubuntu22-default-setting/security-inbound.png)
<p style="text-align:center;color:gray;"><small>보안그룹 Inbound 설정</small></p>

ubuntu 계정으로 로그인하며, 비밀번호 대신 키 파일을 사용합니다. [PuTTY](https://www.putty.org/ "PuTTY"){:target="_blank"}, [Termius](https://termius.com/ "Termius"){:target="_blank"} 같은 관리하기 용이한 프로그램을 사용하시면 편리합니다.
ppk 파일이나 pem 파일을 다운로드 받아서 로그인합니다.

### 2. hostname 변경

```shell
ubuntu@ip-172-0-0-0:~$ sudo hostnamectl set-hostname test
ubuntu@ip-172-0-0-0:~$ sudo reboot

# hostname 변경 완료
ubuntu@test:~$
```

### 3. Ubuntu update

```shell
ubuntu@test:~$ sudo apt update
ubuntu@test:~$ sudo apt upgrade
ubuntu@test:~$ sudo apt dist-upgrade
ubuntu@test:~$ sudo apt autoremove
ubuntu@test:~$ sudo apt clean
ubuntu@test:~$ sudo apt autoclean
```

### 4. history 형식 변경

![History Setup - default format](/uploads/ubuntu22-default-setting/history-default-format.png)
<p style="text-align:center;color:gray;"><small>기존 history 형식</small></p>

```shell
# history 형식 변경
ubuntu@test:~$ sudo vi /etc/profile

# 가장 하단에 아래 내용 추가
# VIM 기준 Shift + G 누르는 경우 가장 하단으로 이동
HISTTIMEFORMAT="[%Y-%m-%d %H:%M:%S] "
export HISTTIMEFORMAT
```

![History Setup - default time format](/uploads/ubuntu22-default-setting/history-default-timeformat.png)
<p style="text-align:center;color:gray;"><small>HISTTIMEFORMAT 내용 추가</small></p>

![History setup](/uploads/ubuntu22-default-setting/history-setup.png)
<p style="text-align:center;color:gray;"><small>history 형식 변경 완료</small></p>

### 5. history cache 늘리기

```shell
# history cache 늘리기
ubuntu@test:~$ sudo vi /etc/bash.bashrc 

# 가장 하단에 아래 내용 추가
# VIM 기준 Shift + G 누르는 경우 가장 하단으로 이동
export HISTSIZE=10000
export HISTFILESIZE=10000
```

![History default size](/uploads/ubuntu22-default-setting/history-default-size.png)
<p style="text-align:center;color:gray;"><small>HISTSIZE 및 HISTFILESIZE 내용 추가</small></p>

### 6. locale 한국으로 설정

```shell
# 현재 locale 확인
ubuntu@test:~$ locale
```

![Locale check](/uploads/ubuntu22-default-setting/locale-check.png)
<p style="text-align:center;color:gray;"><small>현재 locale 설정 값 확인</small></p>

```shell
# 한글 언어팩 설치
ubuntu@test:~$ sudo apt install language-pack-ko

# 한글 적용
ubuntu@test:~$ sudo update-locale LANG=ko_KR.UTF-8 LANGUAGE="ko_KR:ko:en_US:en" LC_MESSAGES=POSIX

# 재부팅 후 적용
ubuntu@test:~$ sudo reboot
```

![Setup locale](/uploads/ubuntu22-default-setting/setup-locale.png)
<p style="text-align:center;color:gray;"><small>locale 변경 완료</small></p>

### 7. timezone 한국으로 설정

```shell
# 타임존 확인
ubuntu@test:~$ timedatectl
```

![Timezone check](/uploads/ubuntu22-default-setting/timezone-check.png)
<p style="text-align:center;color:gray;"><small>현재 timezone 설정 값 확인</small></p>

```shell
#서울 타임존 있는지 확인
ubuntu@test:~$ timedatectl list-timezones | grep Seoul

#타임존 서울로 변경
ubuntu@test:~$ sudo timedatectl set-timezone Asia/Seoul 
```

![Timezone setup](/uploads/ubuntu22-default-setting/timezone-setup.png)
<p style="text-align:center;color:gray;"><small>timezone 변경 완료</small></p>



## 자주 하는 실수

- **보안 그룹에 MySQL(3306) 전 세계 개방**: 스캔·무차별 대입 대상이 됩니다. DB는 프라이빗 서브넷 또는 보안 그룹 소스로 웹 서버 SG만 허용하세요.
- **`HISTFILESIZE` 오타**: `HISTFILESIZE`처럼 쓰면 설정이 무시됩니다. `echo $HISTFILESIZE`로 확인하세요.
- **apt upgrade 중 재부팅 없이 커널 업데이트만 방치**: `reboot`가 필요한 경우가 있습니다.
- **키 파일 공유·슬랙 업로드**: 유출 시 즉시 키 페어를 교체하세요.

## 다음 단계 제안

- 스왑 버퍼가 필요하면 [Ubuntu 22.04 스왑 설정](/posts/ubuntu22-swap-memory/) 글을 이어서 적용하세요.
- 방화벽을 호스트에서도 이중화하려면 `ufw`로 SSH만 허용한 뒤 enable 하는 패턴을 검토하세요.
- 장기 운영 시 unattended-upgrades, fail2ban, 정기 스냅샷을 추가하세요.

## 참고문헌

- [How to set or change timezone](https://linuxize.com/post/how-to-set-or-change-timezone-on-ubuntu-20-04/ "How to set or change timezone"){:target="_blank"}
- [How do I change the default locale](https://askubuntu.com/questions/89976/how-do-i-change-the-default-locale-in-ubuntu-server "How do I change the default locale"){:target="_blank"}
