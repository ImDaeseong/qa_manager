# qa_manager — 검수 시스템

**🤔 [쉬운 설명 보기](https://imdaeseong.github.io/qa_manager/ELI5.html)** — 비개발자를 위한 한 페이지 요약

**바로가기 →** [imdaeseong.github.io/qa_manager](https://imdaeseong.github.io/qa_manager/)

> 문서 구성: 목적 → 시스템 구조/계층 → 작동 흐름 → 실행 방법 → 프로젝트 추가 방법 → 상용 배포 준비도 → 현재 등록 현황 → 검증됨

**구조 문서 →** [qa-manager-architecture.html](qa-manager-architecture.html)  
**LLM 검수 기준 →** [LLM_QA_STANDARD.md](LLM_QA_STANDARD.md)  
**보안·해킹·네트워크 허점 검수 기준 →** [SECURITY_NETWORK_QA_STANDARD.md](SECURITY_NETWORK_QA_STANDARD.md)

여러 독립 프로젝트(저장소)의 requirement · test item · 통과여부를 한 곳에서 보여주는
독립 검수 시스템입니다(특정 프로젝트 소속 대시보드가 아님).

위 링크는 마지막으로 로컬에서 재검사 후 커밋·푸시한 결과이며 실시간이 아닙니다
(최신화하려면 `open_qa_system.bat` 실행 후 커밋·푸시). 생성 HTML에는 로컬 절대경로와
검사 출력의 비밀값을 남기지 않지만, 민감한 내부 프로젝트의 이름·검사 명령 자체도
공개 정보가 될 수 있으므로 등록 전에 사람이 검토합니다.

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

재검사 없이 마지막 생성 결과만 보려면 위 "바로가기" 링크로 보거나, 로컬 폴더에서
`index.html`을 더블클릭합니다. GitHub.com 저장소 화면에서 파일명을 클릭하면
원문 코드(blob) 화면이 열릴 뿐 렌더링되지 않으니, 렌더링된 페이지는 항상 위
"바로가기" 링크로 봅니다.

## 프로젝트 추가 방법

1. `projects/<프로젝트명>/checklist.yaml`을 새로 만듭니다. 스키마는
   `projects/hermes-agents/checklist.yaml` 상단 주석을 따릅니다.
2. `repo_root`를 반드시 지정합니다 — qa_manager 상위 폴더
   (`C:\Users\cs930\Desktop`) 기준 상대경로 (예: `hermes-agents`, `ai_test1`).
3. test_item은 그 프로젝트에 실제로 존재하는 것만 등록합니다(기존 테스트,
   lint 설정, CI workflow, 가드 스크립트 등) — 없는 검사를 지어내지 않습니다.
4. `python scripts\generate_system_index.py`로 새 프로젝트가 index.html에
   나타나고 검사가 실제로 통과/실패하는지 확인합니다.

## 상용 배포 준비도

검수(요구사항 통과)가 끝났다고 곧 상용 판매·배포가 가능하다는 뜻은 아닙니다. hermes-agents
AGENTS.md의 "Commercial-Grade Baseline" 절(ISO/IEC 25010을 1인 유지보수자가 실제로 돌릴 수 있는
게이트로 번역한 것)을 기준으로, 각 프로젝트가 다섯 가지 축을 실제로 갖췄는지 매 실행마다 확인합니다.

| 축 | 뜻 |
|---|---|
| 기능 적합성 | 배포되는 동작마다 자동화된 테스트가 있는가 |
| 보안 | OWASP ASVS Level 1 기준(추적되는 파일에 비밀값 없음, 신뢰 경계마다 입력 검증) |
| 신뢰성 | 외부 호출 실패가 원인과 함께 로그로 남는가 |
| 유지보수성 | 목적을 설명하는 README와 실행 가능한 검증 명령이 있는가 |
| 이식성 | 머신 특유의 설정 없이 클린 체크아웃에서 실행되는가 |

`checklist.yaml`의 각 requirement에 `quality_dimension: <축 이름>`을 선택적으로 붙이면(스키마는
`projects/hermes-agents/checklist.yaml` 상단 주석 참고), `scripts/_checklist_lib.commercial_readiness()`가
그 축에 연결된 요구사항이 있는지·전부 통과했는지를 매 실행마다 집계합니다. 다섯 축 전부 요구사항이
있고 전부 통과해야 "상용 판매·배포 가능"이며, 결과는 `index.html`과 각 프로젝트 `dashboard.html`
상단 박스에 표시됩니다. **축에 연결된 요구사항이 하나도 없으면 "미검토"로 표시됩니다 — 통과한 검사가
아니라 애초에 물어본 적이 없다는 뜻**이며, 이게 실제 부족한 부분입니다(없는 검사를 지어내 채우지
않습니다).

2026-09-20 최초 적용 기준, 9개 프로젝트 중 `ai_prompt` 1개만 다섯 축을 전부 충족했습니다. 나머지는
아래처럼 미검토 축이 남아 있습니다(재검사 없이 기록만 한 값이니 최신 상태는 `index.html` 참고):

| 프로젝트 | 미검토/미달 축 |
|---|---|
| ai_prompt | 없음 (상용 배포 가능) |
| hermes-agents | 신뢰성 |
| ai-workspace | 이식성 |
| skills | 이식성 |
| ai_agent | 신뢰성, 이식성 |
| ai_test1 | 신뢰성, 이식성 |
| ai_test | 신뢰성, 유지보수성, 이식성 |
| ai_test2 | 신뢰성, 유지보수성, 이식성 |
| qa_manager | 기능 적합성, 이식성 |

"이식성"이 가장 많이 미검토로 남은 이유: 클린 체크아웃에서 실제로 실행되는지를 검증하려면 Docker 등
격리된 재현 환경이 필요한데, 현재 등록된 어떤 프로젝트도 그런 검사를 갖추고 있지 않습니다(지어낼
수 없어 기록만 함). "신뢰성"은 외부 API를 직접 호출하는 로직이 있는 프로젝트(`ai_prompt`,
`ai-workspace`)에서만 실제로 검증됐고, 로컬 도구·정적 스캐너 위주인 나머지 프로젝트에는 아직 그런
검사가 없습니다. `ai_test`/`ai_test2`의 "유지보수성" 미검토는 두 저장소 모두 저장소 전체를 아우르는
README 기반 검증 명령이 없고(하위 프로그램별 개별 명령만 존재) 헤더 주석에 그렇게 명시돼 있어 실제
현황과 일치합니다.

## 현재 등록된 프로젝트

hermes-agents, ai_prompt, ai-workspace, skills, ai_test, ai_test1, ai_test2, ai_agent,
qa_manager — 총 9개. 실시간 통과/실패 현황은 `index.html`을 열어 확인합니다.

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

qa_manager 자신의 회귀 테스트·필수 문서 검사·보안 허점 자기검사는 2026-09-18부터
`.github/workflows/validate.yml`로 매 push마다 자동 실행됩니다(다른 8개 형제
프로젝트는 이 저장소에 없으므로 CI 대상이 아니며, 재검사하려면 로컬에서
`open_qa_system.bat`을 실행합니다).
- `python scripts\generate_system_index.py` 전체 재실행(2026-09-18): 9개 프로젝트 전량 `OK`, 0 failing.
