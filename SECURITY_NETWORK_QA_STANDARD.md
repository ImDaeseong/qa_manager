# 보안·해킹·네트워크 허점 검수 기준

## 목적과 경계

사용 사례: 나는 등록된 프로젝트를 검수할 때 이 기준으로 코드에 남은 보안 취약점·해킹 위험·네트워크 문제를 찾아서, 배포 전에 구체적인 개선점을 제시한다.

이 문서는 완전한 침투 테스트를 대체하지 않는다. 여기서 정의하는 검사는 정적 패턴 매칭(코드에 실제로 나타난 표현)에 한정되며, 런타임 동작·인증 우회·업무 로직 결함까지는 잡지 못한다. 발견 항목은 각각 CWE 번호로 분류하고, 의도된 설계라 위험을 감수하기로 했다면 코드에 `qa:allow` 주석으로 근거를 남긴다 — 조용히 억제하지 않는다.

## 반드시 찾아야 할 허점

| 분류 | 패턴 | CWE | 왜 위험한가 |
|---|---|---|---|
| 보안 취약점 | 코드에 리터럴로 박힌 API 키/토큰/비밀번호 | CWE-798 | 저장소가 노출되면 즉시 자격증명 탈취로 이어진다 |
| 해킹 위험 | `shell=True`/`os.system`과 함께 쓰이는, 외부 입력을 그대로 이어붙인 명령 문자열 | CWE-78 | 명령어 삽입으로 임의 코드 실행 가능 |
| 해킹 위험 | 문자열 포맷팅으로 조립된 SQL을 그대로 실행 | CWE-89 | SQL 삽입으로 데이터 유출·변조 가능 |
| 해킹 위험 | 외부 입력에 대한 `eval`/`exec` 호출 | CWE-94 / CWE-95 | 임의 코드 실행 |
| 해킹 위험 | `pickle.loads`, `Loader` 미지정/안전하지 않은 `yaml.load` | CWE-502 | 역직렬화 과정에서 임의 코드 실행 가능 |
| 네트워크 문제 | TLS 인증서 검증 비활성화(`verify=False`, `_create_unverified_context`, `NODE_TLS_REJECT_UNAUTHORIZED=0`) | CWE-295 | 중간자 공격에 노출 |
| 네트워크 문제 | 평문 `http://`로 외부(비-localhost) 엔드포인트 호출 | CWE-319 | 전송 구간 도청·변조 가능 |
| 네트워크 문제 | CORS를 `*`로 전체 허용 | CWE-942 | 신뢰 경계 없는 브라우저發 요청 허용 |

각 발견 항목에는 파일:줄, CWE 번호, 한 줄 개선 제안을 함께 출력한다. 하나의 통과/실패 배지 뒤에 근거를 숨기지 않는다.

## 프로젝트 체크리스트 최소 게이트

이 저장소의 소스 코드를 다루는 프로젝트는 `checklist.yaml`에 아래를 둔다.

- `python scripts/check_security_hotspots.py <repo 상대경로>` 실행 결과가 PASS일 것(신규 미검토 발견 0건)
- 의도적으로 감수하는 항목은 해당 줄에 `# qa:allow <CWE-ID> - <사유>` 주석으로 근거를 남길 것
- 이 검사는 정적 패턴 매칭이므로, 결과가 PASS라도 사람이 설계한 보안 경계(권한 분리, 인증 흐름)를 대체하지 않는다는 점을 문서에 명시할 것

## 근거

- OWASP, *OWASP Top 10:2025*, 2025 — A01(Broken Access Control, SSRF 포함), A02(Security Misconfiguration), A03(Software Supply Chain Failures) 등 웹 애플리케이션 보안 위험의 표준 순위. https://owasp.org/Top10/2025/
- CISA/MITRE, *2025 CWE Top 25 Most Dangerous Software Weaknesses*, 2025-12(공개일 기준 CISA 발표) — 2024-06-01~2025-06-01 사이 보고된 39,080건의 CVE를 분석한 순위. Cross-site Scripting, SQL Injection, CSRF, Missing Authorization이 상위권. https://www.cisa.gov/news-events/alerts/2025/12/11/2025-cwe-top-25-most-dangerous-software-weaknesses
- NIST, *SP 800-53 Rev. 5 (Update 1), Security and Privacy Controls for Information Systems and Organizations* — System and Communications Protection(SC) 계열이 암호화·전송구간 보호를 요구하는 근거. https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final (원본 Rev. 5 단독 페이지는 이 update 1로 대체되어 더 이상 최신판이 아님 — 인용 시 upd1 링크를 사용한다)
- MITRE, *CWE-798: Use of Hard-coded Credentials*, *CWE-78: OS Command Injection*, *CWE-89: SQL Injection*, *CWE-502: Deserialization of Untrusted Data*, *CWE-295: Improper Certificate Validation*, *CWE-319: Cleartext Transmission of Sensitive Information*, *CWE-942: Permissive Cross-domain Policy with Untrusted Domains* — 위 표의 개별 CWE 정의 원문. https://cwe.mitre.org/

조회일: 2026-09-18. 이 표는 정적 패턴 목록이며, 새로운 CWE Top 25가 매년 갱신되므로 최소 연 1회 이 문서의 표를 최신 순위와 대조한다(AGENTS.md Currency Rule).
