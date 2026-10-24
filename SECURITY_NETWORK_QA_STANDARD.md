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
| 해킹 위험 | 외부 입력에 대한 `eval`/`exec` 호출(단, `.exec(`처럼 다른 객체의 메서드 호출은 제외 — JS `RegExp.prototype.exec()`와 구분) | CWE-94 / CWE-95 | 임의 코드 실행 |
| 해킹 위험 | `pickle.loads`, `Loader` 미지정/안전하지 않은 `yaml.load` | CWE-502 | 역직렬화 과정에서 임의 코드 실행 가능 |
| 네트워크 문제 | TLS 인증서 검증 비활성화(`verify=False`, `_create_unverified_context`, `NODE_TLS_REJECT_UNAUTHORIZED=0`) | CWE-295 | 중간자 공격에 노출 |
| 네트워크 문제 | 평문 `http://`로 외부(비-localhost) 엔드포인트 호출(단, `example.com/.org/.net`(RFC 2606 문서·테스트 예약 도메인)과 `www.w3.org`(XML 네임스페이스) 리터럴은 제외) | CWE-319 | 전송 구간 도청·변조 가능 |
| 네트워크 문제 | CORS를 `*`로 전체 허용 | CWE-942 | 신뢰 경계 없는 브라우저發 요청 허용 |

각 발견 항목에는 파일:줄, CWE 번호, 한 줄 개선 제안을 함께 출력한다. 하나의 통과/실패 배지 뒤에 근거를 숨기지 않는다.

## 노출면·가용성 규칙 (`scripts/check_exposure_hotspots.py`)

2026-10 공개 서버가 PHP 취약점 탐색 요청(base64 `assert` 페이로드, 템플릿 주입/OAST 탐침)을 대량으로 받아 OutOfMemoryError까지 간 사례(OKKY 게시글 1565929, 작성자 서술 기준)를 계기로 추가했다. 해당 글에서 페이로드는 비-PHP 대상에서 실행되지 않았고, 피해는 검증 실패 예외가 폭주하며 생긴 자원 고갈이었다고 한다(글쓴이의 설명이며 독립 검증은 아님). 이는 아래 "자원을 제한 없이 할당" 약점군과 같은 종류다.

| 분류 | 패턴 | CWE | 근거 |
|---|---|---|---|
| 네트워크 노출 | 서버가 `0.0.0.0`(모든 인터페이스)에 바인딩 | CWE-1327 | MITRE: 원격 통신하는 자원에 0.0.0.0을 할당하는 약점 |
| 가용성 | 요청 바디를 읽지만 파일 어디에도 크기 상한이 없음(파일당 1건 보고) | CWE-770 | MITRE: 할당 크기·개수에 제한을 두지 않음. 완화책으로 입력 검증(특히 할당 크기에 영향을 주는 값)과 자원 상한 명시를 든다 |
| 가용성 | `0.0.0.0` 바인딩 파일에 속도 제한(rate limit/throttle/429 등) 흔적이 없음 | CWE-400 / CWE-770 | OWASP API4:2023은 요청당 입력 최대 크기 강제, 클라이언트별 호출 빈도 제한, 컨테이너 자원 상한, 서드파티 비용 한도를 예방책으로 든다 |

규칙의 한계: 파일 안에 상한처럼 보이는 이름(`request`·`body`·`content`·`upload`·`payload`가 들어간 `MAX_*` 식별자, `validate_content_length` 호출, `Content-Length` 비교)이 있으면 통과시킨다. 선언된 `Content-Length`만 비교하는 방식은 chunked 요청이나 잘못된 헤더로 우회되므로, 상한은 본문을 읽는 도중에도 세는 방식이 안전하다. 그 상한이 실제로 읽기 전에 적용되는지는 검증하지 못한다. 테스트 파일(`tests/`·`test/`·`__tests__/` 폴더, `test_*`·`*_test.*`·`*.test.*` 파일)은 제외한다. 대상은 git이 추적하는 파일과 아직 추적되지 않은(무시되지 않은) 새 파일이며, 한글 등 비ASCII 파일명도 `git ls-files -z`로 읽어 빠뜨리지 않는다(2026-10-24 독립 검토에서 따옴표로 감싸진 경로가 조용히 누락되는 결함을 찾아 이 스캐너와 qa_manager의 `check_security_hotspots.py`에서 고쳤다. 다른 저장소에 이식된 `check_security_hotspots.py` 사본은 아직 예전 방식이며, 비ASCII 소스 파일이 있는 `ai_test1`·`ai_test2`는 고친 스캐너로 다시 돌려 발견 0건임을 확인했다). 빈 호스트(`("", port)`)와 `listen(port, "0.0.0.0")` 형태의 바인딩도 잡는다. 템플릿 주입(CWE-1336)은 자동 검사가 없고, 2026-10-24 기준 12개 저장소에서 변수를 템플릿 문자열로 렌더링하는 호출은 찾지 못했다(`render_template_string(상수)` 1건뿐). 앞단 프록시·WAF·방화벽이 있는 의도적 공개는 해당 줄에 `# qa:allow <CWE-ID> - <사유>`로 남긴다.

## DDoS 대응의 책임 계층 (무엇을 코드로 검사하고 무엇을 하지 못하는가)

- 공격은 성격별로 나뉜다. Mirkovic & Reiher(2004)는 공격과 방어 메커니즘을 각각 분류했고, Zargar 등(2013)은 플러딩 대응책을 어디서(피해자/중간망/발원지)·언제(예방/탐지/대응) 막는지로 분류했다. CISA/FBI/MS-ISAC 공동 지침(2024 개정)은 기법을 볼류메트릭·프로토콜·애플리케이션 3종으로 나눈다.
- **볼류메트릭(대역폭 소진)은 개별 앱 코드로 막을 수 없다.** 회선 앞단(ISP·클라우드 DDoS 방어 서비스)의 몫이며, CISA 지침도 노출 서비스 식별·자산 중요도 분류·DDoS 방어 서비스 가입·ISP/클라우드 제공 보호 확인·대응 계획을 사전 조치로 든다. 이 저장소의 검사로 "볼류메트릭 DDoS에 안전하다"고 선언하지 않는다.
- **프로토콜 계층**: TCP SYN 폭주의 완화책(필터링, 백로그 확대, SYN-RECEIVED 타이머 단축, 가장 오래된 반개방 TCB 재활용, SYN cache, SYN cookies, 방화벽·프록시)은 RFC 4987이 정리했고 대부분 OS·방화벽 설정 영역이다. RFC 4987 자신이 SYN cookies의 가장 큰 대가로 window scaling 비활성화를 든다. 위조 출발지 주소 차단(ingress filtering)은 BCP 38(RFC 2827)로, ISP 경계의 책임이다. 반사·증폭 공격(UDP 기반 프로토콜 14종 조사, Rossow 2014)은 UDP 서비스를 직접 여는 프로젝트에만 해당한다.
- **프로토콜 구현 취약점**: HTTP/2 Rapid Reset(CVE-2023-44487)은 2023-08~10 실제 공격에 쓰였고 CISA는 HTTP/2 서비스 운영자에게 패치 적용과 설정 변경을 권고한다. 서버·프록시 버전 고정과 보안 공지 확인은 공급망 항목(`RELEASE_READINESS_STANDARD.md`)에서 사람이 본다.
- **애플리케이션 계층(이 저장소가 직접 검사하는 부분)**: 요청 크기·빈도·자원 상한과 로컬 바인딩 기본값. NIST SP 800-53 Rev.5 SC-5는 정의된 서비스 거부 유형에 대해 보호하거나 영향을 제한하는 통제를 요구하며, 경계 장치의 패킷 필터링과 대역폭·중복성 확충을 예로 든다(NIST 공식 OSCAL 카탈로그 Rev 5.2.0의 SC-5 원문과 대조함, 2026-10-24).

## DDoS 외 공격 유형별 근거와 검사 방식

| 공격 유형 | 근거 | 이 저장소의 검사 | 자동 검사의 한계 |
|---|---|---|---|
| 알고리즘 복잡도 공격(해시 충돌 등) | Crosby & Wallach, USENIX Security 2003: 적은 대역폭으로 자료구조 최악 성능을 노려 Perl·Squid·Bro를 공략, 범용 해시가 대안으로 제시됨 | 없음(사람 리뷰: 공격자가 키를 고르는 해시/정렬/파서) | 정적 패턴으로 식별 불가 |
| 정규식 서비스 거부(ReDoS) | Davis 등, FSE 2018: JS·Python 생태계에서 1만 개 이상 모듈에 영향 가능한 초선형 정규식. 휴리스틱은 거짓 음성이 적고 거짓 양성이 많음. CWE-1333은 역추적 없는 패턴, 엔진 제한/시간 상한, 입력 길이 제한을 완화책으로 든다 | 없음(입력 길이 상한 = CWE-770 규칙이 간접 완화) | 거짓 양성이 많아 규칙화하지 않음 |
| 서버측 템플릿 주입(SSTI) | Kettle, Black Hat USA 2015: 사용자 입력이 템플릿에 들어가면 서버 내부 공격·RCE로 이어질 수 있음 | 없음(사람 리뷰: 사용자 입력을 템플릿 문자열로 렌더링하지 않기) | 문자열 렌더링 호출의 신뢰 여부를 정적으로 판정 불가 |
| 간접 프롬프트 주입(LLM 연동 앱) | Greshake 등, arXiv:2302.12173(2023): 모델이 가져온 콘텐츠 속 지시를 따르게 만들어 데이터 탈취 등을 유발 | `AGENTS.md`의 lethal trifecta 규칙(비공개 데이터+신뢰할 수 없는 콘텐츠+외부 통신 동시 금지) | 사람의 설계 검토 필요 |
| 명령·SQL 삽입, 역직렬화, 자격증명, TLS, CORS | 위 "반드시 찾아야 할 허점" 표 | `check_security_hotspots.py` | 패턴 일치만 확인 |

위 표에서 "없음"인 항목은 검사가 없다는 뜻이며, 안전하다는 뜻이 아니다.

## 프로젝트 체크리스트 최소 게이트

이 저장소의 소스 코드를 다루는 프로젝트는 `checklist.yaml`에 아래를 둔다.

- `python scripts/check_security_hotspots.py <repo 상대경로>` 실행 결과가 PASS일 것(신규 미검토 발견 0건)
- 의도적으로 감수하는 항목은 해당 줄에 `# qa:allow <CWE-ID> - <사유>` 주석으로 근거를 남길 것
- `python scripts/check_qa_allow_audit.py`로 모든 `qa:allow` 주석이 CWE 번호와 10자 이상의 실제 사유를 갖추고 있는지 주기적으로 감사할 것(근거 없는 억제가 조용히 쌓이지 않도록)
- `python scripts/check_security_standard_freshness.py`로 이 문서의 CWE/OWASP 근거가 1년 넘게 방치되지 않았는지 확인할 것
- 서버 코드가 있는 프로젝트는 `python ../qa_manager/scripts/check_exposure_hotspots.py .`(repo_root 기준)가 PASS일 것. 회귀 테스트는 `python -m unittest tests.test_exposure_hotspots -q`
- 웹 서버를 새로 만들 때 기본값은 `127.0.0.1` 바인딩, 요청 바디 크기 상한, 외부 공개 시 속도 제한 또는 앞단 방어 문서화일 것
- 이 검사는 정적 패턴 매칭이므로, 결과가 PASS라도 사람이 설계한 보안 경계(권한 분리, 인증 흐름)를 대체하지 않는다는 점을 문서에 명시할 것

## 근거

- OWASP, *OWASP Top 10:2025*, 2025 — A01(Broken Access Control, SSRF 포함), A02(Security Misconfiguration), A03(Software Supply Chain Failures) 등 웹 애플리케이션 보안 위험의 표준 순위. https://owasp.org/Top10/2025/
- CISA/MITRE, *2025 CWE Top 25 Most Dangerous Software Weaknesses*, 2025-12(공개일 기준 CISA 발표) — 2024-06-01~2025-06-01 사이 보고된 39,080건의 CVE를 분석한 순위. Cross-site Scripting, SQL Injection, CSRF, Missing Authorization이 상위권. https://www.cisa.gov/news-events/alerts/2025/12/11/2025-cwe-top-25-most-dangerous-software-weaknesses
- NIST, *SP 800-53 Rev. 5 (Update 1), Security and Privacy Controls for Information Systems and Organizations* — System and Communications Protection(SC) 계열이 암호화·전송구간 보호를 요구하는 근거. https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final (원본 Rev. 5 단독 페이지는 이 update 1로 대체되어 더 이상 최신판이 아님 — 인용 시 upd1 링크를 사용한다)
- MITRE, *CWE-798: Use of Hard-coded Credentials*, *CWE-78: OS Command Injection*, *CWE-89: SQL Injection*, *CWE-502: Deserialization of Untrusted Data*, *CWE-295: Improper Certificate Validation*, *CWE-319: Cleartext Transmission of Sensitive Information*, *CWE-942: Permissive Cross-domain Policy with Untrusted Domains* — 위 표의 개별 CWE 정의 원문. https://cwe.mitre.org/

- Mirkovic, J. & Reiher, P., "A taxonomy of DDoS attack and DDoS defense mechanisms", ACM SIGCOMM Computer Communication Review 34(2):39-53, 2004, DOI 10.1145/997150.997156. https://doi.org/10.1145/997150.997156
- Zargar, S. T., Joshi, J., Tipper, D., "A Survey of Defense Mechanisms Against Distributed Denial of Service (DDoS) Flooding Attacks", IEEE Communications Surveys & Tutorials 15(4):2046-2069, 2013, DOI 10.1109/SURV.2013.031413.00127.
- Eddy, W., RFC 4987 *TCP SYN Flooding Attacks and Common Mitigations*, 2007 (Informational). https://www.rfc-editor.org/rfc/rfc4987
- Ferguson, P. & Senie, D., RFC 2827 / BCP 38 *Network Ingress Filtering*, 2000. https://www.rfc-editor.org/rfc/rfc2827
- Rossow, C., "Amplification Hell: Revisiting Network Protocols for DDoS Abuse", NDSS 2014. https://www.ndss-symposium.org/ndss2014/
- Crosby, S. A. & Wallach, D. S., "Denial of Service via Algorithmic Complexity Attacks", 12th USENIX Security Symposium, 2003, pp. 29-44. https://www.usenix.org/conference/12th-usenix-security-symposium/denial-service-algorithmic-complexity-attacks
- Davis, J. C., Coghlan, C. A., Servant, F., Lee, D., "The Impact of Regular Expression Denial of Service (ReDoS) in Practice", ESEC/FSE 2018, pp. 246-256, DOI 10.1145/3236024.3236027.
- Kettle, J., "Server-Side Template Injection: RCE for the Modern Web App", Black Hat USA 2015. https://portswigger.net/research/server-side-template-injection
- Greshake, K. et al., "Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection", arXiv:2302.12173, 2023. https://arxiv.org/abs/2302.12173
- OWASP, *API Security Top 10 2023*, API4:2023 Unrestricted Resource Consumption. https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption
- MITRE, *CWE-1327: Binding to an Unrestricted IP Address*, *CWE-770: Allocation of Resources Without Limits or Throttling*, *CWE-1333: Inefficient Regular Expression Complexity*. https://cwe.mitre.org/
- CISA, *HTTP/2 Rapid Reset Vulnerability, CVE-2023-44487*, 2023-10-10. https://www.cisa.gov/news-events/alerts/2023/10/10/http2-rapid-reset-vulnerability-cve-2023-44487
- CISA/FBI/MS-ISAC, *Understanding and Responding to Distributed Denial-of-Service Attacks*, 2022-10, updated 2024-03-21. https://www.cisa.gov/resources-tools/resources/understanding-and-responding-distributed-denial-service-attacks
- NIST SP 800-53 Rev. 5.2.0, SC-5 Denial-of-service Protection — NIST 공식 OSCAL 카탈로그(github.com/usnistgov/oscal-content, `NIST_SP-800-53_rev5_catalog.json`, 카탈로그 수정일 2026-10-22)의 통제 본문과 지침을 직접 읽어 확인: (a) 정의된 DoS 이벤트 유형의 영향을 '보호하거나(protect against) 제한(limit)'하고 (b) 유형별 통제를 정의한다. 지침은 경계 보호 장치의 패킷 필터링, 네트워크 용량·대역폭 증설과 서비스 중복을 예로 든다.

출처 확인 방식(2026-10-24): 위 논문·RFC·CVE 항목은 존재와 서지정보를 웹 검색으로 확인했고, OWASP API4·CWE-1327·CWE-770·CWE-1333·RFC 4987·CISA Rapid Reset은 원문 페이지를, NIST SC-5는 NIST 공식 OSCAL 카탈로그 파일을 직접 열어 인용 내용을 대조했다. Mirkovic·Zargar·Crosby·Davis·Kettle·Greshake·Rossow·BCP 38은 초록·서지정보 수준까지만 확인했고 본문 수치는 인용하지 않았다.

조회일: 2026-09-18(CWE/OWASP Top 순위 대조 기준 — 노출면·가용성 절의 출처는 위 "출처 확인 방식"의 2026-10-24 기준이며 이 날짜를 갱신하지 않음). 이 표는 정적 패턴 목록이며, 새로운 CWE Top 25가 매년 갱신되므로 최소 연 1회 이 문서의 표를 최신 순위와 대조한다(AGENTS.md Currency Rule).
