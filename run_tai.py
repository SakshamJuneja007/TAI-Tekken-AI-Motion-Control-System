"""
TAI — Tekken AI Motion Controller
===================================

OpenCV standalone runner

Pipeline:

Camera
 ↓
MediaPipeProcessor
 ↓
VelocityEstimator
 ↓
AtomicActionDetector
 ↓
ActionBuffer  (sliding window, max 10 events)
 ↓
IntentPredictor  (ML — throttled to every 8 frames)
 ↓
Heuristic fallback  (when ML returns IDLE for known actions)
 ↓
CombatResolver  (action-filter + repeat-penalty)
 ↓
MoveExecutor  (with "or"-notation parser)

Fixes applied (see debugging report):
  P0-2  ML IDLE collapse → heuristic fallback. Now delegates to
        core.heuristics.dominant_action so this logic is identical to
        the equivalent override inside combat/resolver.py instead of
        being two independently-tuned copies.
  P0-3  "or" token crash in executor input parsing
  P1    Move filtering: detected actions → allowed move categories
        (enforced in combat/resolver.py — see that file for the
        "sweep" category fix that closes the leg-input-without-leg-
        movement bug)
  P3    Throttled ML (every ML_INTERVAL frames), reduced console
        logging level, buffer capped at BUFFER_MAX_SIZE events

NOT fixed in this revision — flagging explicitly rather than letting it
look resolved:
  P0-1  Action ID mapping bug (report showed LEFT_PUNCH mapping to 7,
        which collides with CROUCH, instead of its real value of 2).
        That translation table lives in wherever AtomicAction enum
        values get converted to executor key IDs — most likely
        vision/detector.py or core/models.py. Neither of those files
        was available when this revision was made, so this bug is
        still live. Don't assume it's handled just because the other
        P0 items are.

Note on logging: dropping the root logger to WARNING quiets framework
noise from MediaPipe etc., but the bare `print()` calls inside
combat/resolver.py ([RESOLVE], [SELECTED MOVE], [HEURISTIC OVERRIDE])
are NOT controlled by this logging level — they print every time a
move is selected, independent of `logger`. If console spam is still a
problem, those need to be gated separately (e.g. behind a DEBUG flag).
"""

import time
import logging
import traceback
from collections import deque

import cv2

from vision.mediapipe_processor import MediaPipeProcessor
from vision.velocity import VelocityEstimator
from vision.detector import AtomicActionDetector

from core.buffer import ActionBuffer
from core.models import SelectedMove
from core.heuristics import dominant_action

from intelligence.predictor import IntentPredictor
from intelligence.move_brain import MoveBrain

from combat.resolver import CombatResolver
from combat.executor import MoveExecutor


# ---------------------------------------------------------------------------
# Logging — INFO only; remove the handler to silence framework noise
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.WARNING,          # was INFO — reduced to cut console spam
    format="[%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("TAI")


# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------

ML_INTERVAL    = 8        # run ML every N frames (keeps MediaPipe realtime)
BUFFER_MAX_SIZE = 10      # sliding window cap for ActionBuffer


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------

_GREY   = (160, 160, 160)
_GREEN  = (0, 220, 80)
_CYAN   = (220, 220, 0)
_ORANGE = (0, 160, 255)
_BLACK  = (0, 0, 0)
_FONT   = cv2.FONT_HERSHEY_SIMPLEX


def _text(frame, msg, pos, scale, color, thickness=1):
    x, y = pos
    cv2.putText(frame, msg, (x+1, y+1), _FONT, scale, _BLACK, thickness+1, cv2.LINE_AA)
    cv2.putText(frame, msg, (x,   y),   _FONT, scale, color,  thickness,   cv2.LINE_AA)


def draw_hud(frame, fps, actions, intent, move):
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (440, 150), (20, 20, 20), -1)
    cv2.addWeighted(overlay, .55, frame, .45, 0, frame)

    _text(frame, f"FPS: {fps:.0f}", (10, 22), .55, _GREY)

    act = " ".join(a.action.name for a in actions)
    _text(frame, "ACTIONS: " + act, (10, 55), .5, _GREEN)

    if intent:
        intent_name = getattr(getattr(intent, "intent", None), "name", str(intent))
        _text(frame, f"INTENT: {intent_name}", (10, 88), .55, _CYAN)

    if move:
        _text(frame, f"MOVE: {move.name}", (10, 125), .65, _ORANGE)


# ---------------------------------------------------------------------------
# FPS counter
# ---------------------------------------------------------------------------

class FPSCounter:

    def __init__(self):
        self.last   = time.time()
        self.buffer = deque(maxlen=30)

    def tick(self):
        now = time.time()
        self.buffer.append(now - self.last)
        self.last = now
        return (len(self.buffer) / sum(self.buffer)) if self.buffer else 0.0


# ---------------------------------------------------------------------------
# Heuristic prediction — duck-typed drop-in for IntentPrediction
# ---------------------------------------------------------------------------

class _HeuristicPrediction:
    """
    Used when ML is stuck on IDLE.  Wraps the dominant detected action
    so the resolver / MoveBrain can still pick a meaningful move.
    """

    class _Intent:
        def __init__(self, name):
            self.name = name

    def __init__(self, action_name, confidence=1.0):
        self.intent     = self._Intent(action_name)
        self.confidence = confidence

    def __repr__(self):
        return f"HeuristicPrediction({self.intent.name}, {self.confidence:.2f})"


def _heuristic_from_sequence(sequence, threshold=0.6):
    """
    If sequence is dominated (≥threshold) by one non-IDLE action,
    return a _HeuristicPrediction for it.  Else None.

    Delegates to core.heuristics.dominant_action — the SAME function
    combat/resolver.py uses for its own IDLE override — so the two
    fallback paths can never disagree about what "dominant" means.
    """
    result = dominant_action(sequence, threshold=threshold)
    if result is None:
        return None

    name, ratio = result
    return _HeuristicPrediction(name, ratio)


# ---------------------------------------------------------------------------
# Executor input parser — fixes the "or" crash
# ---------------------------------------------------------------------------

def parse_move_inputs(raw_inputs):
    """
    Move database entries look like:  ('1', '3', 'or', '2', '4')
    meaning "press 1+3  OR  press 2+4".

    This parser splits on 'or' and returns ONE branch (the first one),
    as a flat list of key tokens ready to press.

    It also skips any token that isn't a single printable character or
    a known multi-char key name, so garbage tokens never reach keyboard.press().

    Returns: list[str]  — tokens safe to pass to keyboard.press()
    """

    if not raw_inputs:
        return []

    # Accept both tuple/list and a single string like "1+3"
    if isinstance(raw_inputs, str):
        tokens = [t.strip() for t in raw_inputs.replace("+", " ").split()]
    else:
        tokens = [str(t).strip() for t in raw_inputs]

    # Split on 'or' — take only the first branch
    branch = []
    for token in tokens:
        if token.lower() == "or":
            break               # ignore alternate branches
        branch.append(token)

    # Whitelist filter — only pass tokens that look like real keys
    _KNOWN_KEYS = {
        "1", "2", "3", "4",            # Tekken attack buttons
        "up", "down", "left", "right",  # directional
        "enter", "space", "shift",
        "ctrl", "alt", "tab", "esc",
    }

    safe = []
    for token in branch:
        token_lower = token.lower()
        if token_lower in _KNOWN_KEYS or (len(token) == 1 and token.isprintable()):
            safe.append(token)
        else:
            print(f"[INPUT PARSER] skipping unknown token: {token!r}")

    return safe


# ---------------------------------------------------------------------------
# Main run loop
# ---------------------------------------------------------------------------

def run(camera_index=0, model_path="models/intent_brain.pth"):

    print("[TAI] Initialising pipeline ...")

    # -- vision --
    mp_processor = MediaPipeProcessor(
        min_detection_confidence=.6,
        min_tracking_confidence=.5
    )
    velocity = VelocityEstimator()
    detector = AtomicActionDetector()

    # -- memory --
    buffer = ActionBuffer()

    # -- ML --
    predictor = IntentPredictor(model_path=model_path)

    # -- combat --
    move_brain = MoveBrain()
    resolver   = CombatResolver()
    resolver.move_brain = move_brain    # share instance
    executor   = MoveExecutor()

    # Patch executor so it uses our safe input parser.
    # If MoveExecutor exposes an input_parser hook, set it.
    # Otherwise we wrap execute() below before calling it.
    _executor_has_parser = hasattr(executor, "input_parser")
    if _executor_has_parser:
        executor.input_parser = parse_move_inputs

    # -- camera --
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("[TAI] Camera failed to open")
        return

    fps_counter = FPSCounter()

    last_actions = []
    last_intent  = None
    last_move    = None

    frame_count   = 0
    last_prediction = None      # cached ML result between throttle frames

    print("[TAI] Running.  ESC = quit  |  R = reset buffer")

    while True:

        ret, frame = cap.read()
        if not ret:
            continue

        fps         = fps_counter.tick()
        frame_count += 1

        frame = cv2.flip(frame, 1)

        landmarks, frame = mp_processor.process(frame)

        if landmarks:

            # -- velocity + detect --
            vel    = velocity.update(landmarks)
            events = detector.detect(landmarks, vel)

            if events:
                buffer.push_many(events)
                last_actions = events

                # Enforce sliding-window cap
                while len(buffer) > BUFFER_MAX_SIZE:
                    buffer.pop_oldest()

            snapshot = buffer.snapshot()
            sequence = snapshot.action_sequence   # list[ActionEvent]

            # -- ML (throttled) --
            if sequence and (frame_count % ML_INTERVAL == 0):
                try:
                    last_prediction = predictor.predict(sequence)
                    last_intent     = last_prediction
                except Exception as e:
                    print(f"[ML ERROR] {e}")

            prediction = last_prediction

            # -- Heuristic fallback when ML stuck on IDLE --
            ml_intent = getattr(getattr(prediction, "intent", None), "name", None)
            if ml_intent is None or ml_intent == "IDLE":
                h = _heuristic_from_sequence(sequence)
                if h:
                    prediction  = h
                    last_intent = h

            # -- Resolve --
            selected = None
            if prediction:
                try:
                    selected = resolver.resolve(prediction, snapshot)
                    if selected:
                        last_move = selected
                except Exception as e:
                    print(f"[RESOLVER ERROR] {e}")
                    traceback.print_exc()

            # -- Execute (with safe input parsing) --
            if selected:
                try:
                    if _executor_has_parser:
                        # executor already uses our parser
                        executor.execute(selected)
                    else:
                        # Manual safe execution: parse inputs before pressing
                        raw   = getattr(selected, "inputs", None)
                        safe  = parse_move_inputs(raw) if raw else []
                        if safe:
                            executor.execute_inputs(safe)
                        else:
                            executor.execute(selected)

                except Exception as e:
                    print(f"[EXEC ERROR] {e}")

        # -- HUD --
        draw_hud(frame, fps, last_actions, last_intent, last_move)
        cv2.imshow("TAI", cv2.resize(frame, (640, 360)))

        key = cv2.waitKey(1) & 0xFF

        if key == 27:   # ESC
            break

        if key in (ord('r'), ord('R')):
            buffer.clear()
            velocity.reset()
            detector.reset()
            last_prediction = None
            print("[TAI] Buffer reset")

    cap.release()
    cv2.destroyAllWindows()
    mp_processor.close()
    print("[TAI] Stopped.")


if __name__ == "__main__":
    run()