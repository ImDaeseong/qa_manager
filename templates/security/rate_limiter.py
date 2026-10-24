"""Per-client sliding-window rate limiter with a bounded key table (stdlib only, copy into your project).

Generalized from hermes-agents' bots/telegram/security.py SlidingWindowLimiter, which keys on an integer user
id and never forgets a key. A limiter keyed by client address needs a cap on the number of remembered keys,
otherwise an attacker who rotates source addresses turns the limiter itself into the memory-exhaustion
problem it is meant to prevent (CWE-770).

Keys are kept in least-recently-seen order, so making room is O(1): the key at the front is the most idle one.
Calls are serialized with a lock, so the limiter can be shared by the threads of a threaded server.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from collections.abc import Hashable


class SlidingWindowLimiter:
    """Allow at most `limit` calls per key within `window_seconds`, remembering at most `max_keys` keys."""

    def __init__(self, limit: int, window_seconds: float = 60.0, max_keys: int = 10_000) -> None:
        if limit < 1 or window_seconds <= 0 or max_keys < 1:
            raise ValueError("limit, window_seconds and max_keys must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._events: OrderedDict[Hashable, deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    def allow(self, key: Hashable, now: float | None = None) -> bool:
        """Consume one allowance for `key` and return whether the call may proceed."""
        current = time.monotonic() if now is None else now
        cutoff = current - self.window_seconds
        with self._lock:
            events = self._events.get(key)
            if events is None:
                if len(self._events) >= self.max_keys:
                    self._events.popitem(last=False)  # least recently seen key, which is also the most idle one
                events = self._events[key] = deque()
            else:
                self._events.move_to_end(key)
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(current)
            return True
