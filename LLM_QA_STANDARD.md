# LLM·OpenAI 응답 검수 기준

## 목적과 경계

사용 사례: 나는 여러 프로젝트를 검수할 때 이 기준으로 LLM 답변의 주장·근거·보안·재현성을 측정해서, 그럴듯하지만 검증되지 않은 답을 배포 전에 차단한다.

이 문서는 프롬프트만으로 진실을 보장한다고 주장하지 않는다. LLM의 자연어 판단은 보조 신호이며, 숫자·날짜·단위·URL·DOI·원문 해시는 결정론적 코드로 대조한다. 외부 문서와 사용자 입력은 **데이터**이지 실행 지시가 아니다. 실제 API 키가 필요한 라이브 평가는 기본 검수에서 분리하고 사람 승인(HOLD) 후 실행한다.

## 반드시 측정할 위험

1. **근거 없는 단정(confabulation)**: 답을 원자 주장으로 나눈 뒤 각 주장에 지원 원문이 있는 비율을 측정한다.
2. **인용 오류**: 인용 존재 여부뿐 아니라 인용 완전성(주요 주장 모두 인용), 정확성(원문이 실제로 주장 지원), 출처 품질을 따로 측정한다.
3. **조작·환각된 출처**: URL 접근, DOI 등록 정보, 출판 상태, 제목·저자·연도 일치를 확인하고 원문 해시와 조회일을 저장한다.
4. **수치 왜곡**: 숫자, 날짜, 통화, 백분율, 단위를 원문과 문자열/정규화 값으로 재대조한다.
5. **불충분한 근거에서의 과신**: 답할 수 없는 평가 사례를 포함하고 `근거 부족`으로 보류하는 정확도를 측정한다.
6. **프롬프트 주입**: 검색 문서·첨부파일 속 지시가 시스템 정책, 도구 권한, 출력 형식을 바꾸지 못하는 공격 사례를 넣는다.
7. **민감정보 노출**: API 키·토큰·개인정보를 입력, 로그, 오류, HTML 보고서에 남기지 않는다.
8. **비결정성과 회귀**: 모델 스냅샷과 프롬프트 버전을 기록하고 대표 사례를 반복 실행한다. 평균만 보지 않고 최악 실패도 보존한다.
9. **편향·유해 조언·자동화 과신**: 고위험 결론은 사람 검토 없이는 외부 행동이나 투자·법률·의료 결정을 실행하지 않는다.

## 프로젝트 체크리스트 최소 게이트

LLM을 호출하는 프로젝트는 `checklist.yaml`에 아래 실제 실행 항목을 둔다. 아직 검사 코드가 없으면 PASS로 쓰지 않고 HOLD/미등록 상태로 둔다.

- 고정된 평가 데이터셋과 예상 근거 또는 정답
- 원자 주장 지원률과 인용 정확성·완전성 계산
- 허위 URL·DOI·날짜·수치·단위의 음성(negative) 테스트
- 근거 부족 답변의 보류 테스트
- 직접·간접 프롬프트 주입 및 도구 권한 테스트
- 비밀값 비노출 테스트
- 구조화 출력 스키마 테스트
- 모델/프롬프트 변경 전후 회귀 비교
- 선택적 라이브 테스트: 개인 키, 비용 상한, 요청 ID, 키/원문 비기록, 사람 승인

권장 지표는 `atomic_claim_support_rate`, `citation_correctness`, `citation_completeness`, `fabricated_reference_rate`, `numeric_exact_match_rate`, `abstention_accuracy`, `prompt_injection_block_rate`, `schema_valid_rate`이다. 프로젝트 성격별 통과 임계값은 별도 SPEC에서 정하고, 표본 수와 실패 사례를 함께 공개한다. 하나의 종합 점수로 위험을 숨기지 않는다.

## 근거

- NIST, *Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile*, NIST AI 600-1, 2024-07-26, DOI: https://doi.org/10.6028/NIST.AI.600-1 — confabulation을 자신 있게 제시되는 오류·거짓 및 조작된 인용까지 포함하는 위험으로 정의하고 지속 평가와 문서화를 요구한다.
- Min et al., *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation*, EMNLP 2023, DOI: https://doi.org/10.18653/v1/2023.emnlp-main.741 — 장문을 원자 사실로 분해해 신뢰 가능한 지식원에 의해 지원되는 비율을 측정한다.
- Gao et al., *Enabling Large Language Models to Generate Text with Citations*, EMNLP 2023, DOI: https://doi.org/10.18653/v1/2023.emnlp-main.398 — 인용의 정확성·완전성을 분리 평가하는 ALCE 기준을 제시한다.
- OWASP GenAI Security Project, *LLM01:2025 Prompt Injection* 및 *LLM02:2025 Sensitive Information Disclosure* — RAG나 미세조정만으로 주입 위험이 제거되지 않으며 입력·출력과 권한 경계를 별도로 통제해야 함을 설명한다.
- OpenAI 공식 문서, *API Overview* 및 *Evals* — 모델 출력은 가변적이므로 고정 모델 버전과 애플리케이션 평가를 사용하고, API 키를 서버 환경변수/키 관리 서비스에 보관하며 요청 ID를 기록하도록 안내한다.

조회일: 2026-09-16. 논문 지표는 검수 설계의 근거이지 모든 도메인에서 동일 임계값을 보장하는 인증이 아니다.
