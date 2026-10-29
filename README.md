# AI 해커톤 프레임워크

FastAPI + Vanilla JS + LangChain + Supabase pgvector 기반 자료 질문·답변 앱입니다. 자료와 프롬프트를 바꿔 주제에 적용합니다. 홈페이지는 RAG 단일 페이지이며 Auth·다중 화면·Topic은 확장용입니다.

## 시작하기

Git과 [uv](https://docs.astral.sh/uv/getting-started/installation/)를 설치하고 clone한 폴더에서 실행합니다. PowerShell·macOS·Linux 공통 명령이며 `.python-version`의 Python 3.12.13과 `uv.lock`의 전체 의존성으로 루트 `.venv`를 준비합니다. uv 0.11.5에서 검증했습니다.

```text
uv sync --locked
```

다른 PC의 `.venv`를 복사하지 않습니다. 기존 환경이 깨졌다면 필요한 로컬 설정을 보존하고 해당 폴더를 별도로 옮긴 뒤 `uv sync --locked`로 만듭니다. 이 PC의 기존 환경은 `.cache/venv-original-20261030`에 보존하고 표준 `.venv`를 복구했습니다.

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
uv run --locked python -m uvicorn app.main:app --app-dir backend --reload --no-access-log --port 8000
```

- 홈페이지: http://localhost:8000
- API 명세: http://localhost:8000/docs
- 상태 확인: http://localhost:8000/health
- Topic 예시: http://localhost:8000/topic_demo.html — 정적 예시 데이터

```text
uv run --locked python -m pytest -q
```

프론트 공통 통신 모듈은 Node.js 18 이상에서 외부 라이브러리 없이 검증합니다.

```text
node --test tests/frontend/http.test.mjs
```

설정 점검은 앱과 같은 루트 `.env`와 프로세스 환경변수를 사용합니다. 기본 명령은 DB가 없으면 키 없는 화면 실행을, DB가 있으면 RAG 설정을 검사합니다. 필요한 기능을 명시할 수도 있습니다.

```text
uv run --locked python utils/scripts/setup_dev.py
uv run --locked python utils/scripts/setup_dev.py --feature rag
uv run --locked python utils/scripts/verify_dev.py
```

프로필: `basic`(화면), `ingest`(적재), `rag`(검색·답변), `llm`(답변 제공자), `auth`(확장 인증). 종료코드 0은 설정 준비, 1은 누락·기본 형식 오류, 2는 설정 타입·의존성 오류입니다. 값은 출력하지 않으며 실제 DB·LLM 접속은 하지 않습니다.

`c521f54`의 KONNECT 비교 테스트를 포함해 백엔드 71개·프론트 통신 7개가 통과했습니다. `d46f82c`의 새 로컬 clone에서도 `.env` 없이 잠금 설치·생성물 검사·기본 설정·오프라인 smoke·전체 테스트가 재현됐습니다(Windows, 기존 uv 패키지 캐시 사용). 다른 OS·팀원 PC·실제 서비스 검증과 구분합니다. `verify_dev.py`는 로컬 키가 있어도 이 프로세스의 RAG 저장소를 꺼 외부 호출 없이 앱 계약을 확인합니다. 오류 확인은 [개발자 오류 가이드](framework_doc/framework.md#3-api와-오류-계약)를 참고하세요. `--no-access-log`는 원본 URL·쿼리 대신 요청 ID·라우트·상태·시간 로그를 사용합니다.

## 의존성 변경과 CI

의존성 원본은 `pyproject.toml`, 전체 잠금은 `uv.lock`입니다. 직접 버전을 바꿀 때 아래 순서로 갱신합니다. `--locked` 실행은 잠금 파일을 몰래 바꾸지 않습니다.

```text
uv lock
uv sync --locked
uv run --locked python utils/scripts/sync_requirements.py
uv run --locked python utils/scripts/sync_requirements.py --check
```

`backend/requirements.txt`와 `requirements-dev.txt`는 pip·Render 호환용 생성물입니다. 직접 수정하지 않습니다. 런타임 전용 환경은 `uv sync --locked --no-dev`로 설치합니다.

`.github/workflows/ci.yml`은 Windows·macOS·Linux에서 잠금 설치, 생성물 일치, 기본 설정, 오프라인 앱 점검, 백엔드·프론트 테스트를 실행하도록 구성했습니다. 외부 API 키·배포 권한을 쓰지 않습니다. 워크플로 작성·로컬 명령 검증과 원격 GitHub Actions 성공은 별개이며, push 보류 상태에서는 원격 실행 결과가 없습니다.

## 문서

Codex는 루트 `AGENTS.md`, Claude Code와 Gemini CLI는 각각 `CLAUDE.md`·`GEMINI.md`에서 같은 파일을 import합니다. 공통 규칙을 수정할 때는 `AGENTS.md`만 바꿉니다.

팀원은 저장소 루트에서 새 세션을 시작한 뒤 적용된 지침 경로·로컬 커밋 규칙·병합 보류 상태를 확인하세요. Claude는 `/memory`에서 파일을, Gemini는 `/memory show`에서 가져온 내용을 확인합니다. Codex에는 적용한 지침 파일을 요약하도록 요청합니다. 여기서는 import 경로·형식만 확인했으며 각 도구의 로그인된 세션 실행은 아직 검증하지 않았습니다.

공식 동작: [Codex AGENTS](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Claude imports](https://code.claude.com/docs/en/memory), [Gemini context imports](https://geminicli.com/docs/cli/gemini-md/).

| 문서 | 용도 |
|---|---|
| [AGENTS.md](AGENTS.md) | 도구와 무관한 팀 공통 개발 규칙 |
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
