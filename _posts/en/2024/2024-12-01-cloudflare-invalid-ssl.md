---
layout: post
title: Why Cloudflare Full (strict) SSL Mode Fails and How to Fix It
description: Learn why the Cloudflare Full (strict) SSL mode fails while Full mode
  works, especially when using GitHub Pages as the origin server. Understand common
  SSL issues and how to fix them for a secure and seamless connection.
tags:
- cloudflare
image: /uploads/cloudflare-invalid-ssl/thumbnail.webp
lang: en
translation_key: cloudflare-invalid-ssl
slug: cloudflare-invalid-ssl
categories:
- Web
permalink: /en/posts/cloudflare-invalid-ssl/
---

The reason why the **Full (strict)** SSL mode in **Cloudflare** doesn't work while the Full mode does is typically due to issues with the SSL certificate provided by the origin server,
in this case, **GitHub Pages**. The Full (strict) mode requires that the SSL certificate on the origin server is not only valid but also trusted by a recognized Certificate Authority (CA),
matches the requested domain, and includes a correct certificate chain.
However, if the GitHub Pages SSL certificate is not fully compliant with these requirements—such as a missing intermediate CA,
domain mismatch, or setup delay—Cloudflare will reject the connection in Full (strict) mode. Conversely, the Full mode does not validate the certificate's trustworthiness,
which allows it to function even if there are issues with the certificate.

<!--more-->

<small style="color:lightgray;font-style: italic;">I also publish on [Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"}.</small>

![SSL/TLS HTTPS Background](/uploads/cloudflare-invalid-ssl/ssl-tls-https.jpg)

<p style="text-align:center;opacity:0.8;">
    <small>&copy; <a href="https://pixabay.com/" title="Pixabay" target="_blank">Pixabay</a></small>
    <small>&copy; <a href="https://pixabay.com/ko/users/skylarvision-2957633" title="Content copyright holder" target="_blank">skylarvision</a></small>
</p>

-----

The reason why Cloudflare's **Full (strict)** SSL mode doesn't work while Full mode operates normally is due to issues with the SSL certificate provided by the origin server (in this case, GitHub Pages).
The **Full (strict)** mode requires the origin server's SSL certificate to be a valid certificate issued by a **trusted Certificate Authority (CA)**, to match the requested domain exactly, and to include the correct certificate chain (including the Intermediate CA) to allow a connection. This process adds a verification step to ensure the certificate's trustworthiness and completeness, thereby enhancing security.

However, the SSL certificate from **GitHub Pages** may not fully meet the requirements of Full (strict) mode in certain situations.
Let's look at some of the main reasons why Cloudflare might block the connection:

1. **Missing Intermediate Certificate**
   - If a part of the SSL certificate chain (the Intermediate CA) is missing, Cloudflare will not trust the certificate.
     Since the certificate chain serves to establish trust between the client and the server, an improperly configured intermediate certificate can cause the connection to be blocked in Full (strict) mode.

2. **Domain Mismatch**
   - A problem occurs if the domain included in the origin server's SSL certificate does not exactly match the requested domain.
     For example, if the certificate only covers `www.jiwon.io` and not the root domain `jiwon.io`, Full (strict) mode will consider it a verification failure and block the connection.

3. **SSL Certificate Renewal Delay**
   - GitHub Pages manages SSL certificates automatically, but temporary delays can occur when setting up a new domain or renewing an existing certificate.
     If the certificate remains expired during this period, Full (strict) mode will identify it as an untrusted connection and block it.

4. **Incomplete DNS and HTTPS Settings**
    - If the "Enforce HTTPS" option is disabled in GitHub Pages, or if the DNS settings are incorrect, the origin server may not be able to provide an HTTPS connection.
      In this case, Cloudflare cannot perform certificate validation, and the connection is dropped in Full (strict) mode.

### Why It Works in Full Mode

On the other hand, Cloudflare's Full mode does not verify the certificate's trustworthiness; it only checks whether encryption is enabled between the server and the client.
Even if the origin server provides an invalid or self-signed certificate, Full mode will allow it.
This approach doesn't guarantee complete security but is designed to offer broader compatibility.

### Why Does This Problem Occur?

GitHub Pages is a hosting platform for personal projects and simple websites, where SSL certificate setup is mostly automated.
While this automated setup is sufficient for typical user needs, it can be limited in meeting enterprise or advanced security requirements.
Cloudflare's Full (strict) mode is designed to block connections if it detects even minor flaws in such automated setups, leading to conflicts between the two systems.

### How to Fix It

1. **Check GitHub Pages SSL Status**
   - Enable the "Enforce HTTPS" option in your GitHub Pages settings to force an HTTPS connection.
   - Verify that your domain is included in the GitHub Pages SSL certificate.
     - If GitHub Pages is not providing an SSL certificate or if issuance is pending, Full (strict) mode will fail.

2. **Adjust Cloudflare SSL Mode**
   - To use Full (strict) mode, the SSL certificate on GitHub Pages must be perfectly valid.
   - If the problem persists with your current settings, switch the Cloudflare SSL mode to "Full" to get your site working first.

3. **Use an SSL Verification Tool**
   - Use a tool like SSL Labs to check the status of your origin server's SSL certificate. You can verify the certificate chain, expiration date, and domain match.

4. **Purge the Cloudflare Cache**
   - In the Cloudflare dashboard, go to Caching > Purge Everything to delete old cached data. This can resolve issues caused by cached error information.

5. **Replace with a Cloudflare Origin CA Certificate**
   - If the security level of Full (strict) mode is required, you might consider setting up a separate server that uses a Cloudflare Origin CA certificate instead of relying on GitHub Pages.

### Conclusion

The reason it works in Full mode but fails in Full (strict) mode is that the SSL certificate from GitHub Pages does not meet Cloudflare's strict validation requirements.
In most cases, the issue can be resolved by re-checking your GitHub Pages SSL settings or purging the Cloudflare cache.
If you must use Full (strict) mode, you need to carefully inspect both your GitHub Pages and Cloudflare settings.

### References

 - [Qualys SSL Labs](https://www.ssllabs.com/ "SSL Labs"){:target="_blank"}
 - [Let's Encrypt CAA Record](https://letsencrypt.org/docs/caa/ "Let's Encrypt"){:target="_blank"}
 - [Cloudflare SSL/TLS Full](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full/ "Cloudflare SSL/TLS Full"){:target="_blank"}