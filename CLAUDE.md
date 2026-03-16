# CLAUDE.md — GitLab Admin CLI 프로젝트 룰셋

이 파일은 Claude Code가 이 프로젝트에서 작업할 때 반드시 따라야 하는 규칙을 정의한다.

---

## 1. 프로젝트 개요

Self-hosted GitLab을 관리하기 위한 CLI + 채팅 통합 도구.
채팅 인터페이스는 **Open WebUI**, LLM은 **로컬 vLLM**, 컨테이너는 **Docker Compose**로 운영한다.

---

## 2. 핵심 설계 원칙 (절대 규칙)

### 2-1. LLM은 "번역기"만 담당한다
- LLM에게 Tool use / Function calling을 직접 시키지 않는다.
- LLM은 자연어 → CLI 명령어 문자열 변환만 한다.
- 생성된 명령어는 Python 레이어에서 독립적으로 검증 후 실행한다.
- 이유: 로컬 vLLM 환경에서 Tool use 안정성을 보장할 수 없다.

### 2-2. 안전 장치는 우회할 수 없다
- 모든 명령어 실행 전 `core/safety.py`를 반드시 통과해야 한다.
- `safety.py`를 생략하는 실행 경로를 만들지 않는다.
- 위험도 등급:
  - `READ` — list, show, export, search → 자동 실행 허용
  - `CONFIRM` — create, update, merge, close, archive → 사용자 확인 필요 (v0.2.0+)
  - `DANGER` — delete, block, remove, destroy, force → 전문 입력 필요 (v0.2.0+)

### 2-3. LLM 호출은 `chat/llm_client.py` 에서만
- 다른 모듈에서 직접 OpenAI 클라이언트를 생성하거나 LLM을 호출하지 않는다.

### 2-4. v0.1.0-beta 범위 제한
- 현재 버전은 READ 명령어만 실제 실행한다.
- CONFIRM/DANGER 등급 요청은 "다음 버전에서 지원 예정" 안내 메시지를 반환한다.
- 범위 밖 기능을 추가할 때는 반드시 버전 계획을 확인한다.

---

## 3. 코드 작성 규칙

### 3-1. 모듈 경계
| 모듈 | 역할 | 금지 사항 |
|------|------|-----------|
| `core/config.py` | 환경변수 로딩 | 비즈니스 로직 없음 |
| `core/safety.py` | 위험도 분류만 | 실행 로직 없음 |
| `core/formatter.py` | 출력만 | API 호출 없음 |
| `adapters/gitlab_api.py` | python-gitlab 래퍼만 | 출력/포맷 없음 |
| `chat/llm_client.py` | LLM HTTP 호출만 | 파싱 로직 없음 |
| `chat/parser.py` | 파싱/검증만 | LLM 호출 없음 |
| `commands/*.py` | CLI 진입점 + 출력 | 직접 API 호출 없음 (`adapters` 경유) |

### 3-2. 페이지네이션
- `python-gitlab` 쿼리는 `as_list=False` 또는 `lazy=True`를 사용한다.
- 전체 결과를 메모리에 한 번에 올리는 `.list()` 호출을 피한다.

### 3-3. 에러 처리
- GitLab API 오류 → `RuntimeError`로 래핑하여 사용자 친화적 메시지 포함
- vLLM 타임아웃 → `RuntimeError("vLLM 응답 타임아웃: ...")`
- 파싱 실패 → `chat/parser.py`의 `ParseError`
- 명령어 모듈에서는 `except Exception as e: print_error(str(e)); raise typer.Exit(1)` 패턴 사용

### 3-4. 출력 형식
- 터미널 출력은 항상 `core/formatter.py`의 함수를 사용한다.
- `print()` 직접 호출 금지 — `print_output()`, `print_error()`, `print_info()` 등 사용
- 기본 출력 형식: `table`. 지원 형식: `table | json | csv`

---

## 4. CHANGELOG 규칙

### 4-1. 변경사항은 반드시 CHANGELOG.md에 기록한다
- 새 기능 추가, 버그 수정, 설계 변경 — 모두 기록
- 포맷: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) 준수

### 4-2. 섹션 구조
```
## [버전] - YYYY-MM-DD
### Added     — 새로운 기능
### Changed   — 기존 기능 변경
### Fixed     — 버그 수정
### Removed   — 제거된 기능
### Security  — 보안 관련 변경
```

### 4-3. [Unreleased] 섹션 유지
- 다음 버전에서 구현 예정인 항목은 `[Unreleased]` 섹션에 기록한다.
- 버전 릴리즈 시 `[Unreleased]`의 항목을 해당 버전으로 이동한다.

### 4-4. 작업 완료 후 CHANGELOG 업데이트
- 새 파일 생성, 기능 추가, 버그 수정 작업 완료 후 반드시 CHANGELOG를 업데이트한다.

---

## 5. 버전 관리 규칙

- `MAJOR.MINOR.PATCH[-stage]` 형식 (예: `0.1.0-beta`, `0.2.0`, `1.0.0`)
- v0.x.x: 초기 개발 단계 — 파괴적 변경 허용
- v1.0.0: READ/CONFIRM/DANGER 전체 구현 완료 시 릴리즈

### 로드맵
| 버전 | 범위 |
|------|------|
| v0.1.0-beta | 데이터 조회(READ) 전용 |
| v0.2.0 | CONFIRM 등급 (create, update, merge, close) |
| v0.3.0 | DANGER 등급 (delete, block) + 확인 플로우 |
| v0.4.0 | 명령어 히스토리, 자동완성 |
| v1.0.0 | 안정화 릴리즈 |

---

## 6. Docker / 인프라 규칙

- 모든 컴포넌트는 Docker Compose로 운영한다.
- 서비스 간 통신은 `gl-net` 브리지 네트워크를 사용한다.
- 환경변수는 `.env` 파일로 관리, `.env`는 절대 커밋하지 않는다 (`.env.example`만 커밋).
- `exports/` 디렉토리는 호스트 볼륨으로 마운트한다.

---

## 7. 파일 생성 가이드라인

- 새 명령어 추가 시: `cli/commands/<name>.py` → `main.py`에 `app.add_typer()` 등록
- 새 adapter 추가 시: `cli/adapters/<name>.py` → `adapters/__init__.py`에 노출
- 설계 변경 시: CHANGELOG `[Unreleased]` 또는 해당 버전 섹션에 기록
- README는 사용자 향 문서 — 내부 설계 결정은 CLAUDE.md에 기록
