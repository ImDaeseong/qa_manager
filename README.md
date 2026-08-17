# qa_manager — 검수 시스템

여러 독립 프로젝트(저장소)의 requirement · test item · 통과여부를 한 곳에서
보여주고 관리하는 시스템입니다. 특정 프로젝트에 속한 대시보드가 아니라,
그 자체로 독립된 검수 시스템입니다.

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

hermes-agents, ai_prompt, ai-workspace, skills, ai_test, ai_test1, ai_test2,
ai_test3 — 총 8개. 실시간 통과/실패 현황은 `index.html`을 열어 확인합니다.
