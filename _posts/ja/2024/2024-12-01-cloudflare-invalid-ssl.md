---
layout: post
title: CloudflareのFull (strict) SSLモードが失敗する理由とその解決策
meta: CloudflareのFullモードでは動作するのに、Full (strict) SSLモードで失敗する理由、特にオリジンサーバーとしてGitHub Pagesを使用している場合について解説します。一般的なSSLの問題を理解し、安全でシームレスな接続を実現するための修正方法を学びましょう。
tags:
- cloudflare
image: /uploads/cloudflare-invalid-ssl/thumbnail.webp
lang: ja
translation_key: cloudflare-invalid-ssl
slug: cloudflare-invalid-ssl
description: CloudflareのFullモードでは動作するのに、Full (strict) SSLモードで失敗する理由、特にオリジンサーバーとしてGitHub
  Pagesを使用している場合について解説します。一般的なSSLの問題を理解し、安全でシームレスな接続を実現するための修正方法を学びましょう。
permalink: /ja/posts/cloudflare-invalid-ssl/
categories:
- DevOps
post_type: deep-dive
---
**Cloudflare**の**Full**モードでは動作するのに**Full (strict)** SSLモードが機能しない理由は、通常、オリジンサーバー（この場合は**GitHub Pages**）が提供するSSL証明書の問題に起因します。Full (strict)モードでは、オリジンサーバーのSSL証明書が有効であるだけでなく、信頼できる認証局（CA）によって信頼され、要求されたドメインと一致し、正しい証明書チェーンを含んでいる必要があります。しかし、GitHub PagesのSSL証明書がこれらの要件（中間CAの欠落、ドメインの不一致、設定の遅延など）を完全に満たしていない場合、CloudflareはFull (strict)モードでの接続を拒否します。対照的に、Fullモードは証明書の信頼性を検証しないため、証明書に問題があっても機能します。

<!--more-->

![SSL/TLS HTTPS Background](/uploads/cloudflare-invalid-ssl/ssl-tls-https.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/skylarvision-2957633" title="Content copyright holder" target="_blank">skylarvision</a></small>
</p>

-----

**Cloudflare**のFull (strict) SSLモードが動作せず、Fullモードでは正常に動作する理由は、オリジンサーバー（この場合はGitHub Pages）が提供するSSL証明書に関連する問題のためです。
**Full (strict)**モードは、オリジンサーバーのSSL証明書が**信頼できる認証局（CA）**によって発行された有効な証明書であり、要求されたドメインと正確に一致し、正しい証明書チェーン（中間CAを含む）を含んでいる場合にのみ接続を許可します。この過程で、証明書の信頼性と完全性を保証するために証明書を検証するプロセスが追加されるため、セキュリティが強化されます。

しかし、**GitHub Pages**のSSL証明書は、特定の状況下ではFull (strict)モードの要件を完全に満たせないことがあります。これによりCloudflareが接続をブロックするいくつかの主な原因を見てみましょう：

1. **中間証明書の欠落**
   - SSL証明書チェーンの一部（中間CA）が欠落している場合、Cloudflareはその証明書を信頼しません。
     証明書チェーンはクライアントとサーバー間の信頼を繋ぐ役割を果たすため、中間証明書が正しく設定されていないとFull (strict)モードでの接続がブロックされることがあります。

2. **ドメインの不一致**
   - オリジンサーバーのSSL証明書に含まれるドメインが、要求されたドメインと正確に一致しない場合に問題が発生します。
     例えば、証明書が`www.jiwon.io`のみを含み、ルートドメインである`jiwon.io`を含まない場合、Full (strict)モードはこれを検証失敗とみなし、接続をブロックします。

3. **SSL証明書の更新遅延**
   - GitHub PagesはSSL証明書を自動的に管理しますが、新しいドメインを設定したり、既存の証明書を更新する過程で一時的な遅延が発生することがあります。
     この期間中に証明書が期限切れの状態になると、Full (strict)モードはこれを信頼できない接続と判断してブロックします。

4. **DNSおよびHTTPS設定の不備**
    - GitHub PagesでEnforce HTTPSオプションが無効になっているか、DNS設定が正しくない場合、オリジンサーバーがHTTPS接続を提供できないことがあります。
      この場合、Cloudflareは証明書の検証を実行できず、Full (strict)モードでの接続が中断されます。

### Fullモードで動作する理由

一方、CloudflareのFullモードは、証明書の信頼性を検証せず、単にサーバーとクライアント間の暗号化が有効になっているかだけを確認します。
オリジンサーバーが自己署名証明書など、信頼できない証明書を提供しても、Fullモードはこれを許可します。
これによりセキュリティは完全には保証されませんが、より広い互換性を提供するために設計された方式です。

### なぜこの問題が発生するのか？

GitHub Pagesは個人プロジェクトや簡単なウェブサイト向けのホスティングプラットフォームであり、SSL証明書の設定はほとんどが自動で行われます。
このような自動化された設定は、一般的なユーザーの要求には十分ですが、企業環境や高度なセキュリティ要件を満たすには限定的である可能性があります。
CloudflareのFull (strict)モードは、このような自動設定のささいな不備でも発見すると接続をブロックするように設計されているため、この2つのシステム間で衝突が発生するのです。

### 解決策

1. **GitHub PagesのSSL状態を確認**
   - GitHub Pagesの設定でEnforce HTTPSオプションを有効にし、HTTPS接続が強制されるようにします。
   - ドメインがGitHub PagesのSSL証明書に含まれているか確認します。
     - GitHub PagesがSSL証明書を提供していないか、発行待機中の場合、Full (strict)モードは失敗します。

2. **CloudflareのSSLモードを調整**
   - Full (strict)モードを使用するには、GitHub PagesのSSL証明書が完全に有効である必要があります。
   - 現在の設定で問題が解決しない場合は、CloudflareのSSLモードをFullに変更し、まずサイトが正常に動作するようにします。

3. **SSL検証ツールを使用**
   - SSL Labsなどのツールを使用して、オリジンサーバーのSSL証明書の状態を確認してください。証明書チェーン、有効期間、ドメインの一致などを確認できます。

4. **Cloudflareのキャッシュをクリア**
   - Cloudflareのダッシュボードで Caching > Purge Everything を実行し、古いキャッシュデータを削除します。キャッシュされたエラー情報が問題を引き起こし続けている場合に解決できます。

5. **Cloudflare Origin CA証明書で代替**
   - Full (strict)モードのセキュリティレベルが必要な場合は、GitHub Pagesの代わりにCloudflare Origin CA証明書を使用する別のサーバーを構成することも検討できます。

### 結論

Fullモードでは動作し、Full (strict)モードで失敗する理由は、GitHub PagesのSSL証明書がCloudflareの厳格な検証条件を満たしていないためです。
ほとんどの場合、GitHub PagesのSSL設定を再確認するか、Cloudflareのキャッシュをクリアすることで問題は解決します。
Full (strict)を必ず使用する必要がある場合は、GitHub PagesとCloudflareの設定を綿密に確認する必要があります。

### 参考資料

 - [Qualys SSL Labs](https://www.ssllabs.com/ "SSL Labs"){:target="_blank"}
 - [Let's Encrypt CAA Record](https://letsencrypt.org/docs/caa/ "Let's Encrypt"){:target="_blank"}
 - [Cloudflare SSL/TLS Full](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full/ "Cloudflare SSL/TLS Full"){:target="_blank"}