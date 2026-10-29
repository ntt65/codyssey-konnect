# 팀 공통 개발 지침

이 파일을 Codex·Claude·Gemini 공통 규칙의 기준으로 사용한다. 현재 사용자 지시를 우선한다.

## 현재 구조

- FastAPI + Vanilla JS + LangChain + Supabase pgvector 기반 범용 RAG 앱이다.
- 홈페이지: `frontend/index.html` → `frontend/js/rag.js` → `POST /api/ask`.
- Auth·다중 화면·Topic은 확장용이다. 정적 Topic 예시를 실제 추천 데이터로 취급하지 않는다.
- 구조·계약·개발 절차는 `framework_doc/framework.md`의 필요한 절만 읽는다.
- 설치·실행·검증 명령은 `README.md`, 적재는 `framework_doc/rag_guide.md`, 운영은 `framework_doc/배포방법.md`를 따른다.

## 작업과 검증

- 시작 시 `git status --short`로 기존 변경을 확인하고 보존한다. 실제 코드·심볼은 `rg`로 찾는다.
- 모든 문서·인덱스·초기 참고 자료를 매번 읽지 않는다. 작업 관련 코드·테스트·계약만 확인한다.
- 요청 범위의 Core 수정은 영향과 검증 방법을 밝히고 진행한다. Topic 호출부와 공통 계약을 보존한다.
- Python 3.12와 저장소 루트 가상환경을 사용한다. 키·실서비스 없이 모의 테스트를 실행한다.
- 백엔드: `uv run --no-project --python .venv python -m pytest -q`.
- 프론트 통신: `node --test tests/frontend/http.test.mjs` (Node.js 18 이상).
- 의미 있는 변경은 관련 테스트로 검증한다. 이미 통과한 검사를 이유 없이 반복하지 않는다.
- 구현·모의 테스트·실제 DB/LLM 연결·브라우저·팀원 PC 재현을 구분한다. 미검증을 완료로 체크하지 않는다.

## 구현 계약

- 기능 API는 Envelope를 사용한다. `/health`는 상태 확인용 예외다.
- 장애와 정상 빈 결과를 구분하고 예상 실패는 안전한 `AppError`로 변환한다.
- 원인은 `raise ... from exc`로 연결한다. 화면 요청 ID와 서버의 원인 유형·코드 위치로 진단한다.
- 응답·로그에 키·토큰·DB 연결 문자열·원본 입력·외부 오류 원문을 넣지 않는다. 비밀값은 `.env`에만 두고 커밋하지 않는다.
- 판정은 코드로, 설명은 LLM으로 한다. 사실을 생성해 채우거나 미확인을 긍정으로 바꾸지 않는다.
- AI 고지·출처·미확인 상태·오류 안내를 유지한다. 서버 문구는 `textContent` 등으로 표시한다.
- 필요할 때만 폴더·템플릿을 추가한다. `konnect` 참조는 `git show konnect:<경로>`로 읽고 자동 덮어쓰지 않는다.

## 기록과 협업

- 완료 시 `framework_doc/준비체크리스트.md`를 실제 증거에 맞춰 갱신한다.
- 작업마다 로컬 커밋한다. 사용자에게 보고한 변경·검토·검증·한계·남은 작업을 상세 커밋 메시지에 남긴다.
- 최종 보고에는 결과·검증·커밋·남은 작업을 포함한다. 중요한 변경·막힘은 작업 중에도 알린다.
- 원격 push·PR·배포·저장소 병합은 별도 사용자 지시를 따른다. `Lab678-Hackathon/lab678` 통합은 보류 중이다.
- 데이터 삭제·호환성 파괴 등 별도 합의 대상은 요청 범위와 구분한다.
