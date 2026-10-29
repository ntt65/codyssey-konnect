# AI 해커톤 프레임워크

FastAPI + Vanilla JS + LangChain + Supabase pgvector 기반 자료 질문·답변 앱입니다. 자료와 프롬프트를 바꿔 주제에 적용합니다. 홈페이지는 RAG 단일 페이지이며 Auth·다중 화면·Topic은 확장용입니다.

## 시작하기

Git과 [uv](https://docs.astral.sh/uv/getting-started/installation/)를 설치하고 clone한 폴더에서 실행합니다. PowerShell·macOS·Linux 공통 명령이며 uv가 Python 3.12와 루트 가상환경을 준비합니다.

```text
uv venv --python 3.12 .venv
uv pip install --python .venv -r backend/requirements-dev.txt
```

다른 PC의 Python 경로를 참조하는 기존 `.venv`는 재사용하지 않습니다. 필요한 로컬 설정을 보존하고 새 환경을 준비하세요. 전체 의존성 잠금과 깨끗한 clone 재현은 후속 작업입니다.

`.env`가 없을 때만 예시를 복사합니다. 기존 파일을 덮어쓰지 않습니다.

```powershell
# PowerShell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

```sh
# macOS / Linux
test -e .env || cp .env.example .env
```

화면·헬스·모의 테스트는 키 없이 확인할 수 있습니다. 실제 적재·검색은 `OPENAI_API_KEY`와 `SUPABASE_DB_URL`, 답변은 선택한 제공자 설정이 필요합니다. [기능별 설정](framework_doc/framework.md#5-설정과-제공자)을 확인하세요.

## 실행과 테스트

저장소 루트에서 실행합니다. FastAPI가 홈페이지도 제공하므로 별도 프론트 서버가 필요 없습니다. 가상환경을 활성화하지 않아도 됩니다.

```text
uv run --no-project --python .venv python -m uvicorn app.main:app --app-dir backend --reload --no-access-log --port 8000
```

- 홈페이지: http://localhost:8000
- API 명세: http://localhost:8000/docs
- 상태 확인: http://localhost:8000/health
- Topic 예시: http://localhost:8000/topic_demo.html — 정적 예시 데이터

```text
uv run --no-project --python .venv python -m pytest -q
```

프론트 공통 통신 모듈은 Node.js 18 이상에서 외부 라이브러리 없이 검증합니다.

```text
node --test tests/frontend/http.test.mjs
```

현재 별도 검증 환경(Python 3.12.13)에서 백엔드 58개·프론트 통신 7개 테스트를 통과했습니다. 실제 서비스·브라우저·팀원 PC 재현과 구분합니다. 오류 확인 방법은 [개발자 오류 가이드](framework_doc/framework.md#3-api와-오류-계약)를 참고하세요. `--no-access-log`는 URL·쿼리가 찍히는 Uvicorn 기본 접근 로그 대신 앱의 요청 ID·라우트·상태·시간 로그를 사용합니다. 기존 `setup_dev.py`의 `.env`·필수 키 판정은 후속 수정 대상이며 시작 필수 절차가 아닙니다.

## 문서

| 문서 | 용도 |
|---|---|
| [framework.md](framework_doc/framework.md) | 구조·계약·개발 절차·오류 처리·검증 |
| [RAG 안내](framework_doc/rag_guide.md) | 자료 적재·컬렉션·출처 확인 |
| [배포방법](framework_doc/배포방법.md) | Render·Vercel·URL·CORS |
| [준비체크리스트](framework_doc/준비체크리스트.md) | 남은 작업·확인 기록 |
| [문서통합 및 lab678 병합계획](framework_doc/문서통합_및_lab678_병합계획.md) | 문서 정리 결과·저장소 통합 보류 계획 |
| [기술 참조](framework_doc/tech.md) | 역할·공식 문서 |
| [재사용 도구](utils/README.md) | 템플릿·스니펫·적재 스크립트 |
| [초기 상세 참고](framework_doc/참고_초기설계.md) · [개발 절차 참고](framework_doc/참고_초기개발절차.md) | 필요할 때만 읽는 과거 설계·절차 |
| [과거 작업 기록](framework_doc/rag_work_report.md) | 이전 구현·테스트 결과 |

비밀값을 커밋하지 않습니다. 작업마다 상세 설명으로 로컬 커밋합니다. `lab678` 이관·push·PR·병합은 팀 합의와 사용자 지시까지 보류합니다.
