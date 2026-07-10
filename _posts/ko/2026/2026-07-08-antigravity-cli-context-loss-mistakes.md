---
layout: post
title: Antigravity CLI 써 봤을 때 생긴 컨텍스트 소실 문제
slug: antigravity-cli-context-loss-mistakes
lang: ko
translation_key: antigravity-cli-context-loss-mistakes
post_type: deep-dive
date: 2026-07-08 00:00:00 +0900
categories:
- AI
tags:
- Antigravity CLI
- 컨텍스트 관리
- CLI 워크플로
- 코딩 자동화
description: Antigravity CLI를 실무에 투입했을 때 컨텍스트 소실로 발생한 문제를 재현하고, 방지 패턴을 단계별로 정리합니다.
  약 150자.
image: /uploads/antigravity-cli-context-loss-mistakes/thumbnail.webp
ai_generated: true
permalink: /posts/antigravity-cli-context-loss-mistakes/
---
레거시 서비스 마이그레이션 작업 중 Antigravity CLI를 처음 도입했습니다. 처음 며칠은 잘 됐는데, 파일 수가 늘어나면서 CLI가 "이미 수정한 파일"을 다시 건드리기 시작했습니다. 확인해보니 세션 간 컨텍스트가 초기화되면서 앞서 내린 결정을 전혀 모르는 상태로 다음 작업을 이어간 것이었습니다. 덕분에 같은 함수의 시그니처가 두 번 바뀌었고, 그 사이에 작성된 테스트는 두 번 다 깨졌습니다.

이 글은 Antigravity CLI가 컨텍스트를 어떻게 다루는지, 어디서 소실이 일어나는지, 그리고 세션을 넘어서도 의도가 유지되도록 하는 패턴을 다룹니다. "CLI가 멋대로 코드를 바꾼다"는 증상을 겪고 있다면 원인이 도구 버그가 아닐 가능성이 높습니다.

이 글을 읽으면 Antigravity CLI에서 세션 경계를 넘을 때 컨텍스트가 왜 끊기는지, 그리고 그걸 막기 위해 어떤 파일 구조와 호출 패턴을 써야 하는지 파악할 수 있습니다.

<!--more-->

![Antigravity CLI 써 봤을 때 생긴 컨텍스트 소실 문제](/uploads/antigravity-cli-context-loss-mistakes/thumbnail.webp "Antigravity CLI 써 봤을 때 생긴 컨텍스트 소실 문제")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>

-----

## 증상부터 확인하기

재현 가능한 시나리오는 이렇습니다.

1. 첫 번째 세션에서 `user_service.py`의 `get_user` 함수 반환 타입을 `dict`에서 `UserDTO`로 바꾸도록 지시합니다.
2. CLI가 수정을 마칩니다.
3. 터미널을 닫고 다음 날 새 세션을 엽니다.
4. `order_service.py`에서 `get_user`를 호출하는 부분을 리팩터링하도록 지시합니다.
5. CLI가 `get_user`를 다시 `dict` 반환으로 되돌립니다.

원인은 간단합니다. Antigravity CLI는 기본적으로 세션 단위로 컨텍스트를 관리합니다. 새 세션이 시작되면 이전 세션에서 내려진 결정이나 파일 변경 이력은 전달되지 않습니다. CLI는 현재 파일 상태만 읽고, 파일 내 주석이나 타입 힌트가 불완전하면 원래 패턴으로 추론해버립니다.

---

## 컨텍스트 소실이 일어나는 세 지점

### 1. 세션 경계

가장 흔한 지점입니다. `antigravity session` 객체는 프로세스가 종료되면 메모리에서 사라집니다. `--session-file` 옵션으로 세션 상태를 파일에 저장할 수 있지만, 기본값은 off입니다.

```bash
# 세션 상태를 파일로 저장 — 기본값은 저장 안 함
antigravity run --session-file .ag/session.json "get_user 반환 타입을 UserDTO로 변경"
```

이 옵션을 빠뜨리면 다음 실행 때 세션 파일이 없으므로 컨텍스트가 완전히 비어있는 상태에서 시작됩니다.

### 2. 스코프 초과

한 번에 너무 많은 파일을 포함하면 내부 컨텍스트 윈도우가 잘립니다. Antigravity CLI는 지시 받은 파일 목록을 토큰으로 변환하는데, 한계를 넘으면 뒤쪽 파일이 누락됩니다. 이때 누락된 파일에 있는 타입 정의나 인터페이스가 잘려 나가면서 앞선 결정과 모순된 수정이 발생합니다.

```bash
# 나쁜 예: 디렉터리 전체를 한 번에 넘기기
antigravity run --include "src/**/*.py" "UserDTO 적용"

# 나은 예: 모듈 단위로 분리
antigravity run --include "src/user/*.py" "UserDTO 적용"
antigravity run --include "src/order/*.py" --session-file .ag/session.json "UserDTO 호출부 수정"
```

### 3. 암묵적 결정의 부재

CLI는 파일을 읽고 패턴을 추론합니다. 도메인 결정("이 서비스는 DTO 레이어를 강제한다")이 코드 어디에도 명시되지 않으면, 새 세션에서 그 결정을 다시 추론할 근거가 없습니다. 결과적으로 CLI는 파일에 보이는 가장 단순한 패턴을 따릅니다.

---

## 방지 패턴

### 컨텍스트 파일로 결정 명시하기

프로젝트 루트에 `.ag/context.md` 파일을 두고, 모든 세션에 자동으로 포함시킵니다. 이 파일에는 코드에서 읽어낼 수 없는 도메인 결정만 씁니다.

```markdown
<!-- .ag/context.md -->
# 프로젝트 컨텍스트

## 아키텍처 결정 (ADR)
- 서비스 레이어는 DTO를 반환한다. dict 직접 반환 금지.
- UserDTO: src/models/dto.py 참조
- 외부 API 응답은 무조건 파싱 후 DTO로 변환한다.

## 현재 진행 중인 마이그레이션
- get_user: dict → UserDTO 변환 완료 (2025-07-01)
- get_order: 진행 중
```

이 파일을 `--context` 옵션으로 항상 포함합니다.

```bash
antigravity run \
  --context .ag/context.md \
  --session-file .ag/session.json \
  --include "src/order/*.py" \
  "get_order에 UserDTO 패턴 적용"
```

### 세션 파일 깃 추적 여부 결정

`.ag/session.json`을 깃에 추가할지는 팀 규모에 따라 다릅니다.

- **혼자 작업**: 추가해도 무방합니다. 세션 상태가 브랜치에 함께 관리됩니다.
- **팀 작업**: `.gitignore`에 추가하고, `context.md`만 공유합니다. 세션 파일은 작업자 개인의 실행 상태를 담고 있어서 충돌이 잦습니다.

```gitignore
# .gitignore
.ag/session.json
.ag/*.log
# context.md는 추적 — 팀 공유 결정 파일
```

### 실행 단위를 작게 자르기

단일 실행이 변경하는 파일 수를 제한합니다. 경험상 한 실행당 10개 이하의 파일, 파일당 200줄 이하가 컨텍스트가 잘리지 않는 안전한 범위였습니다. 정확한 토큰 한계는 버전마다 다를 수 있으므로 `--dry-run`으로 포함 파일 목록을 먼저 확인하는 것이 좋습니다.

```bash
# 실제 수정 전 포함 파일 목록 확인
antigravity run --dry-run \
  --context .ag/context.md \
  --include "src/**/*.py" \
  "UserDTO 적용"
```

출력에서 "context truncated" 경고가 보이면 `--include` 범위를 줄여야 합니다.

---

## 실제로 바뀐 워크플로

이전에는 Antigravity CLI를 즉흥적으로 호출했습니다. 터미널에서 필요할 때 명령 한 줄, 세션 파일 없이, 컨텍스트 파일 없이. 결과가 맘에 안 들면 되돌리고 다시 시도하는 방식이었습니다.

지금은 마이그레이션 단위로 `.ag/context.md`를 먼저 업데이트하고, 모듈별로 세션을 이어가는 방식을 씁니다. 귀찮아 보이지만 실제로 드는 시간은 5분 내외입니다. 반면에 잘못된 수정을 추적해서 되돌리는 시간은 훨씬 깁니다.

```bash
# 마이그레이션 시작 시 컨텍스트 파일 업데이트
echo "- get_order: 진행 중 ($(date +%Y-%m-%d))" >> .ag/context.md

# 모듈 단위 순차 실행
antigravity run \
  --context .ag/context.md \
  --session-file .ag/session.json \
  --include "src/order/service.py" \
  "get_order 반환 타입 OrderDTO로 변경"

antigravity run \
  --context .ag/context.md \
  --session-file .ag/session.json \
  --include "src/order/repository.py" \
  "service 변경사항에 맞게 repository 조정"
```

---

## 팀 도입 시 추가로 챙길 것

3인 이상 팀이라면 `context.md`의 소유권을 정해야 합니다. 누구나 수정할 수 있으면 서로 다른 결정이 섞여서 오히려 노이즈가 됩니다. PR 리뷰 대상에 `context.md`를 포함시키고, ADR(Architecture Decision Record) 형식으로 관리하면 변경 이유를 추적하기 쉽습니다.

또한 CI에서 Antigravity CLI를 자동 실행하는 경우, 세션 파일 경로를 환경변수로 분리하지 않으면 병렬 워크플로 간에 세션 파일이 충돌합니다.

```yaml
# .github/workflows/antigravity.yml 일부
- name: Run Antigravity
  env:
    AG_SESSION_FILE: .ag/session-${{ github.run_id }}.json
  run: |
    antigravity run \
      --context .ag/context.md \
      --session-file $AG_SESSION_FILE \
      --include "src/**/*.py" \
      "lint 수정"
```

---

## 결론

| 상황 | 추천 패턴 | 이유 |
|------|-----------|------|
| 1인 사이드 프로젝트 | `--session-file` + `context.md` 기본 구성 | 세션 재시작 시 컨텍스트 소실 방지에 충분 |
| 스타트업 3~5인 팀 | `context.md` 깃 추적, 세션 파일은 `.gitignore` | 결정 공유는 필요하지만 세션 충돌은 피해야 함 |
| 레거시 마이그레이션 진행 중 | 모듈 단위 실행 + ADR 형식 `context.md` | 파일 수가 많을수록 컨텍스트 잘림 위험이 커짐 |
| CI 자동화 포함 | `run_id` 기반 세션 파일 분리 | 병렬 워크플로 간 세션 파일 충돌 방지 |

Antigravity CLI 자체가 잘못 동작한 게 아니었습니다. 도구가 세션 경계를 어떻게 다루는지 이해하지 못한 채 쓴 것이 문제였습니다. 컨텍스트 파일과 세션 파일을 명시적으로 관리하는 것만으로 대부분의 "멋대로 바뀌는" 증상은 사라집니다.

---

### 참고문헌
- [OpenAI: Best practices for prompt engineering](https://platform.openai.com/docs/guides/prompt-engineering){:target="_blank"}
- [Anthropic: Long context tips](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips){:target="_blank"}
