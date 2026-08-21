# blog.jiwon.io

Jekyll 4 기반 다국어 기술 블로그입니다. 한국어(ko) 원문과 en/ja/zh 번역본을 `translation_key`로 묶어 운영합니다. 주제는 운영자가 정하고, Gemini·Claude·ChatGPT·Grok API로 초안·번역·썸네일만 만듭니다.

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
| `scripts/generate_post.py` | 운영자가 넣은 주제로 deep-dive **초안** 생성 → PR |
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

모든 글은 `deep-dive`입니다. 한국어 원문을 en/ja/zh로 번역합니다.  
`validate_posts.py --audit-translations`로 번역 누락을 점검합니다.

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
| `draft_post.yml` | **수동** | 운영자 주제 → 초안 → 콘텐츠 게이트 → **PR (편집 대기)** |
| `sync_maintenance.yml` | 수 05:00 | 이미지·날짜·폰트·누락 썸네일 동기화 → 직푸시 |
| `weekly_ops.yml` | 토 06:00 | 번역·URL·품질·IndexNow·LLM 비용 |
| `weekly_site_health.yml` | 일 06:00 | 홈 Lighthouse (80% 미만 Slack) |
| `e2e.yml` | 토 08:00 | 프로덕션 Playwright 스모크 (`e2e/**` PR도) |
| `backfill_translations.yml` | 수동 | 누락 번역 백필 → 직푸시 |
| `dependabot_automerge.yml` | Dependabot PR | CI green 시 자동 머지 |

### LLM 라우팅

| 작업 | 기본 provider 순서 |
|------|-------------------|
| `deep-dive` 글 생성 | gemini → anthropic → openai → xai |
| en/ja/zh 번역 | gemini → anthropic → openai → xai (재시도 시 저가 모델) |
| 썸네일 이미지 | gemini → xai (실패 시 기본 썸네일) |

`workflow_dispatch`에서 `text_provider`·`translation_provider`로 override 가능합니다.  
로컬에서는 `LLM_TEXT_PROVIDER`, `LLM_TRANSLATION_PROVIDER` 환경 변수로도 지정할 수 있습니다.

### 게시 정책 (품질 우선)

**주제는 사람, 초안은 AI.** 주제를 떠올릴 때마다 Actions로 초안을 만들고, **편집 체크리스트를 채운 뒤 머지**합니다. 스케줄 자동 생성은 없습니다.

| 원칙 | 내용 |
|------|------|
| 주제 | 운영자가 `--topic` / Actions `topic`으로 지정 |
| 메모 | `notes`에 실측·실패 사례를 넣으면 초안에 반영. 없으면 수치 창작 금지 |
| 기본 게시 | **PR only** (`direct_push` 기본 `false`) |
| 직푸시 | `direct_push=true`일 때만 (예외) |
| 머지 기준 | 실측·실패 사례·경험 보강 후 (PR 본문 체크리스트) |

전체 사이트 빌드·htmlproofer·IndexNow는 머지 후 **Deploy**가 담당합니다.

| 워크플로 | 게시 방식 | 콘텐츠 게이트 | full site 게이트 |
|----------|-----------|---------------|------------------|
| `draft_post` | 기본 PR (`direct_push=true`면 직푸시) | `pre-merge-validate` | Deploy (머지 후) |
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
| `ANTHROPIC_API_KEY` | Claude API (폴백·번역) |
| `OPENAI_API_KEY` | OpenAI API (폴백·번역) |
| `XAI_API_KEY` | Grok/xAI API (폴백·번역·이미지) |
| `GH_APP_ID` | **권장** GitHub App ID (커밋·PR·머지용, 만료 없음) |
| `GH_APP_PRIVATE_KEY` | **권장** GitHub App private key PEM 전체 |
| `MY_PAT` | (폴백) PAT — App 미설정 시 사용 |
| `SLACK_WEBHOOK_URL` | 워크플로 실패·LLM 비용 Slack 알림 (**권장**) |

#### GitHub App 인증 (권장, 설정 완료)

> 상세 체크리스트: [TODO.md](TODO.md)

초안 PR·머지는 **GitHub App 설치 토큰**을 우선 사용합니다 (`GH_APP_ID` + `GH_APP_PRIVATE_KEY`).  
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

# 참고문헌 URL HEAD 검증 (네트워크 필요, 주간 weekly_ops.yml과 동일)
python scripts/validate_posts.py --check-ref-urls --check-external-urls

# LLM 사용량 요약
python scripts/usage_report.py llm-usage.jsonl --warn-budget 75

# 단위 테스트
python -m unittest discover -s scripts/tests -v

# 초안 생성 사전 점검 (API 키만 확인)
python scripts/generate_post.py --dry-run

# 주제 넣고 초안 생성 (로컬)
python scripts/generate_post.py --topic "Cursor로 PR 리뷰 밀림 줄이기" --angle failure --notes "금요일 50파일 PR이 월요일까지 밀렸습니다."

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

### 초안 생성 (Actions)

주제를 정한 뒤 Actions 탭 → **Draft Post from Topic** → Run workflow

| 입력 | 권장값 |
|------|--------|
| `topic` | **필수.** 이번 글의 주제 |
| `angle` | `freeform` / `before-after` / `failure` / `decision` / `hidden-cost` / `team` |
| `notes` | 실측 수치·실패 사례. 비우면 모델이 숫자를 만들지 않음 |
| `direct_push` | 기본 `false` (PR + 편집 검수) |
| `edition_date` | 날짜 고정이 필요할 때만 `YYYY-MM-DD` |

## 참고

- [Jekyll을 사용하여 로컬로 GitHub Pages 사이트 테스트](https://docs.github.com/ko/pages/setting-up-a-github-pages-site-with-jekyll/testing-your-github-pages-site-locally-with-jekyll)
- [Jekyll Installation](https://jekyllrb.com/docs/installation/)