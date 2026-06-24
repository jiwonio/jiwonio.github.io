---
layout: post
title: 'Gemini 1.5 Pro Tool Use: LLM과 외부 세계 연결하기'
slug: gemini-1-5-pro-tool-use-connecting-llms
date: 2026-06-17 10:34:31 +0900
categories:
- AI
tags:
- Gemini
- LLM
- Tool Use
- Function Calling
description: Gemini 1.5 Pro의 Tool Use(함수 호출) 기능을 실무에 적용하는 방법을 알아봅니다. 모델이 외부 함수를 인식하고
  호출을 요청하는 과정, 설정, 그리고 잠재적 실패 사례를 다룹니다.
image: /uploads/gemini-1-5-pro-tool-use-connecting-llms/thumbnail.webp
lang: ko
translation_key: gemini-1-5-pro-tool-use-connecting-llms
post_type: deep-dive
ai_generated: true
---
대규모 언어 모델(LLM)은 방대한 텍스트 데이터를 기반으로 놀라운 언어 능력을 보여줍니다. 하지만 LLM은 그 자체로 외부 세계와 단절되어 있습니다. 실시간 주식 정보를 가져오거나, 데이터베이스에 쿼리하거나, 이메일을 보내는 등의 작업은 직접 수행할 수 없습니다. 이 한계를 극복하는 핵심 기술이 바로 'Tool Use', 즉 함수 호출(Function Calling)입니다.

이 글에서는 Google의 Gemini 1.5 Pro 모델을 중심으로 Tool Use의 개념과 동작 원리를 설명합니다. 단순히 API를 호출하는 것을 넘어, 실무에서 마주할 수 있는 트레이드오프와 잠재적인 실패 사례까지 깊이 있게 다룹니다. 이를 통해 LLM을 단순한 챗봇이 아닌, 실제 작업을 수행하는 에이전트로 만드는 첫걸음을 뗄 수 있을 것입니다.

<!--more-->
![Gemini 1.5 Pro Tool Use: LLM과 외부 세계 연결하기](/uploads/gemini-1-5-pro-tool-use-connecting-llms/thumbnail.webp "Gemini 1.5 Pro Tool Use: LLM과 외부 세계 연결하기")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## LLM과 외부 세계의 단절, 그리고 Tool Use

LLM은 학습 데이터에 없는 최신 정보나 비공개 데이터에 접근할 수 없습니다. "오늘 서울 날씨는 어때?"라고 물어도, 모델은 실시간 데이터를 조회할 수 없으므로 "저는 실시간 정보를 확인할 수 없습니다"라고 답할 뿐입니다.

Tool Use는 이 문제를 해결합니다. 개발자가 미리 정의한 함수(도구) 목록을 LLM에 제공하면, 모델은 사용자 질문의 의도를 파악하고 가장 적합한 함수와 그에 필요한 인자를 찾아냅니다. 중요한 점은 LLM이 직접 함수를 *실행*하는 것이 아니라, 어떤 함수를 어떤 인자로 실행해야 하는지 구조화된 데이터(JSON)로 *요청*한다는 것입니다. 실제 실행은 우리 코드에서 이루어지며, 그 결과를 다시 LLM에 전달해 최종 답변을 생성하게 합니다.

## Tool Use의 동작 원리: 대화형 위임

Tool Use는 LLM과 우리 코드 사이의 정교한 대화 과정입니다. 전체 흐름은 다음과 같습니다.

1.  **사용자 질문과 함수 명세 전달**: 사용자의 프롬프트와 함께 우리가 정의한 '사용 가능한 도구' 목록(함수 이름, 설명, 매개변수 정보)을 모델에 전달합니다.
2.  **모델의 판단 및 함수 호출 요청**: 모델은 프롬프트를 분석하여, 정의된 도구 중 현재 요청을 처리하는 데 도움이 될 만한 것이 있는지 판단합니다. 만약 있다면, 해당 함수 이름과 필요한 인자가 담긴 JSON 객체를 반환합니다.
3.  **우리 코드의 함수 실행**: 우리 쪽 코드는 모델이 반환한 JSON을 파싱하여 실제 로직(예: 날씨 정보 조회)을 실행합니다.
4.  **실행 결과 반환**: 함수 실행 결과를 다시 모델에 전달합니다.
5.  **최종 답변 생성**: 모델은 함수 실행 결과를 바탕으로 사용자에게 자연스러운 언어로 최종 답변을 생성하여 전달합니다.

이 과정은 LLM이 '추론 엔진'으로, 우리 코드가 '실행기'로 역할을 분담하는 협업 모델입니다.

## 파이썬으로 Gemini Tool Use 구현하기

이제 실제 코드를 통해 Gemini 1.5 Pro의 Tool Use를 구현해 보겠습니다. `google-generativeai` 라이브러리가 필요합니다.

### 1. 사전 준비

먼저 필요한 라이브러리를 설치하고 API 키를 설정합니다.

```python
# 필요한 라이브러리 설치
# pip install google-generativeai

import os
import google.generativeai as genai

# API 키 설정
# 실제 코드에서는 환경 변수나 시크릿 관리 도구를 사용하세요.
genai.configure(api_key="<YOUR_GEMINI_API_KEY>")
```

### 2. 실행할 함수 정의

모델이 사용할 수 있는 간단한 함수 두 개를 정의합니다. 하나는 날씨 정보를, 다른 하나는 주식 가격을 반환하는 가상의 함수입니다.

```python
def get_current_weather(location: str, unit: str = "celsius"):
    """지정된 위치의 현재 날씨 정보를 반환합니다."""
    # 실제로는 외부 날씨 API를 호출하는 로직이 들어갑니다.
    if "seoul" in location.lower():
        return {"location": "Seoul", "temperature": "15", "unit": unit}
    elif "tokyo" in location.lower():
        return {"location": "Tokyo", "temperature": "18", "unit": unit}
    else:
        return {"location": location, "temperature": "unknown"}

def get_stock_price(ticker_symbol: str):
    """지정된 티커 심볼의 현재 주식 가격을 반환합니다."""
    # 실제로는 외부 주식 정보 API를 호출하는 로직이 들어갑니다.
    if ticker_symbol.upper() == "GOOG":
        return {"symbol": "GOOG", "price": "175.50", "currency": "USD"}
    elif ticker_symbol.upper() == "AAPL":
        return {"symbol": "AAPL", "price": "190.20", "currency": "USD"}
    else:
        return {"symbol": ticker_symbol, "price": "not found"}
```

### 3. 모델에게 함수 명세 전달

Gemini 모델을 초기화하고, 위에서 정의한 함수들을 '도구'로 등록합니다.

```python
# 사용할 함수들을 딕셔너리로 매핑
available_tools = {
    "get_current_weather": get_current_weather,
    "get_stock_price": get_stock_price,
}

# 모델 초기화 시, 사용할 함수 목록을 함께 전달
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    tools=list(available_tools.values())
)
```

### 4. 모델 호출 및 응답 처리

사용자 질문으로 대화를 시작하고 모델의 응답을 처리하는 전체 로직입니다.

```python
# 대화 시작
chat = model.start_chat()

# 첫 번째 질문
prompt = "서울 날씨와 구글 주식 가격을 알려줘. 온도는 화씨로 부탁해."
response = chat.send_message(prompt)

# 모델이 함수 호출을 요청했는지 확인
function_calls = response.candidates[0].content.parts[0].function_call
if function_calls:
    print(f"Model wants to call functions: {function_calls}")

    # 여러 함수 호출을 순차적으로 처리
    for function_call in function_calls:
        function_name = function_call.name
        function_args = function_call.args

        # 1. 호출할 함수 찾기
        function_to_call = available_tools.get(function_name)
        if not function_to_call:
            print(f"Error: Function '{function_name}' not found.")
            continue

        # 2. 실제 함수 실행
        try:
            # ** 연산자로 딕셔너리를 키워드 인자로 풀어 전달
            function_response = function_to_call(**function_args)
            print(f"Executed '{function_name}' with args {function_args}, got: {function_response}")

            # 3. 실행 결과를 다시 모델에 전달
            response = chat.send_message(
                part=genai.Part(
                    function_response={
                        "name": function_name,
                        "response": function_response,
                    }
                ),
            )
        except Exception as e:
            print(f"Error executing function {function_name}: {e}")
            # 에러 발생 시, 에러 정보를 모델에 전달할 수도 있습니다.

# 최종 답변 출력
final_response = response.candidates[0].content.parts[0].text
print(f"\nFinal Answer:\n{final_response}")
```

위 코드를 실행하면 모델은 `get_current_weather`와 `get_stock_price` 함수를 각각 적절한 인자(`location='Seoul', unit='fahrenheit'`, `ticker_symbol='GOOG'`)와 함께 호출하라는 요청을 반환합니다. 우리 코드가 이 요청에 따라 함수를 실행하고 결과를 다시 전달하면, 모델은 그 정보를 종합하여 최종 답변을 생성합니다.

## 실무 적용 시 고려사항 및 실패 사례

Tool Use는 강력하지만, 실무에 적용할 때는 몇 가지 사항을 신중하게 고려해야 합니다.

### 명확한 함수 명세의 중요성

모델은 함수의 이름과 docstring(설명)을 보고 어떤 함수를 선택할지 결정합니다. 설명이 모호하거나 매개변수 이름이 직관적이지 않으면 모델은 엉뚱한 함수를 선택하거나 인자를 잘못 추론할 수 있습니다.

-   **실패 사례**: `get_data(source, query)`처럼 일반적인 이름과 설명 대신, `get_user_profile_by_email(email_address)`처럼 구체적이고 명확한 이름과 설명을 사용해야 합니다.
-   **팁**: 함수의 docstring은 "무엇을 하는 함수인가?"와 "각 매개변수는 무엇을 의미하는가?"에 대한 답을 명확히 담아야 합니다.

### 반환 값 처리와 오류 보고

우리가 실행한 함수가 실패할 수도 있습니다. 외부 서비스가 다운되거나, 데이터베이스에서 원하는 결과를 찾지 못할 수 있습니다. 이때 `None`을 반환하거나 예외를 발생시키고 끝내면 안 됩니다.

-   **실패 사례**: 날씨 API 호출이 실패했을 때 그냥 `None`을 반환하면, 모델은 정보가 없다는 사실을 인지하지 못하고 이전 대화 내용에 기반해 환각(hallucination)을 일으킬 수 있습니다.
-   **팁**: 함수 실행이 실패하면, 실패 원인이 담긴 명확한 메시지(예: `{"error": "API rate limit exceeded"}`)를 모델에 반환해야 합니다. 그러면 모델은 "죄송하지만, 현재 날씨 정보를 가져오는 데 실패했습니다. 잠시 후 다시 시도해 주세요." 와 같이 사용자에게 상황을 정확히 전달할 수 있습니다.

### 보안: 신뢰할 수 있는 코드만 실행

LLM이 반환하는 함수 이름과 인자를 그대로 `eval()` 같은 위험한 함수에 넘겨서는 절대 안 됩니다. 모델이 반환하는 것은 '요청'일 뿐이며, 어떤 코드를 실행할지에 대한 최종 결정권은 우리에게 있습니다.

-   **팁**: 미리 정의되고 안전성이 검증된 함수 목록(allowlist)을 만들고, 모델이 요청한 함수 이름이 이 목록에 있을 때만 실행하도록 제한해야 합니다.

### 지연 시간과 비용

Tool Use는 최소 두 번의 LLM 호출(질문 → 함수 호출 요청 → 결과 전달 → 최종 답변)을 필요로 합니다. 이는 응답 지연 시간을 증가시키고 API 호출 비용을 높이는 요인이 됩니다. 따라서 모든 상호작용에 Tool Use를 남용하기보다, 외부 정보나 작업이 반드시 필요한 경우에만 선택적으로 사용해야 합니다.

## 결론

Gemini 1.5 Pro의 Tool Use 기능은 LLM의 한계를 뛰어넘어 실제 세계와 상호작용하는 지능형 에이전트를 만들 수 있는 강력한 다리 역할을 합니다. 단순히 기능을 사용하는 것을 넘어, 명확한 명세, 견고한 오류 처리, 보안, 비용 등 실무적 관점을 함께 고려할 때 그 잠재력을 온전히 발휘할 수 있습니다. 이 글에서 다룬 원리와 코드를 바탕으로 여러분의 서비스에 새로운 가능성을 더해 보시길 바랍니다.

### 참고문헌
- [Google AI for Developers - Tool use](https://ai.google.dev/docs/function_calling "Gemini Function Calling Official Documentation"){:target="_blank"}
- [GoogleCloudPlatform/generative-ai-samples on GitHub](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/function-calling/intro_function_calling.ipynb "Gemini Function Calling Examples"){:target="_blank"}