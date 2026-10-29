# AI 해커톤 프레임워크

범용 RAG 문서 도우미: [설정·자료 추가·실행 안내](framework_doc/rag_guide.md).
관광 데이터 없이 시작하며 홈페이지에서 자료 기반 질문과 출처를 확인할 수 있습니다.

FastAPI + Vanilla JS + Supabase + LangChain 기반의 AI 해커톤용 재사용 프레임워크.
**Core를 고정하고 Topic Layer만 교체**해 해커톤 주제가 달라져도 빠르게 시작한다.

---

## 브랜치 구조

| 브랜치 | 용도 |
|---|---|
| `main` | Simple Framework (계획 중) |
| `full-framework` | **Full Framework** — Core + 완전한 Topic scaffold (현재) |
| `konnect` | 기술 참조용 구현 예시 (건드리지 않음) |

---

## 계층 구조

```
┌─────────────────────────────────────────────┐
│  Topic Layer  (주제마다 교체)                │
│  sources · domain · agent · pages · content │
├─────────────────────────────────────────────┤
│  Core  (해커톤마다 재사용)                   │
│  auth · llm-adapter · rag                   │
│  envelope · trace · exceptions · config     │
│  frontend routing · tokens                  │
└─────────────────────────────────────────────┘
```

---

## 기술 스택

| 레이어 | 기술 |
|---|---|
| Frontend | Vanilla HTML / CSS / JavaScript, ES Modules |
| Backend | Python 3.12+ / FastAPI |
| AI / Agent | OpenAI API + LangChain |
| LLM Provider | Adapter 패턴 (OpenAI / Naito 전환) |
| Auth | Supabase Auth (Anonymous → Google OAuth Linking) |
| DB / RAG | Supabase Postgres + pgvector |
| 배포 | Render (backend) / Vercel (frontend) |

---

## 빠른 시작

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일에 필수 키 입력
```

**필수 키:**
```env
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
```

### 2. Backend 실행

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

헬스체크:
```bash
curl http://localhost:8000/health
# {"ok":true,"env":"development","llm_provider":"openai","rag":false,...}
```

### 3. Frontend 실행

```bash
cd frontend
python -m http.server 5500
# 브라우저: http://localhost:5500
```

### 4. 테스트

```bash
cd backend
pytest tests/core/ -v   # Core 테스트 (15개)
pytest tests/ -v        # 전체
```

---

## Core 기능

### 인증 (Supabase Auth)
- Anonymous Sign-in으로 user_id 선발급
- Google OAuth → Identity Linking으로 데이터 보존
- FastAPI: JWT JWKS 검증 (`core/auth.py`)
- 프론트: `js/auth.js` (signInWithGoogle · signOut · getToken)

### LLM Provider Adapter
```env
LLM_PROVIDER=openai   # or naito
```
코드 변경 없이 `.env`만 수정해 전환. (`services/llm/adapter.py`)

### Response Envelope
모든 API 응답:
```json
{"ok": true,  "data": {...}}
{"ok": false, "error": {"code": "AuthError", "message": "..."}}
```

### RAG (선택적)
`SUPABASE_DB_URL` 설정 시 자동 활성화. 없으면 graceful 비활성화.
```bash
python -m app.rag.ingest   # 지식 문서 적재
```

### 디자인 토큰
`frontend/css/tokens.css` — 브랜드 색(`--color-brand-*`)만 교체하면 전체 UI 변경.

---

## 새 주제 적용 순서

```
1. content.js       브랜드명·메뉴·문구 교체
2. .env             주제별 API 키 추가
3. models/          Pydantic 스키마 정의
4. sources/         외부 API 클라이언트 작성
5. domain/          정규화·판정·랭킹
6. agent/           LangChain 파이프라인
7. api/             라우터 추가
8. pages/           화면 추가
9. components/      필요 컴포넌트
```

templates 참조: `utils/templates/` · snippets 참조: `utils/snippets/`

---

## 프로젝트 구조

```
├── framework_doc/      설계·작업 문서 (design, workflow, index, tree)
├── konnect_study/      konnect 참조 자료 (건드리지 않음)
├── utils/              재사용 스크립트·템플릿·스니펫
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py        FastAPI 앱 [Core]
│       ├── config.py      환경변수 [Core]
│       ├── core/          auth · exceptions · trace [Core]
│       ├── models/        Envelope · 주제별 스키마 [Core/Topic]
│       ├── api/           health · 주제별 라우터 [Core/Topic]
│       ├── services/llm/  Provider Adapter [Core]
│       ├── rag/           embed · ingest · retrieve [Core]
│       ├── sources/       외부 API [Topic]
│       ├── domain/        판정 로직 [Topic]
│       └── agent/         LangChain 파이프라인 [Topic]
├── frontend/
│   ├── index.html         앱 진입점 [Core]
│   ├── css/tokens.css     디자인 토큰 [Core]
│   └── js/
│       ├── app.js         부트스트랩·라우팅 [Core]
│       ├── router.js      메뉴 → 페이지 [Core]
│       ├── auth.js        Supabase auth [Core]
│       ├── api.js         fetch 래퍼 [Core]
│       ├── state.js       전역 상태 [Core]
│       ├── content.js     브랜드·문구 [Topic ← 첫 교체]
│       ├── pages/         화면 [Topic]
│       └── components/    컴포넌트 [Topic]
└── tests/core/            Core 단위 테스트 (15개)
```

---

## 문서

| 문서 | 내용 |
|---|---|
| `framework_doc/framework.md` | 프레임워크 통합 계획·구현 완료 상태·남은 검증 |
| `framework_doc/framework_design.md` | 설계 명세 (계층·기능·원칙) |
| `framework_doc/framework_workflow.md` | 작업 절차 (계획→실행→검증→보완) |
| `framework_doc/tech.md` | 기술 스택 상세 (역할·버전·공식 문서·위치) |
| `framework_doc/tree.md` | 전체 디렉터리 구조 |
| `framework_doc/index.md` | 파일 → 심볼 순방향 인덱스 |
| `framework_doc/reverse_index.md` | 심볼 → 파일 역방향 인덱스 |
| `konnect_study/02-code-index.md` | konnect 부품 카탈로그 |

---

## 불변 원칙

1. 판정은 코드로, 설명은 LLM으로
2. LLM이 사실(가격·시간·좌표·가용성)을 생성하지 않는다
3. 미확인을 긍정으로 바꾸지 않는다
4. AI 고지·확인/미확인 구분 UI를 제거하지 않는다
5. API 키를 코드에 하드코딩하지 않는다
