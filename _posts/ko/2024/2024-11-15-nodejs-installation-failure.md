---
layout: post
title: Windows 11 Node.js 설치 오류 해결
tags:
- nodejs
image: /uploads/nodejs-installation-failure/thumbnail.webp
lang: ko
translation_key: nodejs-installation-failure
slug: nodejs-installation-failure
description: Windows 11에서 Node.js 설치 중 Chocolatey와 Visual Studio Build Tools(visualstudio2019-workload-vctools) 실패를 재현·해결하는 절차와 재발 방지 체크리스트를 정리합니다.
post_type: deep-dive
categories:
- DevOps
updated: 2026-07-13 12:00:00 +0900
---
Windows 11에서 **Node.js**를 설치할 때 C/C++, Python 컴파일이 필요한 네이티브 패키지 때문에 오류가 나는 경우가 많습니다. **Chocolatey**로 추가 도구를 설치하는 과정에서 `visualstudio2019-workload-vctools` 설치 실패로 깨끗한 설치가 안 되는 문제를 해결하는 방법을 정리합니다.

<!--more-->

![node.js](/uploads/nodejs-installation-failure/nodejs.png)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/copyrightfreepictures-203" title="Content copyright holder" target="_blank">CopyrightFreePictures</a></small>
</p>

-----

## 왜 이 오류가 나는가

Node.js 자체 설치보다, **네이티브 애드온을 컴파일할 빌드 체인**을 같이 깔 때 문제가 납니다. 일부 npm 패키지는 미리 빌드된 바이너리가 없거나 환경과 맞지 않으면 `node-gyp`가 C/C++·Python 도구로 소스 빌드를 시도합니다. Windows 설치 마법사의 "자동으로 필요한 도구 설치"는 내부적으로 Chocolatey를 쓰고, 그 과정에서 `visualstudio2019-workload-vctools` 같은 패키지를 받습니다.

이미 Chocolatey 캐시·부분 설치가 깨져 있거나, Visual Studio Build Tools 버전·워크로드가 기대와 다르면 다음과 비슷한 메시지가 반복됩니다.

> visualstudio2019-workload-vctools not installed. the package was not found with the source(s) listed.

같은 설치 프로그램을 여러 번 눌러도 **깨진 Chocolatey 상태**가 남으면 클린 설치처럼 보이지 않을 수 있습니다.

## 증상 확인

Windows 11에서 **Node.js**를 설치할 때 추가 패키지 설치와 관련된 오류가 발생할 수 있습니다. 
이러한 오류는 **C/C++**와 **Python**을 사용하여 일부 Node.js 패키지를 컴파일해야 하는 필요성 때문에 발생합니다. 
이러한 문제를 효율적으로 해결하고 원활한 설치 과정에 도움을 드리고자 글로 남깁니다.

일반적인 오류 중 하나는 추가 도구를 설치하기 위해 `chocolaty`를 사용할 때 발생합니다. 
기존 chocolaty 경로에 `visualstudio2019-workload-vctools`를 설치할 수 없는 경우 설치 실패가 발생할 수 있습니다. 

> visualstudio2019-workload-vctools not installed. the package was not found with the source(s) listed.

Windows 11 에서 Node.js 설치 중 추가 패키지 설치 오류 관련해서 위와 같은 메시지를 받은 경우 해결 방법입니다.
이 글은 초보자와 경험 많은 개발자 모두가 설치 과정에서 흔히 겪는 문제를 명확하고 실행 가능한 해결책으로 제공하는 것을 목표로 합니다.

![Automatically install](/uploads/nodejs-installation-failure/automatically-install.png)
<p style="text-align:center;color:gray;"><small>node.js 설치중에 필요한 도구 설치</small></p>

Node.js 설치 중에는 위와 같이, 설치에 필요한 부가적인 필수 항목들을 인스톨 할 수 있도록 도와주는 옵션이 존재합니다.
계속해서 진행하는 경우, 보통의 경우에는 정상적으로 설치가 되어야 합니다.

![Necessary tools installing](/uploads/nodejs-installation-failure/necessary-tools-installing.png)
<p style="text-align:center;color:gray;"><small>필요한 도구 설치중</small></p>

![Installation failure](/uploads/nodejs-installation-failure/installation-failure.png)
<p style="text-align:center;color:gray;"><small>설치중 오류 발생</small></p>

Node.js 사용에 필요한 추가 도구를 설치하기 위한 CMD 화면이 표시되고, PowerShell 을 이용하여 설치가 진행됩니다. 
설치 중에 위와 같은 에러가 표시되고 아무리 다시 실행해봐도 클린 설치가 되지 않습니다.

### 1. Chocolatey 재설치

 - C:\ProgramData\chocolaty 디렉터리로 이동하여 해당 디렉터리를 삭제합니다.
   Node.js를 재설치하면 chocolaty와 필요한 도구들도 함께 재설치됩니다.
   ![Chocolatey folder](/uploads/nodejs-installation-failure/chocolatey.png)

### 2. Visual Studio Build Tools 설치

 - 최신 버전의 [Visual Studio 2019 - Build Tools for Visual Studio 2019](https://visualstudio.microsoft.com/downloads/ "Build Tools for Visual Studio 2019"){:target="_blank"}를 다운로드하고 설치합니다.
   ![Download build tools](/uploads/nodejs-installation-failure/download-build-tools.png)
   ![MSBuild tools download](/uploads/nodejs-installation-failure/msbuild-tools.png)
   ![Install msbuild tools](/uploads/nodejs-installation-failure/install-msbuild-tools.png)
 - 설치가 완료되면 다음 명령어를 실행하여 visualstudio2019-workload-vctools를 [업그레이드](https://community.chocolatey.org/packages/visualstudio2019-workload-vctools "Choco upgrade"){:target="_blank"}합니다:
   ```shell
   choco upgrade visualstudio2019-workload-vctools -y
   ```
   ![Upgrade vctools](/uploads/nodejs-installation-failure/upgrade-vctools.png)

### 설치완료

Node.js 설치 및 필요한 패키지 설치를 모두 완료했습니다! 
이제 개발 환경이 준비되었습니다. 

다음은 추가로 확인할 사항들입니다:

1. Node.js 버전 확인: <br/>
   설치가 제대로 되었는지 확인하려면 다음 명령어를 실행하세요:
   ```shell
   # 이 명령어를 통해 Node.js와 npm의 버전을 확인할 수 있습니다.
   node -v
   npm -v
   ```
2. 기본 프로젝트 생성: <br/>
   Node.js가 제대로 설치되었는지 확인하기 위해 간단한 프로젝트를 생성해볼 수 있습니다. 원하는 디렉터리로 이동한 후, 다음 명령어를 실행하세요:
   ```shell
   # 이 명령어를 통해 새 프로젝트 디렉터리를 만들고, 기본 패키지 설정을 할 수 있습니다.
   mkdir my-node-project
   cd my-node-project
   npm init -y
   ```
3. 필수 패키지 설치: <br/>
   프로젝트에 필요한 기본 패키지를 설치해 보세요. 예를 들어, Express를 설치하려면 다음 명령어를 실행하세요:
   ```shell
   # 이 명령어를 통해 Express 패키지를 설치하고, 서버를 구축할 수 있습니다.
   npm install express
   ```
4. 기타 설정: <br/>
   추가로 필요한 설정이나 패키지가 있다면, 지금 설치해두는 것이 좋습니다. 프로젝트의 요구사항에 따라 필요한 패키지를 설치하고 환경 설정을 마무리하세요.

이제 Windows 11에서 Node.js와 필요한 도구들이 설치 및 설정되었습니다. 개발을 시작할 준비가 완료되었습니다. 즐거운 코딩 되세요!

![Upgrade successful](/uploads/nodejs-installation-failure/upgrade-successful.png)
<p style="text-align:center;color:gray;"><small>설치 완료</small></p>



## 재발 방지 체크리스트

1. **관리자 권한** PowerShell/CMD에서 Chocolatey·Build Tools 작업을 수행했는지 확인합니다.
2. 설치 후 `node -v`, `npm -v`와 함께 네이티브 모듈이 필요한 패키지 하나로 스모크 테스트를 합니다.
3. 회사 PC라면 **정책으로 VS Build Tools 설치가 막혀 있는지** 확인합니다. 이 경우 관리자 배포 패키지가 필요합니다.
4. 가능하면 Node LTS를 [공식 설치 프로그램](https://nodejs.org/){:target="_blank"} 또는 버전 관리 도구(예: `nvm-windows`, `fnm`)로 통일합니다.
5. CI에서는 Windows 러너에 미리 캐시된 Build Tools 이미지를 쓰거나, 네이티브 빌드가 필요 없는 패키지 전략을 검토합니다.

## 대안 경로

- **Chocolatey 없이** Visual Studio Build Tools만 먼저 설치한 뒤 Node를 다시 설치해 보기
- `npm config set msvs_version 2019` (또는 설치한 연도)로 node-gyp가 찾는 도구 연도를 맞추기
- WSL2 Ubuntu 쪽에서 Node를 쓰는 워크플로로 우회하기 (Windows 네이티브 모듈이 꼭 필요하지 않을 때)

환경마다 패키지 소스·프록시·권한이 다르므로, 아래 참고 링크의 오류 메시지와 자신의 로그를 대조하는 것이 중요합니다.

## 참고문헌

- [Windows 11 (Version 22H2)](https://en.wikipedia.org/wiki/Windows_11 "Windows 11"){:target="_blank"}
- [Node.js 18.x LTS (includes npm 9.6.7)](https://nodejs.org/docs/latest-v18.x/api/index.html "Node.js 18.x LTS"){:target="_blank"}
- [choco-install-visualstudio2017-workload-vctools-fails-error-the-install-of](https://stackoverflow.com/questions/65185384/choco-install-visualstudio2017-workload-vctools-fails-error-the-install-of "StackOverflow 참고사항"){:target="_blank"}