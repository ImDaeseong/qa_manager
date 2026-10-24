# 운영 준비도 검수 기준

## 목적과 경계

사용 사례: 나는 등록된 프로젝트를 사용자에게 열기 전에, 비밀값이 브라우저로 나가지 않는지, DB 권한이 과하지 않은지, 핵심 기능에 테스트가 있는지, (공개 서비스라면) 장애 알림과 백업·복원 흔적이 있는지를 `scripts/check_operational_readiness.py`로 확인한다.

이 검사는 소스에 남은 **흔적의 유무**만 본다. 알림 연동 코드가 있다고 알림이 실제로 오는 것도, 백업 스크립트가 있다고 복원이 되는 것도 증명하지 못한다. 그 부분은 사람이 시험하고 기록해야 한다.

## 검사 규칙

| ID | 근거 | 패턴 | 적용 계층 |
|---|---|---|---|
| OP1 | CWE-540 / CWE-798 | 클라이언트로 내려가는 접두사(`NEXT_PUBLIC_`, `VITE_`, `REACT_APP_` 등) 환경변수 이름에 SECRET·PRIVATE·PASSWORD·TOKEN·API_KEY·SERVICE_ROLE·CREDENTIAL이 들어감. 브라우저용 소스에 실제 형식의 키, 비공개 키, `service_role`이 있음. 이름에 PUBLISHABLE·ANON·PUBLIC_KEY·SITE_KEY·CLIENT_ID·ANALYTICS가 있으면 공개 전제로 보고 제외 | 전부 |
| OP2 | CWE-250 | SQL `GRANT` 문으로 모든 권한(ALL PRIVILEGES)을 부여, 또는 root·postgres·sa·admin 계정으로 로그인하는 DB 연결 URL | 전부 |
| OP3 | 이 저장소의 정책 | 결제·계정(가입, 로그인, 비밀번호) 코드가 있는데 그 기능을 언급하는 테스트가 없음 | 전부 |
| OP4 | NIST SP 800-53 AU-5, SI-4 | 오류 알림 연동(Sentry, SMTP, Slack·Discord·Telegram 웹훅 등)과 알림 시험 기록이 없음 | T2만 |
| OP5 | NIST SP 800-53 CP-9, CP-9(1), CP-10 | 백업 도구, 자동 일정, 복원 시험 기록이 없음 | T2만 |

수용한 위험은 같은 줄에 `qa:allow <CWE-ID> - <사유>`로 적는다(`check_qa_allow_audit.py`가 형식을 감사한다).

## 근거 (2026-10-24에 원문 확인)

- NIST SP 800-53 Rev. 5 (OSCAL 카탈로그 5.2.0, 2026-10-22 수정본을 직접 내려받아 확인)
  - AU-5 "Response to Audit Logging Process Failures": 감사 로깅 처리 실패 시 정해진 담당자에게 정해진 시간 안에 알린다.
  - SI-4 "System Monitoring": 공격과 무단 연결을 탐지하도록 시스템을 감시한다.
  - CP-9 "System Backup": 사용자·시스템 수준 정보와 문서를 백업하고 그 기밀성·무결성·가용성을 보호한다.
  - CP-9(1) "Testing for Reliability and Integrity": 백업 정보를 시험해 매체 신뢰성과 정보 무결성을 확인한다.
  - CP-10 "System Recovery and Reconstitution": 중단·침해·장애 뒤 정해진 시간 안에 시스템을 알려진 상태로 복구한다.
  - 주의: 주기·시간 같은 값은 조직이 정하는 매개변수로 비어 있다. 이 검사는 그 값을 정하지 않고 흔적만 본다.
- MITRE CWE-250 "Execution with Unnecessary Privileges": 필요한 최소 수준보다 높은 권한으로 동작을 수행하면 약점이 새로 생기거나 다른 약점의 피해가 커진다. 완화: 필요한 최저 권한으로 실행. 원문 확인.
- MITRE CWE-540 "Inclusion of Sensitive Information in Source Code": 소스에 민감 정보가 있고 사용자가 접근할 수 있으면 노출된다. 원문은 검색 결과로 확인했고 CWE-250과 달리 페이지 전문은 읽지 않았다.
- Next.js 문서 "Environment Variables"(lastUpdated 2026-08-25): `NEXT_PUBLIC_` 변수는 빌드 때 브라우저로 보내는 JS 번들에 값이 박힌다. 원문 확인.
- Vite 문서 "Env Variables and Modes": `VITE_*` 변수는 민감 정보(API 키 등)를 담으면 안 되고 번들에 들어간다. 원문 확인.

## 한계와 하지 않은 것

- OP3은 NIST·CWE가 아니라 이 저장소의 정책이다. "테스트가 기능을 언급하는가"만 보며 테스트의 질은 보지 못한다.
- OP1은 이름과 형식 패턴이라 변수명이 평범한 비밀값, 난독화된 키, 환경변수 파일 바깥의 노출은 놓친다.
- OP2는 URL 문자열만 본다. 환경변수로 주입되는 계정의 권한은 보지 못한다.
- 비밀 값 자체의 저장소 유출은 `check_security_hotspots.py`와 `check_no_example_secrets.py` 쪽 범위다.
- 알림 도달 시험과 복원 훈련, 복구 시간 목표 설정은 사람이 한다. 이 검사는 만들지 않았다.

## 프로젝트 체크리스트 최소 게이트

- T2(공개 인터넷) 프로젝트는 `python ../qa_manager/scripts/check_operational_readiness.py . --tier T2`가 PASS이고, 알림·복원 시험 기록을 사람이 확인할 것.
- T0·T1 프로젝트는 `--tier T0`(기본)이 PASS일 것.
- PASS는 흔적이 있다는 뜻이지 운영 준비가 끝났다는 뜻이 아니다.

## 출처

- NIST, SP 800-53 Rev. 5 OSCAL catalog 5.2.0. https://github.com/usnistgov/oscal-content/tree/main/nist.gov/SP800-53/rev5
- MITRE, *CWE-250*. https://cwe.mitre.org/data/definitions/250.html
- MITRE, *CWE-540*. https://cwe.mitre.org/data/definitions/540.html
- Next.js, *Environment Variables*. https://nextjs.org/docs/app/guides/environment-variables
- Vite, *Env Variables and Modes*. https://vite.dev/guide/env-and-mode

조회일: 2026-10-24.
