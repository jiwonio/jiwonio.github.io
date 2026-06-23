# blog.jiwon.io

Jekyll 4 기반 다국어 기술 블로그입니다. 한국어(ko) 원문과 en/ja/zh 번역본을 `translation_key`로 묶어 운영하며, Gemini API로 심층 기술 글과 AI 뉴스 다이제스트를 자동 생성합니다.

- **사이트:** https://blog.jiwon.io
- **배포 브랜치:** `gh-pages` (GitHub Pages)
- **스택:** Ruby 3.3, Jekyll 4.3, Python 3.11

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
| `scripts/generate_post.py` | 월요일 심층 기술 글(deep-dive) 자동 생성 |
| `scripts/generate_ai_news.py` | 목요일 AI 뉴스 다이제스트(ai-news) 자동 생성 |
| `scripts/backfill_translations.py` | 기존 원문의 누락 번역 백필 |
| `scripts/validate_posts.py` | 배포 전 front matter·이미지·번역 그룹 검증 |

### 포스트 유형 (`post_type`)

| `post_type` | 설명 | 자동 번역 대상 |
|-------------|------|----------------|
| `deep-dive` | 심층 기술 글 (기본값) | en, ja, zh |
| `ai-news` | 개발자 관점 AI 뉴스 다이제스트 | en만 |

### URL 규칙

- 한국어: `/posts/{slug}/`
- 그 외: `/{lang}/posts/{slug}/`
- permalink는 파일 경로가 아니라 front matter의 `slug`·`translation_key`로 결정됩니다.

## GitHub Actions 워크플로

| 워크플로 | 스케줄 (UTC) | 설명 |
|----------|--------------|------|
| `jekyll.yml` | push → `gh-pages` | validate → build → GitHub Pages 배포, IndexNow 알림 |
| `scheduled_ai_post.yml` | 월·목 00:00 | 월=deep-dive, 목=ai-news 생성 후 PR(기본 자동 머지) |
| `ai_news_health_check.yml` | 수 06:00 | ai-news RSS `--dry-run --strict` 사전 점검 |
| `backfill_translations.yml` | 수동 | 누락 번역 백필 (`workflow_dispatch`) |

### Repository Secrets

| Secret | 용도 |
|--------|------|
| `GEMINI_API_KEY` | Gemini API (글·이미지·번역 생성) |
| `MY_PAT` | Actions에서 커밋·PR 생성·푸시용 PAT |
| `SLACK_WEBHOOK_URL` | (선택) 워크플로 실패 시 Slack 알림 |

## 로컬 개발

### Jekyll 사이트 실행

1. [RubyInstaller](https://rubyinstaller.org/downloads/)로 Ruby+Devkit 설치 후 `ridk install`에서 MSYS2 toolchain 선택
2. `gem install jekyll bundler`
3. 저장소 클론 후 `bundle install`
4. `bundle exec jekyll serve`
   - baseurl 무시: `bundle exec jekyll serve --baseurl=""`
   - 외부 접속: `bundle exec jekyll serve --host=0.0.0.0`

### Python 스크립트

```bash
pip install -r scripts/requirements.txt
export GEMINI_API_KEY=...   # Windows: $env:GEMINI_API_KEY="..."

# 포스트 검증 (배포와 동일)
python scripts/validate_posts.py

# ai-news RSS만 확인 (API 호출 없음)
python scripts/generate_ai_news.py --dry-run

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

Actions 탭 → **Bi-weekly AI Post Generation** → Run workflow

| 입력 | 권장값 |
|------|--------|
| `post_type` | `ai-news` 또는 `deep-dive` |
| `dry_run` | ai-news RSS 점검 시 `true` |
| `auto_merge` | 검토 후 머지 시 `false` |

## 참고

- [Jekyll을 사용하여 로컬로 GitHub Pages 사이트 테스트](https://docs.github.com/ko/pages/setting-up-a-github-pages-site-with-jekyll/testing-your-github-pages-site-locally-with-jekyll)
- [Jekyll Installation](https://jekyllrb.com/docs/installation/)