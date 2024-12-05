---
layout: post
title: 'Why Cloudflare Full (strict) SSL Mode Fails and How to Fix It'
meta: 'Learn why the Cloudflare Full (strict) SSL mode fails while Full mode works, especially when using GitHub Pages as the origin server. Understand common SSL issues and how to fix them for a secure and seamless connection.'
tags:
  - cloudflare
---

The reason why the **Full (strict)** SSL mode in **Cloudflare** doesn't work while the Full mode does is typically due to issues with the SSL certificate provided by the origin server, 
in this case, **GitHub Pages**. The Full (strict) mode requires that the SSL certificate on the origin server is not only valid but also trusted by a recognized Certificate Authority (CA), 
matches the requested domain, and includes a correct certificate chain. 
However, if the GitHub Pages SSL certificate is not fully compliant with these requirements—such as a missing intermediate CA, 
domain mismatch, or setup delay—Cloudflare will reject the connection in Full (strict) mode. Conversely, the Full mode does not validate the certificate's trustworthiness, 
which allows it to function even if there are issues with the certificate.
This translation was provided with the assistance of **ChatGPT**.

<!--more-->

<small style="color:lightgray;text-decoration:line-through;font-style: italic;">[Medium](https://jiwonio.medium.com/ "medium.com/@jiwonio"){:target="_blank"} 에도 발행하고 있어요.</small>

<img src="/uploads/cloudflare-invalid-ssl/ssl-tls-https.jpg" alt="SSL/TLS HTTPS Background" />

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/skylarvision-2957633" title="Content copyright holder" target="_blank">skylarvision</a></small>
</p>

-----

**Cloudflare**의 Full (strict) SSL 모드가 작동하지 않고 Full 모드에서는 정상 작동하는 이유는, 원본 서버(이 경우 GitHub Pages)가 제공하는 SSL 인증서와 관련된 문제 때문입니다. 
**Full (strict)** 모드는 원본 서버의 SSL 인증서가 **신뢰할 수 있는 인증 기관(CA)**에서 발급된 유효한 인증서여야 하며, 요청된 도메인과 정확히 일치하고, 
올바른 인증서 체인(Intermediate CA 포함)을 포함해야만 연결을 허용합니다. 이 과정에서 인증서의 신뢰성과 완전성을 보장하기 위해 인증서를 검증하는 과정이 추가되므로 보안이 강화됩니다. 

하지만 **GitHub Pages**의 SSL 인증서는 특정 상황에서 Full (strict) 모드의 요구 사항을 완전히 충족하지 못할 수 있습니다. 
이를 통해 Cloudflare가 연결을 차단하는 몇 가지 주요 원인을 살펴보겠습니다:

1. **중간 인증서 누락**
   - SSL 인증서 체인의 일부(Intermediate CA)가 누락되어 있을 경우, Cloudflare는 인증서를 신뢰하지 않습니다. 
     인증서 체인은 클라이언트와 서버 간의 신뢰를 연결해 주는 역할을 하기 때문에, 중간 인증서가 제대로 설정되지 않으면 Full (strict) 모드에서 연결이 차단될 수 있습니다.

2. **도메인 불일치**
   - 원본 서버의 SSL 인증서에 포함된 도메인이 요청한 도메인과 정확히 일치하지 않을 경우 문제가 발생합니다. 
     예를 들어, 인증서가 `www.jiwon.io`만 포함하고 루트 도메인인 `jiwon.io`은 포함하지 않을 경우, Full (strict) 모드는 이를 검증 실패로 간주해 연결을 차단합니다.

3. **SSL 인증서의 갱신 지연**
   - GitHub Pages는 SSL 인증서를 자동으로 관리하지만, 새 도메인을 설정하거나 기존 인증서를 갱신하는 과정에서 일시적인 지연이 발생할 수 있습니다. 
     이 기간 동안 인증서가 만료된 상태로 남아 있게 되면 Full (strict) 모드는 이를 신뢰할 수 없는 연결로 판단하여 차단합니다.

4. **DNS 및 HTTPS 설정 불완전**
    - GitHub Pages에서 Enforce HTTPS 옵션이 비활성화되어 있거나, DNS 설정이 올바르지 않다면 원본 서버가 HTTPS 연결을 제공하지 못할 수 있습니다. 
      이 경우 Cloudflare는 인증서 검증을 수행하지 못하고 Full (strict) 모드에서 연결이 중단됩니다.

## Full 모드에서 작동하는 이유

반면, Cloudflare의 Full 모드는 인증서의 신뢰성을 검증하지 않고, 단순히 서버와 클라이언트 간의 암호화가 활성화되었는지만 확인합니다. 
원본 서버가 유효하지 않거나 자체 서명된 인증서를 제공하더라도, Full 모드는 이를 허용합니다. 
이는 보안이 완벽하게 보장되지는 않지만, 더 넓은 호환성을 제공하기 위해 설계된 방식입니다.

## 왜 이런 문제가 발생할까?

GitHub Pages는 개인 프로젝트나 간단한 웹사이트를 위한 호스팅 플랫폼으로, SSL 인증서 설정이 대부분 자동으로 이루어집니다. 
이러한 자동화된 설정은 일반적인 사용자 요구에는 충분하지만, 기업 환경이나 고급 보안 요구 사항을 충족하는 데에는 제한적일 수 있습니다. 
Cloudflare의 Full (strict) 모드는 이러한 자동화 설정의 사소한 결함이라도 발견하면 연결을 차단하도록 설계되어 있어, 이 두 시스템 간의 충돌이 발생하는 것입니다.

## 해결 방법

1. **GitHub Pages SSL 상태 확인**
   - GitHub Pages 설정에서 Enforce HTTPS 옵션을 활성화하여 HTTPS 연결이 강제되도록 설정합니다.
   - 도메인이 GitHub Pages의 SSL 인증서에 포함되어 있는지 확인합니다.
     - GitHub Pages가 SSL 인증서를 제공하지 않거나 발급 대기 중인 경우, Full (strict) 모드에서 실패합니다.

2. **Cloudflare SSL 모드 조정**
   - Full (strict) 모드를 사용하려면 GitHub Pages의 SSL 인증서가 완벽히 유효한 상태여야 합니다.
   - 현재 설정에서 문제가 지속된다면, Cloudflare의 SSL 모드를 Full로 변경하여 우선 사이트를 정상 작동하도록 합니다.

3. **SSL 검증 도구 사용**
   - SSL Labs와 같은 도구를 사용하여 원본 서버의 SSL 인증서 상태를 점검하세요. 인증서 체인, 유효 기간, 도메인 일치 여부 등을 확인할 수 있습니다.

4. **Cloudflare 캐시 초기화**
   - Cloudflare 대시보드에서 Caching > Purge Everything을 실행하여 오래된 캐시 데이터를 삭제합니다. 캐시된 오류 정보가 문제를 지속적으로 발생시키는 경우 이를 해결할 수 있습니다.

5. **Cloudflare Origin CA 인증서로 대체**
   - Full (strict) 모드의 보안 수준이 필요하다면, GitHub Pages 대신 Cloudflare Origin CA 인증서를 사용하는 별도 서버를 구성하는 것도 고려할 수 있습니다.

## 결론

Full 모드에서 작동하고 Full (strict) 모드에서 실패하는 이유는, GitHub Pages의 SSL 인증서가 Cloudflare의 엄격한 검증 조건을 충족하지 못하기 때문입니다. 
대부분의 경우, GitHub Pages의 SSL 설정을 다시 확인하거나 Cloudflare 캐시를 초기화하면 문제가 해결됩니다. 
Full (strict)을 반드시 사용해야 한다면, GitHub Pages와 Cloudflare 설정을 면밀히 점검해야 합니다.

## 참고문헌

 - [Qualys SSL Labs](https://www.ssllabs.com/ "SSL Labs"){:target="_blank"}
 - [Let's Encrypt CAA Record](https://letsencrypt.org/docs/caa/ "Let's Encrypt"){:target="_blank"}
 - [Cloudflare SSL/TLS Full](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full/ "Cloudflare SSL/TLS Full"){:target="_blank"}