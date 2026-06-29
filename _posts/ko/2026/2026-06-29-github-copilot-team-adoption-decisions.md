---
layout: post
title: 팀에 GitHub Copilot 도입할 때 리드가 먼저 정해야 할 것
slug: github-copilot-team-adoption-decisions
lang: ko
translation_key: github-copilot-team-adoption-decisions
post_type: deep-dive
date: 2026-06-29 20:52:00 +0900
categories:
- AI
tags:
- GitHub Copilot
- 팀 도입
- 워크플로
- 컨텍스트 관리
- 코드 리뷰
description: GitHub Copilot을 팀에 처음 도입할 때 1인, 3인, 10인 규모별로 달라지는 설정과 규칙. 라이선스 배분부터 리뷰
  기준까지, 리드가 먼저 결정해야 할 항목을 정리합니다.
image: /uploads/github-copilot-team-adoption-decisions/thumbnail.webp
ai_generated: true
permalink: /posts/github-copilot-team-adoption-decisions/
---
스프린트 중반에 팀원 한 명이 Copilot이 만들어준 코드를 그대로 PR에 올렸습니다. 리뷰어는 로직이 맞는지 확인하는 데 평소보다 두 배 시간이 걸렸고, 결국 "이 코드 직접 짠 거야, Copilot이 짠 거야?"라는 질문으로 리뷰가 시작되었습니다. 그 팀은 Copilot을 도입한 지 3주가 지났지만 어떤 기준도 없었습니다.

이런 상황은 도구 자체의 문제가 아닙니다. Copilot은 개인 생산성 도구로 설계되었지만, 팀에서 쓰면 리뷰 기준, 컨텍스트 공유, 라이선스 관리가 동시에 따라옵니다. 아무 준비 없이 "일단 써봐"로 시작하면 생산성이 오르기 전에 마찰이 먼저 생깁니다.

이 글에서는 팀 규모별(1인 → 3인 → 10인)로 리드가 Copilot 도입 전에 결정해야 할 항목과 그 이유를 다룹니다. 설치 방법보다는 팀 합의 포인트에 집중합니다.

<!--more-->

![팀에 GitHub Copilot 도입할 때 리드가 먼저 정해야 할 것](/uploads/github-copilot-team-adoption-decisions/thumbnail.webp "팀에 GitHub Copilot 도입할 때 리드가 먼저 정해야 할 것")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>

-----

## 왜 개인 도구가 팀 문제가 되는가

Copilot은 에디터 플러그인입니다. 각자의 IDE에서 동작하고, 제안은 개인 화면에만 보입니다. 그런데 결과물인 코드는 Git으로 공유됩니다. 이 간극이 문제를 만듭니다.

PR에 올라온 코드가 Copilot 제안을 거의 수정 없이 포함하고 있다면 리뷰어는 두 가지를 동시에 해야 합니다. 첫째, 코드 자체의 정합성 검토. 둘째, 작성자가 이 코드를 충분히 이해하고 있는지 판단. 후자는 원래 리뷰 항목에 없던 것입니다.

또한 Copilot Business 라이선스는 시트 단위 과금입니다. 2025년 기준 월 $19/사용자 (GitHub Copilot Business 요금제)입니다. 팀이 커질수록 "누가 실제로 쓰고 있는지"를 추적하지 않으면 비용이 쌓입니다.

## 1인 사용 단계에서 만들어야 할 기준

혼자 쓸 때는 규칙이 필요 없어 보이지만, 나중에 팀원을 온보딩할 때 기준이 없으면 처음부터 다시 정해야 합니다. 혼자 쓰는 시점에 다음 두 가지를 습관으로 잡아두는 것이 유용합니다.

### 제안 수락 기준 명시화

Copilot 제안을 수락하기 전 스스로에게 묻는 질문 목록을 간단히 정리해 두면 나중에 팀 규칙으로 발전시키기 쉽습니다.

```markdown
# copilot-accept-checklist.md (개인용)

## 제안 수락 전 확인
- [ ] 이 코드가 하는 일을 한 문장으로 설명할 수 있는가?
- [ ] 엣지 케이스(빈 값, 네트워크 오류 등)가 처리되어 있는가?
- [ ] 외부 패키지를 새로 추가하는가? 그 패키지가 이미 검토된 것인가?
- [ ] 시크릿 또는 하드코딩된 값이 포함되어 있지 않은가?
```

이 체크리스트는 Copilot이 틀렸을 때 잡아주는 장치가 아닙니다. 내가 제안을 이해했는지 확인하는 장치입니다.

### `.github/copilot-instructions.md` 작성 시작

GitHub Copilot은 저장소 루트의 `.github/copilot-instructions.md` 파일을 읽어서 제안 스타일에 반영합니다(Copilot for Business, 2024년 하반기부터 지원). 1인 단계에서 이 파일을 만들어두면, 팀원이 합류했을 때 Copilot이 같은 컨텍스트를 공유합니다.

```markdown
# .github/copilot-instructions.md

## 프로젝트 컨텍스트
- 백엔드: Node.js 20 + TypeScript 5, Express 기반
- DB: PostgreSQL 15, Prisma ORM 사용
- 테스트: Vitest, 커버리지 70% 이상 유지

## 코드 스타일 규칙
- `any` 타입 사용 금지. 모르는 타입은 `unknown`으로 선언 후 좁히기
- 에러 처리: try/catch 대신 Result 패턴 사용 (src/utils/result.ts 참조)
- 함수 하나는 한 가지 일만. 30줄 초과 시 분리 검토

## 보안 규칙
- API 키, 비밀번호는 절대 코드에 포함하지 말 것
- 사용자 입력은 반드시 zod로 검증 후 사용
```

이 파일이 없으면 팀원마다 Copilot이 다른 스타일로 제안하고, 코드베이스가 일관성을 잃습니다.

## 3인 팀으로 넘어갈 때 추가되는 결정

팀원이 2~3명이 되면 라이선스 관리와 리뷰 기준이 동시에 필요해집니다.

### 라이선스 배분 기준

GitHub Organization에서 Copilot Business를 켜면 관리자가 사용자별로 시트를 할당합니다. 기본값은 "모든 멤버에게 활성화"인데, 이 상태로 두면 외부 컨트리뷰터나 읽기 전용 멤버에게도 비용이 발생할 수 있습니다.

```yaml
# GitHub Organization > Settings > Copilot
# 권장 설정: "Selected teams and users"로 변경

# 할당 기준 예시
활성화:
  - 풀타임 개발자
  - 6개월 이상 기여 예정인 계약직

비활성화 검토:
  - 디자이너 (코드 리뷰만 하는 경우)
  - DevOps (인프라 코드만 다루는 경우 → 별도 판단)
  - 인턴 (온보딩 기간 종료 후 재평가)
```

월 1회 실제 사용량을 확인하는 것이 좋습니다. GitHub Organization > Insights > Copilot에서 사용자별 수락률과 활성 일수를 볼 수 있습니다. 30일 동안 활성 일수가 0인 시트는 비활성화를 고려할 수 있습니다.

### PR 리뷰 기준 합의

팀에서 Copilot을 쓰기 시작하면 리뷰어가 "이 코드, 이해하고 올린 거 맞아?"를 매번 물어볼 수 없습니다. 그 질문을 구조화하는 방법은 PR 템플릿에 체크항목을 넣는 것입니다.

```markdown
# .github/pull_request_template.md

## 변경 요약
<!-- 무엇을, 왜 바꿨는지 한 문단으로 -->

## 테스트 방법
<!-- 로컬에서 어떻게 확인했는지 -->

## Copilot 사용 여부
- [ ] 이 PR에서 Copilot 제안을 사용했습니다
  - 사용한 경우: 어떤 부분에 사용했는지 간략히 기술
  - 예) "서비스 레이어 단위 테스트 보일러플레이트, 직접 검토 후 수정함"

## 체크리스트
- [ ] 시크릿, 하드코딩된 값 없음
- [ ] 새 의존성 추가 시 팀에 공유함
- [ ] 엣지 케이스 테스트 포함
```

"Copilot 사용 여부"를 의무로 표시하는 것은 감시가 아닙니다. 리뷰어가 어느 부분에 더 집중해야 하는지 알기 위한 정보입니다. Copilot이 생성한 코드 중 비즈니스 로직 부분은 리뷰어가 더 꼼꼼히 보는 것이 자연스럽습니다.

## 10인 팀에서 달라지는 것

팀이 10명 이상이 되면 개인 설정 파일이 아닌 조직 수준 정책이 필요합니다. 주요 변화 포인트는 세 가지입니다.

### 1. `copilot-instructions.md`를 공식 문서로 관리

파일이 존재하는 것과 팀이 그 내용을 신뢰하는 것은 다릅니다. 10인 팀에서는 이 파일을 ADR(Architecture Decision Record)과 같은 수준으로 관리해야 합니다. 변경 시 PR 리뷰를 거치고, 왜 특정 규칙을 넣었는지 주석으로 남깁니다.

```markdown
# .github/copilot-instructions.md

## [2024-11 추가] Result 패턴 강제
# 이유: try/catch 중첩으로 에러 컨텍스트 소실 문제 반복 발생
# 참조: ADR-012
- 에러 처리는 Result<T, E> 패턴만 사용
- src/utils/result.ts의 ok(), err() 헬퍼 사용

## [2025-03 추가] 외부 API 호출 금지
# 이유: Copilot이 외부 SDK를 사용하는 코드를 제안할 때
#       사내 승인되지 않은 패키지가 포함된 사례 발생
- 새 HTTP 클라이언트, SDK는 반드시 의존성 검토 후 추가
```

### 2. Copilot 정책 문서 별도 작성

10인 팀은 온보딩하는 사람이 계속 생깁니다. "Copilot 어떻게 써요?"라는 질문을 반복하지 않으려면 내부 위키에 짧은 정책 문서가 있어야 합니다.

```markdown
# Copilot 사용 정책 (내부 위키)

## 허용
- 보일러플레이트, 반복 코드 생성
- 단위 테스트 초안 작성
- 문서화 주석 초안

## 주의
- 비즈니스 로직 생성 → 반드시 직접 검토 후 수락
- 데이터 접근 레이어 → DB 스키마 이해 없이 수락 금지

## 금지
- 시크릿, 인증 토큰 관련 코드에 Copilot 제안 그대로 적용
- 외부에 공개되지 않은 내부 API 스펙을 채팅(Copilot Chat)에 입력
```

마지막 항목이 중요합니다. Copilot Chat에 내부 API 스펙을 붙여넣는 행동은 해당 내용이 GitHub의 학습 데이터로 쓰일 가능성과 관련된 정책 문제가 될 수 있습니다. GitHub Copilot Business는 기본적으로 사용자 입력을 학습에 사용하지 않는다고 명시하고 있지만([GitHub Copilot Trust Center](https://resources.github.com/copilot-trust-center/ "GitHub Copilot 보안 정책"){:target="_blank"}), 팀원 모두가 이 정책을 인지하고 있어야 합니다.

### 3. 사용량 리뷰 주기 설정

```markdown
# Copilot 사용량 월간 리뷰 항목

1. 미사용 시트 확인
   - GitHub Org > Insights > Copilot
   - 활성 일수 5일 미만 → 다음 달 시트 해제 검토

2. 수락률 팀 평균 확인
   - 수락률이 지나치게 높은 경우(>80%): 제안을 제대로 검토하는지 확인
   - 수락률이 지나치게 낮은 경우(<10%): instructions.md 업데이트 필요

3. 리뷰 마찰 피드백
   - 스프린트 회고에서 "Copilot 때문에 리뷰가 어려웠던 사례" 1~2개 수집
   - instructions.md 또는 PR 템플릿에 반영
```

수락률이 높다고 좋은 것이 아닙니다. 제안을 거의 수정 없이 받아들이고 있다면 검토가 충분한지 확인이 필요합니다.

## 자주 놓치는 비용 두 가지

### 인지 부하

Copilot 제안이 화면에 나타나면 개발자는 "수락할지 말지"를 매번 결정해야 합니다. 익숙한 패턴의 코드라면 빠르게 판단하지만, 낯선 라이브러리나 복잡한 로직이 제안될 때는 판단 자체에 에너지가 씁니다. 팀 전체가 하루 종일 이 결정을 반복하면 실제 설계와 판단에 쓸 집중력이 줄어듭니다.

해결책은 단순합니다. `copilot-instructions.md`에 범위를 명확히 좁혀놓으면 제안의 질이 올라가고 판단 시간이 줄어듭니다. "이 프로젝트에서 쓰는 패턴"을 구체적으로 쓸수록 효과가 있습니다.

### 보안 감사 범위 확대

Copilot을 쓰기 시작하면 코드 출처가 다양해집니다. 동일한 취약점이 여러 파일에 복제될 위험도 있습니다. 예를 들어 SQL 인젝션에 취약한 패턴을 Copilot이 반복 제안하고 팀이 수락하면 같은 취약점이 여러 곳에 퍼질 수 있습니다.

이를 완화하려면 기존 SAST 도구(CodeQL, Semgrep 등)를 CI에 유지하면서, Copilot 도입 후 첫 1~2개월은 보안 관련 지적 사항이 늘었는지 모니터링하는 것이 좋습니다.

## 규모별 결론

| 상황 | 추천 설정 | 이유 |
|------|-----------|------|
| 1인 사이드 프로젝트 | `copilot-instructions.md` + 개인 체크리스트 | 나중에 팀 규칙으로 발전시킬 기반 마련 |
| 스타트업 3~5인 | PR 템플릿에 Copilot 사용 여부 항목 추가 | 리뷰 마찰을 구조로 줄임. 감시 아닌 정보 공유 |
| 10인 이상 팀 | 정책 문서 + 월간 사용량 리뷰 + instructions.md 버전 관리 | 온보딩 비용 절감, 불필요한 시트 비용 방지 |
| 레거시 코드 많은 팀 | instructions.md에 레거시 패턴 명시, 리팩토링 범위 제한 | Copilot이 레거시 스타일을 학습해 역행하는 것 방지 |
| 보안 민감 서비스 | Chat 입력 정책 명문화, SAST CI 필수 유지 | Copilot 도입 후 취약점 패턴 복제 위험 방어 |

도구를 끄거나 켜는 것보다, 팀이 같은 기준으로 쓰는 것이 먼저입니다. Copilot은 합의 없이 켜는 순간 리뷰 비용이 조용히 올라갑니다.

### 참고문헌

- [GitHub Copilot Business - Managing access](https://docs.github.com/en/copilot/managing-copilot/managing-copilot-for-your-enterprise/managing-access-to-copilot-in-your-enterprise "GitHub Copilot 접근 관리"){:target="_blank"}
- [Customizing GitHub Copilot with repository instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot "저장소 커스텀 지침"){:target="_blank"}
- [GitHub Copilot Trust Center](https://resources.github.com/copilot-trust-center/ "Copilot 보안 및 개인정보 정책"){:target="_blank"}
- [Copilot usage metrics API](https://docs.github.com/en/rest/copilot/copilot-usage "Copilot 사용량 API"){:target="_blank"}