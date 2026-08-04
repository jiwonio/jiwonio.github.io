# blog.jiwon.io

Jekyll 4 기반 다국어 기술 블로그입니다. 한국어(ko) 원문과 en/ja/zh 번역본을 `translation_key`로 묶어 운영하며, Gemini·Claude·ChatGPT·Grok API로 심층 기술 글과 AI 뉴스 다이제스트를 자동 생성합니다.

- **사이트:** https://blog.jiwon.io
- **배포 브랜치:** `gh-pages` (GitHub Pages)
- **스택:** Ruby 3.3, Jekyll 4.3, Python 3.11
- **남은 작업:** [TODO.md](TODO.md)

## 아키텍처 개요

```
_posts/
  ko/{year}/   ← 한국어 원문 (기본 언어)
  en/{year}/   ← 영어 번역
  ja/{year}/   ← 일본어 번역
  zh/{year}/   ← 중국어(간체) 번역
```

| 구성 요소 | 역할 |
|-----------|------|
| `_plugins/i18n.rb` | 언어 감지, permalink, 번역 스위처, `site.posts_by_lang` |
| `scripts/generate_post.py` | 주 1회(수) deep-dive **초안** 생성 → PR (품질 우선) |
| `scripts/generate_ai_news.py` | ai-news 초안 (스케줄 없음, 수동 `workflow_dispatch`만) |
| `scripts/backfill_translations.py` | 기존 원문의 누락 번역 백필 |
| `scripts/validate_posts.py` | 배포 전 front matter·이미지·번역 완전성·내부 링크·언어 품질 검증 |
| `scripts/models_config.py` | LLM provider·모델·라우팅·비용 추정 설정 |
| `scripts/llm_client.py` | Gemini/Anthropic/OpenAI/xAI 통합 텍스트·이미지 클라이언트 |
| `scripts/api_monitor.py` | LLM 호출 로깅 (`llm-usage.jsonl`, Actions notice) |
| `scripts/usage_report.py` | LLM 사용량·비용 요약 (jsonl 또는 Actions 로그) |
| `scripts/submit_indexnow.py` | 배포·변경 포스트 URL IndexNow 제출 (번역 그룹 포함) |
| `scripts/indexnow_audit.py` | IndexNow 키 파일 검증 + 최근 URL 재제출 |
| `scripts/check_font_subset.py` | 사이트 글자 변경 시 Noto 폰트 자동 재생성 |
| `scripts/build_site_js.py` | `site.js` 번들 생성 (icons·theme·consent 등) |
| `scripts/sync_translation_dates.py` | 번역본 날짜를 ko 원문과 동기화 |
| `scripts/tests/` | Python 단위 테스트 |

### 포스트 유형 (`post_type`)

| `post_type` | 설명 | 자동 번역 대상 |
|-------------|------|----------------|
| `deep-dive` | 심층 기술 글 (기본값) | en, ja, zh |
| `ai-news` | 개발자 관점 AI 뉴스 다이제스트 | en, ja, zh |

`deep-dive`와 `2026-06-24` 이후 `ai-news`는 en·ja·zh로 자동 번역됩니다.  
그 이전 ai-news는 en만 유지되며, `backfill_translations`로 ja/zh를 추가할 수 있습니다.  
`validate_posts.py --audit-translations`로 post_type별 번역 누락을 주간 점검합니다.

### URL 규칙

- 한국어: `/posts/{slug}/`
- 그 외: `/{lang}/posts/{slug}/`
- permalink는 파일 경로가 아니라 front matter의 `slug`·`translation_key`로 결정됩니다.

## GitHub Actions 워크플로

검증은 **이층 구조**입니다.

1. **콘텐츠 게이트** (`pre-merge-validate`): `validate_posts` · 변경 글 ref URL · 번역 완전성 · sync dry-run · 폰트 verify  
2. **사이트 게이트** (`jekyll.yml` Deploy): unittest · 전체 validate · **Jekyll + Pagefind + htmlproofer** · IndexNow (배포 후 1회)

| 워크플로 | 스케줄 (UTC) | 설명 |
|----------|--------------|------|
| `jekyll.yml` | push/PR → `gh-pages` | **유일한 full site 게이트** + unittest + IndexNow |
| `scheduled_ai_post.yml` | **수 00:00** | deep-dive **초안** → 콘텐츠 게이트 → **PR (편집 대기)**; `direct_push` 기본 `false` |
| `url_check.yml` | 일 04:00 | 참고문헌·본문 외부 URL HEAD 전수 검증 |
| `lighthouse.yml` | 일 06:00 | 홈 Lighthouse (80% 미만 Slack) |
| `indexnow_audit.yml` | 토 05:00 | IndexNow 키·최근 URL 재제출 |
| `llm_usage_weekly.yml` | 토 07:00 | 주간 LLM 비용 Slack |
| `llm_usage_daily.yml` | 매일 08:00 | 일일 예산 점검 |
| `ops_digest_weekly.yml` | 토 08:00 | 주간 Ops 요약 (번역 갭 포함) |
| `sync_maintenance.yml` | 수 05:00 | 이미지·날짜 동기화 → 직푸시 |
| `ai_news_health_check.yml` | **매월 1일** 06:00 | RSS `--dry-run --strict` (ai-news는 수동 발행) |
| `deep_dive_health_check.yml` | 일 06:00 | deep-dive `--dry-run` (수 초안 전) |
| `schedule_watchdog.yml` | **목 08:00** | 주간 초안 파이프라인 생존 (14일 창, gh-pages 당일 글 불필요) |
| `thumbnail_check.yml` | **매월 1일** 07:00 | 누락 썸네일 안전망 |
| `translation_audit.yml` | **매월 1일** 05:00 | 번역 완전성 월간 감사 |
| `content_quality_audit.yml` | 토 06:00 | 콘텐츠 품질·포스트 발견성 (Pagefind full rebuild 없음) |
| `backfill_translations.yml` | 수동 | 누락 번역 백필 → 직푸시 |
| `e2e.yml` | 토 08:00 | 프로덕션 Playwright 스모크 |
| `dependabot_automerge.yml` | Dependabot PR | CI green 시 자동 머지 |

### LLM 라우팅

| 작업 | 기본 provider 순서 |
|------|-------------------|
| `deep-dive` 글 생성 | gemini → anthropic → openai → xai |
| `ai-news` 글 생성 | anthropic → openai → xai → gemini |
| en/ja/zh 번역 | gemini → anthropic → openai → xai (재시도 시 저가 모델) |
| 썸네일 이미지 | gemini → xai (실패 시 기본 썸네일) |

`workflow_dispatch`에서 `text_provider`·`translation_provider`로 override 가능합니다.  
로컬에서는 `LLM_TEXT_PROVIDER`, `LLM_TRANSLATION_PROVIDER` 환경 변수로도 지정할 수 있습니다.

### 게시 정책 (품질 우선, 2026-08-04)

**양보다 질.** AI는 초안·번역·썸네일만 담당하고, **사람이 편집 체크리스트를 채운 뒤 머지**합니다.

| 원칙 | 내용 |
|------|------|
| 빈도 | 주 1회 deep-dive 초안 (수 00:00 UTC). ai-news는 스케줄 없음 |
| 기본 게시 | **PR only** (`direct_push` 기본 `false`). 스케줄 실행은 항상 PR |
| 직푸시 | 수동 실행에서 `direct_push=true`일 때만 (예외) |
| 머지 기준 | 실측·실패 사례·경험 보강 후 (PR 본문 체크리스트) |

전체 사이트 빌드·htmlproofer·IndexNow는 머지 후 **Deploy**가 담당합니다.

| 워크플로 | 게시 방식 | 콘텐츠 게이트 | full site 게이트 |
|----------|-----------|---------------|------------------|
| `scheduled_ai_post` (스케줄) | **PR (편집 대기)** | `pre-merge-validate` | Deploy (머지 후) |
| `scheduled_ai_post` (수동) | 기본 PR (`direct_push=true`면 직푸시) | 동일 | Deploy |
| `backfill_translations` | 직푸시 | 동일 | Deploy |
| `sync_maintenance` | 직푸시 | 동일 | Deploy |

### LLM 사용량 모니터링

- 각 API 호출은 `llm_usage=` JSON notice로 Actions 로그에 기록됩니다 (`usage_report.py`가 파싱).
- 로컬/CI 실행 시 `llm-usage.jsonl`에 JSONL로 누적됩니다 (`LLM_USAGE_LOG`로 경로 변경 가능).
- `python scripts/usage_report.py llm-usage.jsonl` — 로컬 요약
- `python scripts/usage_report.py --from-actions --days 7 --slack` — Actions 로그 파싱 + Slack
- `--warn-budget 75` — 월간 추정 비용 임계값(USD) 경고 (`models_config.LLM_MONTHLY_BUDGET_USD`)

### Repository Secrets

| Secret | 용도 |
|--------|------|
| `GEMINI_API_KEY` | Gemini API (deep-dive·이미지·번역) |
| `ANTHROPIC_API_KEY` | Claude API (ai-news·폴백·번역) |
| `OPENAI_API_KEY` | OpenAI API (ai-news·폴백·번역) |
| `XAI_API_KEY` | Grok/xAI API (ai-news·폴백·번역·이미지) |
| `GH_APP_ID` | **권장** GitHub App ID (커밋·PR·머지용, 만료 없음) |
| `GH_APP_PRIVATE_KEY` | **권장** GitHub App private key PEM 전체 |
| `MY_PAT` | (폴백) PAT — App 미설정 시 사용 |
| `SLACK_WEBHOOK_URL` | 워크플로 실패·LLM 비용 Slack 알림 (**권장**) |

#### GitHub App 인증 (권장, 설정 완료)

> 상세 체크리스트: [TODO.md](TODO.md)

자동 포스팅·PR·머지는 **GitHub App 설치 토큰**을 우선 사용합니다 (`GH_APP_ID` + `GH_APP_PRIVATE_KEY`).  
`MY_PAT`는 App이 없거나 실패할 때만 폴백입니다.

**검증:** Actions → **Weekly Sync Maintenance** (또는 `gh workflow run sync_maintenance.yml`)  
→ `Setup git auth` 로그에 `Using GitHub App installation token.` 확인

App을 새로 만들 때는 [github.com/settings/apps/new](https://github.com/settings/apps/new)에서 Contents·Pull requests **Read and write** 권한으로 생성 후 `jwjp/jwjp.github.io`에 설치합니다.

## 로컬 개발

### Jekyll 사이트 실행

**권장:** VS Code/Cursor **Dev Containers** — `.devcontainer/` (Ruby 3.3 + Python 3.11 + Node 22)

1. [RubyInstaller](https://rubyinstaller.org/downloads/)로 Ruby+Devkit 설치 후 `ridk install`에서 MSYS2 toolchain 선택
2. `gem install jekyll bundler`
3. 저장소 클론 후 `bundle install`
4. `bundle exec jekyll serve`
   - baseurl 무시: `bundle exec jekyll serve --baseurl=""`
   - 외부 접속: `bundle exec jekyll serve --host=0.0.0.0`

### Python 스크립트

```bash
pip install -r scripts/requirements.txt
pip install -e ./scripts
export GEMINI_API_KEY=...   # Windows: $env:GEMINI_API_KEY="..."
# 선택: ANTHROPIC_API_KEY, OPENAI_API_KEY, XAI_API_KEY

# 포스트 검증 (배포와 동일)
python scripts/validate_posts.py

# post_type별 번역 완전성 점검
python scripts/validate_posts.py --audit-translations

# 참고문헌 URL HEAD 검증 (네트워크 필요, 주간 url_check.yml과 동일)
python scripts/validate_posts.py --check-ref-urls --check-external-urls

# LLM 사용량 요약
python scripts/usage_report.py llm-usage.jsonl --warn-budget 75

# 단위 테스트
python -m unittest discover -s scripts/tests -v

# deep-dive 사전 점검 (API 키만 확인)
python scripts/generate_post.py --dry-run

# ai-news RSS만 확인 (API 호출 없음)
python scripts/generate_ai_news.py --dry-run

# 번역 날짜 동기화 (dry-run)
python scripts/sync_translation_dates.py --dry-run

# 한국어 메타데이터 정규화 (lang, translation_key, post_type 등)
python scripts/backfill_translations.py --prepare

# 누락 번역 백필 (dry-run)
python scripts/backfill_translations.py --dry-run --langs ja

# 특정 slug만 번역
python scripts/backfill_translations.py --slug my-post --langs en,ja,zh
```

### 수동 번역 백필 (Actions)

Actions 탭 → **Backfill Post Translations** → Run workflow

| 입력 | 설명 |
|------|------|
| `langs` | `en,ja,zh` 등 (쉼표 구분) |
| `slug` | 특정 포스트만 처리 (비우면 전체) |
| `prepare_only` | 메타데이터 정규화만 수행 |

### 수동 AI 글 생성 (Actions)

Actions 탭 → **Scheduled AI Post Generation** → Run workflow

| 입력 | 권장값 |
|------|--------|
| `post_type` | `ai-news` 또는 `deep-dive` |
| `dry_run` | ai-news RSS 점검 시 `true` |
| `direct_push` | 기본 `false` (PR + 편집 검수; `true`면 직푸시 예외) |
| `edition_date` | 백필 시 `YYYY-MM-DD` |

## 참고

- [Jekyll을 사용하여 로컬로 GitHub Pages 사이트 테스트](https://docs.github.com/ko/pages/setting-up-a-github-pages-site-with-jekyll/testing-your-github-pages-site-locally-with-jekyll)
- [Jekyll Installation](https://jekyllrb.com/docs/installation/)