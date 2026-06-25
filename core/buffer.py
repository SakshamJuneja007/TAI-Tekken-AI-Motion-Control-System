"""
TAI Action Buffer
=================
Sliding-window memory of recent ActionEvents.

Design rationale:
  The buffer is the system's short-term memory. It bridges the stateless
  detector (which fires one frame at a time) and the intent layer (which
  needs temporal context: "what happened in the last 2 seconds?").

  Implementation choices:
  - deque with maxlen: we primarily prune by time, but enforce a hard cap
    (MAX_EVENTS) to prevent memory leaks if timestamps break or a bug occurs.
  - snapshot() is non-destructive: the intent layer reads without
    consuming. The buffer keeps filling until pruned.
  - IDLE events are not stored — they add noise without adding signal.
    The absence of events is itself the idle signal.
"""

import time
from collections import deque
from typing import Deque, List

from configs.constants import AtomicAction, Thresholds
from core.models import ActionEvent, BufferSnapshot


class ActionBuffer:

    def __init__(self, window_seconds: float = Thresholds.BUFFER_WINDOW):
        self.window_seconds = window_seconds

        # Using maxlen as a safety net against timestamp bugs/memory leaks
        self._events: Deque[ActionEvent] = deque(
            maxlen=Thresholds.MAX_EVENTS
        )

    def push(self, event: ActionEvent) -> None:
        """
        Add an ActionEvent. IDLE events are ignored.
        Prune stale events after every push to keep memory bounded.
        """

        print(
            "[BUFFER]",
            event.action.name,
            event.confidence
        )

        if event.action == AtomicAction.IDLE:
            return

        self._events.append(event)

        self._prune()

    def push_many(self, events: List[ActionEvent]) -> None:

        for e in events:
            self.push(e)

    def snapshot(self) -> BufferSnapshot:
        """
        Return a BufferSnapshot of everything currently in the window.
        The snapshot is a frozen copy — the buffer continues to evolve.
        """

        self._prune()

        print(
            "[SNAPSHOT]",
            [e.action.name for e in self._events]
        )

        return BufferSnapshot(
            action_sequence=list(self._events),
            window_seconds=self.window_seconds,
        )

    def recent(self, n: int) -> List[ActionEvent]:
        """
        Get the n most recent events.
        Useful for quick combo or repeated input checks.
        """

        self._prune()

        return list(self._events)[-n:]

    def sequence(self) -> List[ActionEvent]:
        """
        Get the full sequence of current events.
        Clearer intent for ML prediction pipelines.
        """

        self._prune()

        return list(self._events)

    def pop_oldest(self):
        """
        Remove and return the oldest event.

        Compatibility method used by run_tai.py
        when enforcing BUFFER_MAX_SIZE.
        """

        if self._events:
            return self._events.popleft()

        return None

    def clear(self) -> None:

        self._events.clear()

    def __len__(self) -> int:

        self._prune()

        return len(self._events)

    # --------------------------------------------------
    # Internal
    # --------------------------------------------------

    def _prune(self) -> None:
        """
        Remove events older than window_seconds
        from the left side of the deque.
        """

        cutoff = time.time() - self.window_seconds

        while (
            self._events
            and
            self._events[0].timestamp < cutoff
        ):
            self._events.popleft()