# ai_prompt 무료 소스 공개 검토

## 2026-09-21 제3자 스킬 라이선스 확인

- 후속 기준 커밋 `b707c1f`: `alirezarezvani/claude-skills`에서 가져온 고문 스킬 10개에 [`NOTICE.md`](https://github.com/ImDaeseong/ai_prompt/blob/main/NOTICE.md)를 연결하고, [공식 MIT 허락·저작권 고지](https://github.com/alirezarezvani/claude-skills/blob/main/LICENSE)와 본문 일치를 확인했다. `skill_creator.md`와 `web_artifacts_builder.md`에도 원본과 같은 Apache 2.0 `LICENSE.txt` 참조를 명시했다.
- 추적 문서 3곳의 개인 PC 홈 경로를 상대적인 저장소 경로로 바꾸고, Markdown/HTML의 로컬 홈 경로를 잡는 회귀 검사를 추가했다. 추적 문서 재검사 결과 해당 경로 0건, `scripts/verify_repo.ps1` 통과(114개 스킬 포함).
- `doc_coauthoring.md`는 원본 [`anthropics/skills/doc-coauthoring`](https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md)을 참고한 이력이 있지만, 그 폴더의 개별 LICENSE 파일을 확인하지 못했다. [원본 저장소 README](https://github.com/anthropics/skills/blob/main/README.md)는 많은 스킬이 Apache 2.0이라고만 설명한다. 이 파일과 다른 외부 자료의 배포 권리는 계속 **HOLD**.

- `antigravity_test/skills/internal_comms.md`와 `claude_api_skill.md`의 누락된 라이선스 참조는 `ai_prompt@4429b68`에서 같은 디렉터리의 `LICENSE.txt`를 포함해 해결했다. `scripts/validate_skills.ps1`에 누락 검사와 회귀 테스트를 추가했다.
- 원본 `anthropics/skills`의 [`internal-comms/LICENSE.txt`](https://github.com/anthropics/skills/blob/main/skills/internal-comms/LICENSE.txt)와 [`claude-api/LICENSE.txt`](https://github.com/anthropics/skills/blob/main/skills/claude-api/LICENSE.txt)는 동일한 Apache License 2.0 본문을 포함한다. 추가된 파일은 원본과 줄 단위 내용이 일치했다. 스킬 본문의 원본 버전·수정 범위와 다른 외부 자료의 권리는 추가 확인이 필요하다.
- 저장소 루트에도 `LICENSE`, `NOTICE`, `ATTRIBUTION` 추적 파일이 없다. 프로젝트 전체를 어떤 조건으로 무료 재사용 허용할지는 아직 확정되지 않았다.
- 검증: `scripts/verify_repo.ps1` 통과(114개 스킬, 링크, 보안 패턴, 회귀 검사와 부작용 검사). 조치 기준: 나머지 외부 스킬의 원본 버전·수정 이력과 고지를 확인하고 프로젝트 전체의 재사용 조건을 결정한다. 검토 완료 전 출시 승인을 기록하지 않는다.

상태: **HOLD**. 기준 커밋 `b707c1f`의 프롬프트·스킬 자료를 전세계에 무료 공개하는 검토다. `README.md`에 따르면 직접 작성한 자료와 외부 자료를 참고·보완한 스킬이 함께 있다. 공개 재사용 조건과 외부 자료 권리가 확인되기 전에는 전체 저장소 출시를 승인하지 않는다. 아래 내용은 `README.md`와 현재 체크리스트의 1차 대조이며 전 영역의 결정은 `pending`이다.

## 기능 적합성
- 근거: 체크리스트는 스킬 구조와 참조·링크 검사를 실행한다. 남은 검토: 실제 프롬프트 과업의 성공 기준과 표본 평가를 정의한다.

## 성능 효율성
- 근거: `README.md`는 프롬프트 성능을 자동 검사가 보장하지 않는다고 밝힌다. 남은 검토: 대표 과업의 응답 시간·토큰·비용 목표와 반복 측정을 기록한다.

## 호환성
- 근거: 검증 명령은 Git과 Windows PowerShell을 요구한다. 남은 검토: 지원할 AI 도구·모델·OS 조합과 실제 로딩 결과를 확인한다.

## 상호작용 능력
- 근거: README는 스킬 색인과 입력 작성 순서를 안내한다. 남은 검토: 처음 사용하는 사람이 적절한 스킬을 찾아 실행·오류를 이해하는지 평가한다.

## 신뢰성
- 근거: 체크리스트는 검증 부작용과 링크·훅 회귀를 검사한다. 남은 검토: 모델 응답 변동과 외부 도구 실패에서 결과의 일관성·복구를 평가한다.

## 보안
- 근거: README는 예시에 비밀값·고객·회사 정보를 넣지 않도록 안내하고 보안 검사가 연결되어 있다. 남은 검토: 공개 파일과 외부 자료의 간접 지시·민감정보를 사람과 도구로 확인한다.

## 유지보수성
- 근거: 스킬 구조·참조·로컬 링크 검사와 변경 이력이 있다. 남은 검토: 제3자가 스킬 갱신 후 실행·회귀 검증을 문서만으로 재현한다.

## 유연성 이식성
- 근거: 저장소는 다른 프로젝트에 파일·참조 자료를 제공하는 사용법을 설명한다. 남은 검토: 깨끗한 환경에서 스킬과 상대 참조 경로가 동작하는지 확인한다.

## 안전성
- 근거: 프롬프트는 개발·분석·창작 행동을 유도할 수 있다. 남은 검토: 위험한 도구 호출, 외부 전송, 근거 없는 판단을 요구하는 입력에 대한 안전 경계를 시험한다.

## 실사용 품질
- 근거: 현재 검증은 구조·링크 중심이며 사용자 과업 성과는 체크리스트에 없다. 남은 검토: 실제 사용자의 과업 완료·오류·수정 횟수를 기록한다.

## 개인정보 데이터 거버넌스
- 근거: README는 비밀값·고객·회사 자료를 예시에 넣지 않도록 안내한다. 남은 검토: 전체 공개 파일·예제·참조 자료에서 개인·내부 정보의 포함 여부와 제거 절차를 확인한다.

## 공급망 라이선스
- 근거: README는 외부 자료를 참고·보완한 스킬이 있다고 밝히며 저장소 루트 `LICENSE`는 확인되지 않았다. 남은 검토: 파일별 원저작권·인용·재배포 허락과 스킬이 참조하는 자산의 권리를 확인한다.

## 배포 운영
- 근거: 통합 검증 명령은 문서 구조와 링크를 검사한다. 남은 검토: 릴리스 버전 고정, 공개 전 검토, 잘못된 프롬프트의 회수·수정·공지 절차를 정한다.

## 법률 규제
- 근거: 전세계 무료 소스 공개를 검토하며 외부 자료가 포함된다. 남은 검토: 저작권과 관할별 개인정보·콘텐츠 의무를 검토한다. 이 문서는 법률 적합성 판단이 아니다.

## 사업 운영
- 근거: README는 개인 프롬프트 저장소로 소개한다. 남은 검토: 대상 사용자, 문의 채널, 지원 범위와 공개 후 유지 책임자를 정한다.
