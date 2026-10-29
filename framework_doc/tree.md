# 프레임워크 디렉터리 트리

아래는 과거 scaffold 구상을 포함한 스냅샷이다. 현재 파일·개발 절차는 [framework.md](./framework.md)를 기준으로 확인하며 `konnect_study/` 등 모든 폴더가 존재한다고 가정하지 않는다.

> 생성일: 2026-10-29 | 브랜치: full-framework
> Core(항상 재사용) / Topic(주제마다 교체) / Doc(문서) 구분

```
codyssey-konnect/
│
├── .claude/
│   └── settings.json              [Doc] 하네스 설정 — git·테스트·서버 자동 허용
│
├── framework_doc/                 [Doc] 프레임워크 설계·작업 문서
│   ├── framework.md               [Doc] 현재 구조·설계·개발 절차·검증 기준
│   ├── tree.md                    [Doc] 이 파일 — 디렉터리 구조
│   ├── index.md                   [Doc] 순방향 인덱스 (파일 → 심볼)
│   └── reverse_index.md           [Doc] 역방향 인덱스 (심볼 → 파일)
│
├── konnect_study/                 [Doc] konnect 분석 참조 (건드리지 않음)
│
├── utils/                         [Tool] 재사용 스크립트·템플릿·스니펫
│   ├── README.md
│   ├── scripts/
│   │   ├── setup_dev.py           [Tool] 환경변수 확인
│   │   └── ingest_rag.py          [Tool] RAG 적재 헬퍼
│   ├── templates/
│   │   ├── source_template.py     [Template] 외부 API 클라이언트
│   │   ├── domain_template.py     [Template] 판정 로직
│   │   ├── api_router_template.py [Template] FastAPI 라우터
│   │   └── page_template.js       [Template] 프론트 페이지
│   └── snippets/
│       ├── llm_call.py            [Snippet] LLM structured output 패턴
│       └── parallel_fetch.py      [Snippet] 병렬 소스 조회 패턴
│
├── backend/
│   ├── requirements.txt           [Core] Python 의존성
│   └── app/
│       ├── main.py                [Core] FastAPI 앱 — CORS·에러핸들러·라우터
│       ├── config.py              [Core] pydantic-settings 환경변수
│       ├── core/
│       │   ├── auth.py            [Core] Supabase JWT 검증, AuthUser, Depends
│       │   ├── exceptions.py      [Core] AppError 계층
│       │   └── trace.py           [Core] AI 파이프라인 단계 추적
│       ├── models/
│       │   ├── common.py          [Core] Envelope[T], ErrorDetail
│       │   └── [topic].py         [Topic] 주제별 Pydantic 스키마
│       ├── api/
│       │   ├── health.py          [Core] GET /health
│       │   └── [feature].py       [Topic] 주제별 라우터
│       ├── services/
│       │   ├── llm/
│       │   │   ├── adapter.py     [Core] get_llm() — provider 추상화
│       │   │   ├── openai.py      [Core] ChatOpenAI 래퍼
│       │   │   └── naito.py       [Core] Naito LLM 래퍼
│       │   └── [feature].py       [Topic] 흐름 조합
│       ├── rag/
│       │   ├── embed.py           [Core] OpenAI Embeddings
│       │   ├── ingest.py          [Core] 문서 → pgvector 적재
│       │   ├── retrieve.py        [Core] 유사도 검색 + LLM 답변
│       │   └── knowledge/         [Topic] 주제별 지식 문서 (*.md)
│       ├── sources/               [Topic] 외부 API 클라이언트
│       ├── domain/                [Topic] 결정론적 판정 로직
│       └── agent/                 [Topic] LangChain 파이프라인
│
├── frontend/
│   ├── index.html                 [Core] 앱 진입점 — nav·view 구조
│   ├── css/
│   │   └── tokens.css             [Core] 디자인 토큰 (색·타이포·간격)
│   └── js/
│       ├── app.js                 [Core] 부트스트랩·메뉴 렌더·페이지 전환
│       ├── router.js              [Core] 메뉴명 → 페이지 함수 매핑
│       ├── auth.js                [Core] Supabase auth (Anonymous·OAuth)
│       ├── api.js                 [Core] fetch 래퍼 (JWT·Envelope)
│       ├── state.js               [Core] 최소 전역 상태
│       ├── content.js             [Topic] 브랜드·메뉴·문구 ← 첫 번째 교체 대상
│       ├── pages/                 [Topic] 화면 로직
│       └── components/            [Topic] 재사용 DOM 컴포넌트
│
├── tests/
│   └── core/
│       ├── test_exceptions.py     [Test] AppError 계층
│       ├── test_envelope.py       [Test] Envelope 모델
│       └── test_trace.py          [Test] Trace 추적
│
├── CLAUDE.md                      [Doc] 자동 로드 — 라우팅·원칙
├── .env.example                   [Doc] 환경변수 템플릿
└── .gitignore
```

## 범례

| 태그 | 의미 |
|---|---|
| [Core] | 공통 계약·재사용 기능. 요청 범위의 수정은 영향과 검증을 확인하고 진행 |
| [Topic] | 주제마다 교체. 자유롭게 작업 |
| [Doc] | 문서·설정. 코드 아님 |
| [Tool] | 개발 보조 스크립트·템플릿 |
| [Test] | 테스트 파일 |
| [Template] | 복사 후 교체해서 사용 |
| [Snippet] | 참조 후 필요한 부분만 사용 |
