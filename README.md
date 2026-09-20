# qa_manager — 검수 시스템

**🤔 [쉬운 설명 보기](https://imdaeseong.github.io/qa_manager/ELI5.html)** — 비개발자를 위한 한 페이지 요약

**바로가기 →** [imdaeseong.github.io/qa_manager](https://imdaeseong.github.io/qa_manager/)

> 문서 구성: 목적 → 시스템 구조/계층 → 작동 흐름 → 실행 방법 → 프로젝트 추가 방법 → 상용 배포 검토 → 현재 등록 현황 → 검증됨

**구조 문서 →** [qa-manager-architecture.html](qa-manager-architecture.html)  
**LLM 검수 기준 →** [LLM_QA_STANDARD.md](LLM_QA_STANDARD.md)  
**보안·해킹·네트워크 허점 검수 기준 →** [SECURITY_NETWORK_QA_STANDARD.md](SECURITY_NETWORK_QA_STANDARD.md)
**상용 출시 검토 기준 →** [RELEASE_READINESS_STANDARD.md](RELEASE_READINESS_STANDARD.md)
**qa_manager 출시 검토 기록 →** [QA_MANAGER_RELEASE_REVIEW.md](QA_MANAGER_RELEASE_REVIEW.md)

소스코드에는 [MIT 라이선스](LICENSE)를 적용합니다. 출시 검토는 현재 [HOLD](QA_MANAGER_RELEASE_REVIEW.md) 상태입니다.
주 사용자는 전세계 개발자·QA 담당자로 두고 있습니다. 사용 중 발견한 문제와 기능 제안은 [GitHub Issues](https://github.com/ImDaeseong/qa_manager/issues)에 남길 수 있습니다. 답변 시간은 보장하지 않으며, 공개 이슈에 비밀번호·토큰·개인정보·내부 로그를 올리지 마세요.

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

`open_qa_system.bat` 실행 시: `generate_system_index.py`가 `projects/*/checklist.yaml`을 전부 찾음 → 각 파일의 `repo_root`를 실제 폴더 경로로 바꿈(예: `ai_test1` → `../ai_test1`) → 그 폴더 안에서 test_item의 `check` 명령을 **지금 이 순간 직접 실행**(`pytest`, `npm run lint`, PowerShell 가드 스크립트 등 프로젝트에 실제로 있는 명령 — `checklist.yaml`의 `status`/`last_verified`는 참고용 마지막 기록일 뿐, 매번 다시 실행함) → 아래에서 위로 집계 → 프로젝트별 `dashboard.html`과 전체 `index.html`을 씀.

## 실행 방법

Python 의존성 설치: `python -m pip install -r requirements.txt`.
기본 체크리스트 9개는 이 작업공간의 형제 저장소를 검사합니다. `qa_manager`만 새로 복제한 환경에서는 그 저장소들이 없어 전체 재검사가 실행되지 않습니다. 다른 환경에서 재사용하려면 실제 검사할 저장소를 함께 준비하고 `repo_root`와 검사 명령을 조정한 뒤 공개 허용 목록을 검토하세요. 공개된 HTML은 마지막으로 생성된 결과를 읽을 수 있습니다.

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
   공개 HTML에 프로젝트 이름·설명·검사 명령을 포함해도 되는지 검토한 뒤
   `scripts/_checklist_lib.py`의 `PUBLIC_PROJECTS`에 이름을 추가합니다.
2. `repo_root`를 반드시 지정합니다 — qa_manager 상위 폴더
   (`..`) 기준 상대경로 (예: `hermes-agents`, `ai_test1`).
3. test_item은 그 프로젝트에 실제로 존재하는 것만 등록합니다(기존 테스트,
   lint 설정, CI workflow, 가드 스크립트 등) — 없는 검사를 지어내지 않습니다.
4. `python scripts\generate_system_index.py`로 새 프로젝트가 index.html에
   나타나고 검사가 실제로 통과/실패하는지 확인합니다.

## 상용 배포 검토

기준과 1차 근거는 [RELEASE_READINESS_STANDARD.md](RELEASE_READINESS_STANDARD.md)에 정리했습니다.
현행 ISO/IEC 25010:2023의 9개 제품 품질 특성과 실사용 품질, 개인정보, 공급망·라이선스, 배포·운영,
법률·규제, 사업 운영까지 **15개 영역**을 검토합니다. 종전 5개 축의 자동 검사 통과는 부분 근거였으므로
그것만으로 상용 배포 가능을 선언하지 않습니다. `checklist.yaml`의 `quality_dimension`은 검사 결과를
영역에 연결하지만 전체 영역의 검토 완료를 뜻하지 않습니다.

각 프로젝트는 출시 범위(`release`, `audience`, `distribution`, `jurisdictions`)와 15개 영역의 결정·근거,
승인자·승인일·승인 근거를 `release_review`에 기록해야 합니다. 비적용 결정에는 이유를 적습니다.
연결된 검사에 실패했거나 근거가 빠졌으면 **출시 검토 보류**로 표시합니다. 기록을 모두 채워도
화면은 **출시 검토 근거 완료**까지만 표시하며 최종 배포 결정은 별도입니다. 현재 등록된 프로젝트에는
승인된 전체 출시 검토 기록이 없으므로 모두 보류입니다. 없는 검사를 만들어 통과로 표시하지 않습니다.

정적 보고서는 완성된 임시 파일을 교체하는 방식으로 기록하며, 공개 전 사용자 홈 경로와 자격증명 형태의 문자열을 검사합니다. 이 패턴 검사는 모든 민감 정보를 식별하지 못하므로 프로젝트 이름·검사 명령과 결과의 공개 적합성은 사람이 확인해야 합니다.
검사 실패의 상세 출력은 공개 HTML에 넣지 않습니다. 로컬에서 `python scripts\run_checklist.py projects\<프로젝트명>\checklist.yaml`로 확인합니다.

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
