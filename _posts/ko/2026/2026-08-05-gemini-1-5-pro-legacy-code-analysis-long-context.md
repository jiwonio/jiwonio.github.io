---
layout: post
title: 'Gemini 1.5 Pro로 레거시 분석 시간 줄이기: 긴 컨텍스트 창 활용법'
slug: gemini-1-5-pro-legacy-code-analysis-long-context
lang: ko
translation_key: gemini-1-5-pro-legacy-code-analysis-long-context
post_type: deep-dive
date: 2026-08-05 11:36:38 +0900
updated: 2026-08-11 12:00:00 +0900
categories:
- AI
tags:
- Gemini
- LLM
- Legacy Code
description: 긴 컨텍스트 창으로 여러 파일에 흩어진 레거시 의존성을 한 번에 읽는 워크플로를 정리합니다. 통째 덤프의 실패 사례, 토큰 추정,
  검증 루프까지 포함합니다.
image: /uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp
ai_generated: true
permalink: /posts/gemini-1-5-pro-legacy-code-analysis-long-context/
---
오래된 서비스에 기능 수정 요청이 들어왔습니다. 담당자는 이미 퇴사했고, 위키에는 배포 순서만 남아 있습니다. 결제 관련 로직이 컨트롤러·서비스·모델·외부 클라이언트에 나뉘어 있어, 함수 이름 검색만으로는 실제 호출 스택을 가리기 어렵습니다. 파일 단위로 LLM에 붙여넣다 보면 파일 A의 맥락이 파일 B 질문 시점에 사라지고, 이전 답변을 다시 붙여 넣는 오버헤드가 분석보다 커집니다.

긴 컨텍스트 창은 이 문제를 “관련 모듈을 한 번에 읽게” 만들어 줍니다. Gemini 1.5 Pro가 백만 토큰급 컨텍스트를 대중화했고, 이후 모델도 같은 계열의 워크플로를 이어갑니다. 이 글에서는 **무엇을 넣고 무엇을 빼는지**, **답이 틀릴 때 어디서 검증하는지**를 중심으로 실무 절차를 정리합니다. Tool Use(함수 호출) 자체는 [별도 글](/posts/gemini-1-5-pro-tool-use-connecting-llms/)에서 다룹니다.

<!--more-->
![Gemini 1.5 Pro로 레거시 분석 시간 줄이기: 긴 컨텍스트 창 활용법](/uploads/gemini-1-5-pro-legacy-code-analysis-long-context/thumbnail.webp "Gemini 1.5 Pro로 레거시 분석 시간 줄이기: 긴 컨텍스트 창 활용법")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## 문제 정의: 파편화된 컨텍스트

레거시 분석이 느린 이유는 “한 파일이 어렵다”기보다 **맥락이 파일 경계로 쪼개져 있기** 때문입니다. 결제 요청 한 건이 대략 이런 식으로 흩어져 있다고 가정합니다.

* `controllers/payment_controller.rb` — HTTP 진입, 파라미터 검증
* `services/payment_service.rb` — 비즈니스 규칙, 여러 모델 호출
* `models/order.rb` / `models/user.rb` — 상태·권한
* `lib/external_api_client.rb` — PG 연동

`payment_service.rb`만 넣고 “버그 찾아줘”라고 물으면, 모델은 `Order` 상태 전이와 외부 클라이언트 타임아웃 정책을 모르므로 **절반의 정보로 그럴듯한 추측**을 합니다. 짧은 컨텍스트 모델에 파일을 순차로 넣으면 [컨텍스트가 대화 중 유실](/posts/antigravity-cli-context-loss-mistakes/)되는 문제도 겹칩니다. 긴 컨텍스트는 “관련 파일을 한 프롬프트에 고정”해 이 두 문제를 동시에 줄이려는 시도입니다.

## 긴 컨텍스트가 바꾸는 것 (그리고 바꾸지 않는 것)

백만 토큰은 중소 모듈 소스 대부분을 한 번에 넣기 충분한 크기입니다. 다만 창이 크다고 해서 다음이 자동으로 해결되지는 않습니다.

| 해결되는 쪽 | 해결되지 않는 쪽 |
| --- | --- |
| 여러 파일에 걸친 호출 흐름 초안 | 존재하지 않는 메서드·설정 값을 지어내는 환각 |
| “어느 파일이 관련 있는지” 지도 | `vendor`/`node_modules`까지 넣은 노이즈 |
| 리팩터 후보 목록 | 운영 환경의 실제 장애 재현 |

즉 긴 컨텍스트는 **지도 그리기 도구**에 가깝고, **배포 전 검증을 대체하지 않습니다.**

## 실무 워크플로: 범위 정하기 → 취합 → 질문 → 검증

### 1. 모노레포 전체가 아니라 모듈 경계부터

처음 시도에서 자주 실패하는 패턴은 “저장소 루트 `find` 한 방”입니다. 테스트 픽스처·생성된 코드·의존성 디렉터리까지 들어가면 토큰만 쓰고 신호는 옅어집니다. 먼저 도메인 경계를 좁힙니다.

1. 진입점 파일 1~2개 확정 (예: `PaymentController#create`)
2. 그 파일의 import/require·메서드 호출로 1-hop, 2-hop 파일만 수집
3. 그래도 부족할 때만 같은 도메인 디렉터리(`app/services/payment*`)를 확장

### 2. 취합 스크립트 (제외 목록 포함)

```bash
cd path/to/legacy/project

# 대략 토큰 상한 가늠: ASCII 위주 코드는 글자 수 / 4 전후
# 목표 예: 1차 분석 8만~20만 토큰 (제품·요금제 한도 확인)

OUT=combined_payment.txt
rm -f "$OUT"

{
  echo "Project structure (payment-related):"
  # tree가 없으면 find로 대체
  find app/controllers app/services app/models lib \
    -type f -name '*payment*' -o -name '*order*' 2>/dev/null | head -200
  echo
  echo "--- End of structure ---"
  echo
} > "$OUT"

# 제외: 의존성, 빌드 산출물, 초대형 생성 파일
find app lib \
  \( -path '*/node_modules/*' -o -path '*/vendor/*' -o -path '*/tmp/*' \
     -o -path '*/.git/*' -o -name '*.min.js' \) -prune -o \
  -type f \( -name '*.rb' -o -name '*.rake' \) -print0 \
| while IFS= read -r -d '' file; do
    case "$file" in
      *payment*|*order*|*checkout*) ;;
      *) continue ;;
    esac
    echo "--- File: $file ---" >> "$OUT"
    cat "$file" >> "$OUT"
    echo >> "$OUT"
  done

wc -c "$OUT"
# 예: 400KB ≈ 대략 10만 토큰 전후(언어·공백에 따라 편차 큼) → 한도 대비 여유 확인
```

실패 사례: 한 번은 관련 없는 `app/admin` 전체와 스펙 픽스처를 같이 넣었더니, 모델이 **존재하지 않는 `PaymentService#settle_async!`** 를 “핵심 경로”로 요약했습니다. 해당 심볼은 코드에 없었고, 스펙의 더블/목 이름과 본문 메서드를 섞은 것으로 보였습니다. 이후 **“답변의 모든 심볼을 `rg`로 재검색”** 단계를 고정했습니다.

### 3. 프롬프트: 실행 흐름 + 근거 강제

```text
당신은 레거시 결제 모듈을 인계받은 백엔드 엔지니어입니다.
아래에 제공된 코드만 근거로 답하세요. 코드에 없는 클래스·메서드·설정 키는
지어내지 말고 "코드에서 확인 불가"라고 쓰세요.

[목표]
1. PaymentController#create 부터 외부 PG 호출까지 실행 흐름을 번호 목록으로.
   각 단계: 파일 경로 / 클래스#메서드 / 한 줄 역할.
2. PaymentService의 핵심 책임 1~2문장. 근거가 되는 메서드명을 괄호로.
3. 버그·성능 위험 후보 최대 3개. 각 항목에 "근거 파일:라인 근처 심볼" 필수.
4. 스키마는 코드/마이그레이션에 나타난 관계만 Mermaid ERD로.
   추측 컬럼은 넣지 말 것.

출력은 한국어 마크다운. 불확실하면 확신도를 낮게 표시.

--- BEGINNING OF CODEBASE ---
(combined_payment.txt 전체)
--- END OF CODEBASE ---
```

“20년 경력 페르소나”보다 **근거 강제**가 환각을 더 잘 줄입니다. ERD·성능 진단은 보너스일 뿐, 1번 실행 흐름이 틀리면 나머지를 버려야 합니다.

### 4. 검증 루프 (15~30분 예산)

| 단계 | 하는 일 | 통과 기준 |
| --- | --- | --- |
| 심볼 검증 | 답변의 클래스·메서드를 `rg` | 전원 코드에 존재 |
| 진입 추적 | IDE “Find Usages”로 create → service | 모델이 말한 다음 호출과 일치 |
| 반례 질문 | “이 흐름을 깨는 early return이 있나?” | 새 분기가 코드에 실재 |
| 비용 점검 | 입력 토큰·지연 | 사소 질문에는 전체 덤프 재사용 금지 |

Before/After를 과장 없이 적으면 대략 이렇습니다. (팀·코드 규모에 따라 편차 큼)

* **Before**: 관련 파일 찾기 + 호출 스택 스케치 3~6시간, 중간에 잘못된 진입점 가정 1~2회
* **After (모듈 범위 긴 컨텍스트)**: 취합·1차 지도 20~40분, 심볼 검증 15분, 남은 시간을 실제 디버깅에 사용
* **After가 더 느린 경우**: 저장소 전체 덤프 + 검증 생략 → 잘못된 리팩터 계획으로 반나절 낭비

## 비용·한계·운영 팁

* **비용**: 대용량 입력을 매 질문마다 반복하지 않습니다. 큰 그림은 1~2회, 이후는 해당 파일 몇 개만 넣는 짧은 컨텍스트로 충분한 경우가 많습니다. 요금은 [Vertex AI / Gemini 가격표](https://cloud.google.com/vertex-ai/generative-ai/pricing)를 기준으로 팀 예산을 맞춥니다.
* **건초더미 속 바늘**: 컨텍스트가 길어질수록 특정 구절 회수 성능이 들쭉날쭉할 수 있습니다. 중요한 파일 경로를 질문 본문에 다시 적거나, “`external_api_client.rb`만 근거로”처럼 주의를 고정합니다. 공식 가이드는 [Long context](https://ai.google.dev/gemini-api/docs/long-context)를 참고합니다.
* **지연**: 수십 초~수분 응답은 실시간 페어 프로그래밍보다 **비동기 분석 작업**에 맞습니다.
* **모델 선택**: 제품명은 해마다 바뀝니다. 워크플로의 핵심은 “긴 컨텍스트 + 좁은 범위 + 심볼 검증”이며, 1.5 Pro는 그 패턴을 실무에 퍼뜨린 이정표로 이해하면 됩니다.

## 언제 쓰고, 언제 쓰지 않을지

| 상황 | 접근 | 이유 |
| --- | --- | --- |
| 작은 사이드 프로젝트 | 짧은 컨텍스트 IDE 채팅 | 모듈이 한 화면에 들어옴 |
| 신규 기능, 파일이 3~5개 | 파일 직접 첨부 | 긴 창 비용 대비 이득 작음 |
| 인계받은 레거시 도메인, 파일 15개+ | 긴 컨텍스트로 **지도** 후 좁혀 디버깅 | 탐색 시간 절감이 큼 |
| 프로덕션 장애 핫픽스 | 로그·메트릭 우선, 모델은 보조 | 환각 비용이 큼 |

## 결론

긴 컨텍스트는 레거시 분석에서 **파편화된 맥락을 한 판에 올려 두는 도구**입니다. 효과를 보려면 (1) 모듈 단위로 범위를 자르고, (2) 제외 목록을 두며, (3) 답의 모든 심볼을 코드에서 다시 확인하고, (4) 큰 덤프는 자주 돌리지 않아야 합니다. 통째 붙여넣기만으로는 오히려 잘못된 확신을 만듭니다.

### 참고문헌
- [Google AI, "Our next-generation model: Gemini 1.5"](https://blog.google/technology/ai/google-gemini-next-generation-model-february-2024/ "Google AI Blog on Gemini 1.5"){:target="_blank"}
- [Google AI for Developers, "Long context"](https://ai.google.dev/gemini-api/docs/long-context "Gemini API long context"){:target="_blank"}
- [Google Cloud, "Vertex AI pricing"](https://cloud.google.com/vertex-ai/generative-ai/pricing "Vertex AI Pricing Page"){:target="_blank"}
