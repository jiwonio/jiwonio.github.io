# TODO

나중에 Grok 등으로 이어서 작업할 항목입니다. 완료되면 체크하고 날짜를 적어 주세요.

---

## 우선순위 높음

### GitHub App으로 MY_PAT 대체 (보류)

현재는 `MY_PAT` 폴백으로 자동 포스팅·PR·머지가 동작합니다. App 미설정 시에도 문제 없음.

- [ ] [GitHub App 생성](https://github.com/settings/apps/new)
  - Contents: Read and write
  - Pull requests: Read and write
  - Webhook: 비활성 가능
- [ ] Repository Secrets 등록
  - `GH_APP_ID`
  - `GH_APP_PRIVATE_KEY` (PEM 전체)
- [ ] App을 `jwjp/jwjp.github.io`에 설치
- [ ] Actions 수동 실행 후 로그 확인: `Using GitHub App installation token.`
- [ ] (선택) `MY_PAT` Secret 제거 또는 만료 후 비활성

관련 코드: `.github/actions/setup-git-auth/`, `.github/actions/verify-git-auth/`  
README 절차: `README.md` → "GitHub App으로 MY_PAT 대체하기"

### 운영 Secret 점검

- [ ] `MY_PAT` 만료일 확인 및 갱신 (App 전환 전 필수)
- [ ] `SLACK_WEBHOOK_URL` 설정 여부 확인 (실패·비용 알림)
- [ ] LLM API 키 4종 정상 동작 확인 (`GEMINI`, `ANTHROPIC`, `OPENAI`, `XAI`)

### 레거시 ai-news 번역 백필

`2026-06-24` 이전 ai-news는 en만 유지됩니다. ja/zh 추가가 필요하면:

- [ ] Actions → **Backfill Post Translations**
  - `slug`: `ai-news-2026-06-23`
  - `langs`: `ja,zh`

---

## 우선순위 중간

### 자동화 검증 강화

- [ ] `pre-merge-validate` 실패 시 Slack 알림 메시지에 실패 단계 명시
- [ ] `llm_usage_weekly.yml` Slack 요약이 실제로 오는지 확인
- [ ] `translation_audit.yml` 주간 실행 결과 모니터링
- [ ] `schedule_watchdog.yml` — AI 포스팅 8일 이상 누락 시 알림 동작 확인

### 성능·에셋

- [ ] Noto Sans KR woff2 서브셋 수 축소 (현재 파일 수 많음 → repo 용량)
- [ ] Lighthouse 주간 리포트(`lighthouse.yml`) 성능 80 미만 시 개선
- [ ] Pagefind 인덱스 lazy load 실제 Core Web Vitals 영향 측정

### 콘텐츠·SEO

- [ ] 레거시 ai-news 전부 ja/zh 백필할지 정책 결정
- [ ] `AI_NEWS_FULL_I18N_START` (`scripts/blog_i18n.py`) 날짜 상수 정리 여부

---

## 우선순위 낮음

### 개발 환경

- [ ] `scripts/`를 `pyproject.toml` 기준 installable package로 전환 (`pip install -e .`)
- [ ] `sys.path.insert` 제거 및 import 경로 정리

### 테스트·품질

- [ ] E2E(`e2e/`) CI 주간 실행 결과 확인
- [ ] 로컬 E2E: `cd e2e && npm ci && npx playwright test`
- [ ] `validate_posts.py` 네트워크 URL 검증(`url_check.yml`) 주기적 실패 URL 정리

### 정리

- [ ] GitHub App 전환 완료 후 README에서 MY_PAT 폴백 설명 축소
- [ ] Dependabot auto-merge(`dependabot_automerge.yml`) 실제 머지 동작 확인

---

## 완료된 항목 (참고)

- [x] 쿠키 동의 + 테마 연동
- [x] Pagefind 언어별 검색
- [x] SEO/hreflang/접근성 대량 개선
- [x] Python 파이프라인 (atomic publish, LLM 폴백, 비용 로깅)
- [x] CI/CD 워크플로 확장 (url_check, sync, e2e, lighthouse, watchdog 등)
- [x] 수동 검수 제거 → pre-merge 자동 검증 + auto-merge
- [x] Font Awesome 제거 → SVG 아이콘
- [x] ai-news 신규 글(2026-06-24~) en/ja/zh 자동 번역
- [x] GitHub App용 action 스캐폴딩 (Secret만 넣으면 활성화)

---

## Grok에 요청할 때 복붙용

```
프로젝트: jwjp/jwjp.github.io (gh-pages)
TODO.md 기준으로 [항목명] 작업해줘.
현재 MY_PAT 사용 중, GitHub App은 미설정.
```