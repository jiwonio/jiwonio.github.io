---
layout: post
title: 为什么 Cloudflare Full (strict) SSL 模式会失败以及如何修复
meta: 了解为什么 Cloudflare Full (strict) SSL 模式会失败而 Full 模式却能正常工作，尤其是在使用 GitHub Pages
  作为源服务器时。理解常见的 SSL 问题，并学习如何修复它们，以实现安全无缝的连接。
tags:
- cloudflare
image: /uploads/cloudflare-invalid-ssl/thumbnail.webp
lang: zh
translation_key: cloudflare-invalid-ssl
slug: cloudflare-invalid-ssl
description: 了解为什么 Cloudflare Full (strict) SSL 模式会失败而 Full 模式却能正常工作，尤其是在使用 GitHub
  Pages 作为源服务器时。理解常见的 SSL 问题，并学习如何修复它们，以实现安全无缝的连接。
permalink: /zh/posts/cloudflare-invalid-ssl/
---
**Cloudflare** 的 **Full (strict)** SSL 模式无法正常工作，而 Full 模式却可以，其原因通常在于源服务器（在此例中为 **GitHub Pages**）提供的 SSL 证书存在问题。Full (strict) 模式要求源服务器上的 SSL 证书不仅要有效，还必须由公认的证书颁发机构（CA）信任，与请求的域名匹配，并包含正确的证书链。然而，如果 GitHub Pages 的 SSL 证书不完全符合这些要求——例如缺少中间 CA、域名不匹配或设置延迟——Cloudflare 将在 Full (strict) 模式下拒绝连接。相反，Full 模式不验证证书的可信度，因此即使证书存在问题，它也能正常工作。

<!--more-->

![SSL/TLS HTTPS Background](/uploads/cloudflare-invalid-ssl/ssl-tls-https.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/skylarvision-2957633" title="Content copyright holder" target="_blank">skylarvision</a></small>
</p>

-----

**Cloudflare** 的 Full (strict) SSL 模式无法工作，而 Full 模式却能正常运行，其原因在于源服务器（本例中为 GitHub Pages）提供的 SSL 证书存在问题。
**Full (strict)** 模式要求源服务器的 SSL 证书必须是由**受信任的证书颁发机构（CA）**颁发的有效证书，与请求的域名完全匹配，并包含正确的证书链（包括中间 CA）。在此过程中，会增加一个验证证书的步骤以确保其可信度和完整性，从而增强安全性。

然而，在某些情况下，**GitHub Pages** 的 SSL 证书可能无法完全满足 Full (strict) 模式的要求。
下面我们来看看导致 Cloudflare 阻止连接的几个主要原因：

1.  **缺少中间证书**
    -   如果 SSL 证书链的一部分（中间 CA）缺失，Cloudflare 将不信任该证书。
        证书链的作用是连接客户端和服务器之间的信任关系，因此如果中间证书未正确设置，连接可能会在 Full (strict) 模式下被阻止。

2.  **域名不匹配**
    -   如果源服务器 SSL 证书中包含的域名与请求的域名不完全匹配，就会出现问题。
        例如，如果证书只包含 `www.jiwon.io` 而不包含根域名 `jiwon.io`，Full (strict) 模式会将其视为验证失败并阻止连接。

3.  **SSL 证书续订延迟**
    -   尽管 GitHub Pages 会自动管理 SSL 证书，但在设置新域名或续订现有证书的过程中可能会出现临时延迟。
        在此期间，如果证书过期，Full (strict) 模式会将其判断为不可信连接并予以阻止。

4.  **DNS 和 HTTPS 设置不完整**
    -   如果在 GitHub Pages 中禁用了“强制 HTTPS”（Enforce HTTPS）选项，或者 DNS 设置不正确，源服务器可能无法提供 HTTPS 连接。
        在这种情况下，Cloudflare 无法执行证书验证，连接将在 Full (strict) 模式下中断。

### 为什么在 Full 模式下可以工作

相比之下，Cloudflare 的 Full 模式不验证证书的可信度，只检查服务器和客户端之间是否启用了加密。
即使源服务器提供的是无效或自签名证书，Full 模式也会允许连接。
这种方式虽然不能完全保证安全，但旨在提供更广泛的兼容性。

### 为什么会发生这种问题？

GitHub Pages 是一个为个人项目或简单网站设计的托管平台，其 SSL 证书设置大多是自动完成的。
这种自动化设置对于普通用户的需求来说已经足够，但在满足企业环境或高级安全要求方面可能存在局限性。
Cloudflare 的 Full (strict) 模式旨在发现并阻止这些自动化设置中的任何微小缺陷，从而导致这两个系统之间发生冲突。

### 解决方法

1.  **检查 GitHub Pages 的 SSL 状态**
    -   在 GitHub Pages 设置中启用“强制 HTTPS”（Enforce HTTPS）选项，以强制使用 HTTPS 连接。
    -   确认您的域名是否已包含在 GitHub Pages 的 SSL 证书中。
        -   如果 GitHub Pages 未提供 SSL 证书或证书正在等待颁发，Full (strict) 模式将失败。

2.  **调整 Cloudflare SSL 模式**
    -   要使用 Full (strict) 模式，GitHub Pages 的 SSL 证书必须完全有效。
    -   如果当前设置下问题仍然存在，请将 Cloudflare 的 SSL 模式更改为 Full，以确保网站能正常运行。

3.  **使用 SSL 验证工具**
    -   使用 SSL Labs 等工具检查源服务器的 SSL 证书状态。您可以检查证书链、有效期、域名匹配情况等。

4.  **清除 Cloudflare 缓存**
    -   在 Cloudflare 仪表板中，通过“缓存 (Caching) > 清除所有内容 (Purge Everything)”来删除旧的缓存数据。如果缓存的错误信息导致问题持续存在，此操作可以解决问题。

5.  **替换为 Cloudflare Origin CA 证书**
    -   如果您需要 Full (strict) 模式提供的安全级别，可以考虑配置一个独立的服务器，并使用 Cloudflare Origin CA 证书，而不是依赖 GitHub Pages。

### 结论

Full 模式下正常工作而 Full (strict) 模式下失败的原因，是 GitHub Pages 的 SSL 证书未能满足 Cloudflare 严格的验证条件。
在大多数情况下，重新检查 GitHub Pages 的 SSL 设置或清除 Cloudflare 缓存即可解决问题。
如果必须使用 Full (strict) 模式，则需要仔细检查 GitHub Pages 和 Cloudflare 的配置。

### 参考资料

 - [Qualys SSL Labs](https://www.ssllabs.com/ "SSL Labs"){:target="_blank"}
 - [Let's Encrypt CAA Record](https://letsencrypt.org/docs/caa/ "Let's Encrypt"){:target="_blank"}
 - [Cloudflare SSL/TLS Full](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full/ "Cloudflare SSL/TLS Full"){:target="_blank"}