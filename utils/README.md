# utils/

프레임워크 개발 중 만들어지는 재사용 스크립트·템플릿·헬퍼 모음.
작업하다 두 번 이상 쓰일 것 같으면 여기에 저장한다.

## 구조

```
utils/
├── scripts/      ← 개발·배포·DB 작업용 셸/Python 스크립트
├── templates/    ← 새 기능 추가 시 복사해서 쓰는 코드 템플릿
└── snippets/     ← 자주 쓰는 패턴 조각 (konnect 참조 검증 완료 버전)
```

## 규칙

- 스크립트는 단독 실행 가능하게 작성 (의존 최소화)
- 경로는 인수로 받고 하드코딩하지 않는다
- 추가할 때 이 README에 한 줄 설명을 추가한다

## 목록

| 파일 | 용도 |
|---|---|
| `scripts/setup_dev.py` | 앱과 같은 루트 .env를 읽어 basic·ingest·rag·llm·auth 설정을 값·외부 호출 없이 점검 |
| `scripts/ingest_rag.py` | RAG 지식 문서 → pgvector 적재 (SUPABASE_DB_URL 필요) |
| `templates/source_template.py` | 외부 API 클라이언트 템플릿 |
| `templates/domain_template.py` | 판정 로직 모듈 템플릿 |
| `templates/api_router_template.py` | FastAPI 라우터 템플릿 |
| `templates/page_template.js` | 프론트엔드 페이지 템플릿 |
| `snippets/llm_call.py` | LLM structured output 호출 패턴 |
| `snippets/parallel_fetch.py` | asyncio 병렬 소스 조회 패턴 |
