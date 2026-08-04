# qa_manager — 검수 시스템

여러 독립 프로젝트(저장소)의 요구사항·검사항목·통과여부를 한 곳에서 보여주고
관리하는 시스템입니다. 특정 프로젝트에 속한 대시보드가 아니라, 그 자체로
독립된 검수 시스템입니다.

## 왜 별도 위치인가

qa_manager는 검사 대상 프로젝트들과 형제 폴더로 존재합니다
(`C:\Users\cs930\Desktop\qa_manager`), 그중 어느 하나(예: hermes-agents)
안에 속해 있지 않습니다. 여러 독립 저장소를 검사하는 시스템이 그중 한
저장소 안에 종속되면, 다른 저장소를 검사할 때도 그 저장소 하나를 기준으로
경로를 계산해야 하는 구조적 모순이 생기기 때문입니다.

## 시스템 구조

```
qa_manager/                       (독립 git 저장소, github.com/ImDaeseong/qa_manager)
  index.html                      생성됨 — 전체 프로젝트 목록 + 통과/실패 요약 (시작점)
  open_qa_system.bat              전체 재검사 + index.html 열기 (더블클릭 실행)
  scripts/                        검사 도구 (프로젝트별 데이터는 없음)
    _checklist_lib.py             checklist.yaml 로드, repo_root 경로 계산, check 명령 실행
    _style.py                     index.html/dashboard.html 공통 디자인(CSS)
    run_checklist.py              프로젝트 1개를 터미널에 텍스트로 보고
    generate_checklist_dashboard.py   프로젝트 1개의 dashboard.html 생성
    generate_system_index.py      전체 프로젝트를 스캔해 index.html 생성
  projects/
    <프로젝트명>/
      checklist.yaml              요구사항 -> 개발항목 -> 검사항목 + repo_root 경로
      dashboard.html               생성됨 (직접 수정하지 않음)
```

**계층 구조**: 요구사항(requirement) 아래에 개발항목(dev_item), 그 아래에
실제 실행 가능한 검사항목(test_item)이 있습니다. 검사항목 하나가
`check:` 명령을 갖고, 그 명령이 통과해야 개발항목이 통과, 개발항목이 전부
통과해야 요구사항이 통과로 집계됩니다. 화면에 보이는 설명 문구는 개발자가
아닌 운영 담당자도 읽고 이해할 수 있도록 평범한 한글로 작성합니다 —
전문 용어나 코드 오류 메시지를 그대로 노출하지 않습니다.

**핵심 원칙 — 항상 실행 결과, 기록값 아님**: `checklist.yaml`의
`status`/`last_verified`는 마지막으로 실행했을 때의 기록일 뿐입니다.
`run_checklist.py`나 `generate_checklist_dashboard.py`를 실행하면 매번
`check:` 명령을 **그 자리에서 실제로 다시 실행**해서 결과를 보여줍니다.
화면에 보이는 PASS/FAIL은 항상 방금 실행한 결과입니다.

## 환경 관련 참고사항

- **실행 위치 분리**: qa_manager 스크립트 자신은 `qa_manager/` 폴더에서
  시작하지만, 각 검사항목의 `check` 명령은 그 프로젝트의 실제 폴더
  (`repo_root`, qa_manager의 상위 폴더 `C:\Users\cs930\Desktop` 기준
  상대경로)에서 실행됩니다. 예: `ai_test1`의 검사는
  `C:\Users\cs930\Desktop\ai_test1`에서 실행됩니다.
- **OS/셸**: Windows 10, PowerShell 스크립트(`.ps1`)와 Python 스크립트가
  섞여 있으며, `check:` 명령은 `cmd.exe`에서 실행됩니다(`cd X && Y`,
  `powershell.exe -NoProfile -File ...` 형태로 작성).
- **인코딩**: 이 머신의 콘솔 기본 코드페이지(cp949)가 npm/eslint 등이
  출력하는 UTF-8/유니코드 문자를 그대로 처리하지 못해 초기 버전에서 두
  차례 크래시가 발생했습니다 — `_checklist_lib.py`는 `check` 명령의
  출력을 `encoding="utf-8", errors="replace"`로 읽고, `run_checklist.py`는
  콘솔에 출력할 때도 `errors="replace"`로 재설정합니다. 새 프로젝트를
  추가할 때 이 부분을 건드릴 필요는 없습니다.
- **자동 실행 없음**: qa_manager는 어떤 프로젝트의 커밋/작업 시작에도
  자동으로 걸리지 않습니다. 각 프로젝트 자신의 pre-commit 훅과 별개로,
  필요할 때 사람이 직접 실행하는 도구입니다(자동 훅으로 연결하면 각
  프로젝트가 자기 훅에서 이미 실행하는 검사를 qa_manager가 다시 실행해
  중복이 발생하므로 의도적으로 분리했습니다).

## 실행 방법

```
open_qa_system.bat                                              # 전체 재검사 + 브라우저로 index.html 열기
python scripts\generate_system_index.py                         # 전체 프로젝트 재검사 + index.html 생성
python scripts\generate_checklist_dashboard.py [checklist.yaml] # 프로젝트 1개만 재검사
python scripts\run_checklist.py [checklist.yaml]                 # 프로젝트 1개를 터미널 텍스트로 보고
```

## 프로젝트 추가 방법

1. `projects/<프로젝트명>/checklist.yaml`을 새로 만듭니다. 스키마와 필드
   설명은 `projects/hermes-agents/checklist.yaml` 상단 주석을 그대로
   따릅니다.
2. `repo_root`를 반드시 지정합니다 — `C:\Users\cs930\Desktop` 기준 상대경로
   (예: `hermes-agents`, `hermes-agents/ai_prompt`, `ai_test1`, `skills`).
3. 검사항목은 그 프로젝트에 **실제로 존재하는** 것만 등록합니다(기존
   테스트, lint 설정, CI 워크플로, 가드 스크립트 등). 없는 검사를
   지어내지 않습니다 — 프로젝트 코드를 직접 읽고 확인한 뒤에만 추가합니다.
4. `python scripts\generate_system_index.py`를 실행해 새 프로젝트가
   index.html에 나타나는지, 검사가 실제로 통과/실패하는지 확인합니다.

## 현재 등록된 프로젝트 (2026-08-05 기준)

hermes-agents, ai_prompt, ai-workspace, skills, ai_test, ai_test1, ai_test2,
ai_test3 — 총 8개. 실시간 통과/실패 현황은 `index.html`을 열어 확인합니다
(고정된 숫자를 여기 문서에 적지 않는 이유는, 그 숫자가 다음 실행 때마다
바뀔 수 있는 실시간 값이기 때문입니다).
