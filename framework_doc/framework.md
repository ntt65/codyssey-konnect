# AI 해커톤 프레임워크

갱신: 2026-10-30. 기존 설계·워크플로·경량화 계획을 통합한 현재 구조와 개발 절차의 기준 문서다. 설치·실행은 [README](../README.md), 적재는 [RAG 안내](./rag_guide.md), 운영은 [배포방법](./배포방법.md), 상태는 [준비체크리스트](./준비체크리스트.md)에서 관리한다.

## 1. 현재 앱과 확장 범위

현재 앱은 관광 데이터 없이 시작하는 **자료 기반 질문·답변 단일 페이지**다. FastAPI + Vanilla JS + LangChain + Supabase pgvector를 사용한다. 프론트 빌드 도구는 없다.

```text
index.html → js/rag.js → POST /api/ask
  → rag/retrieve.py → embed.py → store.py → pgvector
  → 근거 선별 → services/llm/adapter.py → 답변·출처
```

- 기본 페이지는 `rag.js`를 실행한다. `app.js`·`router.js`·`auth.js` 기반 다중 화면은 확장용 scaffold이며 현재 홈페이지에는 연결되어 있지 않다.
- `/api/topic/discover`는 정적인 예시 데이터다. 실제 외부 API·추천 결과로 취급하지 않는다.
- 현재 RAG 질문 API는 인증 없는 데모다. 실제 공개 시 인증·사용량 제한을 결정한다.
- 과거 main/full-framework 분리 구상을 현재 상태로 단정하지 않는다. 작업 브랜치와 기준 커밋을 확인한다.
- `konnect`는 필요할 때 `git show konnect:<경로>`로 참조만 한다. 없는 `konnect_study/`·`study/` 경로를 전제로 삼지 않는다.

## 2. 파일 책임과 Core/Topic 경계

| 위치 | 책임 |
|---|---|
| `backend/app/main.py` | 앱 시작, CORS, 라우터·오류 처리, 정적 파일 제공 |
| `backend/app/config.py` | 루트 `.env` 로드와 설정 |
| `backend/app/core/` | 공통 예외·인증·단계 추적 |
| `backend/app/models/common.py`, `models/rag.py` | 공통 응답·질문·답변·출처 계약 |
| `backend/app/services/llm/` | 제공자 선택, 답변 모델·임베딩 생성 |
| `backend/app/rag/` | 자료 적재·검색·근거 기반 답변 |
| `frontend/index.html`, `js/rag.js`, `css/rag.css` | 현재 단일 질문 화면 |
| `frontend/css/tokens.css` | 공통 색·타이포·간격 |
| `frontend/js/{app,router,auth,api,state}.js` | 확장용 화면·인증·통신·상태 |
| `utils/templates/`, `utils/snippets/` | 복사 후 주제에 맞게 바꾸는 예시 |
| `backend/tests/`, `tests/` | Core·RAG·Topic 테스트 |

Core는 공통 계약과 재사용 기능, Topic은 주제별 모델·소스·판정·프롬프트·화면이다. 필요할 때만 `sources/`, `domain/`, `agent/`, `pages/`, `components/`를 만든다. 계획 디렉터리를 구현된 기능처럼 안내하지 않는다.

Core 변경도 요청 범위에 포함되면 영향과 검증 방법을 밝히고 진행한다. 데이터 삭제·공개 계약의 호환성 파괴·원격 작업 등 별도 합의 대상은 구분한다. 작업마다 로컬 커밋하며 보고한 변경·검토·검증·한계·남은 작업을 자세히 기록한다.

## 3. API와 오류 계약

기능 API의 목표 계약은 아래와 같다. HTTP 상태와 `ok`를 함께 확인한다.

```json
{"ok": true, "data": {}, "error": null}
```

```json
{"ok": false, "data": null, "error": {"code": "ExternalSourceError", "message": "안전한 안내"}}
```

`GET /health`는 상태 확인용 dict를 반환하는 예외다. HTTP 200은 앱 응답 여부이며 DB·LLM 연결 성공을 증명하지 않는다.

| 오류 | 상태 | 기준 |
|---|---|---|
| 요청 검증·`ValidationFailure` | 422 | 입력 항목을 안내하고 수정 가능하게 처리 |
| `AuthError` | 401 | 토큰 없음·만료·검증 실패. 인증 서버 장애와 구분 |
| `ConfigurationError` | 500 | 필요한 설정 이름·조치 안내, 값은 노출하지 않음 |
| `ExternalSourceError` | 503 | 외부 DB·임베딩·LLM 장애. 정상 빈 결과로 바꾸지 않음 |
| 예상하지 못한 오류·서버 데이터 검증 실패 | 500 | 사용자 입력 문제와 구분 |

`AppError.message`는 공개 문구다. 키·토큰·DB 주소·원본 외부 응답·`str(exc)`를 넣지 않는다. 원인은 `raise ExternalSourceError("안전한 안내") from exc`로 연결한다.

현재 기능 API인 `/api/ask`와 `/api/topic/discover`는 같은 Envelope 계약을 사용한다. 404·405·요청 검증·공통 예외·예상하지 못한 서버 오류도 Envelope로 반환한다. 정적 파일은 `/css`·`/js`에만 마운트하고 홈페이지·Topic 데모를 명시적으로 제공해 API의 405가 정적 파일 404에 가려지지 않게 한다. 새 정적 자산 폴더·HTML 화면은 `main.py`에 명시적으로 등록한다.

### 개발자가 오류를 확인하는 순서

1. 화면 안내의 **요청 ID** 또는 Network의 `X-Request-ID`를 복사한다. 서버가 생성한 ID이며 클라이언트 입력을 그대로 사용하지 않는다.
2. 같은 ID를 서버 로그에서 검색한다. `code`, `status`, 라우트, 원인 예외 유형, `파일:줄:함수` 위치, 경과시간을 확인한다.
3. 422라면 `error.issues`의 필드·유형·안내를 확인한다. 원본 입력이나 Pydantic 내부 오류 객체를 복사해 로그에 남기지 않는다.
4. 아래 원인별 조치를 적용하고 같은 작업을 다시 실행한다. 응답 메시지만 바꾸어 오류를 감추지 않는다.

```json
{"ok": false, "data": null, "error": {"code": "ValidationError", "message": "입력값을 확인해 주세요.", "issues": [{"field": "body.question", "code": "string_too_long", "message": "입력값이 너무 깁니다."}]}, "request_id": "서버가 생성한 ID"}
```

| 확인한 값 | 조치 |
|---|---|
| `ValidationError` / 422 | 지정 필드·JSON 형식·길이·범위를 확인 |
| `HTTP404` / 404 | 호출 경로와 API 기본 주소 확인 |
| `HTTP405` / 405 | HTTP 메서드와 `Allow` 헤더 확인 |
| `AuthError` / 401 | 재로그인, 실제 서명 방식·issuer·audience·키 갱신 확인 |
| `ConfigurationError` / 500 | 안내된 설정 이름 확인. 값은 공유하지 않음 |
| `ExternalSourceError` / 503 | 원인 유형으로 인증 서버·DB·임베딩·LLM의 연결·키·상태 확인 |
| `InternalServerError` / 500 | 같은 요청 ID의 파일·줄과 원인 유형을 따라 서버 로직·출력 스키마 수정 |
| 프론트 `InvalidResponse` | HTML 프록시 오류·잘못된 API 주소·Envelope 위반 확인 |
| 프론트 `NetworkError` | 서버 실행·주소·CORS·네트워크 확인 |
| 프론트 `RequestTimeout` / `RequestCancelled` | 지연과 사용자 취소를 구분. 자동 중복 호출하지 않음 |

프론트는 `js/http.js`의 `requestJSON`·`ApiError`·`formatApiError`를 공유한다. RAG는 직접 사용하고 인증이 필요한 기능은 `api.js`를 통해 JWT를 부착한다. 개발자 콘솔에는 코드·상태·요청 ID만 남긴다. 문구는 `textContent`로 표시한다.

서버의 `core/errors.py`는 원본 질문·본문·인증 헤더·쿼리·외부 응답·원본 예외 메시지를 기록하지 않는다. 원인 유형과 코드 위치만 남기므로 `raise ... from exc`를 사용한다. AppError 공개 문구의 안전성은 작성자가 책임진다. HTTPException의 raw detail은 공개하지 않는다. CORS 오류 응답에서도 요청 ID를 읽을 수 있게 노출한다.

기본 접근 로그의 URL·쿼리를 피하도록 시작 명령에 `--no-access-log`를 사용한다. 이미 전송을 시작한 스트리밍 응답·백그라운드 작업의 오류는 응답을 새 JSON으로 바꿀 수 없으며 향후 해당 기능을 추가할 때 별도 처리가 필요하다. 현재 RAG는 비스트리밍 응답이다.

## 4. RAG 동작과 제약

1. 하위 폴더의 `.md`·`.txt`를 읽고 기본 800자 청크·100자 겹침으로 분할한다.
2. 임베딩 후 상대 경로를 출처로 적재하며 같은 출처의 기존 청크를 교체한다.
3. 질문을 임베딩하고 `RAG_TOP_K`만큼 검색한다. distance를 `1 - distance` 유사도로 변환한다.
4. 임계치 이상의 근거만 모델에 제공하고 답변·문서명·발췌·유사도를 반환한다.

| 상태 | 뜻 | 답변 LLM 호출 |
|---|---|---|
| `not_configured` | DB 미설정 | 안 함 |
| `no_evidence` | 근거 없음 | 안 함 |
| `answered` | 검색 근거로 답변 생성 | 함 |

`grounded=true`는 근거를 모델에 제공했다는 뜻이며 모든 문장·인용의 자동 검증을 뜻하지 않는다. 각 질문은 독립적이고 화면 내역을 모델에 다시 보내지 않는다. 자료 안의 지시는 따르지 않게 하며 출력은 `textContent` 등으로 처리한다.

PDF·Word 직접 적재, 파일 삭제·이름 변경에 따른 옛 출처 자동 삭제, 문서 교체의 단일 트랜잭션은 지원하지 않는다. 모델·차원 변경 시 새 컬렉션에 전체 재적재한다. 상세 명령은 [RAG 안내](./rag_guide.md)에 둔다.

## 5. 설정과 제공자

값은 `.env` 또는 배포 서비스의 비밀 환경변수에 넣는다. 키 이름·기본값은 [`.env.example`](../.env.example)과 `config.py`에서 확인한다.

| 용도 | 필요한 설정 |
|---|---|
| 화면·헬스·모의 테스트 | 외부 키 없이 확인 가능 |
| 실제 적재·검색 | `OPENAI_API_KEY`, `SUPABASE_DB_URL` |
| OpenAI 답변 | `LLM_PROVIDER=openai`, `OPENAI_MODEL`, `OPENAI_API_KEY` |
| Naito 답변 | `LLM_PROVIDER=naito`, `NAITO_BASE_URL`, `NAITO_API_KEY`, `NAITO_MODEL` |
| 검색 조정 | `RAG_COLLECTION`, `RAG_TOP_K`, `RAG_SIMILARITY_THRESHOLD`, `RAG_EMBEDDING_DIMENSION` |
| 역할 변경 | `RAG_SYSTEM_PROMPT` |
| 확장용 Auth | `SUPABASE_URL`, 프론트 공개 키·OAuth 설정 |

Naito 답변을 써도 현재 검색 임베딩은 OpenAI 키가 필요하다. Naito의 호환 여부·모델·토큰 배분은 제공 환경에서 확인한다. 장애 시 승인되지 않은 유료 제공자로 자동 전환하지 않는다.

`Settings.configuration_report()`·`/health`·`setup_dev.py`는 같은 기능별 설정 기준을 사용한다. 기본 `app`은 DB 설정이 있으면 `rag`, 없으면 키가 필요 없는 `basic`을 검사한다. `ingest`는 답변 제공자 키를 요구하지 않고, Naito의 `rag`는 OpenAI 임베딩 키도 검사한다. `auth`는 URL·프론트 공개 키를 확인하며 JWKS에 서비스 역할 시크릿을 요구하지 않는다. 누락·기본 URL 형식·미지원 제공자를 값 없이 진단하며 실제 연결 성공을 의미하지 않는다. 실행·프로필·종료코드는 README에서 관리한다.

## 6. 주제별 개발 절차

1. 핵심 사용자·문제·입력·결과·완료 기준을 정한다.
2. 관련 코드·테스트·템플릿과 이 문서의 필요한 절만 읽는다.
3. RAG형 주제는 자료·역할 프롬프트·현재 화면 문구를 교체한다. 다중 화면 확장 시 `content.js`·페이지·라우트 등록을 연결한다.
4. 외부 데이터가 필요하면 모델 → 소스 → 정규화·판정·랭킹 → 서비스 → 라우터 → 화면 순으로 추가한다. 라우터는 `main.py`에 등록한다.
5. 입력·정상·빈 결과·장애를 검증하고 핵심 사용자 흐름을 끝낸다.
6. 바뀐 계약의 문서만 갱신하고 검증·미검증 범위를 상세 커밋한다.

확장형 파이프라인은 `parse → fetch → judge → rank → compose → explain`이다. 정적 Topic 예시는 전체 구현이 아니다.

불변식:

- 판정은 코드로, 설명은 LLM으로 한다.
- 가격·시간·좌표·가용성을 만들어 채우거나 미확인을 긍정으로 바꾸지 않는다.
- 제외 후보를 섞거나 개수를 맞추려고 부적합 후보를 추가하지 않는다.
- AI 고지·근거·미확인 상태·오류 안내를 유지한다.
- 외부 조회에 시간 제한을 두며 실패와 정상 0건을 구분한다.

## 7. 인증·Trace·화면 확장

- 인증 코드는 있지만 RAG 홈페이지에는 연결되지 않았다. `signInWithOAuth` 존재만으로 익명 사용자 Identity Linking·동일 user_id 보존이 검증됐다고 보지 않는다.
- JWT는 RS256·ES256 비대칭 서명, 프로젝트 issuer, `aud=authenticated`, 만료·필수 claim을 검사한다. 알 수 없는 kid는 키를 한 번 새로 가져와 확인하고 임의의 첫 키로 대체하지 않는다. 기존 HS256 공유 시크릿은 이 JWKS 경로로 지원하지 않는다. 실제 Supabase 설정과 맞춰 연결 검증해야 한다. [Supabase 서명 키 안내](https://supabase.com/docs/guides/auth/signing-keys)
- `Trace.step()`은 단계·경과시간·데이터를 기록하고 `to_dict()`는 리스트를 반환한다. 운영 trace 자동 숨김은 구현 완료로 주장하지 않는다. 민감 데이터를 공개 응답에 넣지 않는다.
- 화면은 idle·loading·success·empty·error를 구분하고 중복 전송 방지·재시도를 제공한다.
- `content.js`에는 설정·문구만 둔다. 현재 RAG 문구는 별도로 있으므로 실제 수정 대상을 먼저 확인한다.

## 8. 검증과 완료 기준

명령은 [README](../README.md)에 모은다. 외부 API를 모의 객체로 대체한 테스트와 실제 연결·브라우저·배포 검증을 구분한다.

- [x] 자료 적재·검색·답변·출처·질문 화면 구현
- [x] DB 미설정·근거 없음·외부 장애 구분 구현
- [x] 기존 Core·RAG 29개 통과 기록 확인 — [과거 기록](./rag_work_report.md)
- [x] 설계·워크플로·경량화 계획을 이 문서로 통합
- [x] 오류 처리 보강과 회귀 검증 — 백엔드 58개·프론트 통신 7개 통과
- [ ] 실제 적재 → 질문 → 답변·출처 확인
- [ ] 브라우저 입력·오류·출처·좁은 화면 검증
- [ ] Auth·Identity Linking 실제 검증 — 사용할 때 진행
- [ ] 새 clone·다른 팀원 PC 재현
- [ ] Vercel·Render 배포·연결 검증

과거 29개와 달리 현재 백엔드 58개에는 루트 Topic·공통 오류·JWT·제공자 설정 테스트도 포함한다. Python 3.12.13의 별도 `.cache/test-venv`에서 검증했으며 기존 `.venv`는 보존했다. 서버 임시 경로 권한 때문에 `-p no:cacheprovider --basetemp .cache/pytest-errors-run1`을 사용했다. 새 clone·팀원 PC와 실제 연결 검증은 별도다. Starlette·python-jose의 deprecation 경고가 남아 있다.

## 9. 문서 사용과 갱신

| 작업 | 문서 |
|---|---|
| 설치·로컬 실행·테스트 | [README](../README.md) |
| 구조·계약·개발·오류 원칙 | 이 문서의 해당 절 |
| 자료 적재·RAG 사용 | [RAG 안내](./rag_guide.md) |
| 배포·URL·CORS·운영 설정 | [배포방법](./배포방법.md) |
| 상태·남은 작업·담당자 | [준비체크리스트](./준비체크리스트.md) |
| 문서 통합·lab678 보류 계획 | [문서통합 및 병합계획](./문서통합_및_lab678_병합계획.md) |
| 기술별 공식 문서 | [tech.md](./tech.md) |
| 재사용 코드 | [utils 안내](../utils/README.md) |

모든 문서를 매번 읽지 않는다. `rg`로 실제 코드를 찾고 필요한 절만 읽는다. 초기 상세 내용은 [초기 설계 참고](./참고_초기설계.md)와 [초기 개발 절차 참고](./참고_초기개발절차.md)에 보존한다. 현재 지침과 구분하고 필요할 때만 읽는다. `lab678` 이관·push·PR·병합은 팀 합의와 사용자 지시까지 보류한다.
