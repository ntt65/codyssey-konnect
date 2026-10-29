# 기술 스택 상세

> 각 기술의 역할·버전·공식 문서·프레임워크 내 사용 위치를 정리한다.
> 구조·계약·개발 절차: [framework.md](./framework.md)

---

## Backend

### FastAPI
- **역할:** REST API 서버. 라우터·미들웨어·예외핸들러 등록.
- **버전:** 0.115.x
- **공식 문서:** https://fastapi.tiangolo.com
- **사용 위치:** `backend/app/main.py`, `backend/app/api/*.py`
- **핵심 패턴:** `APIRouter` + `Depends` + `@app.exception_handler`

### Pydantic v2 + pydantic-settings
- **역할:** 입출력 스키마 검증, 환경변수 자동 로드.
- **버전:** pydantic 2.10.x, pydantic-settings 2.6.x
- **공식 문서:** https://docs.pydantic.dev/latest
- **사용 위치:** `backend/app/config.py`, `backend/app/models/*.py`
- **핵심 패턴:** `BaseSettings`로 `.env` 자동 로드. `Generic[T]` Envelope.

### LangChain + LangChain-OpenAI
- **역할:** LLM 파이프라인·Tool·Chain 오케스트레이션.
- **버전:** langchain 0.3.x, langchain-openai 0.2.x
- **공식 문서:** https://python.langchain.com/docs
- **사용 위치:** `backend/app/services/llm/`, `backend/app/agent/` (Topic)
- **핵심 패턴:** `ChatPromptTemplate | LLM | OutputParser` 체인. `with_structured_output(Schema)`.

### OpenAI Python SDK
- **역할:** GPT 모델 호출, Embeddings (RAG).
- **버전:** openai 1.57.x
- **공식 문서:** https://platform.openai.com/docs
- **사용 위치:** `services/llm/openai.py`, `rag/embed.py` (LangChain 래퍼를 통해)

### python-jose
- **역할:** Supabase JWT JWKS 비대칭 검증.
- **버전:** 3.3.x
- **공식 문서:** https://python-jose.readthedocs.io
- **사용 위치:** `backend/app/core/auth.py`
- **핵심 패턴:** `jwt.decode(token, jwks_key, algorithms=["RS256", "HS256"])`

### httpx
- **역할:** 비동기 HTTP 클라이언트. 외부 API 호출·JWKS 로드.
- **버전:** 0.28.x
- **공식 문서:** https://www.python-httpx.org
- **사용 위치:** `backend/app/core/auth.py`, `backend/app/sources/*.py` (Topic)

### vecs
- **역할:** Supabase pgvector Python 클라이언트.
- **버전:** 0.4.x
- **공식 문서:** https://github.com/supabase/vecs
- **사용 위치:** `backend/app/rag/ingest.py`, `backend/app/rag/retrieve.py`
- **조건:** `SUPABASE_DB_URL` 없으면 자동 비활성화.

---

## Auth & DB

### Supabase
- **역할:** Auth (Anonymous Sign-in + Google OAuth), Postgres DB, pgvector.
- **공식 문서:** https://supabase.com/docs
- **사용 위치:**
  - Auth: `core/auth.py` (백엔드 JWT 검증), `frontend/js/auth.js`
  - DB: `backend/app/db/` (Topic 사용자·세션 저장)
  - pgvector: `backend/app/rag/`
- **핵심 설정:**
  - JWKS endpoint: `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`
  - Anonymous Sign-in: 대시보드 Authentication > Providers에서 활성화
  - pgvector: Database > Extensions에서 `vector` 활성화
  - Google OAuth: Authentication > Providers에서 client id/secret 입력

---

## LLM Provider

### OpenAI API
- **역할:** 기본 LLM provider.
- **공식 문서:** https://platform.openai.com/docs
- **환경변수:** `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL`
- **전환:** `LLM_PROVIDER=openai` (기본값)

### Naito API
- **역할:** 해커톤 주최 측 제공 LLM. OpenAI 호환 포맷 가정하나 사전 확인 필요.
- **환경변수:** `NAITO_BASE_URL`, `NAITO_API_KEY`, `NAITO_MODEL`
- **전환:** `LLM_PROVIDER=naito`
- **주의:** endpoint·인증·모델·요청 형식을 주최 측 문서로 반드시 확인. 토큰량·소진 정책도 확인.
- **참조:** `konnect_study/Naito_win.md` (Windows 설치 가이드)

---

## Frontend

### Vanilla JS + ES Modules
- **역할:** 프레임워크·빌드 도구 없는 순수 JS.
- **이유:** 해커톤 시간 제약. React 학습 비용 없이 즉시 시작.
- **패턴:** `import/export` 정적 모듈. 동적 `import()` lazy loading.
- **사용 위치:** `frontend/js/*.js`, `frontend/js/pages/*.js`

### Supabase JS SDK
- **역할:** 프론트 Supabase Auth 클라이언트.
- **로드:** `https://esm.sh/@supabase/supabase-js@2` (CDN ESM)
- **공식 문서:** https://supabase.com/docs/reference/javascript
- **사용 위치:** `frontend/js/auth.js`

### Google Fonts — Inter
- **역할:** 기본 폰트. 다국어 지원, 가독성 우수.
- **로드:** `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700`
- **사용 위치:** `frontend/index.html`, `frontend/css/tokens.css` `--font-sans`

---

## 배포

### Render (Backend)
- **역할:** FastAPI 서버 호스팅.
- **공식 문서:** https://render.com/docs
- **설정 파일:** `render.yaml` (추가 예정)
- **주의:** 무료 티어 cold start ~30초. 데모 전 warm-up 필요.

### Vercel (Frontend)
- **역할:** 정적 프론트엔드 호스팅.
- **공식 문서:** https://vercel.com/docs
- **설정 파일:** `frontend/vercel.json` (추가 예정)

---

## 개발 도구

### pytest
- **역할:** Python 단위 테스트.
- **버전:** 9.x
- **공식 문서:** https://docs.pytest.org
- **실행:** `pytest tests/core/ -v` (Core), `pytest tests/ -v` (전체)

### uvicorn
- **역할:** FastAPI ASGI 서버.
- **공식 문서:** https://www.uvicorn.org
- **실행:** `uvicorn backend.app.main:app --reload --port 8000`
