# qa_manager — 검수 시스템

> 문서 구성: 목적 → 시스템 구조/계층 → 작동 흐름 → 실행 방법 → 프로젝트 추가 방법 → 현재 등록 현황 → 검증됨

여러 독립 프로젝트(저장소)의 requirement · test item · 통과여부를 한 곳에서
보여주고 관리하는 시스템입니다. 특정 프로젝트에 속한 대시보드가 아니라,
그 자체로 독립된 검수 시스템입니다.

**바로가기 →** [imdaeseong.github.io/qa_manager](https://imdaeseong.github.io/qa_manager/)

`index.html`과 각 프로젝트의 `dashboard.html`은 마지막으로 로컬에서 재검사를 실행하고
커밋·푸시한 시점의 결과입니다(실시간 재실행 아님) — 최신 상태를 보려면
`open_qa_system.bat`을 실행한 뒤 커밋·푸시합니다. 경로에 로컬 사용자 폴더명이
그대로 노출되므로 민감한 내부 정보를 다루는 프로젝트는 등록하지 않습니다.

## 시스템 구조

```
qa_manager/                       (독립 git 저장소, github.com/ImDaeseong/qa_manager)
  index.html                      생성됨 — 전체 프로젝트 목록 + 통과/실패 요약 (시작점)
  open_qa_system.bat              전체 재검사 + index.html 열기 (더블클릭 실행)
  scripts/
    _checklist_lib.py             checklist.yaml 로드, repo_root 경로 계산, check 명령 실행
    _style.py                     index.html/dashboard.html 공통 CSS
    run_checklist.py              프로젝트 1개를 터미널에 텍스트로 보고
    generate_checklist_dashboard.py   프로젝트 1개의 dashboard.html 생성
    generate_system_index.py      전체 프로젝트를 스캔해 index.html 생성
  projects/
    <프로젝트명>/
      checklist.yaml              requirement -> dev_item -> test_item + repo_root
      dashboard.html               생성됨 (직접 수정하지 않음)
```

**계층**: requirement → dev_item → test_item. test_item의 `check` 명령이 PASS해야 dev_item이 PASS, dev_item이 전부 PASS해야 requirement가 PASS입니다. 화면 문구는 운영 담당자도 읽을 수 있는 평범한 한글로 쓰되, 파일명·명령어는 원문 그대로 둡니다.

## 작동 흐름

`open_qa_system.bat` 실행 시: `generate_system_index.py`가 `projects/*/checklist.yaml`을 전부 찾음 → 각 파일의 `repo_root`를 실제 폴더 경로로 바꿈(예: `ai_test1` → `C:\Users\cs930\Desktop\ai_test1`) → 그 폴더 안에서 test_item의 `check` 명령을 **지금 이 순간 직접 실행**(`pytest`, `npm run lint`, PowerShell 가드 스크립트 등 프로젝트에 실제로 있는 명령 — `checklist.yaml`의 `status`/`last_verified`는 참고용 마지막 기록일 뿐, 매번 다시 실행함) → 아래에서 위로 집계 → 프로젝트별 `dashboard.html`과 전체 `index.html`을 씀.

## 실행 방법

```
open_qa_system.bat                                               # 전체 재검사 + 브라우저로 index.html 열기
python scripts\generate_system_index.py                          # 전체 프로젝트 재검사 + index.html 생성
python scripts\generate_checklist_dashboard.py [checklist.yaml]  # 프로젝트 1개만 재검사
python scripts\run_checklist.py [checklist.yaml]                 # 프로젝트 1개를 터미널 텍스트로 보고
```

재검사 없이 마지막 생성 결과만 보려면 위 "바로가기" 링크(GitHub Pages)로 보거나,
이 저장소를 로컬 폴더에서 열어 `index.html` 파일을 직접 더블클릭합니다. (주의: GitHub.com
저장소 화면에서 `index.html` 파일명을 클릭하면 렌더링된 페이지가 아니라 원문 코드
화면(blob)이 열립니다 — 렌더링된 페이지를 보려면 반드시 위 Pages 링크를 사용합니다.)

## 프로젝트 추가 방법

1. `projects/<프로젝트명>/checklist.yaml`을 새로 만듭니다. 스키마는
   `projects/hermes-agents/checklist.yaml` 상단 주석을 따릅니다.
2. `repo_root`를 반드시 지정합니다 — qa_manager 상위 폴더
   (`C:\Users\cs930\Desktop`) 기준 상대경로 (예: `hermes-agents`, `ai_test1`).
3. test_item은 그 프로젝트에 실제로 존재하는 것만 등록합니다(기존 테스트,
   lint 설정, CI workflow, 가드 스크립트 등) — 없는 검사를 지어내지 않습니다.
4. `python scripts\generate_system_index.py`로 새 프로젝트가 index.html에
   나타나고 검사가 실제로 통과/실패하는지 확인합니다.

## 현재 등록된 프로젝트

hermes-agents, ai_prompt, ai-workspace, skills, ai_test, ai_test1, ai_test2, ai_agent
— 총 8개. 실시간 통과/실패 현황은 `index.html`을 열어 확인합니다.

`ai_agent`는 2026-09-10에 등록했습니다. 아직 Phase 0(설계 단계)라 src/ 에이전트나
실제 모델·전송 어댑터가 없어, 등록 시점 검사항목은 문서/링크 검증
(`scripts/validate_docs.ps1`), eval 스키마 검증기 자체 테스트, `api/` 공공데이터
클라이언트 라이브러리(모듈별 + 전체 스위트)로 한정했습니다.

`ai_test3`는 2026-09-06 CareerDiff가 `ai_test2`로 이동하면서 등록 프로젝트가
0개가 돼 2026-09-07에 이 목록에서 제외했습니다(테스트 항목은 `ai_test2`
checklist.yaml의 R1-D7~D10으로 이관).

## 검증됨 (2026-08-17)

위 "작동 흐름"의 주장을 코드와 실제 실행으로 대조 확인했습니다.

- `_checklist_lib.py`의 `run_test_item()`을 직접 읽어 확인: `check` 명령을 매번 `Popen`으로 실행하고, `checklist.yaml`의 `status`/`last_verified`를 읽어 스킵하는 경로는 없음 — "항상 실행 결과" 주장과 일치.
- 개별 check당 300초 타임아웃 + `taskkill /F /T`로 프로세스 트리 강제 종료(Windows에서 `subprocess.run(timeout=)`이 cmd.exe 래퍼만 죽이고 실제 자식 프로세스는 안 죽는 문제를 우회) — 행(hang) 방지 주장과 일치.
- `python scripts\generate_system_index.py` 전체 재실행: 8개 프로젝트 전량 `OK`, 0 failing.
