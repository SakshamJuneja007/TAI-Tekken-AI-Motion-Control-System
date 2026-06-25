"""
TAI Executor
============
Executes Tekken moves using pynput.
"""

import logging
import time
from threading import Event

from core.models import SelectedMove

logger = logging.getLogger(__name__)

KEY_MAP = {
    # Attack buttons
    "1": "x",
    "2": "a",
    "3": "s",
    "4": "z",

    # Movement
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",

    "forward": "right",
    "back": "left",

    "neutral": None
}

DEFAULT_DELAY = 0.10
FRAME_DURATION = 0.10


class MoveExecutor:

    def __init__(
        self,
        backend="keyboard",
        dry_run=False
    ):

        self.backend = backend
        self.dry_run = dry_run

        # Compatibility with run_tai.py
        self.input_parser = None

        self.is_busy = False

        self.cancel_event = Event()

        self._keyboard = None

        self._init_backend()

    def execute(
        self,
        move: SelectedMove
    ):

        if not isinstance(move, SelectedMove):
            raise TypeError(
                f"Executor expects SelectedMove, got {type(move)}"
            )

        if self.is_busy:
            return False

        self.is_busy = True

        self.cancel_event.clear()

        try:

            inputs = move.inputs

            # Optional parser hook
            if self.input_parser:
                try:
                    inputs = self.input_parser(inputs)
                except Exception as exc:
                    print(
                        f"[PARSER ERROR] {exc}"
                    )
                    logger.exception(
                        "Input parser failed"
                    )

            print(
                f"\n[EXECUTOR] {move.name}"
            )

            print(
                f"[INPUTS] {inputs}"
            )

            for key in inputs:

                if self.cancel_event.is_set():
                    return False

                self._press_key(key)

                time.sleep(
                    DEFAULT_DELAY
                )

            return True

        except Exception as exc:

            print(
                "[EXECUTOR ERROR]",
                exc
            )

            logger.exception(
                "Execution failed"
            )

            return False

        finally:

            self.is_busy = False

    def execute_inputs(
        self,
        inputs
    ):
        """
        Compatibility wrapper for older run_tai.py versions.
        """

        try:

            print(
                f"[RAW INPUTS] {inputs}"
            )

            for key in inputs:

                if self.cancel_event.is_set():
                    return False

                self._press_key(key)

                time.sleep(
                    DEFAULT_DELAY
                )

            return True

        except Exception as exc:

            print(
                "[EXEC INPUTS ERROR]",
                exc
            )

            logger.exception(
                "Raw input execution failed"
            )

            return False

    def cancel_execution(
        self
    ):
        self.cancel_event.set()

    def _init_backend(
        self
    ):

        if self.dry_run:

            print(
                "[EXECUTOR] Dry Run Enabled"
            )

            return

        try:

            from pynput.keyboard import Controller

            self._keyboard = Controller()

            print(
                "[EXECUTOR] pynput backend loaded"
            )

        except ImportError:

            logger.exception(
                "Could not import pynput"
            )

            self.dry_run = True

    def _press_key(
        self,
        key
    ):

        if key == "neutral":

            time.sleep(
                FRAME_DURATION
            )

            return

        mapped = KEY_MAP.get(
            key,
            key
        )

        if mapped is None:

            time.sleep(
                FRAME_DURATION
            )

            return

        if self.dry_run:

            print(
                f"[KEY] {mapped}"
            )

            return

        try:

            print(
                f"[PRESS] {mapped}"
            )

            self._keyboard.press(
                mapped
            )

            time.sleep(
                0.10
            )

            self._keyboard.release(
                mapped
            )

        except Exception as exc:

            print(
                f"[KEY ERROR] {mapped}",
                exc
            )

            logger.exception(
                f"Failed to press key: {mapped}"
            )