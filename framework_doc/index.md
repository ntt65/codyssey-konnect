# 프레임워크 순방향 인덱스 (파일 → 심볼)

현재 구조·계약·개발 절차의 기준은 [framework.md](./framework.md)다. 아래 심볼 목록은 과거 스냅샷이므로 실제 위치는 `rg`로 확인한다.

## 범용 RAG 작업 문서

- [구현 작업 기록·검증 결과](./rag_work_report.md) — 2026-10-30, `framework`
- [설정·자료 추가·실행 안내](./rag_guide.md)
- [Vercel·Render 배포 방법](./배포방법.md)
- [해커톤 전 준비 체크리스트](./준비체크리스트.md)

> 생성일: 2026-10-29 | 브랜치: full-framework
> Core 파일 중심. "이 파일에 뭐가 있나"를 빠르게 찾는 용도.
> 관련: [reverse_index.md](./reverse_index.md) | [tree.md](./tree.md)

---

## backend/app/config.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `Settings` | BaseSettings | 전체 환경변수 (pydantic-settings, .env 자동 로드) |
| `settings` | 싱글톤 | `Settings()` 인스턴스 — 모든 모듈이 import |
| `Settings.cors_origins` | cached_property | CORS_ALLOW_ORIGINS 쉼표 → list |
| `Settings.is_production` | property | app_env == "production" 여부 |
| `Settings.rag_enabled` | property | supabase_db_url 설정 여부 |
| `Settings.missing_keys` | method | 빈 필수 키 이름 반환 (값 미출력) |

---

## backend/app/core/exceptions.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `AppError` | Exception | 공통 베이스. `message`, `status_code` 보유 |
| `ExternalSourceError` | AppError | 외부 API 실패 → 503 |
| `ValidationFailure` | AppError | 입력 오류 → 422 |
| `AuthError` | AppError | 인증 실패 → 401 |
| `ConfigurationError` | AppError | 필수 설정 누락 → 500 |

---

## backend/app/core/trace.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `Trace` | dataclass | AI 파이프라인 단계 추적 |
| `Trace.step` | method | 단계명·데이터·경과시간 기록 |
| `Trace.to_dict` | method | 기록된 steps 리스트 반환 |

---

## backend/app/core/auth.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `AuthUser` | dataclass | 검증된 사용자 신원 (id, is_anonymous, role) |
| `verify_token` | async func | JWT → AuthUser (JWKS 비대칭 검증) |
| `get_optional_user` | async func | FastAPI Depends — 토큰 없으면 None 반환 |
| `get_current_user` | async func | FastAPI Depends — 토큰 필수, 없으면 AuthError(401) |
| `_get_jwks` | func | JWKS 로드·캐시 (lru_cache, 재시작 시 갱신) |

---

## backend/app/models/common.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `Envelope[T]` | Generic[BaseModel] | 모든 API 응답 공통 포맷 {ok, data, error, trace} |
| `Envelope.ok_response` | classmethod | ok=True 응답 생성 |
| `Envelope.error_response` | classmethod | ok=False 응답 생성 |
| `ErrorDetail` | BaseModel | 오류 상세 {code, message} |

---

## backend/app/api/health.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `router` | APIRouter | health 라우터 |
| `health` | GET /health | 환경·LLM provider·RAG 상태 반환 |

---

## backend/app/main.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `app` | FastAPI | 앱 인스턴스 (CORS·예외핸들러·라우터 등록) |
| `lifespan` | async generator | 시작 시 필수 키 확인·로그 출력 |
| `app_error_handler` | handler | AppError → Envelope(ok=False) |
| `validation_error_handler` | handler | pydantic ValidationError → 422 Envelope |

---

## backend/app/services/llm/adapter.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `get_llm` | func | LLM_PROVIDER에 따라 BaseChatModel 반환 |
| `get_embedding_model` | func | OpenAI Embeddings 인스턴스 반환 |

---

## backend/app/services/llm/openai.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `build_openai_llm` | func | ChatOpenAI 인스턴스 생성 (streaming 옵션) |

---

## backend/app/services/llm/naito.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `build_naito_llm` | func | Naito endpoint·auth·model로 ChatOpenAI 생성. 미설정 시 ConfigurationError |

---

## backend/app/rag/embed.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `embed_query` | async func | 단일 텍스트 → 벡터 (검색용) |
| `embed_documents` | async func | 텍스트 리스트 → 벡터 리스트 (적재용) |

---

## backend/app/rag/retrieve.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `_SIM_THRESHOLD` | const | 0.35 — 근거 판정 유사도 임계치 |
| `search_knowledge` | async func | pgvector 유사도 검색 → [{text, similarity}] |
| `answer_question` | async func | RAG 전체 흐름: 검색→판정→LLM 답변 |

---

## backend/app/rag/ingest.py

| 심볼 | 종류 | 역할 |
|---|---|---|
| `_chunk_text` | func | 텍스트 → 청크 분할 (800자, 100자 overlap) |
| `ingest` | async func | knowledge/*.md → pgvector 적재 |

---

## frontend/js/app.js

| 심볼 | 종류 | 역할 |
|---|---|---|
| `boot` | async func | 앱 초기화 진입점 (DOMContentLoaded에 등록) |
| `_registerRoutes` | func | Topic 페이지 라우터 등록 블록 |
| `_renderNav` | func | CONTENT.menu 기반 메뉴 렌더 |
| `_goto` | async func | 페이지 전환 (currentPage 갱신 + navigate) |

---

## frontend/js/router.js

| 심볼 | 종류 | 역할 |
|---|---|---|
| `register` | func | 메뉴명 + dynamic import loader 등록 |
| `navigate` | async func | 등록된 페이지로 이동 (loader 실행 + render) |
| `routes` | func | 등록된 라우트 목록 반환 |

---

## frontend/js/auth.js

| 심볼 | 종류 | 역할 |
|---|---|---|
| `ready` | Promise | 초기화 완료 신호 |
| `init` | async func | Supabase 클라이언트 생성 + Anonymous Sign-in |
| `onAuthChange` | func | 세션 변경 구독 |
| `isSignedIn` | func | 비익명 정식 로그인 여부 (동기) |
| `getToken` | async func | 현재 세션 JWT 반환 |
| `signInWithGoogle` | async func | Google OAuth 시작 |
| `signOut` | async func | 로그아웃 + 세션 초기화 |

---

## frontend/js/api.js

| 심볼 | 종류 | 역할 |
|---|---|---|
| `request` | async func | 공통 fetch 래퍼 (JWT 자동 부착, Envelope 파싱) |
| `get` | async func | GET 편의 함수 |
| `post` | async func | POST 편의 함수 |
| `put` | async func | PUT 편의 함수 |
| `del` | async func | DELETE 편의 함수 |

---

## frontend/js/state.js

| 심볼 | 종류 | 역할 |
|---|---|---|
| `state` | object | 전역 공유 상태 (session·lastRequest·lastResults·selectedId·currentLocation) |
| `setResults` | func | 추천 요청·결과 상태 갱신 |
| `ensureLocation` | async func | GPS 위치 1회 요청·캐시 (멱등) |

---

## frontend/js/content.js  [Topic]

| 심볼 | 종류 | 역할 |
|---|---|---|
| `CONTENT` | object | 브랜드·메뉴·문구 — 주제마다 교체하는 유일한 설정 파일 |
| `CONTENT.brand` | object | name, tagline |
| `CONTENT.menu` | object | key → label (router.js 등록명 일치) |
| `CONTENT.copy` | object | aiNotice, empty, error, loginPrompt |
