---
layout: post
title: Resolving Package Installation Errors During Node.js Setup on Windows 11
description: Discover how to fix common package installation errors when setting up
  Node.js on Windows 11. This guide provides clear solutions for handling compilation
  issues with C/C++ and Python using Chocolaty.
tags:
- nodejs
image: /uploads/nodejs-installation-failure/thumbnail.webp
lang: en
translation_key: nodejs-installation-failure
slug: nodejs-installation-failure
categories:
- dev
permalink: /en/posts/nodejs-installation-failure/
post_type: deep-dive
updated: 2024-11-15 10:00:00 +0900
---
When installing [Node.js](https://nodejs.org/ "nodejs"){:target="_blank"} on Windows 11, you may encounter errors related to additional package installations. 
These errors often occur due to the necessity to compile some Node.js packages using **C/C++** and **Python**. 
This guide provides detailed solutions to efficiently resolve these issues and ensure a smooth installation process.
One common error arises from the use of `chocolatey` for installing additional tools. 
If `visualstudio2019-workload-vctools` cannot be installed in the existing chocolatey path, it may result in installation failures. 
The installation process involves displaying a CMD screen where the installation proceeds using PowerShell. 
Despite several attempts, you might find that a clean installation cannot be achieved.

<!--more-->

![node.js](/uploads/nodejs-installation-failure/nodejs.png)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/copyrightfreepictures-203" title="Content copyright holder" target="_blank">CopyrightFreePictures</a></small>
</p>

-----

When installing **Node.js** on Windows 11, you might run into errors related to installing additional packages.
These errors often happen because some Node.js packages need to be compiled using **C/C++** and **Python**.
I'm writing this guide to help you efficiently solve these problems and ensure a smooth installation process.

One common error occurs when using `chocolatey` to install additional tools.
If `visualstudio2019-workload-vctools` can't be installed in the existing Chocolatey path, the installation may fail.

> visualstudio2019-workload-vctools not installed. the package was not found with the source(s) listed.

If you received a message like the one above regarding an additional package installation error while installing Node.js on Windows 11, here is the solution.
This article aims to provide clear, actionable solutions for common problems that both beginners and experienced developers face during the installation process.

![Automatically install](/uploads/nodejs-installation-failure/automatically-install.png)
<p style="text-align:center;color:gray;"><small>Installing necessary tools during Node.js setup</small></p>

During the Node.js installation, as shown above, there is an option to help you install additional required tools.
If you proceed, the installation should normally complete successfully.

![Necessary tools installing](/uploads/nodejs-installation-failure/necessary-tools-installing.png)
<p style="text-align:center;color:gray;"><small>Installing necessary tools</small></p>

![Installation failure](/uploads/nodejs-installation-failure/installation-failure.png)
<p style="text-align:center;color:gray;"><small>Error during installation</small></p>

A CMD window appears to install the additional tools required for Node.js, and the installation proceeds using PowerShell.
During the installation, an error like the one above is displayed, and a clean installation fails no matter how many times you retry.

### 1. Reinstall Chocolatey

 - Navigate to the `C:\ProgramData\chocolatey` directory and delete it.
   Reinstalling Node.js will also reinstall Chocolatey and the necessary tools.
   ![Chocolatey folder](/uploads/nodejs-installation-failure/chocolatey.png)

### 2. Install Visual Studio Build Tools

 - Download and install the latest version of [Build Tools for Visual Studio 2019](https://visualstudio.microsoft.com/downloads/ "Build Tools for Visual Studio 2019"){:target="_blank"}.
   ![Download build tools](/uploads/nodejs-installation-failure/download-build-tools.png)
   ![MSBuild tools download](/uploads/nodejs-installation-failure/msbuild-tools.png)
   ![Install msbuild tools](/uploads/nodejs-installation-failure/install-msbuild-tools.png)
 - Once the installation is complete, run the following command to [upgrade](https://community.chocolatey.org/packages/visualstudio2019-workload-vctools "Choco upgrade"){:target="_blank"} `visualstudio2019-workload-vctools`:
   ```shell
   choco upgrade visualstudio2019-workload-vctools -y
   ```
   ![Upgrade vctools](/uploads/nodejs-installation-failure/upgrade-vctools.png)

### Installation Complete

You have now completed the installation of Node.js and the necessary packages!
Your development environment is now ready.

Here are some additional steps to verify your setup:

1. Check the Node.js Version: <br/>
   To verify that the installation was successful, run the following command:
   ```shell
   # This command allows you to check the versions of Node.js and npm.
   node -v
   npm -v
   ```
2. Create a Basic Project: <br/>
   To confirm that Node.js is installed correctly, you can create a simple project. Navigate to your desired directory and run the following commands:
   ```shell
   # These commands create a new project directory and initialize it with default package settings.
   mkdir my-node-project
   cd my-node-project
   npm init -y
   ```
3. Install Essential Packages: <br/>
   Try installing some basic packages for your project. For example, to install Express, run the following command:
   ```shell
   # This command installs the Express package, which you can use to build a server.
   npm install express
   ```
4. Other Configurations: <br/>
   If you need any other configurations or packages, it's a good idea to install them now. Install any additional packages required by your project and finalize your environment setup.

Node.js and the necessary tools are now installed and configured on Windows 11. You are ready to start developing. Happy coding!

![Upgrade successful](/uploads/nodejs-installation-failure/upgrade-successful.png)
<p style="text-align:center;color:gray;"><small>Installation complete</small></p>

### References

- [Windows 11 (Version 22H2)](https://en.wikipedia.org/wiki/Windows_11 "Windows 11"){:target="_blank"}
- [Node.js 18.x LTS (includes npm 9.6.7)](https://nodejs.org/docs/latest-v18.x/api/index.html "Node.js 18.x LTS"){:target="_blank"}
- [choco-install-visualstudio2017-workload-vctools-fails-error-the-install-of](https://stackoverflow.com/questions/65185384/choco-install-visualstudio2017-workload-vctools-fails-error-the-install-of "StackOverflow Reference"){:target="_blank"}