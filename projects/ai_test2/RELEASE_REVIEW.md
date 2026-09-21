# ai_test2 무료 소스 공개 검토

## 2026-09-21 창작 입력과 미디어 권리

- 기준 커밋 `fa88c21`의 Git 추적 파일 891개를 점검했다. `ai_anime/input/` 239개, `ai_img_video_aiBoygirl/input/` 238개, `ai_img_video_prompt_capcut/input/` 15개는 곡 텍스트·음원·자막·영상 클립 등의 작업 입력이다. `ai_test2@afc9cbe`에서 492개 전부 Git 추적을 해제하고 로컬 원본은 보존했다. 세 폴더에 `.gitkeep`을 두고 재추적을 거부하는 `[TRACKED-USER-INPUT]` 검사를 추가했다.
- 공개 문서 3개의 사용자 홈 경로 11줄을 이식 가능한 예시로 바꾸고 `[LOCAL-HOME-PATH]` 회귀 검사를 추가했다. 현재 HEAD는 추적 파일 402개, 입력 데이터 추적 0건, 홈 경로 검사 0건이다.
- 검증: 보안 회귀 검사 12개와 세 프로젝트의 독립 테스트 77개·337개·65개 통과. 세 프로젝트를 한 pytest 호출로 묶으면 동일한 `main.py` 이름 때문에 수집 충돌이 발생하므로 각각의 폴더에서 실행했다. Boygirl 테스트는 기존 `.pytest_tmp` 접근 오류를 피해 새 임시 디렉터리 `--basetemp`로 재실행해 통과했다.
- 참조 PNG 35개와 테스트 음원 3개(MP3 2개·WAV 1개)는 계속 추적된다. 파일별 원본·생성 조건·재배포 허락과 이 저장소의 코드 라이선스는 확인 전이다. 과거 Git 이력의 492개 입력도 HEAD 변경으로 지워지지 않으므로 원격 공개 범위와 이력 조치 여부를 따로 확인해야 한다. 출시 판단은 **HOLD**다.

상태: **HOLD**. 기준 커밋 `afc9cbe`의 6개 독립 프로젝트 소스를 전세계에 무료 공개하는 검토다. `README.md`와 `SPEC.md`의 저장소 범위, 현재 체크리스트를 1차 대조했다. 채용 적합도 분석과 미디어 제작은 데이터·권리 경계가 달라 개별 제품 출시는 별도로 판단한다. 아래 15개 영역은 모두 `pending`이다.

## 기능 적합성
- 근거: 프로젝트별 실행·검증 명령이 README에 있다. 남은 검토: 6개 프로젝트별 사용자 과업·결과 정확도·오류 조건을 정하고 실제 입력으로 확인한다.

## 성능 효율성
- 근거: 미디어 처리, 음악 분석, 웹 분석의 부하가 다르다. 남은 검토: 프로젝트별 입력 규모와 시간·메모리·비용 목표를 반복 측정한다.

## 호환성
- 근거: Windows PowerShell, Python 버전 차이, CareerDiff의 Node.js/npm, 선택적 CapCut이 명시돼 있다. 남은 검토: 지원 플랫폼·브라우저·외부 도구 조합을 빈 환경에서 실행한다.

## 상호작용 능력
- 근거: CLI와 웹 UI가 함께 있다. 남은 검토: 오류 안내와 사용 흐름, CareerDiff·음악 분석 UI의 키보드·보조기술 접근성을 확인한다.

## 신뢰성
- 근거: README에 프로젝트별 테스트가 있다. 남은 검토: 외부 API 실패, 입력 누락, 렌더 중단, 반복 실행과 복구를 검증한다. 이전 전체 검사에서 CareerDiff의 일시적 실패 원인은 아직 확인되지 않았다.

## 보안
- 근거: 체크리스트에 보안 검사가 연결되어 있고 `SECURITY_BOUNDARY.md`가 있다. 남은 검토: 로컬 파일·업로드·API 키·외부 메타데이터와 브라우저 입력 경계를 프로젝트별로 확인한다.

## 유지보수성
- 근거: README·SPEC·ARCHITECTURE·VERIFICATION 문서와 테스트 명령이 있다. 남은 검토: 제3자가 프로젝트별 의존성 설치, 테스트, 버전 갱신을 재현한다.

## 유연성 이식성
- 근거: 프로젝트별 런타임과 선택적 미디어 도구가 나뉘어 있다. 남은 검토: 지원 플랫폼에서 개별 프로젝트를 다른 프로젝트 없이 설치·실행한다.

## 안전성
- 근거: 미디어 파일과 채용 판단 자료가 입력되며 생성 결과는 로컬 폴더에 남을 수 있다. 남은 검토: 입력·출력 덮어쓰기, 민감 자료 공개, 채용 결과 오해의 위해와 안전 안내를 점검한다.

## 실사용 품질
- 근거: 개발 테스트는 있으나 실제 사용자 과업 성과는 현재 체크리스트에 없다. 남은 검토: 제작자·구직자 등 대상별 결과 이해도와 오류 대응을 평가한다.

## 개인정보 데이터 거버넌스
- 근거: README는 `uploads/`, `CareerDiff/data/` 등 개인 입력 저장 가능 경로를 명시한다. 남은 검토: 공개 저장소·샘플·로그와 실행 중 수집·전송·보관·삭제 절차를 확인한다.

## 공급망 라이선스
- 근거: 루트 `LICENSE`는 확인되지 않았고 음악·가사·영상·외부 서비스가 관련된다. 남은 검토: 코드·의존성·입력 자산·생성물 재배포 권리를 각각 확인한다.

## 배포 운영
- 근거: README와 VERIFICATION 문서에 로컬 검증 경로가 있다. 남은 검토: 공개 릴리스 재현, 장애·취약점 신고, 롤백·지원 책임을 정한다.

## 법률 규제
- 근거: 전세계 무료 공개를 검토하며 채용 분석과 저작물 처리 프로그램이 포함된다. 남은 검토: 개인정보·채용 관련 의무, 저작권·플랫폼 약관을 관할별로 검토한다. 이 문서는 법률 적합성 판단이 아니다.

## 사업 운영
- 근거: 6개 독립 프로젝트 모음이다. 남은 검토: 각 프로젝트의 대상 사용자, 문의 채널, 지원·유지 책임 범위를 정한다.

## 2026-09-21 source-only scope update

- Owner decision: publish source code only worldwide; exclude images, audio, video, and executables.
- `ai_test2@540ce35` removed 38 media/executable files from the Git index; all 38 local originals were retained. `.gitignore` excludes their extensions. `python scripts/check_source_only.py` reports 0 tracked files and its negative test rejects a staged PNG.
- Impacted tests: 444 passed, 4 skipped. Fresh clones must supply their own media for media-dependent workflows.
- HOLD remains: earlier public Git history still contains excluded files, source-code and dependency license decisions are unresolved, and the 15 release areas still need human review. Removing files at HEAD does not erase older commits.
