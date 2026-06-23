---
layout: post
title: '프로덕션급 LLM 애플리케이션 모니터링: LangSmith를 활용한 완벽한 관측성(Observability) 구축 가이드'
slug: llm-application-monitoring-observability-with-langsmith
date: 2026-06-15 10:22:24 +0900
categories:
- AI
- DevOps
tags:
- LLMOps
- Observability
- LangSmith
- Monitoring
- LLM
- LangChain
- AI
description: LLM 애플리케이션의 '깜깜이' 운영에 지치셨나요? 본 가이드는 LangSmith를 활용하여 토큰 비용, 지연 시간, 실행
  추적 등 프로덕션 환경에 필수적인 LLM 관측성(Observability) 시스템을 구축하는 실전 방법을 다룹니다. 단순한 로깅을 넘어 AI 성능을
  최적화하세요.
image: /uploads/llm-application-monitoring-observability-with-langsmith/thumbnail.webp
lang: ko
translation_key: llm-application-monitoring-observability-with-langsmith
post_type: deep-dive
---
AI 기반 애플리케이션, 특히 LLM(대규모 언어 모델)을 활용하는 시스템은 복잡한 내부 동작으로 인해 종종 '블랙박스'처럼 느껴지곤 합니다. 사용자의 프롬프트가 입력되고 그럴듯한 결과가 출력되지만, 그 과정에서 어떤 일이 벌어지는지, 비용은 얼마나 발생하는지, 어디서 병목이 생기는지 파악하기는 매우 어렵습니다. 기존의 서버 모니터링 방식으로는 CPU, 메모리 사용량 정도만 알 수 있을 뿐, LLM 애플리케이션의 핵심인 '품질', '비용', '지연 시간'을 추적할 수 없습니다.

이러한 문제를 해결하기 위해 **LLMOps(LLM Operations)**의 핵심 요소인 **관측성(Observability)** 확보가 필수적입니다. LLM 관측성은 단순히 로그를 쌓는 것을 넘어, 모델의 모든 요청과 응답, 내부 처리 과정을 상세히 추적하고, 성능 지표를 시각화하며, 사용자 피드백을 수집하여 AI 애플리케이션을 데이터 기반으로 개선할 수 있게 해주는 엔지니어링 실천법입니다. 좋은 관측성 시스템이 없다면, 우리는 문제 발생 시 원인을 추측에 의존해야 하며, 비용 최적화나 성능 개선은 불가능에 가깝습니다.

본 포스트에서는 LangChain 개발팀이 만든 LLM 애플리케이션 개발 플랫폼인 **LangSmith**를 활용하여, 프로덕션 환경에서 LLM 애플리케이션의 관측성을 완벽하게 구축하는 방법을 단계별로 상세히 다룹니다. LangSmith를 통해 복잡한 RAG(Retrieval-Augmented Generation) 파이프라인이나 AI 에이전트의 실행 과정을 추적하고, 토큰 비용과 지연 시간을 분석하며, 품질 평가를 자동화하는 실전 노하우를 얻어 가시길 바랍니다.

<!--more-->
![프로덕션급 LLM 애플리케이션 모니터링: LangSmith를 활용한 완벽한 관측성(Observability) 구축 가이드](/uploads/llm-application-monitoring-observability-with-langsmith/thumbnail.webp "프로덕션급 LLM 애플리케이션 모니터링: LangSmith를 활용한 완벽한 관측성(Observability) 구축 가이드")

<p style="text-align:center;opacity:0.8;">
    <small>&copy; AI Generated Image</small>
</p>
-----

## LLM 애플리케이션 관측성(Observability)의 세 가지 기둥

LLM 애플리케이션의 상태를 온전히 파악하기 위해서는 전통적인 모니터링을 넘어선 세 가지 핵심 요소가 필요합니다. 이들은 서로 유기적으로 연결되어 시스템의 내부 동작에 대한 깊은 통찰력을 제공합니다.

### 1. 추적 (Tracing)

추적은 LLM 애플리케이션에서 발생한 단일 요청의 전체 생명주기를 시각화하는 기술입니다. 사용자의 입력부터 시작하여 내부의 모든 컴포넌트(LLM 호출, 데이터베이스 조회, API 요청 등)를 거쳐 최종 응답이 생성되기까지의 과정을 마치 흐름도처럼 보여줍니다.

예를 들어, RAG 파이프라인의 경우 추적을 통해 다음과 같은 과정을 한눈에 파악할 수 있습니다.
- **입력 (Input):** 사용자가 입력한 질문
- **문서 검색 (Retriever):** 벡터 DB에서 어떤 문서를 어떤 검색어(query)로 조회했는가?
- **프롬프트 생성 (Prompt Generation):** 검색된 문맥과 질문을 조합하여 최종 프롬프트를 어떻게 만들었는가?
- **LLM 호출 (LLM Call):** 최종 프롬프트를 어떤 모델(e.g., `gpt-4-turbo`)에 전달했는가?
- **출력 (Output):** 모델이 생성한 최종 답변은 무엇인가?

이러한 상세한 추적 정보는 **"왜 AI가 이런 답변을 했지?"** 라는 질문에 대한 근본적인 원인을 찾고 디버깅하는 데 결정적인 역할을 합니다.

### 2. 메트릭 (Metrics)

메트릭은 시스템의 성능과 비용을 정량적으로 측정하는 핵심 지표입니다. LLM 애플리케이션에서는 다음과 같은 메트릭이 특히 중요합니다.

- **지연 시간 (Latency):** 요청 시작부터 최종 응답까지 걸리는 시간. 특히, 첫 번째 토큰이 생성되기까지의 시간(Time to First Token)은 사용자 경험에 직접적인 영향을 줍니다.
- **비용 (Cost) / 토큰 사용량 (Token Usage):** 각 LLM 호출에 사용된 프롬프트 토큰과 생성된 토큰의 수. 이는 API 비용과 직결되므로 반드시 추적하고 최적화해야 합니다.
- **에러율 (Error Rate):** LLM API 호출 실패, 타임아웃, 유효하지 않은 응답 형식 등 다양한 유형의 에러 발생 빈도.
- **처리량 (Throughput):** 단위 시간당 처리하는 요청의 수.

이러한 메트릭을 대시보드로 시각화하고 임계치 기반의 알림을 설정하면, 시스템의 이상 징후를 조기에 발견하고 신속하게 대응할 수 있습니다.

### 3. 피드백 (Feedback)

피드백은 모델이 생성한 결과물의 '품질'을 측정하는 가장 중요한 수단입니다. 아무리 빠르고 저렴하게 답변을 생성하더라도, 그 내용이 부정확하거나 사용자 의도와 맞지 않으면 아무 소용이 없습니다.

피드백은 다양한 형태로 수집될 수 있습니다.
- **사용자 피드백:** 챗봇 인터페이스의 '좋아요/싫어요' 버튼, 별점 평가, 댓글 등
- **프로그래밍적 피드백:** 생성된 답변이 특정 형식(e.g., JSON)을 준수하는지, 내부 비즈니스 로직 검증을 통과하는지 등을 코드로 평가
- **전문가 평가:** 내부 운영팀이나 전문가가 직접 답변의 품질을 평가하고 점수를 매김

수집된 피드백 데이터는 특정 프롬프트의 문제점을 파악하거나, 향후 모델 성능 평가(Evaluation) 및 미세 조정(Fine-tuning)을 위한 귀중한 데이터셋으로 활용됩니다.

## LangSmith를 활용한 실전 모니터링 시스템 구축

이제 LangSmith를 사용하여 위에서 설명한 관측성의 세 기둥을 실제로 구축해 보겠습니다. LangSmith는 환경 변수 설정만으로 기존의 LangChain, OpenAI SDK 코드에 완벽하게 통합되어 매우 편리합니다.

### 1. 환경 설정 및 API 키 발급

먼저, [LangSmith 공식 웹사이트](https://smith.langchain.com/ "LangSmith Website"){:target="_blank"}에 접속하여 회원가입을 합니다. 그 후, **Settings > API Keys** 메뉴에서 새로운 API 키를 생성합니다.

생성된 키들은 매우 민감한 정보이므로, 코드에 직접 하드코딩하지 말고 반드시 환경 변수로 관리해야 합니다. 프로젝트 루트 디렉터리에 `.env` 파일을 생성하고 아래와 같이 키를 추가합니다.

**.env**
```env
# [🚨 보안 주의] 실제 키 값으로 교체하고, 이 파일은 .gitignore에 추가하세요.
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="<YOUR_LANGCHAIN_API_KEY>"
LANGCHAIN_PROJECT="My-AI-Project" # 프로젝트별로 추적을 그룹화합니다.

OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
```

- `LANGCHAIN_TRACING_V2="true"`: LangSmith 추적 기능을 활성화하는 핵심 설정입니다.
- `LANGCHAIN_ENDPOINT`: LangSmith API 서버 주소입니다.
- `LANGCHAIN_API_KEY`: 발급받은 LangSmith API 키입니다.
- `LANGCHAIN_PROJECT`: 생성되는 추적(Trace)들을 그룹화할 프로젝트 이름입니다. 지정하지 않으면 'default'로 설정됩니다.

### 2. Python 애플리케이션에 LangSmith 연동하기

이제 Python 코드에서 LangSmith를 연동해 보겠습니다. 먼저 필요한 라이브러리를 설치합니다.

```bash
pip install openai langchain langchain-openai python-dotenv
```

환경 변수를 로드하고 OpenAI 클라이언트를 사용하는 간단한 코드를 작성합니다.

**simple_llm_call.py**
```python
import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수 설정만으로 LangSmith가 자동으로 OpenAI 호출을 추적합니다.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_question(question):
    print("질문을 시작합니다...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": question}],
        temperature=0.7,
    )
    answer = response.choices[0].message.content
    print("답변:", answer)
    return answer

if __name__ == "__main__":
    ask_question("LLMOps에서 관측성의 중요성에 대해 설명해줘.")
```

위 코드를 실행하기만 하면, `LANGCHAIN_TRACING_V2` 환경 변수 덕분에 OpenAI API 호출에 대한 모든 정보(프롬프트, 응답, 토큰 사용량, 지연 시간 등)가 자동으로 LangSmith의 'My-AI-Project' 프로젝트에 기록됩니다.

이제 LangChain을 사용하는 좀 더 복잡한 RAG 예시를 살펴보겠습니다.

**rag_chain_example.py**
```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# .env 파일에서 환경 변수 로드
load_dotenv()

# 가짜 Retriever (실제로는 VectorDB를 사용)
def fake_retriever(query: str) -> str:
    print(f"'{query}'에 대한 문서를 검색합니다...")
    # 실제 구현에서는 여기서 VectorDB를 조회합니다.
    return "LangSmith는 LLM 애플리케이션의 추적, 모니터링, 평가를 위한 플랫폼이다."

# LangChain Expression Language (LCEL)을 사용한 RAG Chain 정의
template = """
당신은 질문에 답변하는 AI 어시스턴트입니다.
제공된 컨텍스트를 사용하여 질문에 답변하세요.

컨텍스트: {context}

질문: {question}

답변:
"""
prompt = ChatPromptTemplate.from_template(template)
model = ChatOpenAI(model="gpt-4-turbo-preview")

rag_chain = (
    {"context": fake_retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

if __name__ == "__main__":
    print("RAG Chain을 실행합니다...")
    result = rag_chain.invoke("LangSmith가 무엇인가요?")
    print("최종 결과:", result)
```

이 코드를 실행하면 LangSmith 대시보드에서 `rag_chain`의 전체 실행 흐름을 시각적으로 확인할 수 있습니다. `fake_retriever` 함수 호출, `prompt` 생성, `model` 호출 등 각 단계별 입력, 출력, 소요 시간을 모두 분해해서 볼 수 있어 디버깅이 매우 용이해집니다.

### 3. LangSmith 대시보드 탐색

코드를 실행한 후 LangSmith 대시보드를 방문하면, 수집된 데이터를 다양한 방식으로 탐색할 수 있습니다.

- **Projects/Traces 뷰:** 실행된 모든 요청의 목록이 나타납니다. 각 항목을 클릭하면 해당 요청의 상세 추적 정보를 볼 수 있습니다. RAG 예시의 경우, retriever와 LLM 호출이 계층적으로 표시되어 전체 파이프라인의 흐름을 직관적으로 이해할 수 있습니다.
- **Monitoring 탭:** 프로젝트 전체의 핵심 메트릭(지연 시간, 토큰 비용, 에러율 등)을 시간 흐름에 따라 보여주는 대시보드입니다. 이를 통해 "지난주부터 갑자기 API 비용이 급증했다" 또는 "특정 시간대에 지연 시간이 길어진다"와 같은 문제를 즉시 파악할 수 있습니다.

## 고급 활용: 성능 최적화 및 평가(Evals)

LangSmith는 단순한 로깅과 모니터링을 넘어, 애플리케이션을 개선하는 데 필요한 강력한 기능들을 제공합니다.

### 1. 사용자 피드백(Feedback) 프로그래밍 방식으로 기록하기

애플리케이션에서 사용자가 '좋아요/싫어요' 버튼을 눌렀을 때, 해당 피드백을 특정 LLM 실행(run)과 연결하여 LangSmith에 기록할 수 있습니다.

```python
from langsmith import Client

client = Client()

# ... LLM 호출 후 run_id를 얻었다고 가정 ...
# rag_chain.invoke()는 run_id를 포함한 객체를 반환하도록 설정할 수 있습니다.
# 예시 run_id (실제로는 invoke 결과에서 추출)
example_run_id = "a1b2c3d4-e5f6-..." 

# 사용자가 '좋아요'를 눌렀을 때
client.create_feedback(
    run_id=example_run_id,
    key="user_score",  # 피드백 종류를 나타내는 키
    score=1,           # 1: 좋음, 0: 나쁨
    comment="답변이 매우 정확하고 유용했어요."
)

# 사용자가 '싫어요'를 눌렀을 때
client.create_feedback(
    run_id=example_run_id,
    key="user_score",
    score=0,
    comment="질문과 관련 없는 답변을 합니다."
)
```
이렇게 수집된 피드백은 LangSmith 대시보드에서 각 추적과 함께 표시되며, "사용자들이 싫어하는 답변은 주로 어떤 유형의 질문에서 발생하는가?"를 분석하는 데 사용될 수 있습니다.

### 2. 데이터셋을 생성하고 평가 실행하기

운영 중 발견된 중요한 성공/실패 사례들을 LangSmith UI에서 '데이터셋'으로 저장할 수 있습니다. 예를 들어, '답변이 부정확했던 사례 모음' 데이터셋을 만들 수 있습니다.

이렇게 만들어진 데이터셋을 기준으로 새로운 프롬프트나 모델의 성능을 자동으로 평가할 수 있습니다.

```python
from langsmith.evaluation import evaluate

# ... 이전에 정의한 rag_chain ...

# '답변이 부정확했던 사례 모음' 데이터셋에 대해 rag_chain의 성능을 평가
# LangSmith는 정답(ground truth)과 모델의 답변을 비교하는 다양한 평가자(evaluator)를 제공합니다.
evaluation_results = evaluate(
    rag_chain.invoke, # 평가 대상 함수
    data="incorrect-answers-dataset", # LangSmith에 저장된 데이터셋 이름
    # 필요에 따라 커스텀 평가자 추가 가능
)
```
`evaluate` 함수는 데이터셋의 각 항목에 대해 `rag_chain`을 실행하고, 그 결과를 미리 정의된 기준(e.g., 정답과의 유사도)에 따라 채점하여 리포트를 생성합니다. 이를 통해 프롬프트를 수정한 후 성능이 실제로 개선되었는지 객관적으로 검증할 수 있습니다.

## 결론: 관측성은 '나이스 투 해브'가 아닌 '머스트 해브'

LLM 기반 AI 애플리케이션 개발은 한 번 만들고 끝나는 것이 아니라, 지속적인 측정과 개선이 필요한 여정입니다. LangSmith와 같은 관측성 도구는 이 여정의 필수적인 나침반 역할을 합니다. 추측과 감에 의존하여 프롬프트를 수정하고 문제를 해결하던 시대를 지나, 이제는 데이터와 메트릭에 기반하여 AI 애플리케이션의 성능, 비용, 품질을 체계적으로 관리해야 합니다.

본 가이드에서 소개한 방법을 통해 LLM 애플리케이션의 내부를 투명하게 들여다보고, 문제의 근본 원인을 신속하게 파악하며, 최종적으로는 사용자에게 더 나은 가치를 제공하는 똑똑한 AI 시스템을 구축하시기를 바랍니다. **프로덕션 환경에서 AI를 운영한다면, 관측성 시스템은 선택이 아닌 필수입니다.**

### 참고문헌
- [LangSmith 공식 문서](https://docs.smith.langchain.com/ "LangSmith Official Documentation"){:target="_blank"}
- [LangChain Python 공식 문서](https://python.langchain.com/docs/get_started/introduction "LangChain Python Documentation"){:target="_blank"}
- [OpenAI API 문서](https://platform.openai.com/docs/api-reference "OpenAI API Reference"){:target="_blank"}