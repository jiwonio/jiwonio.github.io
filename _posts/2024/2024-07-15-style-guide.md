---
layout: post
title: 'Style Guide'
meta: 'As this is the first post on my blog, it serves as a record and an explanation of the basic style guide for this site.'
tags:
  - tutorial
---

This is the **first** post on my **GitHub Pages powered by Jekyll**. You can consider it a note-taking post.
When I write after a long time, I tend to forget my previous styles, leading to a mishmash of different styles.
To prevent such a mess and to practice writing, I decided to write this post.
While it might look nicer in Korean fonts, even the default browser fonts would be fine.
For now, only the styles for English fonts are added.
The CSS part might change gradually as I continue to manage the page.
Since this post is about styles, there's no interesting story to read.
I plan to gradually fill in more interesting stories as I go along.

<!--more-->

<img src="/uploads/style-guide/style-guide.png" alt="style guide" />

### 1. Code

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

Vivamus velit nulla, consectetur vel velit at, `aliquet sodales arcu`. Duis laoreet risus sapien. Praesent vestibulum leo et neque varius, nec sagittis velit rutrum. Etiam scelerisque id lorem elementum tempus. Curabitur eget orci mollis, efficitur ligula id, vulputate tortor.
**Lorem ipsum** dolor sit amet, consectetur adipiscing elit. Aenean maximus dolor non hendrerit placerat. Nam erat metus, malesuada pharetra ultricies sed, consequat ut nisi.

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

[`Lorem` ipsum](https://www.lipsum.com/ "Lorem ipsum"){:target="_blank"} dolor sit amet, consectetur adipiscing elit. Nulla varius cursus commodo. Aliquam nec sem efficitur, efficitur leo at, eleifend nibh.
Vestibulum ut malesuada odio, vel lacinia magna. Nullam eget lobortis dui. Integer sollicitudin urna sit amet magna consectetur iaculis. Sed ac tristique tellus.
Aenean at auctor risus. Ut a urna venenatis, tempor purus vitae, **sollicitudin mauris**. In finibus, ante eu tempor efficitur, est orci vehicula nulla,
vel scelerisque justo magna molestie ligula. Mauris ac risus in tortor ultrices laoreet sit amet nec nibh. Quisque risus diam, blandit quis euismod dignissim, lobortis eu ex.
Proin varius, enim vehicula sollicitudin bibendum, massa lectus pretium eros, vel congue quam justo sit amet tortor.

### 2. Links

<a href="https://blog.jiwon.io/" title="Blog link" target="_blank">
    <img src="/uploads/style-guide/square.png" style="max-width:150px;border-radius:20%;margin:0 auto;" alt="Blue Square" />
</a>

### 3. Images

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem 0 0;">
    <div>
        <img src="/uploads/style-guide/coding1.png" alt="Coding" />
    </div>
    <div>
        <img src="/uploads/style-guide/coding2.png" alt="Coding" />
    </div>
    <div>
        <img src="/uploads/style-guide/coding1.png" alt="Coding" />
    </div>
</div>

<div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem auto 0;max-width:400px;">
    <div>
        <img src="/uploads/style-guide/coding1.png" alt="Coding" />
    </div>
    <div>
        <img src="/uploads/style-guide/coding2.png" alt="Coding" />
    </div>
</div>

Nulla eu libero ut dui **volutpat luctus**. Nulla tempor mi at venenatis commodo. Nulla eget posuere ligula.
Duis varius quis urna in efficitur. Vivamus rhoncus neque ac `justo commodo`, vel commodo purus laoreet.
Mauris *efficitur vehicula sem*, ut lobortis mauris consequat non. Donec condimentum sem nunc, imperdiet ornare purus hendrerit vitae.
Suspendisse bibendum scelerisque tempus.
Quisque nisl lectus, aliquam sed sem ut, venenatis ultricies dui.

<div style="max-width:500px;margin:0 auto;">
  <img src="/uploads/style-guide/shadow.png" alt="Shadow" />
</div>

### 4. Videos

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

### 5. Lists

1. Lorem ipsum dolor sit amet, _consectetur_ adipiscing elit. `Praesent` quis nisi id massa aliquam accumsan. Donec ac massa non orci placerat aliquet **eget** in erat. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
2. Fusce quis nulla viverra, tincidunt est non, tristique orci. Sed dictum elit eu egestas consequat. Aliquam pellentesque lectus quis leo eleifend porttitor. Duis consectetur erat quis justo molestie ultrices.
3. Phasellus molestie justo in *vestibulum* facilisis. Ut id dui eleifend, auctor tellus eu, vestibulum ante. Aenean at ex pretium, mattis metus sit amet, luctus ex. Proin congue arcu eu ultricies iaculis.
4. Ut **gravida enim** sit amet condimentum blandit. Nullam et ligula luctus, vulputate sem vel, pharetra nulla. Cras at lacus at nulla tincidunt luctus vitae a tellus. Nullam quis dui vitae elit congue `convallis eget` nec nibh.
5. In nec mi non eros malesuada sollicitudin. Proin sed neque non justo efficitur suscipit. Cras accumsan odio ut nisl faucibus varius sit amet quis lacus. Nunc id nibh vehicula, iaculis mauris ut, maximus lorem.

- **Lorem ipsum dolor** - sit amet, consectetur adipiscing elit. Praesent quis nisi id __massa aliquam accumsan__. Donec ac massa non orci placerat aliquet eget in erat. Lorem ipsum dolor sit amet, **consectetur adipiscing** elit.
- **Fusce quis nulla** - viverra, tincidunt est non, tristique orci. Sed dictum elit eu egestas consequat. Aliquam pellentesque lectus quis leo eleifend porttitor. Duis consectetur erat quis justo molestie ultrices.
- **Phasellus molestie justo** - in vestibulum facilisis. Ut id dui eleifend, _auctor tellus eu_, vestibulum ante. Aenean at ex pretium, mattis metus sit amet, luctus ex. Proin congue arcu eu ultricies iaculis.
- **Ut gravida enim** - sit amet `condimentum blandit`. Nullam et ligula luctus, vulputate sem vel, pharetra nulla. Cras at lacus at nulla tincidunt luctus vitae a tellus. Nullam quis dui `vitae elit` congue convallis eget nec nibh.
- **In nec mi** - non eros malesuada sollicitudin. Proin sed neque non justo efficitur suscipit. ___Cras accumsan odio___ ut nisl faucibus varius sit amet quis lacus. [Nunc id nibh vehicula](https://www.lipsum.com/), iaculis mauris ut, maximus lorem.

### 6. Blockquotes

> If a tree falls in the woods, does it make a sound? If a pure function mutates some local data in order to produce an immutable return value, is that ok?

### 7. Tables

| Lorem ipsum                                                                                                                           | Curabitur                                                                                                                  | Pellentesque                                                                  |
|---------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [Spring Authorization Server](https://spring.io/projects/spring-authorization-server "Spring Authorization Server"){:target="_blank"} | Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam quis dui vitae elit congue convallis eget nec nibh.        | Java `17.0.3`                                                                 |
| [TypeORM](https://typeorm.io/ "TypeORM"){:target="_blank"}                                                                            | Pellentesque et leo nec felis pharetra maximus.                                                                            | SpringBoot `Java 18.x`                                                        |
| [Class Validation](https://github.com/typestack/class-validator "Class Validation"){:target="_blank"}                                 | Curabitur maximus sem a elit egestas, interdum egestas sapien mattis.                                                      | [NestJS](https://github.com/nestjs/nest "NestJS"){:target="_blank"} `10.4.10` |
| [Spring HATEOAS](https://spring.io/projects/spring-hateoas "Spring HATEOAS"){:target="_blank"}                                        | Morbi ac mi id nulla iaculis facilisis non nec lacus. Integer pharetra augue non ex malesuada, non blandit arcu malesuada. | Java `Java 21.x`                                                              |

### 8. Iframes

<p class="codepen" data-height="300" data-default-tab="html,result" data-slug-hash="mdNZWNe" data-pen-title="Waves Hello: css only" data-user="ghaste" style="height: 300px; box-sizing: border-box; display: flex; align-items: center; justify-content: center; border: 2px solid; margin: 1em 0; padding: 1em;">
  <span>See the Pen <a href="https://codepen.io/ghaste/pen/mdNZWNe">
  Waves Hello: css only</a> by Amit (<a href="https://codepen.io/ghaste">@ghaste</a>)
  on <a href="https://codepen.io">CodePen</a>.</span>
</p>
<script async src="https://cpwebassets.codepen.io/assets/embed/ei.js"></script>

