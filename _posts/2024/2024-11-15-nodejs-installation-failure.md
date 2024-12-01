---
layout: post
title: 'Resolving Package Installation Errors During Node.js Setup on Windows 11'
meta: 'Discover how to fix common package installation errors when setting up Node.js on Windows 11. This guide provides clear solutions for handling compilation issues with C/C++ and Python using Chocolaty.'
tags:
  - nodejs
---

When installing [Node.js](https://nodejs.org/ "nodejs"){:target="_blank"} on Windows 11, you may encounter errors related to additional package installations. 
These errors often occur due to the necessity to compile some Node.js packages using **C/C++** and **Python**. 
This guide provides detailed solutions to efficiently resolve these issues and ensure a smooth installation process.
One common error arises from the use of `chocolaty` for installing additional tools. 
If `visualstudio2019-workload-vctools` cannot be installed in the existing chocolaty path, it may result in installation failures. 
The installation process involves displaying a CMD screen where the installation proceeds using PowerShell. 
Despite several attempts, you might find that a clean installation cannot be achieved.
This translation was provided with the assistance of **Microsoft Copilot**.

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">제목과 첫 문단은 영어가 멋있어요.</small>

<img src="/uploads/nodejs-installation-failure/nodejs.png" alt="node.js" />

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/copyrightfreepictures-203" title="Content copyright holder" target="_blank">CopyrightFreePictures</a></small>
</p>

-----

Windows 11에서 **Node.js**를 설치할 때 추가 패키지 설치와 관련된 오류가 발생할 수 있습니다. 
이러한 오류는 **C/C++**와 **Python**을 사용하여 일부 Node.js 패키지를 컴파일해야 하는 필요성 때문에 발생합니다. 
이러한 문제를 효율적으로 해결하고 원활한 설치 과정에 도움을 드리고자 글로 남깁니다.

일반적인 오류 중 하나는 추가 도구를 설치하기 위해 `chocolaty`를 사용할 때 발생합니다. 
기존 chocolaty 경로에 `visualstudio2019-workload-vctools`를 설치할 수 없는 경우 설치 실패가 발생할 수 있습니다. 

> visualstudio2019-workload-vctools not installed. the package was not found with the source(s) listed.

Windows 11 에서 Node.js 설치 중 추가 패키지 설치 오류 관련해서 위와 같은 메시지를 받은 경우 해결 방법입니다.
이 글은 초보자와 경험 많은 개발자 모두가 설치 과정에서 흔히 겪는 문제를 명확하고 실행 가능한 해결책으로 제공하는 것을 목표로 합니다.

<div style="display:grid;">
    <img src="/uploads/nodejs-installation-failure/automatically-install.png" alt="Automatically install" style="justify-self:center;" />
</div>
<p style="text-align:center;color:gray;"><small>node.js 설치중에 필요한 도구 설치</small></p>

Node.js 설치 중에는 위와 같이, 설치에 필요한 부가적인 필수 항목들을 인스톨 할 수 있도록 도와주는 옵션이 존재합니다.
계속해서 진행하는 경우, 보통의 경우에는 정상적으로 설치가 되어야 합니다.

<div style="display:grid;">
    <img src="/uploads/nodejs-installation-failure/necessary-tools-installing.png" alt="Necessary tools installing" style="justify-self:center;" />
</div>
<p style="text-align:center;color:gray;"><small>필요한 도구 설치중</small></p>

<div style="display:grid;">
    <img src="/uploads/nodejs-installation-failure/installation-failure.png" alt="Installation failure" style="justify-self:center;" />
</div>
<p style="text-align:center;color:gray;"><small>설치중 오류 발생</small></p>

Node.js 사용에 필요한 추가 도구를 설치하기 위한 CMD 화면이 표시되고, PowerShell 을 이용하여 설치가 진행됩니다. 
설치 중에 위와 같은 에러가 표시되고 아무리 다시 실행해봐도 클린 설치가 되지 않습니다.

## 1. Chocolaty 재설치

 - C:\ProgramData\chocolaty 디렉터리로 이동하여 해당 디렉터리를 삭제합니다.
   Node.js를 재설치하면 chocolaty와 필요한 도구들도 함께 재설치됩니다.
   <img src="/uploads/nodejs-installation-failure/chocolatey.png" alt="Chocolatey folder" />

## 2. Visual Studio Build Tools 설치

 - 최신 버전의 [Visual Studio 2019 - Build Tools for Visual Studio 2019](https://my.visualstudio.com/Downloads?q=visual%20studio%202019 "Build Tools for Visual Studio 2019"){:target="_blank"}를 다운로드하고 설치합니다.
   <img src="/uploads/nodejs-installation-failure/download-build-tools.png" alt="Download build tools" />
   <img src="/uploads/nodejs-installation-failure/msbuild-tools.png" alt="MSBuild tools download" />
   <img src="/uploads/nodejs-installation-failure/install-msbuild-tools.png" alt="Install msbuild tools" />
 - 설치가 완료되면 다음 명령어를 실행하여 visualstudio2019-workload-vctools를 [업그레이드](https://community.chocolatey.org/packages/visualstudio2019-workload-vctools#upgrade "Choco upgrade"){:target="_blank"}합니다:
   ```shell
   choco upgrade visualstudio2019-workload-vctools -y
   ```
   <img src="/uploads/nodejs-installation-failure/upgrade-vctools.png" alt="Upgrade vctools" />

## 설치완료

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

<div style="display:grid;">
   <img src="/uploads/nodejs-installation-failure/upgrade-successful.png" alt="Upgrade successful" style="justify-self:center;" />
</div>
<p style="text-align:center;color:gray;"><small>설치 완료</small></p>

## 참고문헌

- [Windows 11 (Version 22H2)](https://en.wikipedia.org/wiki/Windows_11 "Windows 11"){:target="_blank"}
- [Node.js 18.x LTS (includes npm 9.6.7)](https://nodejs.org/docs/latest-v18.x/api/index.html "Node.js 18.x LTS"){:target="_blank"}
- [choco-install-visualstudio2017-workload-vctools-fails-error-the-install-of](https://stackoverflow.com/questions/65185384/choco-install-visualstudio2017-workload-vctools-fails-error-the-install-of "StackOverflow 참고사항"){:target="_blank"}