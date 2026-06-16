---
layout: post
title: "Ollama와 파이썬으로 나만의 로컬 코드 리뷰 CLI 만들기"
slug: "building-local-code-review-cli-with-ollama-python"
date: 2024-06-17 11:15:25 +0900
categories: [AI]
tags: [Ollama, LLM, Code Review, Python, CLI]
description: "API 비용과 보안 걱정 없이, Ollama와 Llama 3를 활용해 로컬 환경에서 동작하는 코드 리뷰 CLI 도구를 직접 만들어 봅니다. 프롬프트 설계부터 한계점까지 실무 팁을 다룹니다."
---

코드 리뷰는 소프트웨어 품질을 유지하는 핵심 과정이지만, 동료의 시간을 많이 소요하게 만드는 작업이기도 합니다. GitHub Copilot이나 ChatGPT 같은 AI 도구가 훌륭한 보조 수단이 되었지만, 민감한 코드를 외부 API로 전송하는 것에 대한 보안 우려나 비용 문제는 여전히 남아있습니다.

이 글에서는 이러한 문제를 해결하기 위해 로컬 환경에서 완전히 독립적으로 동작하는 코드 리뷰 CLI(Command-Line Interface) 도구를 직접 만들어 보겠습니다. 인기 있는 로컬 LLM 실행 도구인 **Ollama**와 **Python**을 사용하여, 외부 네트워크 연결 없이 안전하고 빠르게 코드에 대한 피드백을 받는 방법을 알아봅니다.

<!--more-->


-----

## 왜 로컬 코드 리뷰어인가?

상용 AI 서비스를 사용하는 대신 로컬에서 직접 LLM을 실행하여 코드 리뷰 도구를 만들면 몇 가지 명확한 이점이 있습니다.

1.  **보안**: 소스 코드가 개인 컴퓨터나 내부 서버를 벗어나지 않습니다. 기업의 보안 정책이 엄격하거나 외부로 유출되어서는 안 될 코드를 다룰 때 결정적인 장점입니다.
2.  **비용**: 초기 하드웨어 투자를 제외하면 API 호출에 따른 추가 비용이 발생하지 않습니다. 마음껏 실험하고 원하는 만큼 사용할 수 있습니다.
3.  **오프라인 작동**: 인터넷 연결이 불안정하거나 없는 환경에서도 코드 리뷰를 수행할 수 있습니다.
4.  **맞춤화**: 프롬프트와 모델을 자유롭게 수정하여 우리 팀만의 코드 리뷰 스타일과 규칙에 맞는 도구를 만들 수 있습니다.

## 사전 준비: Ollama와 Llama 3 설치

먼저 로컬에서 LLM을 실행할 수 있는 환경을 준비해야 합니다. Ollama는 복잡한 설정 없이 간단한 명령어로 LLM을 설치하고 실행할 수 있게 해주는 훌륭한 도구입니다.

공식 웹사이트인 [ollama.com](https://ollama.com "Ollama 공식 웹사이트"){:target="_blank"}에서 자신의 운영체제에 맞는 설치 프로그램을 다운로드하여 설치합니다.

설치가 완료되면 터미널에서 다음 명령어를 실행하여 최신 Llama 3 8B 모델을 내려받습니다. Llama 3 8B 모델은 일반적인 개발자용 노트북에서도 비교적 쾌적하게 동작하며 코드 관련 작업에서 준수한 성능을 보입니다.

```bash
# Llama 3 8B 모델을 로컬에 다운로드합니다.
ollama pull llama3
```

모델 다운로드가 완료되면 `ollama list` 명령어로 설치된 모델 목록을 확인할 수 있습니다.

## 핵심 로직: Python CLI 스크립트 설계

이제 파이썬으로 코드 파일을 읽어 Ollama로 실행 중인 Llama 3 모델에게 리뷰를 요청하는 CLI 스크립트를 작성해 보겠습니다.

### 1. 프로젝트 구조 및 의존성 설치

간단한 구조로 시작하겠습니다. `review.py` 파일 하나만 있으면 됩니다. 스크립트 실행에 필요한 `ollama` 파이썬 라이브러리를 설치합니다.

```bash
# Ollama 파이썬 클라이언트 라이브러리 설치
pip install ollama
```

### 2. CLI 스크립트 작성 (`review.py`)

사용자가 터미널에서 `python review.py <파일명>` 형태로 쉽게 실행할 수 있도록 `argparse`를 사용하여 파일 경로를 인자로 받습니다.

```python
# review.py

import ollama
import argparse
import sys

# 코드 리뷰를 위한 시스템 프롬프트 정의
# 모델이 어떤 역할을 수행해야 하는지 명확하게 지시합니다.
SYSTEM_PROMPT = """
You are an expert software developer acting as a code reviewer.
Your task is to provide a constructive and concise code review.
Focus on the following aspects:
1.  **Logic and Bugs**: Identify potential logical errors, edge cases not handled, or bugs.
2.  **Clarity and Readability**: Suggest improvements for variable names, comments, and overall structure to make the code easier to understand.
3.  **Performance**: Point out potential performance bottlenecks and suggest optimizations.
4.  **Best Practices**: Check if the code follows common language-specific best practices and conventions.

Provide your feedback in a clear, bulleted list. Do not be overly verbose.
Start the review directly without any introductory phrases.
"""

def review_code(file_path: str):
    """
    지정된 파일의 코드를 읽어 Ollama를 통해 코드 리뷰를 수행합니다.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Ollama 스트리밍 API 호출
        stream = ollama.chat(
            model='llama3',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f"Please review the following Python code:\n\n```python\n{code_content}\n```"},
            ],
            stream=True,
        )

        print(f"\n--- Code Review for {file_path} ---\n")
        # 스트리밍 응답을 실시간으로 출력
        for chunk in stream:
            print(chunk['message']['content'], end='', flush=True)
        print("\n--- End of Review ---")

    except Exception as e:
        print(f"An error occurred during the API call: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform a code review on a given file using a local LLM with Ollama.")
    parser.add_argument("file", help="The path to the file you want to review.")
    args = parser.parse_args()
    
    review_code(args.file)

```

이 스크립트의 핵심은 `SYSTEM_PROMPT`입니다. 여기서 LLM의 역할을 '전문 코드 리뷰어'로 명확히 지정하고, 어떤 관점(버그, 가독성, 성능 등)에서 코드를 분석해야 하는지 구체적인 지침을 제공합니다. 이는 더 일관되고 품질 높은 리뷰 결과를 얻는 데 매우 중요합니다.

## 실행 및 결과 분석

리뷰할 간단한 예제 파이썬 파일을 하나 만들어 보겠습니다.

**`example.py`**
```python
# 사용자의 이름과 나이를 받아 인사하는 함수
def great_user(name, age):
    # 나이가 18세 미만이면 다른 메시지를 출력
    if age < 18:
        msg = "Hello " + name + ", you are still young!"
    else:
        msg = "Hello " + name + ", welcome!"
    
    # 메시지를 여러 번 출력하여 강조
    for i in range(5):
        print(msg)

# 함수 테스트
great_user("Alice", 25)
great_user("Bob", 15)
```

이제 터미널에서 우리가 만든 리뷰 스크립트를 실행합니다.

```bash
python review.py example.py
```

잠시 후 Llama 3 모델이 생성한 코드 리뷰 결과가 스트리밍 형태로 출력됩니다.

```
--- Code Review for example.py ---

*   **Clarity and Readability**: The function name `great_user` could be more descriptive, perhaps `greet_user` would be clearer. Using f-strings for string formatting is more modern and readable than string concatenation (e.g., `f"Hello {name}, welcome!"`).
*   **Best Practices**: The magic number `18` could be defined as a constant, like `LEGAL_ADULT_AGE = 18`, to improve maintainability.
*   **Logic and Bugs**: The loop `for i in range(5):` prints the same message five times. This might not be the intended behavior. If the goal is emphasis, a comment explaining why would be helpful. Otherwise, it seems redundant.
*   **Performance**: For this simple function, performance is not a concern. However, in a real-world scenario, printing inside a loop within a function that returns a value can be an undesirable side effect. It's often better to return the message and let the caller handle the printing.

--- End of Review ---
```

결과에서 볼 수 있듯이, 로컬 LLM은 함수명 오타 제안, f-string 사용 권장, 매직 넘버 문제, 불필요한 반복문 등 꽤 의미 있는 피드백을 제공합니다.

## 실용성을 높이기 위한 고민: 한계와 트레이드오프

이 도구는 분명 유용하지만, 실무에 바로 적용하기 전에 몇 가지 명백한 한계점을 인지해야 합니다.

-   **컨텍스트 부족**: 이 스크립트는 단일 파일만 분석합니다. 프로젝트 전체의 구조, 다른 파일과의 의존성, 전체 비즈니스 로직을 전혀 이해하지 못합니다. 따라서 아키텍처 수준의 리뷰나 복잡한 로직의 오류를 찾아내는 데는 한계가 있습니다.
-   **모델 성능**: Llama 3 8B와 같은 소형 모델은 GPT-4나 Claude 3 Opus 같은 최상위 모델에 비해 코드 이해도나 추론 능력이 떨어질 수 있습니다. 때로는 부정확하거나 상투적인 피드백을 생성할 수도 있습니다. 더 큰 모델(예: `llama3:70b`)을 사용하면 품질이 향상되지만, 더 높은 사양의 하드웨어(특히 VRAM)가 필요합니다.
-   **환각(Hallucination)**: 모든 LLM과 마찬가지로, 로컬 모델도 사실이 아닌 내용을 그럴듯하게 만들어낼 수 있습니다. "이 코드는 X 라이브러리의 최신 버전과 호환되지 않습니다"와 같은 구체적인 주장은 반드시 직접 확인해야 합니다.
-   **결과의 비일관성**: 같은 코드를 여러 번 리뷰해도 약간씩 다른 결과가 나올 수 있습니다.

## 결론

Ollama를 활용한 로컬 코드 리뷰 CLI는 외부 서비스에 대한 의존 없이, 보안과 비용 문제를 해결하며 AI의 도움을 받을 수 있는 훌륭한 방법입니다. 특히 민감한 코드를 다루거나, 간단한 코드 스타일에 대한 1차 검토를 자동화하는 용도로 매우 유용합니다.

이 도구는 숙련된 동료 개발자의 깊이 있는 리뷰를 대체할 수는 없지만, 리뷰 요청 전 스스로 코드를 개선하는 `셀프 체크` 도구나, 리뷰어의 부담을 덜어주는 `보조 수단`으로서 충분한 가치를 가집니다. 여기서 더 나아가 Git의 pre-commit 훅(hook)에 연동하여 커밋 전에 자동으로 리뷰를 수행하도록 만들거나, 팀의 코딩 컨벤션을 프롬프트에 더 구체적으로 명시하여 맞춤형 리뷰어로 발전시킬 수도 있을 것입니다.

### 참고문헌
- [Ollama 공식 웹사이트](https://ollama.com "Ollama"){:target="_blank"}
- [Ollama Python Library (GitHub)](https://github.com/ollama/ollama-python "ollama-python on GitHub"){:target="_blank"}