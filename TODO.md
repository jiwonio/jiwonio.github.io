# TODO — blog.jiwon.io

> **마지막 갱신:** 2026-06-25  
> **브랜치:** `gh-pages` (배포·개발 모두 이 브랜치)  
> **저장소:** https://github.com/jwjp/jwjp.github.io  
> **사이트:** https://blog.jiwon.io

나중에 Grok 등으로 이어서 작업할 항목입니다. 완료되면 `- [x]` 체크하고 날짜를 적어 주세요.

---

## 다른 PC에서 Grok 켤 때 (필독)

### 1. 저장소 받기

```bash
git clone https://github.com/jwjp/jwjp.github.io.git
cd jwjp.github.io
git checkout gh-pages
git pull origin gh-pages
```

### 2. Grok에게 먼저 읽히게 할 파일 (순서)

| 순서 | 파일 | 이유 |
|------|------|------|
| 1 | `TODO.md` (이 파일) | 남은 작업·정책·맥락 |
| 2 | `README.md` | 아키텍처·워크플로·Secrets |
| 3 | 작업 대상 파일 | 예: `_plugins/i18n.rb`, `scripts/` |

### 3. 첫 메시지 복붙용 (전체 점검)

```
프로젝트: jwjp/jwjp.github.io (브랜치 gh-pages)
TODO.md와 README.md를 읽고 전체 상태를 파악해줘.

아래를 알려줘:
1. TODO에 빠진 항목이 있는지
2. 보완·추가 수정이 필요한 곳
3. 우선순위 제안 (높음/중간/낮음)

현재 정책:
- GitHub App 설정 완료 (`GH_APP_ID` + `GH_APP_PRIVATE_KEY`), MY_PAT는 폴백
- AI 포스트는 수동 검수 없이 pre-merge-validate 통과 시 auto-merge
- ai-news 2026-06-24 이후만 en/ja/zh 자동 번역
```

### 4. 특정 작업 요청 시

```
프로젝트: jwjp/jwjp.github.io (gh-pages)
TODO.md 기준으로 [항목명] 작업해줘.
현재 MY_PAT 사용 중, GitHub App은 미설정.
완료 후 커밋·푸시까지 해줘.
```

### 5. 로컬 검증 (가능한 환경에서)

```bash
# Python
pip install -r scripts/requirements.txt
python -m unittest discover -s scripts/tests -v
python scripts/validate_posts.py

# Jekyll (Ruby 3.3 + bundle install 필요)
bundle exec jekyll build --baseurl ""
bundle exec htmlproofer ./_site --disable-external --allow-hash-href --ignore-empty-alt

# E2E (선택)
cd e2e && npm ci && npx playwright test
```

**Windows 참고:** `htmlproofer`가 libcurl 오류로 실패할 수 있음 → CI 결과를 신뢰. PowerShell에서 `;` 명령 연결 대신 명령을 나눠 실행.

---

## 프로젝트 한눈에 보기

| 항목 | 내용 |
|------|------|
| 사이트 | Jekyll 4 다국어 기술 블로그 (ko 기본, en/ja/zh) |
| AI 글 | 월=deep-dive, 목=ai-news (`scheduled_ai_post.yml`) |
| 번역 묶음 | front matter `translation_key` |
| 인증 | GitHub App 우선 (`setup-git-auth`), `MY_PAT` 폴백 |
| 머지 | `pre-merge-validate` 통과 시 auto-merge (수동 검수 없음) |
| 검증 | unittest, validate_posts, Jekyll build, htmlproofer, Pagefind |

### 언어·URL 규칙

- ko 포스트: `/posts/{slug}/`
- en/ja/zh: `/{lang}/posts/{slug}/`
- 태그 아카이브: `/archive/tag/{slug}/` 또는 `/{lang}/archive/tag/{slug}/`

### ai-news 번역 정책

- `scripts/blog_i18n.py` → `AI_NEWS_FULL_I18N_START = "2026-06-24"`
- 이 날짜 **이후** ai-news: en/ja/zh 자동 번역
- **이전** ai-news: en만 (예: `ai-news-2026-06-23`) — ja/zh는 backfill 필요

---

## 핵심 파일 지도

| 영역 | 경로 |
|------|------|
| 다국어·태그·페이지네이션 | `_plugins/i18n.rb` |
| 언어 전환 URL | `_includes/i18n-page-url.html`, `_includes/lang-switcher.html` |
| hreflang | `_includes/hreflang.html` |
| AI 글 생성 | `scripts/generate_post.py`, `scripts/generate_ai_news.py` |
| 번역·백필 | `scripts/backfill_translations.py`, `scripts/blog_i18n.py` |
| 검증 | `scripts/validate_posts.py`, `scripts/post_schema.py` |
| LLM | `scripts/llm_client.py`, `scripts/models_config.py`, `scripts/api_monitor.py` |
| 머지 전 검증 | `.github/actions/pre-merge-validate/` |
| Git 인증 | `.github/actions/setup-git-auth/`, `verify-git-auth/` |
| 배포 CI | `.github/workflows/jekyll.yml` |
| 자동 포스팅 | `.github/workflows/scheduled_ai_post.yml` |
| UI 문구·SEO 메타 | `_data/languages.yml` |
| E2E | `e2e/tests/smoke.spec.ts` |

---

## 최근 변경 이력 (맥락)

| 커밋 | 요약 |
|------|------|
| `8412740` | 태그 아카이브 언어 전환: 존재하는 페이지만 링크, `tag_slug_translations` 매핑 |
| `8c6331a` | TODO.md 추가, README 정리 |
| `1526fd5` | GitHub App 스캐폴딩, auto-merge, ai-news i18n |
| `ec38946` | consent, Pagefind i18n, SEO, Python 파이프라인, CI 확장 |

---

## 알려진 이슈 · 검토 필요

CI 통과 여부·아래 항목은 **다른 PC Grok 세션에서 우선 확인** 권장.

- [ ] `8412740` 이후 `jekyll.yml` htmlproofer가 CI에서 통과하는지 확인 (푸시 후 Actions 확인)
- [x] **중복 태그 slug:** ko `개발 환경` / en `Development Environment` 등 언어별 표기로 정리 (2026-06-25)
- [x] **번역본 태그 언어 혼용:** cursor 포스트 en/ja 태그 현지화 + `validate_posts.py` 검사 추가 (2026-06-25)
- [x] `tag_slug_translations` 엣지 케이스 단위 테스트 — `scripts/tests/test_i18n_tags.py` (2026-06-25)
- [x] `_config.yml` `exclude`에 `e2e/`, `TODO.md` 추가 (2026-06-25)
- [ ] Windows 로컬 `htmlproofer` libcurl 미설치로 실패 가능 — CI가 정본

---

## 우선순위 높음

### GitHub App으로 MY_PAT 대체

- [x] [GitHub App 생성](https://github.com/settings/apps/new) (2026-06-25)
- [x] Repository Secrets: `GH_APP_ID`, `GH_APP_PRIVATE_KEY` (2026-06-25)
- [x] App을 `jwjp/jwjp.github.io`에 설치 (2026-06-25)
- [x] Actions 로그 `Using GitHub App installation token.` 확인 (2026-06-25)
- [x] `setup-git-auth`: `gh auth login`을 별도 step으로 분리 (GITHUB_ENV 타이밍 버그 수정, 2026-06-25)
- [ ] (선택) `MY_PAT` Secret 제거 — App 안정화 후

관련: `.github/actions/setup-git-auth/`, `README.md` → "GitHub App으로 MY_PAT 대체하기"

### 운영 Secret 점검

- [ ] `MY_PAT` 만료일 확인 및 갱신 (App 전환 전 필수)
- [ ] `SLACK_WEBHOOK_URL` 설정·알림 수신 확인
- [ ] LLM API 키 4종 동작 확인 (`GEMINI`, `ANTHROPIC`, `OPENAI`, `XAI`)

### 레거시 ai-news 번역 백필

- [ ] Actions → **Backfill Post Translations** (`ai-news-2026-06-23` → ja,zh) — setup-git-auth 수정 후 재실행 필요
- [ ] 백필 후 `validate_posts.py --audit-translations` 통과 확인

### CI 안정성 (최근 수정 후속)

- [ ] `8412740` 태그 링크 수정 후 `jekyll.yml` 전체 파이프라인 green 확인
- [ ] 실패 시 Actions 로그에서 htmlproofer / Pagefind 단계 확인

---

## 우선순위 중간

### 태그·i18n 품질

- [x] 포스트 태그 표기 정책: 번역 그룹마다 **언어별 현지화 태그** + `tag_slug_translations` 매핑 (2026-06-25)
- [x] `개발-환경` / `development-environment` ko 포스트 태그 통일 (`개발 환경`) (2026-06-25)
- [x] en/ja 포스트 한국어 태그 현지화 (`Coding Tools`, `コーディングツール`) (2026-06-25)
- [x] `build_tag_slug_translations` 단위 테스트 — `scripts/i18n_tags.py` (2026-06-25)

### Jekyll 빌드·배포

- [x] `_config.yml` `exclude`에 `e2e/`, `TODO.md` 추가 (2026-06-25)
- [ ] `_site`에 테스트 산출물이 올라가지 않도록 `.gitignore`·CI 정리

### 자동화 모니터링

- [x] `pre-merge-validate` 실패 시 Slack에 실패 단계 명시 — `notify-slack-failure` action (2026-06-25)
- [ ] `llm_usage_weekly.yml` Slack 요약 수신 확인
- [ ] `translation_audit.yml` 주간 결과 모니터링
- [ ] `schedule_watchdog.yml` — AI 포스팅 8일 이상 누락 시 알림 확인
- [ ] `thumbnail_check.yml` 자동 생성 PR 정상 머지 확인

### 성능·에셋

- [ ] Noto Sans KR woff2 서브셋 수 축소 (repo 용량)
- [ ] Lighthouse(`lighthouse.yml`) 성능 80 미만 시 개선
- [ ] Pagefind lazy load Core Web Vitals 영향 측정

### 콘텐츠·SEO

- [ ] 레거시 ai-news 전부 ja/zh 백필할지 정책 결정
- [ ] `AI_NEWS_FULL_I18N_START` 날짜 상수 유지·변경 여부
- [ ] IndexNow 제출(`submit_indexnow.py`) 실제 색인 반영 모니터링

---

## 우선순위 낮음

### 개발 환경

- [x] `scripts/pyproject.toml` 추가 (`pip install -e scripts/`) (2026-06-25)
- [ ] `sys.path.insert` 제거 및 import 경로 정리
- [ ] Windows 로컬 Jekyll·htmlproofer 원클릭 셋업 문서화 (또는 devcontainer)

### 테스트·품질

- [ ] E2E(`e2e.yml`) CI 주간 결과 확인
- [ ] 로컬 E2E: `cd e2e && npm ci && npx playwright test`
- [ ] `url_check.yml` 주기적 실패 URL 정리
- [x] smoke 테스트에 태그 아카이브 언어 전환 케이스 추가 (`개발-환경` → en) (2026-06-25)

### 정리·문서

- [x] GitHub App 전환 후 README MY_PAT 폴백 설명 축소 (2026-06-25)
- [ ] `dependabot_automerge.yml` 실제 머지 동작 확인
- [ ] README 워크플로 표와 TODO 동기화 유지

---

## 완료된 항목 (참고)

- [x] 쿠키 동의 + 테마 연동 (2026-06)
- [x] Pagefind 언어별 검색
- [x] SEO/hreflang/접근성 대량 개선
- [x] Python 파이프라인 (atomic publish, LLM 폴백, 비용 로깅)
- [x] CI/CD 확장 (url_check, sync, e2e, lighthouse, watchdog 등)
- [x] 수동 검수 제거 → pre-merge 자동 검증 + auto-merge
- [x] Font Awesome 제거 → SVG 아이콘
- [x] ai-news 신규 글(2026-06-24~) en/ja/zh 자동 번역
- [x] GitHub App용 action 스캐폴딩 (Secret만 넣으면 활성화)
- [x] 태그 아카이브 언어 전환 깨진 링크 수정 (`tag_slug`, `tag_slug_translations`) — `8412740`

---

## Grok에게 물어볼 질문 (리뷰용)

다른 PC에서 아래를 그대로 붙여 넣어 **보완·추가 수정 목록**을 받을 수 있습니다.

```
TODO.md "알려진 이슈"와 전체 코드베이스를 보고 답해줘:

1. TODO.md에 빠진 작업이 뭐가 있어?
2. 지금 구조에서 깨지기 쉬운 부분은?
3. 자동화(ai-news, backfill, auto-merge) 리스크는?
4. i18n(태그·hreflang·번역)에서 추가로 손봐야 할 곳은?
5. CI/CD·Secrets·모니터링에서 빈 구멍은?
6. 우선순위 높음/중간/낮음으로 정리해줘.

제약: GitHub App은 당분간 보류, MY_PAT 유지.
```

---

## Secrets 요약

| Secret | 상태 | 용도 |
|--------|------|------|
| `GEMINI_API_KEY` | 필요 | deep-dive, 이미지, 번역 |
| `ANTHROPIC_API_KEY` | 필요 | ai-news, 폴백 |
| `OPENAI_API_KEY` | 필요 | ai-news, 폴백 |
| `XAI_API_KEY` | 필요 | ai-news, 폴백, 이미지 |
| `MY_PAT` | 폴백 | App 미동작 시 git push, PR, merge |
| `GH_APP_ID` | **설정됨** | git push, PR, merge (우선) |
| `GH_APP_PRIVATE_KEY` | **설정됨** | git push, PR, merge (우선) |
| `SLACK_WEBHOOK_URL` | 권장 | 실패·LLM 비용 알림 |

`MY_PAT` = GitHub Personal Access Token. repo Secret으로 저장되며 워크플로에서 `GH_TOKEN`으로 쓰임. 만료 시 자동 포스팅·머지가 멈춤.