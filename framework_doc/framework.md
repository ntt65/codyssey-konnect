# AI 해커톤 프레임워크 설계

> 작성일: 2026-10-29  
> 목적: FastAPI + Vanilla JS + Supabase + LangChain 기반의 AI 해커톤용 재사용 프레임워크 설계.  
> 해커톤 주제가 바뀌어도 **Core는 그대로 두고 Topic Layer만 교체**한다.  
> konnect 브랜치: 검증된 구현 부품 라이브러리 (삭제하지 않음).

> 진행 상태 갱신: 2026-10-30. 아래 설계에는 기존 Full Framework 구상이 포함되어 있으며, 현재 홈페이지는 범용 RAG 단일 페이지(`frontend/index.html` → `frontend/js/rag.js`)다. §11에서 코드 구현·과거 검증 기록·현재 미검증 항목을 구분한다. 팀 공용 환경과 `lab678` 병합 준비는 [준비 체크리스트 §0·§4](./준비체크리스트.md)를 따른다. 대상 저장소 병합은 팀 상의 후 진행 지시까지 보류한다.

---

## 0. 프레임워크 한 줄 정의

**"Core를 고정하고 Topic Layer를 교체하는 AI 웹 앱 스캐폴드"**

```
┌──────────────────────────────────────────────────────┐
│  Topic Layer  (주제마다 교체)                         │
│  sources · domain · agent · pages · content          │
├──────────────────────────────────────────────────────┤
│  Core  (해커톤마다 재사용)                            │
│  auth · llm-adapter · rag 구조 · envelope            │
│  routing · tokens · trace · exceptions               │
└──────────────────────────────────────────────────────┘
```

---

## 1. 기술 스택 (확정)

| 레이어 | 기술 | 비고 |
|---|---|---|
| Frontend | Vanilla HTML / CSS / JavaScript, ES Modules | 프레임워크·빌드 도구 없음 |
| Backend | Python 3.12+ / FastAPI | pydantic-settings 환경변수 |
| AI / Agent | OpenAI API + LangChain | Tool·Chain 패턴 |
| LLM Provider | Adapter 패턴 (OpenAI / Naito) | `LLM_PROVIDER` 환경변수로 전환 |
| RAG | Supabase pgvector + OpenAI Embeddings | 선택적 — 주제에 따라 활성화 |
| Auth | Supabase Auth (Anonymous → OAuth Linking) | Google OAuth 기본 |
| DB | Supabase (Postgres) | 사용자·세션·상태 저장 |
| 배포 | Backend: Render / Frontend: Vercel | GPU V100 배포 서버 가능성은 주최 측 확인 후 검토 |

---

## 2. Core 기능 (항상 포함, 주제와 무관)

### 2.1 인증 (Auth)

Supabase Anonymous Sign-in → Google OAuth Identity Linking 패턴.

```
비회원 첫 진입
  → Anonymous user_id 선발급 (Supabase Anonymous Sign-in)
  → 핵심 기능 제한 허용 (주제별 범위 설정)
  → 로그인 유도
  → Google OAuth → Identity Linking → 동일 user_id 영구 승격
```

- 프론트: `auth.js` — `signInWithGoogle`, `signOut`, `getToken`, `onAuthChange`
- 백엔드: `core/auth.py` — JWT 검증만 (provider-agnostic)
- 첫 진입 강제 로그인 없음. 비회원→로그인 데이터 자동 보존.
- **주제별 조정**: 비회원 허용 범위, 기능 게이팅 조건만 `content.js` / 설정으로 조정.

konnect 참조: `core/auth.py`, `frontend/js/auth.js` (그대로 재사용 가능)

---

### 2.2 LLM Provider Adapter

단일 `LLM_PROVIDER` 환경변수로 OpenAI ↔ Naito 전환.

```
backend/app/services/llm/
├── adapter.py    ← get_llm() — provider에 따라 LangChain LLM 반환
├── openai.py     ← ChatOpenAI 래퍼
└── naito.py      ← Naito endpoint·auth·model 래퍼
```

```python
# adapter.py 핵심 구조
def get_llm(streaming: bool = False) -> BaseChatModel:
    if settings.llm_provider == "naito":
        return build_naito_llm(streaming=streaming)
    return build_openai_llm(streaming=streaming)
```

**Naito 규칙:**
- endpoint·인증·모델명·요청 형식은 주최 측 문서와 토큰 수령 후 확인. OpenAI 호환 API라고 단정하지 않음.
- 제공 토큰량·계정 배분·소진 정책은 사전 확인 필수.
- Naito 미설정 시 명확한 설정 오류 반환. 빈 응답으로 대체 금지.
- provider 출력: `message` + 선택적 `citations`만. 사실 필드(가격·좌표·시간) 생성 금지.
- Naito 장애 시 자동으로 사실을 만들어내지 않음. 오류 안내 또는 명시적 OpenAI fallback만.

---

### 2.3 Response Envelope

모든 API 응답은 동일한 Envelope로 감쌈.

```python
class Envelope(BaseModel, Generic[T]):
    ok: bool
    data: T | None = None
    error: ErrorDetail | None = None
```

- `ok=True` + data: 정상 (빈 결과 포함)
- `ok=False` + error: 실패 (시스템 오류와 빈 결과를 구분)
- 프론트 `api.js`의 `request()` 함수가 Envelope를 파싱하고 에러를 throw.

---

### 2.4 예외 계층

```python
class AppError(Exception): ...        # 공통 베이스
class ExternalSourceError(AppError):  # 외부 API 실패 → 503
class ValidationFailure(AppError):    # 입력 오류 → 422
class AuthError(AppError):            # 인증 실패 → 401
```

`main.py` 핸들러가 `AppError` → `Envelope(ok=False)`로 변환.

konnect 참조: `core/exceptions.py` (클래스명만 `KonnectError` → `AppError` 변경)

---

### 2.5 Trace (에이전트 추적)

AI 파이프라인 각 단계를 Trace로 기록.

```python
class Trace:
    def step(self, name: str, data: dict) -> None: ...
    def to_dict(self) -> dict: ...
```

- 개발: 응답에 `trace` 포함 (디버깅·PoC 증빙)
- 운영: `TRACE_ENABLED=false`로 미포함

konnect 참조: `core/trace.py` (그대로 재사용 가능)

---

### 2.6 Config (환경변수)

pydantic-settings `BaseSettings`로 `.env` 자동 로드.

```python
class Settings(BaseSettings):
    # Core 필수
    openai_api_key: str
    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: str
    cors_allow_origins: str = "http://localhost:5500"

    # LLM Provider
    llm_provider: str = "openai"
    naito_base_url: str = ""
    naito_api_key: str = ""
    naito_model: str = ""

    # RAG (선택)
    supabase_db_url: str = ""

    # Topic Layer 키는 주제 확정 후 추가
```

konnect 참조: `config.py` (KONNECT 전용 키 제거 후 재사용)

---

### 2.7 RAG (선택적 Core — 주제에 따라 활성화)

Supabase pgvector 기반. 지식 문서를 적재하면 자동 활성화.

```
backend/app/rag/
├── embed.py        ← OpenAI Embeddings
├── ingest.py       ← 문서 → 청크 → pgvector 적재
├── retrieve.py     ← 유사도 검색 → 근거 있을 때만 LLM 답변
└── knowledge/      ← 주제별 지식 문서 (*.md) ← Topic
```

- 근거 없으면 생성하지 않고 거부.
- `SUPABASE_DB_URL` 없으면 graceful — 다른 기능에 영향 없음.
- 주제가 바뀌면 `knowledge/*.md`만 교체.

konnect 참조: `rag/embed.py`, `rag/retrieve.py` (그대로 재사용), `rag/ingest.py` (그대로)

---

### 2.8 프론트엔드 Core

```
frontend/js/
├── app.js      ← 부트스트랩·페이지 전환·메뉴 렌더 (라우팅만)
├── router.js   ← 메뉴 이름 → 페이지 함수 매핑
├── auth.js     ← Supabase auth (Core, 그대로)
├── api.js      ← fetch 래퍼 (JWT 자동 부착, Envelope 파싱)
└── state.js    ← 최소 공유 상태만 (로그인 유저, 현재 선택)

frontend/css/
└── tokens.css  ← 디자인 토큰 (색·타이포·간격·반경)
```

`app.js` 역할: 부트스트랩과 라우팅만. 도메인 로직 없음.

konnect 참조: `auth.js` (그대로), `api.js` (KONNECT 전용 엔드포인트 제거), `tokens.css` (그대로)

---

## 3. Topic Layer (주제마다 교체)

Core 위에 얹는 주제별 레이어. 매 해커톤마다 새로 작성하되, konnect 구현을 참조 예시로 활용.

### 3.1 백엔드 Topic 구조

```
backend/app/
├── sources/          ← 외부 데이터 API 클라이언트
│   └── [source].py  ← timeout·retry 내장, 실패 시 ExternalSourceError
├── domain/           ← 결정론적 판정 (LLM 미사용)
│   ├── normalize.py  ← 외부 데이터 → 내부 Candidate 스키마
│   ├── judge.py      ← 제약 판정 (가용성·예산·시간 등)
│   └── rank.py       ← 정렬·필터
├── agent/            ← LangChain 파이프라인
│   ├── pipeline.py   ← 메인 오케스트레이션
│   ├── tools/        ← LangChain Tools (소스 조회 래핑)
│   └── prompts/      ← 프롬프트 템플릿
├── api/
│   └── [feature].py  ← 얇은 라우터 (검증·인증·서비스 호출·Envelope 반환)
├── services/
│   └── [feature].py  ← 흐름 조합 (라우터 ↔ 에이전트 사이)
└── models/
    └── [topic].py    ← Pydantic 스키마 (입력·출력·도메인)
```

### 3.2 프론트엔드 Topic 구조

```
frontend/js/
├── content.js        ← 브랜드명·메뉴·사용자-facing 문구 (주제마다 교체)
├── pages/            ← 화면 로직
│   └── [page].js
└── components/       ← 재사용 DOM 컴포넌트
    └── [component].js

frontend/index.html   ← 메뉴 구조·진입점
```

### 3.3 Content 분리 규칙

주제가 바뀔 때 **가장 먼저** 수정하는 파일:

```js
// content.js
export const CONTENT = {
  brand: { name: "서비스명", tagline: "한 줄 설명" },
  menu: { home: "Home" /* 주제별 메뉴 */ },
  copy: {
    aiNotice: "AI-assisted results · unconfirmed details marked",
    /* 주제별 문구 */
  },
};
```

Content 파일 금지: API 호출·DOM 조작·판정 로직.  
코드 파일 금지: 주제별 문구 직접 기입.

---

## 4. AI 파이프라인 구조

단계별 파이프라인. 각 단계는 독립 테스트 가능.

```
[parse]    자연어 입력 → 구조화 조건 (LLM structured output)
    ↓
[fetch]    외부 소스 조회 (LangChain Tools, 병렬)
    ↓
[judge]    사실·제약 판정 (결정론적 코드, LLM 미사용)
    ↓
[rank]     필터링·정렬
    ↓
[compose]  결과 구성 (0건 세이프, 후보 부족 시 재판단 루프)
    ↓
[explain]  사용자-facing 설명 (LLM — 확인된 근거 범위 안에서만)
```

**불변 원칙 (Core → Topic 전체 관철):**

| # | 원칙 |
|---|---|
| 1 | 판정(judge)은 코드로, 설명(explain)은 LLM으로 |
| 2 | LLM이 사실(가격·시간·좌표·가용성)을 생성하지 않는다 |
| 3 | 미확인을 긍정(무료·가능·이용 가능)으로 바꾸지 않는다 |
| 4 | Hard 제외 후보는 정상 결과에 섞이지 않는다 |
| 5 | AI 고지·확인/미확인 구분 UI를 제거하지 않는다 |
| 6 | 강제 채움 금지 — 숫자 맞추려고 부적합 후보를 넣지 않는다 |

konnect 참조: `agent/orchestrator.py` (파이프라인 구조 예시), `domain/timing.py`, `domain/budget.py` (판정 패턴 예시)

---

## 5. 디렉터리 구조

```
[project-root]/
├── CLAUDE.md
├── framework_workflow.md
├── .env.example
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py                ← CORS·에러핸들러·라우터 등록 (Core)
│       ├── config.py              ← pydantic-settings (Core)
│       ├── core/
│       │   ├── auth.py            ← JWT 검증 (Core)
│       │   ├── exceptions.py      ← AppError 계층 (Core)
│       │   └── trace.py           ← Trace (Core)
│       ├── models/
│       │   ├── common.py          ← Envelope, ErrorDetail (Core)
│       │   └── [topic].py         ← 주제별 스키마 (Topic)
│       ├── api/
│       │   ├── health.py          ← GET /health (Core)
│       │   └── [feature].py       ← 주제별 라우터 (Topic)
│       ├── services/
│       │   ├── llm/               ← LLM Provider Adapter (Core)
│       │   │   ├── adapter.py
│       │   │   ├── openai.py
│       │   │   └── naito.py
│       │   └── [feature].py       ← 흐름 조합 (Topic)
│       ├── rag/                   ← 선택적 Core
│       │   ├── embed.py
│       │   ├── ingest.py
│       │   ├── retrieve.py
│       │   └── knowledge/         ← 주제별 지식 문서 (Topic)
│       ├── sources/               ← 외부 API 클라이언트 (Topic)
│       ├── domain/                ← 판정 로직 (Topic)
│       └── agent/                 ← LangChain 파이프라인 (Topic)
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── tokens.css             ← 디자인 토큰 (Core)
│   └── js/
│       ├── app.js                 ← 부트스트랩·라우팅 (Core)
│       ├── router.js              ← 메뉴→페이지 매핑 (Core)
│       ├── auth.js                ← Supabase auth (Core)
│       ├── api.js                 ← fetch 래퍼 (Core)
│       ├── state.js               ← 최소 공유 상태 (Core)
│       ├── content.js             ← 주제별 문구·메뉴 (Topic)
│       ├── pages/                 ← 화면 로직 (Topic)
│       └── components/            ← DOM 컴포넌트 (Topic)
│
└── study/                         ← 참조 문서 (수정하지 않음)
    ├── 02-code-index.md           ← konnect 부품 카탈로그
    ├── 03-reverse-index.md        ← 함수 위치 역방향 찾기
    ├── 06-platform-assessment.md  ← 재사용 가능 범위 평가
    └── 07-handover-guide.md       ← 환경 세팅 명령어 레퍼런스
```

---

## 6. 새 해커톤 프로젝트 시작 순서

```
1. main 기반으로 시작 (Core 이미 포함)
2. content.js      브랜드명·메뉴·기본 문구 교체
3. models/[topic]  핵심 Pydantic 스키마 정의
4. sources/        외부 데이터 클라이언트 작성
5. domain/         정규화·판정·랭킹 작성
6. agent/          LangChain 파이프라인·프롬프트 작성
7. api/[feature]   라우터 추가 (main.py에 include)
8. pages/          화면 추가 (router.js에 등록)
9. components/     필요 컴포넌트 추가
10. rag/knowledge/ 지식 문서 추가 (RAG 쓰는 경우)
```

**주제가 달라져도 1은 항상 같다.**  
**4~9는 `study/02-code-index.md`에서 konnect 구현 참조.**

---

## 7. konnect 브랜치 활용법

konnect 브랜치는 삭제하지 않고 **부품 라이브러리**로 유지.

```bash
# 파일 내용 확인 (체크아웃 없이)
git show konnect:backend/app/core/auth.py

# 파일 직접 가져오기
git checkout konnect -- backend/app/core/auth.py
```

**바로 재사용 가능 (Core 부품):**

| 파일 | 처리 |
|---|---|
| `core/auth.py` | 그대로 |
| `core/trace.py` | 그대로 |
| `core/exceptions.py` | `KonnectError` → `AppError` 이름 변경 |
| `config.py` | KONNECT 전용 키 제거 |
| `rag/embed.py`, `rag/retrieve.py`, `rag/ingest.py` | 그대로 |
| `frontend/js/auth.js` | 그대로 |
| `frontend/js/api.js` | KONNECT 전용 엔드포인트 제거 |
| `frontend/css/tokens.css` | 그대로 |

**참조 예시로 활용 (Topic 작성 시):**

| konnect 파일 | 참조 용도 |
|---|---|
| `agent/orchestrator.py` | 파이프라인 구조·단계 패턴 |
| `domain/timing.py`, `domain/budget.py` | judge 로직 패턴 |
| `domain/normalize.py` | 외부 데이터 정규화 패턴 |
| `frontend/js/pages/` | 화면 로직 패턴 |
| `frontend/js/components/` | 컴포넌트 패턴 |

---

## 8. LLM 작업 원칙

### 8.1 읽는 순서

```
CLAUDE.md
  → framework_workflow.md
  → study/02-code-index.md  (konnect 부품 찾기)
  → 해당 Core 파일 (auth · exceptions · trace)
  → 해당 Topic 파일 (sources · domain · agent · pages)
  → 관련 테스트
```

### 8.2 Core vs Topic 수정 원칙

| 대상 | 원칙 |
|---|---|
| **Core 수정** | 모든 Topic에 영향. 반드시 사용자 확인 후 진행 |
| **Topic 수정** | 해당 기능에만 영향. 자유롭게 작업 |
| **konnect 참조** | `git show konnect:파일` 또는 `study/02-code-index.md` 먼저 확인 |

### 8.3 작업 요청 표준 형식

```
목표: [무엇을 만들거나 수정할지]
읽을 파일: [CLAUDE.md + 관련 Core/Topic 파일]
수정 범위: [해당 파일과 테스트만]
보존 조건: [Envelope 계약, 신뢰 불변식, Core 인터페이스]
검증: [pytest 또는 브라우저 smoke test]
```

### 8.4 파일 책임 (1 파일 = 1 문장)

| 파일 | 책임 |
|---|---|
| `main.py` | 앱을 시작하고 라우터·핸들러를 등록한다 |
| `config.py` | 환경변수를 로드하고 검증한다 |
| `core/auth.py` | JWT를 검증하고 사용자 신원을 반환한다 |
| `core/exceptions.py` | 예외를 HTTP 응답으로 변환하는 계층을 정의한다 |
| `services/llm/adapter.py` | 설정에 따라 LLM 인스턴스를 반환한다 |
| `rag/retrieve.py` | 근거가 있을 때만 LLM 답변을 생성한다 |
| `app.js` | 앱을 시작하고 현재 페이지를 표시한다 |
| `router.js` | 메뉴 이름과 페이지 함수를 연결한다 |
| `api.js` | JWT를 붙여 요청을 보내고 Envelope를 파싱한다 |
| `content.js` | 사용자에게 보이는 문구를 제공한다 |

---

## 9. 환경변수 (.env.example)

```dotenv
# ── Core 필수 ──────────────────────────────
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
SUPABASE_DB_URL=           # RAG 사용 시 필요. 없으면 RAG만 503, 나머지 무관

CORS_ALLOW_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

# ── LLM Provider ────────────────────────────
LLM_PROVIDER=openai        # openai | naito
NAITO_BASE_URL=            # 주최 측 문서 확인 후 입력
NAITO_API_KEY=
NAITO_MODEL=

# ── Topic Layer (주제 확정 후 추가) ──────────
# TOPIC_SPECIFIC_KEY=
```

---

## 10. 위험과 대응

| 위험 | 대응 |
|---|---|
| Core 수정이 Topic 전체를 깨뜨림 | Core 수정 시 반드시 사용자 확인. Core 테스트 먼저 실행 |
| Topic이 Core 인터페이스를 우회 | api.js·Envelope·AppError를 직접 대체하지 않음 |
| LLM이 사실을 생성 | judge 단계는 코드로. LLM 출력에서 사실 필드 직접 수신 금지 |
| Naito 계약이 예상과 다름 | adapter 내부에서만 흡수. 외부 인터페이스 불변 |
| Naito 장애로 전체 기능 중단 | Naito는 Plan 채팅 등 특정 기능에만 연결. 핵심 기능은 독립 유지 |
| Naito 토큰 소진 | 토큰량·소진 정책 사전 확인. 핵심 기능은 OpenAI fallback |
| RAG 없이 기능 미동작 | RAG 없이도 핵심 기능 동작. RAG는 보강 전용 |
| konnect 코드를 그대로 복사해 KONNECT 로직이 섞임 | 부품 가져올 때 KONNECT 전용 로직 제거 여부 확인 |
| 콘텐츠 교체 중 판정 로직이 바뀜 | content.js와 domain/ 코드를 분리 유지 |
| GPU V100 배포 서버 활용 여부 | 접근 권한·네트워크·운영 정책 주최 측 확인 후 결정. 기본은 Render |

---

## 11. 완료 기준

체크 기준: 구현 항목의 `[x]`는 해당 코드가 있음을 뜻한다. 실행 검증 항목의 `[x]`는 아래에 명시한 과거 검증 기록을 근거로 한다. 이번 정리에서는 `.venv`가 참조하는 Python 실행 파일을 찾지 못해 테스트를 다시 실행하지 못했다. 실제 DB·LLM·브라우저·배포 검증은 별도 미완료로 남긴다.

### 현재 완료된 구현 — 범용 RAG 단일 페이지

- [x] 관광 지식 없이 시작하는 범용 RAG와 빈 `knowledge/` 폴더 구성
- [x] `.md`·`.txt` 자료의 하위 폴더 탐색, 청크 분할, 임베딩·pgvector 적재 구현
- [x] 동일 출처 재적재 시 기존 청크 교체 및 임베딩 차원 검사 구현
- [x] 검색 거리의 유사도 변환, 임계치 필터링, 출처 메타데이터 반환 구현
- [x] 근거 없을 때 LLM 호출을 생략하고 `no_evidence`를 반환하도록 구현
- [x] DB 미설정 시 `not_configured` 안내 구현 — 이 설계 §9의 과거 503 설명과 다름
- [x] `POST /api/ask`에 질문 검증, 답변·출처 스키마, 공통 Envelope 적용
- [x] DB·LLM 장애를 정상 빈 결과와 구분하는 오류 응답 구현
- [x] 루트 `.env`를 실행 위치와 관계없이 읽는 앱 설정 구현
- [x] 검색 수·유사도 기준·컬렉션·임베딩 차원·역할 프롬프트 설정 구현
- [x] FastAPI에서 API 등록 후 홈페이지 정적 파일 제공 구현
- [x] 질문·답변 내역, 출처 펼치기, 대화 지우기, 대기·빈 결과·오류 안내 화면 구현
- [x] 홈페이지에서 `tokens.css`와 `rag.css` 연결 및 AI 고지 표시 구현
- [x] RAG 모의 테스트와 실행·적재·배포 안내 문서 작성

근거: `backend/app/rag/`, `backend/app/api/ask.py`, `backend/app/models/rag.py`, `backend/app/main.py`, `frontend/index.html`, `frontend/js/rag.js`, `backend/tests/test_rag.py`. 이전 실행 결과와 제약은 [RAG 작업 기록](./rag_work_report.md), 사용 방법은 [RAG 사용 안내](./rag_guide.md)에 있다.

### Core 완료 기준

- [x] `GET /health`가 `ok: true`를 반환한다 — 이전 API 검증 기록 기준, 추가 상태 필드 포함
- [ ] Supabase Anonymous Sign-in과 Google OAuth Linking이 동작한다.
- [ ] JWT Bearer 검증이 동작한다.
- [ ] 모든 API 응답이 `{ok, data, error}` Envelope 형식이다.
- [x] `AppError` 계층이 올바른 HTTP 상태코드로 변환된다 — 이전 Core 단위 테스트 및 RAG 장애 응답 검증 기록 기준
- [ ] `LLM_PROVIDER=openai`로 LLM 호출이 된다.
- [ ] `LLM_PROVIDER=naito`로 전환이 된다 (미설정 시 명확한 오류).
- [ ] 프론트 `auth.js` 로그인·로그아웃·세션 확인이 동작한다.
- [ ] 프론트 `api.js` fetch 래퍼가 JWT를 자동 부착하고 Envelope를 파싱한다.
- [ ] `tokens.css` 디자인 토큰이 적용된다.
- [x] Core 단위 테스트가 모두 통과한다 — 이전 Core·RAG 합계 29개 통과 기록 기준

미완료 사유·확인 범위:

- 인증·JWT·OpenAI/Naito 어댑터·`api.js`는 코드가 있으나 실제 서비스 연결 검증은 확인되지 않았다. `signInWithOAuth` 호출만으로 동일 익명 사용자에 대한 Identity Linking을 완료했다고 판정하지 않는다.
- 현재 홈페이지는 `rag.js`를 사용하며 `app.js`·`auth.js`·`api.js` 기반 화면 흐름을 실행하지 않는다. 파일 존재만으로 홈페이지 인증 연동 완료로 체크하지 않는다.
- 전체 Envelope 통일은 미완료다. `/health`는 상태 dict, `/api/topic/discover`는 `DiscoverResponse`를 직접 반환한다.
- `tokens.css`는 연결되어 있으나 실제 브라우저에서 레이아웃·반응형 표시를 확인하지 못했다.
- Core·RAG 29개 통과 기록은 루트 `tests/test_topic.py`까지 포함한 전체 테스트 결과가 아니다. 현재 환경 복구 후 전체 테스트를 다시 확인한다.

### Topic 완료 기준 (매 해커톤마다)

- [ ] 주제별 외부 API 클라이언트가 실제 데이터를 반환한다.
- [ ] 정규화·판정 파이프라인이 올바른 결과를 내놓는다.
- [ ] AI 파이프라인이 단계별로 Trace를 남긴다.
- [ ] 프론트 화면이 결과 상태를 구분해 표시한다 (정상·미확인·대안).
- [ ] 비회원 상태에서 허용된 기능이 동작한다.
- [ ] Core 테스트가 Topic 변경 후에도 모두 통과한다.
- [ ] RAG를 쓰는 경우, RAG 없이도 핵심 기능이 동작한다.
- [ ] Naito API 없이 mock provider로 전체 UI를 검증할 수 있다.

### 공용 환경·실제 연결·통합 후속 작업

- [ ] Codex·Claude·Gemini 공통 지침과 도구별 진입점 정리
- [ ] Python·가상환경·의존성 잠금·테스트 명령 통일 및 팀원 clone 재현
- [ ] 실제 DB·임베딩·OpenAI/Naito 연결 검증
- [ ] 실제 브라우저에서 질문·답변·출처·오류·좁은 화면 확인
- [ ] Vercel·Render 배포 및 연결 확인
- [ ] 주제별 외부 API·판정·Trace·화면 시연 검증
- [ ] `Lab678-Hackathon/lab678` 통합 범위·배치·시점에 대한 팀 합의
- [ ] 팀 합의 후 통합 브랜치에서 충돌 해결·테스트·PR 검토, 사용자 지시 후 병합

구체적인 실행 순서와 확인 기록은 [준비 체크리스트](./준비체크리스트.md)에 모아 관리한다. 이 계획의 과거 `study/` 경로와 필수 인증 구상은 현재 구현과 대조해 갱신할 대상으로 남아 있다.

## 12. 문서 병합 계획

2026-10-30 사용자 요청에 따른 계획이다. 이번에는 계획만 기록하며 기존 설계·워크플로·배포 문서는 삭제하거나 합치지 않는다. `lab678` 저장소 통합 계획과는 별개의 문서 정리 작업이다.

### 목표 구조와 문서별 책임

| 문서 | 최종 책임 | 통합·정리 방법 |
|---|---|---|
| 루트 `README.md` | clone 후 설치·실행·검증의 가장 짧은 시작 안내 | 공통 명령을 한 번만 설명하고 상세 문서로 연결 |
| `framework.md` | 현재 구조·Core/Topic 계약·기능 추가 절차·오류 처리·검증 기준의 기준 문서 | `framework_design.md`와 `framework_workflow.md`의 유효한 내용을 여기에 통합 |
| `배포방법.md` | Render·Vercel 설정, 공개 URL·CORS·환경변수·배포 확인 | 별도 실행 안내로 유지. 설계 문서에는 배포 개요와 링크만 남김 |
| `rag_guide.md` | 자료 형식·적재·컬렉션·질문 및 출처 확인 | RAG 사용법만 유지하고 설치·배포의 중복 설명은 기준 문서로 연결 |
| `준비체크리스트.md` | 미완료 작업·담당자·완료 증거·확인 기록 | 실행 명령과 설계 설명은 복사하지 않고 링크 |
| `AGENTS.md` 및 도구별 진입점 | 짧은 작업 규칙·작업별 문서 라우팅 | 전체 설계·워크플로를 자동 로드하지 않음 |

배포는 사용하는 순간에만 읽는 상세 안내이므로 별도 유지한다. `framework`로 시작하는 기준 문서는 최종적으로 `framework.md` 하나로 줄이고, 실제 배포 명령·설정은 `배포방법.md`에만 관리한다.

### 통합 순서

1. 현재 코드·검증 기록을 기준으로 기존 세 문서의 내용을 구현 완료·계획·폐기할 과거 안내로 분류한다.
2. `framework.md`의 중복 설계·긴 디렉터리 트리를 축약하고 현재 RAG 흐름과 확장용 Auth/Topic scaffold를 구분한다.
3. `framework_design.md`의 유효한 계약·책임·불변식을 해당 절에 흡수한다. 인증 필수·없는 `study/` 경로·DB 미설정 503 같은 과거 안내는 그대로 복사하지 않는다.
4. `framework_workflow.md`에서 기능 추가·검증·문서 갱신에 필요한 절차만 흡수한다. 모든 작업에 긴 사전 루틴을 강제하지 않고 요청 범위의 개발과 별도 합의 대상을 구분한다.
5. 개발자용 오류 처리 계약과 디버깅 절차를 `framework.md`에 포함한다. 진행 중인 구현·테스트 결과가 확정된 뒤 내용을 반영한다.
6. 로컬 시작 명령은 README, 배포 명령은 배포방법, 자료 적재는 RAG 안내로 모으고 다른 문서는 링크로 바꾼다. 중복된 필수 키 설명도 기능별로 일치시킨다.
7. README·CLAUDE·기술 문서·인덱스 등의 기존 설계·워크플로 링크와 절 번호를 새 경로로 수정한다.
8. 연결을 모두 갱신한 뒤 `framework_design.md`와 `framework_workflow.md`를 제거한다. 과거 내용은 Git 이력으로 확인하며 자동 로드 경로에 중복 보관하지 않는다.
9. 깨끗한 clone 안내를 실제로 따라가고, 링크·명령·완료 체크를 검증한 뒤 문서 통합 작업을 별도 커밋한다.

### 완료 기준

- [x] 중복 문서와 역할을 확인하고 문서 병합 계획 작성
- [ ] 실제 구현 기준으로 내용 대조 및 `framework.md` 통합 편집
- [ ] README·배포·RAG 안내·체크리스트의 설명 중복 제거
- [ ] 에이전트 진입점과 모든 기존 문서 참조 갱신
- [ ] 이전 설계·워크플로 문서 제거 및 끊어진 링크 검색
- [ ] 문서의 설치·실행·검증 명령 재현 및 별도 커밋
