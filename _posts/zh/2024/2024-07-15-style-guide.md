---
layout: post
title: 风格指南
meta: 这是我博客的第一篇文章，旨在记录和解释本站的基本风格指南。
tags:
- tutorial
image: /uploads/style-guide/thumbnail.webp
lang: zh
translation_key: style-guide
slug: style-guide
description: 这是我博客的第一篇文章，旨在记录和解释本站的基本风格指南。
permalink: /zh/posts/style-guide/
categories:
- DevOps
post_type: deep-dive
---
这是我基于 **Jekyll 的 GitHub Pages** 博客上的**第一篇**文章。你可以把它看作是一篇笔记。
当我隔了很久再写作时，往往会忘记之前的风格，导致各种风格混杂在一起。
为了防止这种混乱并练习写作，我决定写下这篇文章。
虽然用韩语字体看起来可能更漂亮，但即使是浏览器的默认字体也足够了。
目前，只添加了英文字体的样式。
随着我继续维护这个页面，CSS 部分可能会逐渐改变。
由于这篇文章是关于样式的，所以没有什么有趣的故事可读。
我计划在未来逐渐填充更多有趣的故事。

<!--more-->

![style guide](/uploads/style-guide/style-guide.png)

### 1. 代码

```
@RestController
@RequiredArgsConstructor
public class MemberController {
 
    private final MemberService memberService;
 
    @GetMapping("/members")
    public List<MemberResponseDto.ListDto> getMemberList(){
        return memberService.findAll();
    }
 
    @PostMapping("/members")
    public Long createMember(@RequestBody MemberRequestDto.CreateDto createDto){
        return memberService.createMember(createDto.getName(), createDto.getAge());
    }
}
```

```ts
import { evaluate } from '@user/opensource-library';

evaluate('[1, 2, 3] |> map(_ + 1) |> sum');

evaluate('puts("Hello, world")', { puts: console.log.bind(console) });
```

Vivamus velit nulla, consectetur vel velit at, `aliquet sodales arcu`。Duis laoreet risus sapien。Praesent vestibulum leo et neque varius, nec sagittis velit rutrum。Etiam scelerisque id lorem elementum tempus。Curabitur eget orci mollis, efficitur ligula id, vulputate tortor。
**Lorem ipsum** dolor sit amet，这是一种常用的占位文本。Aenean maximus dolor non hendrerit placerat。Nam erat metus, malesuada pharetra ultricies sed, consequat ut nisi。

```php
<?php

$solution = file_get_contents(__DIR__ . '/solution.openai');

proxy_run($solution, cwd: __DIR__);

proxy_test($solution);

evaluate('1.. |> filter(_ % 2) |> take(3);');
```

```rust
#[macro_export]
macro_rules! T {
    [INT] => { $crate::lexer::TokenKind::Integer };
    [+]   => { $crate::lexer::TokenKind::Plus };
    [||]  => { $crate::lexer::TokenKind::PipePipe };
    // ..
}
```

[`Lorem` ipsum](https://www.lipsum.com/ "Lorem ipsum"){:target="_blank"} dolor sit amet, consectetur adipiscing elit。Nulla varius cursus commodo。Aliquam nec sem efficitur, efficitur leo at, eleifend nibh。
Vestibulum ut malesuada odio, vel lacinia magna。Nullam eget lobortis dui。Integer sollicitudin urna sit amet magna consectetur iaculis。Sed ac tristique tellus。
Aenean at auctor risus。Ut a urna venenatis, tempor purus vitae, **sollicitudin mauris**。In finibus, ante eu tempor efficitur, est orci vehicula nulla,
vel scelerisque justo magna molestie ligula。Mauris ac risus in tortor ultrices laoreet sit amet nec nibh。Quisque risus diam, blandit quis euismod dignissim, lobortis eu ex。
Proin varius, enim vehicula sollicitudin bibendum, massa lectus pretium eros, vel congue quam justo sit amet tortor。

### 2. 链接

<a href="https://blog.jiwon.io/" title="博客链接" target="_blank">
    <img src="/uploads/style-guide/square.png" style="max-width:150px;border-radius:20%;margin:0 auto;" alt="蓝色方块" />
</a>

### 3. 图片

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem 0 0;">
    <div>
        <img src="/uploads/style-guide/coding1.png" alt="编程" />
    </div>
    <div>
        <img src="/uploads/style-guide/coding2.png" alt="编程" />
    </div>
    <div>
        <img src="/uploads/style-guide/coding1.png" alt="编程" />
    </div>
</div>

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem auto 0;max-width:400px;">
    <div>
        <img src="/uploads/style-guide/coding1.png" alt="编程" />
    </div>
    <div>
        <img src="/uploads/style-guide/coding2.png" alt="编程" />
    </div>
</div>

Nulla eu libero ut dui **volutpat luctus**。Nulla tempor mi at venenatis commodo。Nulla eget posuere ligula。
Duis varius quis urna in efficitur。Vivamus rhoncus neque ac `justo commodo`, vel commodo purus laoreet。
Mauris *efficitur vehicula sem*, ut lobortis mauris consequat non。Donec condimentum sem nunc, imperdiet ornare purus hendrerit vitae。
Suspendisse bibendum scelerisque tempus。
Quisque nisl lectus, aliquam sed sem ut, venenatis ultricies dui。

<div style="max-width:500px;margin:0 auto;">
  <img src="/uploads/style-guide/shadow.png" alt="阴影" />
</div>

### 4. 视频

<div style="margin:0 auto;max-width:200px">
  <video style="width:100%" controls muted>
    <source src="/uploads/style-guide/sample-video.mp4" type="video/mp4">
  </video>
</div>

<div style="display:flex;gap:1rem;align-items:center;margin:1rem 0 0;">
    <div>
        <video style="width:100%;" controls muted>
            <source src="/uploads/style-guide/sample-video.mp4" type="video/mp4">
        </video>
    </div>
    <div>
        <video style="width:100%" controls muted>
            <source src="/uploads/style-guide/sample-video.mp4" type="video/mp4">
        </video>
    </div>
</div>

### 5. 列表

1. Lorem ipsum dolor sit amet, _consectetur_ adipiscing elit。`Praesent` quis nisi id massa aliquam accumsan。Donec ac massa non orci placerat aliquet **eget** in erat。Lorem ipsum dolor sit amet, consectetur adipiscing elit。
2. Fusce quis nulla viverra, tincidunt est non, tristique orci。Sed dictum elit eu egestas consequat。Aliquam pellentesque lectus quis leo eleifend porttitor。Duis consectetur erat quis justo molestie ultrices。
3. Phasellus molestie justo in *vestibulum* facilisis。Ut id dui eleifend, auctor tellus eu, vestibulum ante。Aenean at ex pretium, mattis metus sit amet, luctus ex。Proin congue arcu eu ultricies iaculis。
4. Ut **gravida enim** sit amet condimentum blandit。Nullam et ligula luctus, vulputate sem vel, pharetra nulla。Cras at lacus at nulla tincidunt luctus vitae a tellus。Nullam quis dui vitae elit congue `convallis eget` nec nibh。
5. In nec mi non eros malesuada sollicitudin。Proin sed neque non justo efficitur suscipit。Cras accumsan odio ut nisl faucibus varius sit amet quis lacus。Nunc id nibh vehicula, iaculis mauris ut, maximus lorem。

- **Lorem ipsum dolor** - sit amet, consectetur adipiscing elit。Praesent quis nisi id __massa aliquam accumsan__。Donec ac massa non orci placerat aliquet eget in erat。Lorem ipsum dolor sit amet, **consectetur adipiscing** elit。
- **Fusce quis nulla** - viverra, tincidunt est non, tristique orci。Sed dictum elit eu egestas consequat。Aliquam pellentesque lectus quis leo eleifend porttitor。Duis consectetur erat quis justo molestie ultrices。
- **Phasellus molestie justo** - in vestibulum facilisis。Ut id dui eleifend, _auctor tellus eu_, vestibulum ante。Aenean at ex pretium, mattis metus sit amet, luctus ex。Proin congue arcu eu ultricies iaculis。
- **Ut gravida enim** - sit amet `condimentum blandit`。Nullam et ligula luctus, vulputate sem vel, pharetra nulla。Cras at lacus at nulla tincidunt luctus vitae a tellus。Nullam quis dui `vitae elit` congue convallis eget nec nibh。
- **In nec mi** - non eros malesuada sollicitudin。Proin sed neque non justo efficitur suscipit。___Cras accumsan odio___ ut nisl faucibus varius sit amet quis lacus。[Nunc id nibh vehicula](https://www.lipsum.com/), iaculis mauris ut, maximus lorem。

### 6. 引用块

> 如果森林里一棵树倒下，它会发出声音吗？如果一个纯函数为了生成一个不可变的返回值而修改了某些局部数据，这样做可以吗？

### 7. 表格

| Lorem ipsum                                                                                                                           | Curabitur                                                                                                                  | Pellentesque                                                                  |
|---------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [Spring Authorization Server](https://spring.io/projects/spring-authorization-server "Spring Authorization Server"){:target="_blank"} | Lorem ipsum dolor sit amet, consectetur adipiscing elit。Nullam quis dui vitae elit congue convallis eget nec nibh。        | Java `17.0.3`                                                                 |
| [TypeORM](https://typeorm.io/ "TypeORM"){:target="_blank"}                                                                            | Pellentesque et leo nec felis pharetra maximus。                                                                            | SpringBoot `Java 18.x`                                                        |
| [Class Validation](https://github.com/typestack/class-validator "Class Validation"){:target="_blank"}                                 | Curabitur maximus sem a elit egestas, interdum egestas sapien mattis。                                                      | [NestJS](https://github.com/nestjs/nest "NestJS"){:target="_blank"} `10.4.10` |
| [Spring HATEOAS](https://spring.io/projects/spring-hateoas "Spring HATEOAS"){:target="_blank"}                                        | Morbi ac mi id nulla iaculis facilisis non nec lacus。Integer pharetra augue non ex malesuada, non blandit arcu malesuada。 | Java `Java 21.x`                                                              |

### 8. Iframe

<p class="codepen" data-height="300" data-default-tab="html,result" data-slug-hash="mdNZWNe" data-pen-title="Waves Hello: css only" data-user="ghaste" style="height: 300px; box-sizing: border-box; display: flex; align-items: center; justify-content: center; border: 2px solid; margin: 1em 0; padding: 1em;">
  <span>在 <a href="https://codepen.io">CodePen</a> 上查看由 Amit (<a href="https://codepen.io/ghaste">@ghaste</a>) 创作的 <a href="https://codepen.io/ghaste/pen/mdNZWNe">
  Waves Hello: css only</a>。</span>
</p>
<script async src="https://cpwebassets.codepen.io/assets/embed/ei.js"></script>