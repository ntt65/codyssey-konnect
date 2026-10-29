# 범용 RAG 사용 안내

관광 데이터 없이, 나중에 등록하는 자료만 근거로 답하는 문서 도우미입니다.
초기 `backend/app/rag/knowledge/`는 비어 있습니다.

## 실행

가상환경 설치·로컬 서버 실행·모의 테스트 명령은 [README](../README.md)를 따릅니다. 아래는 RAG 전용 설정과 자료 적재 안내입니다.

기존 .env가 있다면 복사 대신 필요한 설정만 추가합니다.
루트 .env에 아래 값을 설정합니다. 비밀값을 커밋하지 마세요.

- `OPENAI_API_KEY`: 검색용 임베딩에 필요합니다. 답변 제공자가 Naito여도 필요합니다.
- `SUPABASE_DB_URL`: pgvector를 사용할 Postgres 연결 문자열. Supabase의 session pooler 또는 직접 연결 주소를 사용합니다.
- `LLM_PROVIDER=openai`: 답변 생성 제공자. `OPENAI_MODEL`로 모델을 선택합니다.
- Naito 사용 시 `LLM_PROVIDER=naito`, `NAITO_BASE_URL`, `NAITO_API_KEY`, `NAITO_MODEL`을 설정합니다. OpenAI 호환 API인지 확인해야 합니다.
- `RAG_COLLECTION=knowledge`: 앱별로 다른 이름을 쓰면 기존 앱 자료와 분리할 수 있습니다.
- `RAG_SYSTEM_PROMPT`: 주제에 맞는 도우미 역할을 선택적으로 설정합니다.

Supabase Auth 설정은 이 RAG 데모의 질문 API에는 필요하지 않습니다.
문서 적재는 관리자 CLI에서만 수행하며 웹 업로드 API는 제공하지 않습니다.

홈페이지·API 명세 주소는 README를 확인합니다. 별도 프론트 호스팅의 URL·CORS 설정은 [배포방법](./배포방법.md)에서 관리합니다.

## 나중에 자료 추가

1. `backend/app/rag/knowledge/`에 UTF-8 .md 또는 .txt 파일을 넣습니다. 하위 폴더도 읽습니다.
2. 저장소 루트에서 아래 명령을 실행합니다.

```powershell
uv run --no-project --python .venv python utils/scripts/ingest_rag.py
# 다른 폴더 사용
uv run --no-project --python .venv python utils/scripts/ingest_rag.py "D:/my documents"
```

PDF·Word는 텍스트 또는 Markdown으로 변환한 뒤 넣습니다.
파일명은 출처로 노출됩니다. 안내문은 이 폴더 밖에 두어 검색 자료에 섞이지 않게 합니다.

같은 상대 경로의 문서를 다시 적재하면 이전 청크를 지우고 교체합니다.
문서가 짧아져도 낡은 청크가 남지 않습니다. 교체는 문서 단위이며 삭제와 저장 사이에 장애가 나면 재실행해야 합니다.
폴더에서 파일을 삭제하거나 이름을 바꾼 경우 DB의 이전 출처는 자동 삭제되지 않습니다. 새 컬렉션에 재적재하거나 관리자가 해당 출처를 제거해야 합니다.
모델·임베딩 차원을 바꾸면 새 컬렉션에 전체 자료를 재적재합니다.
기본 임베딩은 text-embedding-3-small, 1536차원입니다. RAG_EMBEDDING_DIMENSION은 모델의 실제 출력 차원과 일치해야 합니다.

## 응답과 확인

`POST /api/ask`에 `{"question":"질문"}`을 보냅니다.
공통 Envelope의 data에 answer, grounded, status, sources_count, citations가 들어갑니다.

- DB 미설정: not_configured. LLM을 호출하지 않습니다.
- 자료 없음 또는 유사도 기준 미달: no_evidence. 답변을 생성하지 않습니다.
- 검색 근거로 답변 생성: answered. 문서명·발췌·유사도를 함께 반환합니다.
- DB·임베딩·LLM 장애: 정상 빈 결과와 구분하여 오류 응답을 반환합니다.

grounded는 검색 근거가 제공됐다는 의미이며, 답변의 모든 문장이 자동 검증됐다는 의미는 아닙니다.
화면의 대화 기록은 브라우저 메모리에만 있고, 각 질문은 독립적으로 검색합니다.
현재는 공개 데모 API입니다. 실제 서비스 공개 전 인증·사용량 제한 정책을 앱에 맞게 적용해야 합니다.

모의 테스트는 [README](../README.md)의 전체 테스트 명령을 사용합니다. 외부 DB·LLM 비용 없이 검증하며 실제 연결 성공과 구분합니다.

실제 연결 검증은 키 설정 → 자료 적재 → 답이 있는 질문/없는 질문을 보내 출처를 확인하는 순서입니다.
