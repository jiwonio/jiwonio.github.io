# TODO — blog.jiwon.io

> **마지막 갱신:** 2026-07-06
> **브랜치:** `gh-pages` (배포·개발 모두 이 브랜치)  
> **저장소:** https://github.com/jwjp/jwjp.github.io  
> **사이트:** https://blog.jiwon.io

나중에 Grok 등으로 이어서 작업할 항목입니다. 완료되면 `- [x]` 체크하고 날짜를 적어 주세요.

### 다음 작업 (2026-07-06 기준)

**미완료:** 선택 항목만 남음. zh 참고문헌 파싱·정규화 보완 완료, Deploy #28761998817 green.

| 우선순위 | 할 일 | 비고 |
|----------|--------|------|
| **나중** | (선택) `MY_PAT` Secret 제거 | App 안정화 2~4주 후 (~2026-07 말) |

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
GitHub App 우선, MY_PAT는 폴백.
완료 후 커밋·푸시까지 해줘.
```

### 5. 로컬 검증 (가능한 환경에서)

```bash
# Python
pip install -r scripts/requirements.txt
pip install -e ./scripts
python -m unittest discover -s scripts/tests -v
python scripts/validate_posts.py

# Jekyll (Ruby 3.3 + bundle install 필요)
bundle exec jekyll build --baseurl ""
bundle exec htmlproofer ./_site --disable-external --allow-hash-href --ignore-empty-alt

# E2E (선택)
cd e2e && npm ci && npx playwright test
```

**Windows:** VS Code/Cursor **Dev Containers** (`.devcontainer/`) 권장. 로컬 `htmlproofer` libcurl 오류 가능 → CI가 정본.

---

## 프로젝트 한눈에 보기

| 항목 | 내용 |
|------|------|
| 사이트 | Jekyll 4 다국어 기술 블로그 (ko 기본, en/ja/zh) |
| AI 글 | 월·수=deep-dive, 금=ai-news (`scheduled_ai_post.yml`) |
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
- **이전** ai-news: en만 — ja/zh는 backfill 완료 (`ai-news-2026-06-23`)

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
| 폰트 서브셋 | `scripts/download_noto_font.py`, `scripts/check_font_subset.py` |
| IndexNow | `scripts/submit_indexnow.py`, `scripts/indexnow_audit.py` |

---

## 최근 변경 이력 (맥락)

| 커밋 | 요약 |
|------|------|
| `e415dae` | fix(refs): zh 참고문헌 파싱(`-*` 불릿) + 2건 정규화 — Deploy #28761998817 green |
| `39eec16` | ai-news auto-repair (summary bullets, tone, front matter) — zh refs 미정규화로 CI 실패 잔존 |
| `c9c7ee4` | ai-news reference sync·tone repair·watchdog 강화 |
| `89e6ac7` | perf 4차: inline @font-face, optional, preload — Lighthouse 주간만, Deploy #216 green |
| `fa67f37` | perf 3차 (회귀 61%) — async font CSS, deploy 직후 Lighthouse (이후 롤백) |
| `8dcd011` | htmlproofer 수정, JP/SC 단일 woff2, 폰트·IndexNow 자동화, devcontainer |
| `b059f9e` | perf 2차: KR 단일 woff2, Cloudflare email-decode 제거 |
| `12fce6b` | TODO 갱신 (Deploy #212–213 htmlproofer 실패) |
| `14db9ef` | pip openai 2.x·google-genai 2.x — Deploy #202 green |

---

## 알려진 이슈 · 검토 필요

- [x] zh 번역 참고문헌 0건으로 검증 실패 — `-*` 불릿 파싱 + 2건 `rebuild_references_section` 정규화 (2026-07-06)
- [x] Deploy #212–213 htmlproofer 실패 — 이메일 링크 `href="#"` 추가 (2026-06-26)
- [x] Windows 로컬 `htmlproofer` libcurl 미설치로 실패 가능 — CI·devcontainer가 정본 (수용, 2026-06-26)

---

## 우선순위 높음

### GitHub App으로 MY_PAT 대체

- [x] GitHub App 생성·Secrets·설치·토큰 확인 (2026-06-25)
- [x] `setup-git-auth`: git HTTPS `x-access-token` 설정 (2026-06-25)
- [ ] (선택) `MY_PAT` Secret 제거 — App 안정화 2~4주 후

### 운영 Secret 점검 (GitHub UI에서 수동 확인)

- [x] `MY_PAT` 만료일 확인 — Classic PAT, **만료 없음** (2026-06-26)
- [x] `SLACK_WEBHOOK_URL` 설정·알림 수신 확인 (2026-06-26)
- [x] LLM API 키 4종 동작 확인 (2026-06-26)

### CI·의존성

- [x] Actions·Gemfile·pip 의존성 일괄 업데이트 (2026-06-26)
- [x] Deploy #202 green (2026-06-26)
- [x] Deploy #216 green — perf 4차 후 배포 (2026-06-26)

---

## 우선순위 중간

### 태그·i18n 품질

- [x] 포스트 태그 표기 정책 + `tag_slug_translations` (2026-06-25)
- [x] `build_tag_slug_translations` 단위 테스트 (2026-06-25)

### Jekyll 빌드·배포

- [x] `_config.yml` `exclude`에 `e2e/`, `TODO.md` (2026-06-25)
- [x] `_site` git 미추적 확인, `.gitignore`에 `.venv/` 추가 (2026-06-25)
- [x] CI에서 `build_site_js.py`·`check_font_subset.py` 검증 (2026-06-26)

### 자동화 모니터링

- [x] `pre-merge-validate` 실패 시 Slack (2026-06-25)
- [x] 주간 워크플로 일괄 점검 green (2026-06-26)

### 성능·에셋

- [x] Noto Sans KR/JP/SC 단일 woff2 (`--single-file --prune`, 2026-06-26)
- [x] 신규 글자 시 폰트 자동 재생성 — `check_font_subset.py --fix` (AI 포스트·sync_maintenance, 2026-06-26)
- [x] Cloudflare `email-decode` 제거 (2026-06-26)
- [x] Pagefind lazy load — `pagefind-search.html` IntersectionObserver (2026-06-26)
- [x] Lighthouse 80% 달성 — 4차 검증 run #28235201791 ≥80% (Slack 없음), `lighthouse.yml` 주간 측정·Slack (2026-06-26)

### 콘텐츠·SEO

- [x] 레거시 ai-news ja/zh 백필 (2026-06-25)
- [x] IndexNow 배포 시 자동 제출 (기존)
- [x] IndexNow 주간 감사 — `indexnow_audit.yml` (2026-06-26)

---

## 우선순위 낮음

### 개발 환경

- [x] `scripts/pyproject.toml` + editable install (2026-06-25)
- [x] Windows devcontainer — `.devcontainer/devcontainer.json` (2026-06-26)

### 테스트·품질

- [x] E2E·url_check 주간 green (2026-06-26)

### 정리·문서

- [x] README 워크플로 표 갱신 (2026-06-26)
- [x] LLM 예산 `$75` (2026-06-25)

---

## 완료된 항목 (참고)

- [x] 쿠키 동의 + 테마 연동 (2026-06)
- [x] Pagefind 언어별 검색 + lazy load
- [x] SEO/hreflang/접근성 대량 개선
- [x] Python 파이프라인 (atomic publish, LLM 폴백, 비용 로깅)
- [x] CI/CD 확장 (url_check, sync, e2e, lighthouse, watchdog, indexnow_audit)
- [x] 수동 검수 제거 → pre-merge 자동 검증 + auto-merge
- [x] GitHub App용 action 스캐폴딩
- [x] perf 1차·2차 (critical CSS, site.js, KR/JP/SC 단일 woff2)
- [x] perf 4차 (inline @font-face, optional, preload, Lighthouse 주간 전환)

---

## Secrets 요약

| Secret | 상태 | 용도 |
|--------|------|------|
| `GEMINI_API_KEY` | **설정됨** | deep-dive, 이미지, 번역 |
| `ANTHROPIC_API_KEY` | **설정됨** | ai-news, 폴백 |
| `OPENAI_API_KEY` | **설정됨** | ai-news, 폴백 |
| `XAI_API_KEY` | **설정됨** | ai-news, 폴백, 이미지 |
| `MY_PAT` | 폴백 (Classic, **만료 없음**) | App 미동작 시 git push, PR, merge |
| `GH_APP_ID` | **설정됨** | git push, PR, merge (우선) |
| `GH_APP_PRIVATE_KEY` | **설정됨** | git push, PR, merge (우선) |
| `SLACK_WEBHOOK_URL` | **설정됨** | 실패·LLM 비용·Lighthouse 알림 |

`MY_PAT` = GitHub Personal Access Token (classic). repo Secret으로 저장되며 워크플로에서 `GH_TOKEN`으로 쓰임. 현재 만료일 없음.