# ai_test1 무료 소스 공개 검토

## 2026-09-21 추적 이력과 미디어 권리

- 기준 커밋 `cbc8ac77`의 추적 파일 1,453개를 검사했다. 제작 이력 `aim_music_mp4_app/data/production_history.jsonl`에 곡 이름·출력 경로·검증 메모를 포함한 20건이 있었다. `ai_test1@dc2129be`에서 Git 추적을 해제하고 `.gitignore`와 `[TRACKED-PRODUCTION-HISTORY]` 회귀 검사를 추가했다. 로컬 원본은 보존했다.
- 사용자 홈 경로가 있는 추적 문서 4개(5줄)를 이식 가능한 예시로 바꾸고 `[LOCAL-HOME-PATH]` 검사를 추가했다. 현재 추적 목록 재검사에서 제작 이력 0건, 사용자 홈 경로 0건이며 관련 55개 테스트와 보안 검사가 통과했다.
- PNG 140개와 MP4 4개가 계속 추적된다(`aim_music_mp4_app` 80개, `aim_music_app` 53개, `aim_music_character_app` 11개). 파일별 원본·생성 조건·재배포 권리는 확인 전이다. 루트 `LICENSE`·`NOTICE`·`ATTRIBUTION`도 없다. 미디어 포함 여부와 직접 작성 코드의 라이선스는 이 저장소에 맞춰 별도로 결정해야 한다.
- 과거 Git 커밋에 들어간 제작 이력은 HEAD에서 제거해도 기록에 남을 수 있다. 원격 저장소의 공개 범위와 이력 정리 필요성은 확인 전이며, 공개 출시 판단은 **HOLD**다. 이력 강제 재작성은 실시하지 않았다.

상태: **HOLD**. 기준 커밋 `dc2129be`의 13개 독립 창작 도구·스킬 소스를 전세계에 무료 공개하는 검토다. 실행 제품과 생성물 배포는 별개다. `README.md`와 현재 체크리스트의 근거를 대조했으며 영역별 결정은 모두 `pending`이다.

## 기능 적합성
- 근거: README는 13개 프로젝트별 실행법과 테스트를 안내한다. 남은 검토: 각 도구의 대표 창작 과업·입력·출력 수용 기준을 확인한다.

## 성능 효율성
- 근거: MP4 렌더링과 LLM 생성은 작업 시간·자원 사용이 다르다. 남은 검토: 입력 길이·영상 길이별 시간·메모리·비용 목표를 측정한다.

## 호환성
- 근거: Windows PowerShell·Python 3, 일부 FFmpeg/FFprobe·OpenRouter가 필요하다. 남은 검토: 프로젝트별 지원 버전·브라우저·코덱 조합을 설치해 실행한다.

## 상호작용 능력
- 근거: CLI·웹 UI·문서형 스킬이 혼재한다. 남은 검토: 각 사용 흐름과 오류 안내, 웹 UI의 키보드·보조기술 접근성을 평가한다.

## 신뢰성
- 근거: README에 프로젝트별 단위 테스트가 있다. 남은 검토: 렌더 중단·디스크 부족·API 실패 시 부분 파일 정리와 안전한 재실행을 시험한다.

## 보안
- 근거: 체크리스트에 보안 검사가 연결되어 있고 README는 실제 `.env`·API 키를 커밋하지 않도록 안내한다. 남은 검토: 외부 요청, 파일 경로, 사용자 환경변수 설정 스크립트의 공개 사용 경계를 확인한다.

## 유지보수성
- 근거: 각 프로젝트의 README와 별도 테스트 명령이 있다. 남은 검토: 외부 사용자가 하나씩 설치·변경·테스트·문제 진단을 재현한다.

## 유연성 이식성
- 근거: 실행 의존성이 없는 문서형 프로젝트와 외부 도구가 필요한 앱이 분리된다. 남은 검토: 빈 Windows 환경과 지원할 다른 플랫폼에서 프로젝트별 설치·실행을 확인한다.

## 안전성
- 근거: 생성 결과와 입력이 로컬 `output/`, `input/`에 저장될 수 있다(`README.md`). 남은 검토: 덮어쓰기·삭제·부분 생성·잘못된 공개의 위해를 평가한다.

## 실사용 품질
- 근거: README는 정서·매력·저작권·플랫폼 정책을 자동 테스트로 판단할 수 없다고 밝힌다. 남은 검토: 실제 창작자가 결과물과 작업 흐름을 평가한다.

## 개인정보 데이터 거버넌스
- 근거: 입력과 생성 결과가 로컬 폴더에 저장될 수 있다. 남은 검토: 공개 저장소의 실제 입력·출력·로그와 API 전송·보관·삭제 경로를 확인한다.

## 공급망 라이선스
- 근거: 루트 `LICENSE`는 확인되지 않았고 FFmpeg·OpenRouter 등 외부 구성요소와 미디어를 사용한다. 남은 검토: 프로젝트별 코드·미디어·생성물·의존성의 권리를 확인한다.

## 배포 운영
- 근거: 프로젝트별 실행·테스트 절차가 있다. 남은 검토: 공개 전 파일 검토, 릴리스 재현, 문제 신고, 수정·롤백·지원 절차를 정한다.

## 법률 규제
- 근거: 전세계 무료 공개를 검토하며 창작물·외부 API·사용자 입력이 관련된다. 남은 검토: 저작권·개인정보·플랫폼 약관과 관할별 의무를 검토한다. 이 문서는 법률 적합성 판단이 아니다.

## 사업 운영
- 근거: README는 개인 창작 자동화 작업 공간으로 소개한다. 남은 검토: 지원할 13개 프로젝트, 대상 사용자, 문의 경로와 담당자를 정한다.

## 2026-09-21 source-only scope update

- Owner decision: publish source code only worldwide; exclude images, audio, video, and executables.
- `ai_test1@ffc86e61` removed 144 media/executable files from the Git index; all 144 local originals were retained. `.gitignore` excludes their extensions. `python scripts/check_source_only.py` reports 0 tracked files and its negative test rejects a staged PNG.
- Impacted tests: 174 passed. Fresh clones must supply their own media for media-dependent workflows.
- HOLD remains: earlier public Git history still contains excluded files, source-code and dependency license decisions are unresolved, and the 15 release areas still need human review. Removing files at HEAD does not erase older commits.

## 2026-09-21 extended source-only audit

- `ai_test1@6a868852`: no additional tracked media were found; `.gitignore` and the tracked-media guard now also cover ICO, SVG, FLAC, subtitle/lyric files, and Visual Studio build-state extensions. A staged FLAC is rejected in a negative check; HEAD reports zero tracked media.
- HOLD: old Git history, original-code license, dependency notices, and human release checks remain open.
