---
layout: post
title: 'Creating Multiple Development Environments with WSL2 on Windows 11'
meta: 'Learn how to set up and manage multiple development environments using WSL2 on Windows 11. This guide covers installation, configuration, and tips for optimizing your workflow.'
tags:
  - wsl2
---

In today's fast-paced development world, efficiently managing **multiple development environments** is essential. 
Windows Subsystem for Linux 2 (**WSL2**) provides a powerful and flexible way to create and manage isolated environments directly on your **Windows 11** machine.
Whether you're a software developer or a hobbyist, having separate environments for different projects can streamline your workflow and minimize conflicts. 
This guide will walk you through setting up and configuring **multiple WSL2 instances** on Windows 11, ensuring you can optimize your development productivity.
This translation was provided with the assistance of **Microsoft Copilot**.

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">제목과 첫 문단은 영어가 멋있어요.</small>

<img src="/uploads/multiple-wsl2-instances/server.jpg" alt="Multiple WSL2 Instances" />

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
    <small>&copy; <a href="https://unsplash.com/ko/@benofthenorth" title="Content copyright holder" target="_blank">Ben Griffiths</a></small>
</p>

-----

레거시 환경이나 분산 환경 등 모든 개발 환경에서 환경 설정을 하는 것은 여간 번거로운 일이 아닙니다. 
매번 환경을 새로 세팅하는 일은 드물고, 한번 설정하면 몇 개월 혹은 몇 년 동안 큰 변화 없이 사용하게 되는 경우가 많습니다. 
이렇다 보니 개발자들은 환경 설정 방법을 매번 구글링하여 찾아보는 경우가 많습니다.

PHP를 개발할 때는 [MAMP](https://www.mamp.info/ "MAMP"){:target="_blank"}나 [XAMPP](https://www.apachefriends.org/ "XAMPP"){:target="_blank"}와 같은 도구를 사용하여 개발 환경을 쉽게 구성할 수 있습니다. 
또한, [Docker](https://www.docker.com/ "Docker"){:target="_blank"}와 같은 컨테이너 기술을 이용하거나 [VirtualBox](https://www.virtualbox.org/ "VirtualBox"){:target="_blank"}, [VMware](https://www.vmware.com/ "VMware"){:target="_blank"}와 같은 가상 환경을 활용하는 방법도 좋은 대안이 될 수 있습니다. 
이러한 도구들은 각각의 필요에 맞게 다양한 방식으로 개발 환경을 제공해줍니다.

이 글에서는 여러 개발 환경 설정 방법 중에서도 특히 Windows 11의 [WSL2](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux "Windows Subsystem for Linux"){:target="_blank"}를 이용한 개발 환경 설정 방법에 대해 자세히 알아보겠습니다. 
WSL2를 통해 보다 쉽게 격리된 환경을 구축하고 관리하는 방법을 소개하여, 여러분의 개발 생산성을 높이는 데 도움을 드리고자 합니다.

## WSL 사용 설정

Windows 11에서 **Windows Subsystem for Linux(WSL)**를 사용하려면, 먼저 관련된 기능을 켜서 레지스트리에 등록해야 합니다. 
이 기능을 활성화하지 않으면 WSL 설치 도중에 `wslregisterdistribution failed with error: 0x800701bc` 또는 `wslregisterdistribution failed with error: 0x80370102`와 같은 오류가 발생할 수 있습니다. 
이러한 오류는 WSL이 정상적으로 설치되지 않았음을 의미하며, 이를 해결하기 위해서는 몇 가지 설정이 필요합니다.

먼저, Windows 기능에서 '**Linux용 Windows 하위 시스템**' 및 '**가상 머신 플랫폼**'을 활성화해야 합니다. 이 두 가지 기능은 WSL2가 올바르게 작동하기 위해 필수적입니다. 
기능을 활성화한 후 시스템을 재부팅하면, 필요한 레지스트리 설정이 완료되어 WSL을 문제없이 설치할 수 있습니다.

<div style="display:grid;">
    <img src="/uploads/multiple-wsl2-instances/windows-features.png" alt="Windows features on or off" style="justify-self:center;" />
</div>

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem auto 0;max-width:100%;">
    <div>
        <img src="/uploads/multiple-wsl2-instances/windows-features-1.png" alt="Windows features on or off" />
    </div>
    <div>
        <img src="/uploads/multiple-wsl2-instances/windows-features-2.png" alt="Windows features on or off" />
    </div>
</div>
<p style="text-align:center;color:gray;"><small>Windows 기능 켜기/끄기</small></p>

추가로, WSL 설치 후 최신 [Linux 커널 업데이트 패키지](https://learn.microsoft.com/ko-kr/windows/wsl/install-manual#step-4---download-the-linux-kernel-update-package "Linux 커널 업데이트 패키지 다운로드"){:target="_blank"}를 다운로드하여 설치해야 할 수도 있습니다. 
이를 통해 WSL 환경이 최신 상태로 유지되며, 잠재적인 오류를 방지할 수 있습니다. 
모든 준비가 완료되면, 이제 다양한 Linux 배포판을 설치하고 개발 환경을 구성할 수 있습니다.

## WSL 배포판 설치

WSL 설치할 준비는 모두 완료되었으므로, 배포판을 설치해보겠습니다.

<div style="display:grid;">
    <img src="/uploads/multiple-wsl2-instances/wsl-installable-list.png" alt="WSL Installable List" style="justify-self:center;" />
</div>
<p style="text-align:center;color:gray;"><small>WSL 설치 가능 배포판</small></p>

`wsl -l -o` 명령어로 설치 가능한 배포판 이미지를 확인할 수 있습니다. 
이 명령어를 사용하면 현재 설치 가능한 모든 Linux 배포판 목록이 표시됩니다. 

Ubuntu, Debian, Kali Linux 등 여러 옵션을 확인할 수 있습니다. 
다음 단계로는 원하는 배포판을 선택하여 설치하는 것입니다. 
배포판을 설치하려면 다음과 같이 `wsl --install -d <배포판 이름>` 명령어를 사용하면 됩니다.
예를 들어, Ubuntu를 설치하고 싶다면 `wsl --install -d Ubuntu` 명령어를 입력하면 됩니다.

설치가 완료되면 자동으로 해당 배포판이 실행되고 초기 설정을 진행할 수 있습니다. 
이제 원하는 Linux 배포판을 선택하고 설치하여 WSL 환경에서 다양한 개발 작업을 시작해 보세요. 
각각의 배포판은 고유한 특성과 도구를 제공하므로, 프로젝트에 가장 적합한 배포판을 선택하는 것이 중요합니다.

## 같은 종류의 리눅스 다중 설치

*2024년 12월* 기준으로 `wsl --install` 명령어를 입력하면 기본 배포판인 **Ubuntu**가 설치됩니다.
설치되는 버전은 가장 최신의 LTS 버전인 **Ubuntu 24.04.1 LTS**입니다. 이 이미지를 설치한 후, 기본적인 설정을 마치고 나면 해당 이미지를 `export` 명령어로 내보내어 추후에 다시 `import` 명령어를 사용해 재생성할 수 있습니다.

```shell
wsl --export Ubuntu Ubuntu-clean.tar
wsl --import Ubuntu-clean .\Ubuntu-clean .\Ubuntu-clean.tar
```

이 명령어들을 실행하면, 현재 설정된 Ubuntu 이미지를 Ubuntu-clean.tar 파일로 내보내고, 필요할 때 해당 이미지를 다시 가져와 새로운 인스턴스로 사용할 수 있습니다. 
이는 동일한 개발 환경을 여러 개 생성하거나, 초기 상태를 유지하면서 다양한 설정을 테스트할 때 유용합니다.

이후 `wsl -l -v` 명령어를 입력하면 현재 설치된 WSL 배포판 목록을 확인할 수 있습니다. 
아래 이미지는 설치 완료된 이미지 목록을 보여줍니다. 이후에는 `wsl -d Ubuntu-clean` 명령어를 입력하여 특정 배포판을 실행 할 수 있습니다.

<div style="display:grid;">
    <img src="/uploads/multiple-wsl2-instances/wsl-installed-list.png" alt="WSL Installed List" style="justify-self:center;" />
</div>
<p style="text-align:center;color:gray;"><small>설치 완료 된 이미지</small></p>

이렇게 설치된 각각의 이미지마다 개발 환경을 별도로 구성하면 다양한 실험과 테스트를 진행할 수 있습니다.
예를 들어, 한 이미지에서는 Apache 웹서버를 운영하고, 다른 이미지에서는 Nginx 웹서버를 설치하여 서로 다른 웹서버의 성능과 특성을 비교해 볼 수 있습니다. 
또한, 같은 웹서버의 다른 버전을 설치하거나, 다양한 개발 언어의 버전을 설치하여 각 환경에서의 호환성 및 성능을 테스트할 수 있습니다.

이처럼 각각의 WSL2 인스턴스에 별도의 개발 환경을 설정함으로써, 특정 프로젝트에 맞춘 최적의 환경을 구축할 수 있습니다. 
이는 개발 중 발생할 수 있는 종속성 충돌을 최소화하고, 프로젝트 간의 격리된 테스트 환경을 제공하여 보다 효율적인 개발 프로세스를 지원합니다.
테스트 환경의 등록을 해제하고, vhd 파일까지 삭제하려면 `wsl --unregister Ubuntu-clean` 명령어를 입력하면 됩니다.

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem auto 0;max-width:100%;">
    <div>
        <img src="/uploads/multiple-wsl2-instances/wsl-ubuntu-apache2.png" alt="WSL Ubuntu Apache2" />
    </div>
    <div>
        <img src="/uploads/multiple-wsl2-instances/wsl-ubuntu-nginx.png" alt="WSL Ubuntu Nginx" />
    </div>
</div>
<p style="text-align:center;color:gray;"><small>각각 웹서버 설정</small></p>

결론적으로, WSL2를 이용한 다중 인스턴스 환경은 개발자들에게 유연성과 확장성을 제공하며, 다양한 실험과 테스트를 손쉽게 수행할 수 있는 강력한 도구가 됩니다. 
이렇게 설정된 환경을 통해 개발 생산성을 극대화하고, 다양한 시나리오에 대한 검증을 보다 체계적으로 수행할 수 있습니다.

## 참고문헌

- [WSL을 사용하여 Windows에 Linux를 설치하는 방법](https://learn.microsoft.com/ko-kr/windows/wsl/install "WSL을 사용하여 Windows에 Linux를 설치하는 방법"){:target="_blank"}
- [WSL-Error-0x80370102-해결](https://velog.io/@jaylnne/WSL-Error-0x80370102-해결 "wslregisterdistribution failed with error: 0x80370102"){:target="_blank"}
- [WSL-WSL2-Ubuntu-구동-시-0x800701bc-에러](https://velog.io/@meek/WSL-WSL2-Ubuntu-구동-시-0x800701bc-에러 "wslregisterdistribution failed with error: 0x800701bc"){:target="_blank"}
- [윈도우 WSL 환경에서 같은 종류의 리눅스를 다중으로 설치하는 방법](https://blog.naver.com/techshare/222596544852 "윈도우 WSL 환경에서 같은 종류의 리눅스를 다중으로 설치하는 방법"){:target="_blank"}
