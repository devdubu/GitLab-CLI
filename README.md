# GitLab Admin CLI — v0.1.0-beta

Self-hosted GitLab을 관리하기 위한 **CLI + 채팅 통합 도구**

> **핵심 철학:** LLM은 자연어를 CLI 명령어로 "번역"만 한다. 실행은 항상 Python CLI가 책임진다.

---

## 아키텍처

```
[ Open WebUI ]
      ↓ 자연어 입력
[ Open WebUI Functions (Python) ]
      ↓ Few-shot 프롬프트 전송
[ vLLM (GPT-OSS-120B) - OpenAI 호환 엔드포인트 ]
      ↓ CLI 명령어 문자열 반환
[ Python 검증 레이어 (core/safety.py) ]
      ↓ 검증 통과 (READ 등급만)
[ Adapter Layer (python-gitlab) ]
      ↓
[ Self-hosted GitLab (Docker) ]
```

---

## 빠른 시작

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 GITLAB_URL, GITLAB_TOKEN 등 설정
```

### 2. Docker Compose 실행

```bash
# 기존 GitLab이 없는 경우 전체 스택 구동
docker compose up -d

# 기존 GitLab이 있는 경우 gitlab 서비스 제외
docker compose up -d gl-cli open-webui
```

### 3. CLI 직접 사용

```bash
# 컨테이너 접속 후 CLI 사용
docker exec -it gl-cli python main.py issue list --state=open

# 또는 호스트에서 직접 (Python 3.12+, 의존성 설치 필요)
cd cli
pip install -r requirements.txt
python main.py --help
```

---

## 명령어 참조

### 이슈 조회

```bash
gl issue list                              # 열린 이슈 전체
gl issue list --project=myapp             # 특정 프로젝트
gl issue list --state=closed              # 닫힌 이슈
gl issue list --assignee=john             # 담당자 필터
gl issue list --format=json               # JSON 출력
```

### MR 조회

```bash
gl mr list                                 # 열린 MR 전체
gl mr list --project=myapp --state=merged  # 머지된 MR
gl mr list --created-after=2026-03-01      # 날짜 필터
gl mr list --format=csv                    # CSV 출력
```

### 파이프라인 조회

```bash
gl pipeline list --project=myapp           # 프로젝트 파이프라인
gl pipeline list --status=failed           # 실패 파이프라인
```

### 유저/프로젝트 조회

```bash
gl user list                               # 전체 유저
gl user list --active                      # 활성 유저만
gl project list --owned                    # 내 프로젝트
gl project list --starred                  # 즐겨찾기 프로젝트
```

### 데이터 내보내기

```bash
gl export issues --project=myapp --format=csv --output=/exports/issues.csv
gl export mrs --format=json --output=/exports/mrs.json
gl export users --format=csv
gl export projects --format=json
```

### 검색

```bash
gl search --query="login bug" --scope=issues
gl search --query="myapp" --scope=projects
```

### Chat 모드

```bash
# 단일 자연어 명령
gl chat "열린 이슈 보여줘"
gl chat "myapp 프로젝트 머지된 MR 뽑아줘"

# 대화형 모드
gl chat
```

---

## 안전 장치 (v0.1.0-beta)

| 등급 | 키워드 | v0.1.0-beta |
|------|--------|-------------|
| READ | list, show, export, search | ✅ 자동 실행 |
| CONFIRM | create, update, merge, close, archive | 🚫 다음 버전 지원 |
| DANGER | delete, block, remove, destroy, force | 🚫 다음 버전 지원 |

---

## 디렉토리 구조

```
gitlab-admin-cli/
├── docker-compose.yml
├── .env.example
├── cli/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py               # Typer CLI 진입점
│   ├── commands/             # 명령어 모듈
│   ├── adapters/
│   │   └── gitlab_api.py     # python-gitlab 래퍼
│   ├── core/
│   │   ├── safety.py         # 위험도 분류
│   │   ├── formatter.py      # Rich 출력 포맷터
│   │   └── config.py         # 환경변수 설정
│   └── chat/
│       ├── llm_client.py     # vLLM HTTP 클라이언트
│       ├── prompt.py         # Few-shot 프롬프트
│       └── parser.py         # LLM 응답 파싱/검증
└── openwebui/
    └── functions/
        └── gitlab_cli.py     # Open WebUI Function
```

---

## 기술 스택

| 구성 요소 | 기술 |
|-----------|------|
| CLI 프레임워크 | Typer |
| 출력 포맷 | Rich |
| GitLab API | python-gitlab |
| LLM 통신 | openai SDK (vLLM 호환) |
| 채팅 UI | Open WebUI |
| 내보내기 | CSV (표준 라이브러리) |
| 컨테이너 | Docker Compose |
