# 보안 구현 조각 (복사해서 쓰는 stdlib 전용 파일)

`SECURITY_NETWORK_QA_STANDARD.md`의 상황별 매트릭스가 요구하는 통제 중 코드로 바로 옮길 수 있는 세 가지입니다.
프로젝트에 파일을 복사해 쓰고, 의존 패키지는 없습니다. 새로 만들기 전에 이 목록과 매트릭스 3절의 기존 구현을 먼저 확인하세요.

| 파일 | 막는 것 | 매트릭스에서 쓰는 곳 |
|---|---|---|
| `request_limits.py` | 크기를 정하지 않은 요청 본문 읽기(CWE-770) | 모든 계층의 `http.server` 핸들러 |
| `rate_limiter.py` | 클라이언트 하나의 과도한 요청(CWE-400) | T1 권장, T2 필수. 키 개수에 상한이 있어 주소를 바꿔 가며 보내도 메모리가 늘지 않음 |
| `bind_host.py` | 의도하지 않은 외부 노출(CWE-1327) | T0 기본값, T1 옵트인 |

## 쓰는 법

```python
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from bind_host import resolve_host
from rate_limiter import SlidingWindowLimiter
from request_limits import read_limited_body

LIMITER = SlidingWindowLimiter(limit=30, window_seconds=60)
MAX_REQUEST_BYTES = 100_000


class Handler(BaseHTTPRequestHandler):
    timeout = 10  # seconds a client may stall on a read

    def do_POST(self) -> None:
        if not LIMITER.allow(self.client_address[0]):
            self.send_error(429, "Too many requests")
            return
        body = read_limited_body(self, MAX_REQUEST_BYTES)
        if body is None:  # a 4xx response was already sent
            return
        ...


host, warning = resolve_host("MY_APP_HOST")
if warning:
    print(warning)
server = ThreadingHTTPServer((host, 8080), Handler)
server.daemon_threads = True
server.serve_forever()
```

## 한계

- 시간 제한이 없습니다. 헤더만 보내고 멈추는 클라이언트(slowloris류)가 읽기에서 서버를 붙잡을 수 있으니, 핸들러 클래스에 `timeout = 10`을 두고 `ThreadingHTTPServer`(`daemon_threads = True`)로 서비스하세요. 동시 연결 상한은 이 조각이 다루지 않으며 앞단이나 서버 설정의 몫입니다.
- 키 개수가 상한에 닿으면 가장 오래 안 보인 키부터 잊습니다. 새 주소를 대량으로 보내면 실제 남용자의 기록이 밀려날 수 있고, IPv6 클라이언트가 같은 /64 안에서 주소를 바꾸면 주소별 키를 피해 갑니다. 이 한계는 앞단 방어가 보완해야 합니다.
- 클라이언트 주소는 프록시 뒤에서는 프록시 주소로 보입니다. T2에서 프록시를 쓴다면 신뢰할 수 있는 헤더 처리를 따로 설계해야 합니다.
- 속도 제한은 프로세스 메모리 안에서만 셉니다. 프로세스가 여러 개이거나 재시작하면 카운터가 나뉘거나 사라집니다.
- 이 조각들은 볼륨형 DDoS를 막지 못합니다. 그것은 앞단(ISP·클라우드)의 몫입니다.
- Flask는 `app.config["MAX_CONTENT_LENGTH"]`, Next.js는 `ai_test2/CareerDiff/app/src/core/http/readJsonLimited.ts`를 쓰세요.

`rate_limiter.py`는 `hermes-agents/bots/telegram/security.py`의 `SlidingWindowLimiter`를 일반화한 것입니다(정수 키 → 해시 가능한 키, 키 개수 상한 추가).
