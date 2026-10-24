# 호출·연동 경계의 오류 검수 기준

## 목적과 경계

사용 사례: 나는 등록된 프로젝트에서 오류가 났을 때, 어느 단위(모듈·클래스·함수)가 어느 경계(파일·프로세스·네트워크·파서·다른 단위의 호출)를 건너다 왜 실패했는지를 구조로 바로 찾는다.

이 문서는 오류가 모두 경계에서 난다고 주장하지 않는다. 아래 근거가 말하는 것은 "경계와 오류 처리 코드가 결함의 큰 비중을 차지한다"까지다. 정적 검사는 패턴만 보며, 오류를 삼키는 것이 옳은지는 판단하지 못하고 사유가 적혀 있는지만 확인한다.

## 근거 (확인 깊이를 함께 적는다)

| 출처 | 내용 | 확인 깊이 |
|---|---|---|
| Yuan 등, OSDI 2014, 분산 시스템 장애 198건(Cassandra·HBase·HDFS·Hadoop MapReduce·Redis) | 치명적 장애의 92%가 소프트웨어가 명시적으로 알린 비치명적 오류의 잘못된 처리였다. 세 가지 쉬운 패턴(핸들러가 비었거나 로그만 찍음, 너무 넓은 예외에서 중단, 핸들러의 TODO·FIXME)을 찾는 검사기가 치명적 장애의 30% 이상을 막았을 것이고 9개 시스템에서 찾은 버그와 나쁜 관행 143건이 개발자에게 수정·확인됐다. 로그에 진단 정보는 충분했고 어려운 점은 잡음 많은 로그를 뒤지는 일이었다. | 논문 전문을 직접 읽음 |
| Basili·Perricone, CACM 1984(중규모 프로젝트) | 오류 222건 중 인터페이스 오류가 87건(39%)으로 가장 큰 분류였고, 모듈 종류와 무관하게 인터페이스가 주된 문제였다. | 같은 연구의 1982년 기술보고서 전문을 직접 읽음 |
| Perry·Stieg, ESEC 1993(대형 실시간 시스템) | 인터페이스 결함 49%, 구현 결함 51%. 찾는 노력은 비슷하고 고치는 노력은 인터페이스 쪽이 더 크다(수정 가중 56%). 같은 연구진의 이전 연구는 68%였다고 인용한다. | 사전 인쇄본 전문을 직접 읽음. 68%는 2차 인용 |
| MITRE CWE-390, CWE-755 | 오류를 감지하고도 조치하지 않는 약점, 예외 조건의 부적절한 처리. 모든 예외를 처리하고, 조용히 삼키지 말고, 정적 분석을 쓰라고 한다. | 원문 확인 |
| OpenTelemetry, Recording errors | 실패하면 `error.type`을 남기고, 같은 예외를 두 번 기록하지 않으며, 이미 처리했거나 재시도된 오류는 기록하지 않는다. | 원문 확인 |
| Meyer, IEEE Computer 1992, Design by Contract | 호출하는 쪽이 사전 조건을, 호출되는 쪽이 사후 조건을 지킨다는 계약으로 단위 경계를 정의한다. 신뢰성은 정확성과 견고성의 합이다. | 검색 결과 수준(방법론 문헌, 효과 수치는 인용하지 않음) |

한계: 위 연구들은 1980~90년대 대형 시스템과 Java 분산 시스템이고, 분류 기준도 연구마다 다르다(39%, 49%, 68%). 마이크로서비스 최근 연구에서는 "서비스 실행과 통신" 문제가 이슈의 8.84%였다(Waseem 등, 2021, 검색 결과 수준). 그래서 이 저장소들에서 직접 측정해 규칙을 정했다.

## 이 작업 공간에서 측정한 것 (2026-10-24)

- 호출 시그니처 불일치: 같은 프로젝트 안의 함수 호출 4,008건을 `ast`로 검사해 0건. 단순 인자 개수·키워드 불일치는 문제가 아니었다. 최상위 함수만 봤고 메서드와 런타임 데이터 모양은 보지 못했다.
- 오류를 삼키는 핸들러: 테스트 제외 Python 552개 파일에서 1차 휴리스틱으로 후보 189건(빈 핸들러 87, 로그만 29, 값 없이 반환·continue 73)이었고 그중 넓은 예외를 잡는 것이 36건이었다. 규칙을 정제하고(아래) JS/TS까지 모든 저장소에 적용하자 넓은 예외 핸들러 후보가 60건이었고, 그중 테스트 설정 파일 1건은 제외했다. 이후 `/* */` 주석만 있는 JS catch를 잡도록 넓히자 6건이 더 나왔고, BOM 때문에 읽지 못하던 Python 파일 23개를 읽도록 고쳤으나 거기서는 새 후보가 없었다.
- 그렇게 모인 65건은 모두 코드를 읽고 사유를 적어 `qa:allow CWE-390 - <사유>`로 인정했다. 사유는 "청소가 실패해도 무해함", "다음 후보로 넘어감", "실패를 기록하고 서비스는 계속", "LLM 조회 실패 시 검사를 건너뜀(fail-open)" 같은 실제 동작이다. 사유 없이 남은 건은 0건이다. 이 인정은 삼켜도 된다는 판정이 아니라 누가 왜 그렇게 했는지를 적어 둔 것이다.

## 검사 규칙 (`scripts/check_error_handling_hotspots.py`)

| CWE | 패턴 | 결과 |
|---|---|---|
| CWE-390 | Python: 넓은 예외(bare `except`, `Exception`, `BaseException`)를 잡고 본문이 비었거나, 로그만 남기거나, `continue`·`break`·상수 반환뿐. JS/TS: 본문이 비었거나 주석만 있는 `catch`, 빈 `.catch(() => {})` (JS는 빈 본문만 본다. `catch (e) { console.log(e) }`처럼 로그만 남기는 JS 핸들러는 잡지 않는다) | 실패(`qa:allow` 필요) |
| CWE-755 | 오류 핸들러 안에 TODO·FIXME | 실패(`qa:allow` 필요) |
| — | 구체적인 예외 하나를 삼킴(`except FileNotFoundError: pass`) | 정보로만 집계, 실패 아님 |

판단 기준(이 저장소의 선택이며 근거 문헌의 문구가 아니다): 구체적 예외를 삼키는 것은 실패 조건을 이름으로 밝힌 것이라 정보로만 센다. `print`는 CLI 도구에서 사용자에게 알리는 통로로 보고 로그로 세지 않는다. 0이 아닌 종료 코드 반환과 `st.error` 같은 화면 표시는 호출자나 사용자에게 알리는 것으로 본다. 테스트, `conftest.py`, 최소화·번들·`node_modules` 같은 외부 코드는 제외한다. `qa:allow`는 `qa:allow CWE-390 - <10자 이상의 사유>` 형식으로 `except`가 있는 줄, 여러 줄로 쓴 `except (` 절의 이어지는 줄, 또는 핸들러 첫 본문 줄에 적고(JS는 `catch`가 있는 줄), `check_qa_allow_audit.py`가 형식을 감사한다.

알려진 한계(정적 패턴이라 보지 못하는 것):
- 값을 대입하고 넘어가는 핸들러(`except Exception: ok = False`)는 잡지 않는다.
- `parser.error()`처럼 로그 이름이 붙었지만 프로그램을 끝내는 호출도 로그로 센다.
- JS 정규식은 문자열이나 템플릿 안의 `catch {}`도 잡을 수 있다.
- 구문 오류로 읽을 수 없는 Python 파일은 검사하지 못한다. 건수는 `INFO`로 알려 준다(BOM은 `utf-8-sig`로 읽어 처리한다).
- JS의 로그만 남기는 핸들러는 보지 못한다(위 표).

## 오류 기록 규약 (`templates/errors/boundary_errors.py`)

경계를 건너는 호출을 `call_boundary(unit, boundary, func, ...)`로 감싼다(코루틴 함수는 `call_boundary_async`). 실패하면 `BoundaryError`가 `unit`, `boundary`, `kind`(timeout, rate_limit, auth, provider, parse, io, contract, unknown)를 담고 원래 예외를 원인(`__cause__`)으로 가진 채 올라가며, 경계를 처음 건너는 곳에서 한 번만 기록된다. `error_chain`이 바깥 오류에서 근본 원인까지 한 줄씩 보여 준다. kind는 AGENTS.md의 실패 종류 태그에 parse·io·contract를 더한 소수의 값이라 집계와 알림에 쓸 수 있다.

## 데이터 계약 (`expect_shape`)

경계를 넘어오는 JSON·LLM 출력·모듈 간 딕셔너리는 사용하기 전에 입구에서 `expect_shape(data, shape, unit)`로 키와 타입을 확인한다. 어긋나면 어느 경로에서 무엇이 기대와 달랐는지를 `contract` 오류로 알려 준다. 이미 스키마 검증이 있는 곳(`ai_agent`의 평가 스키마 검증, 구조화된 모델 출력 등)은 새로 만들지 말고 그것을 쓴다.

## 연동 흐름 테스트

여러 단위를 거치는 흐름은 처음부터 끝까지 실행하는 시나리오를 하나 둔다. 이 규칙은 `AGENTS.md`의 Test Scope Rule에 이미 있으며, 이 문서는 새 도구를 만들지 않고 그 규칙이 지켜지는지 확인하는 쪽을 택한다.

## 하지 않은 것과 이유

- 의심 줄에 순위를 매기는 도구(spectrum-based fault localization): 그런 도구가 기대는 개발자 행동에 대한 강한 가정이 사용자 연구에서 맞지 않는 것으로 나타났고(Parnin·Orso, ISSTA 2011), 인위적 결함에서 얻은 결과가 실제 결함으로 이어지지 않았다(Pearson 등, ICSE 2017). 둘 다 검색 결과 수준으로 확인했다.
- 의존 그래프 중심성으로 검토 우선순위를 매기는 도구(Zimmermann·Nagappan, ICSE 2008, 검색 결과 수준): 이번 범위에서 만들지 않았다.
- 실패 입력 최소화(Zeller·Hildebrandt, TSE 2002, delta debugging): 이번 범위에서 만들지 않았다.
- 호출 시그니처 검사기: 측정값이 0건이라 만들지 않았다. 값이 생기면 그때 추가한다.

## 프로젝트 체크리스트 최소 게이트

- 파이썬 또는 JS/TS 소스가 있는 등록 프로젝트는 `python ../qa_manager/scripts/check_error_handling_hotspots.py .`(repo_root 깊이만큼 `../`)가 PASS일 것. 빠지면 `tests/test_error_handling_hotspots.py`가 실패한다.
- 새 프로젝트는 `new_project.py`로 시작하면 이 검사가 처음부터 등록된다.
- 이 검사의 PASS는 오류 처리가 옳다는 뜻이 아니다. 사람이 사유를 읽고 동의해야 한다.

## 출처

- Yuan, D. et al., "Simple Testing Can Prevent Most Critical Failures: An Analysis of Production Failures in Distributed Data-Intensive Systems", OSDI 2014, pp. 249-265. https://www.usenix.org/conference/osdi14/technical-sessions/presentation/yuan
- Basili, V. R. & Perricone, B. T., "Software Errors and Complexity: An Empirical Investigation", Communications of the ACM 27(1):42-52, 1984. 확인한 판본은 NASA NTRS 보고서 19870015469(1982).
- Perry, D. E. & Stieg, C. S., "Software Faults in Evolving a Large, Real-Time System: A Case Study", ESEC 1993, LNCS 717. 확인한 판본은 1992년 8월 사전 인쇄본.
- MITRE, *CWE-390: Detection of Error Condition Without Action*, *CWE-755: Improper Handling of Exceptional Conditions*. https://cwe.mitre.org/
- OpenTelemetry, *Recording errors*. https://opentelemetry.io/docs/specs/semconv/general/recording-errors/
- Meyer, B., "Applying 'Design by Contract'", IEEE Computer 25(10):40-51, 1992.
- Parnin, C. & Orso, A., "Are Automated Debugging Techniques Actually Helping Programmers?", ISSTA 2011.
- Pearson, S. et al., "Evaluating and Improving Fault Localization", ICSE 2017, pp. 609-620.
- Zimmermann, T. & Nagappan, N., "Predicting Defects Using Network Analysis on Dependency Graphs", ICSE 2008, pp. 531-540.
- Zeller, A. & Hildebrandt, R., "Simplifying and Isolating Failure-Inducing Input", IEEE TSE 28(2):183-200, 2002.
- Waseem, M. et al., "On the Nature of Issues in Five Open Source Microservices Systems: An Empirical Study", arXiv:2104.12192, 2021.

조회일: 2026-10-24. 위 수치와 "검색 결과 수준"으로 표시한 항목은 인용 전에 원문을 다시 확인한다.
