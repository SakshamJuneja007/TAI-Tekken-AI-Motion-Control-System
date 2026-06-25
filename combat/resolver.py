"""
TAI Combat Resolver
===================

Connects:
ML Intent Prediction
        ↓
Combat Intent  (with heuristic override when ML returns IDLE)
        ↓
Action-based Move Filter  (blocks kicks when no kick detected, etc.)
        ↓
Move Brain  (with repeat-penalty so AI doesn't spam same move)
        ↓
Selected Move

Fixes applied (see debugging report):
  - snapshot.actions → snapshot.action_sequence  [was crashing every frame]
  - No longer returns None when snapshot is missing actions
  - Heuristic override when ML is stuck on IDLE (now shared with
    run_tai.py via core.heuristics.dominant_action — see note below)
  - Move filtering by detected action category (punches → no kicks)
  - Repeat-penalty: tracks last N moves, down-weights already-used ones
  - Reduced logging: verbose output only when something actually changes

Fix applied in THIS revision (was still broken before):
  - "sweep" was incorrectly listed as an allowed category for CROUCH.
    That meant a crouch + punch buffer (zero leg movement detected)
    could still authorize a move like "Double High Sweep" — exactly the
    bug described in the report (leg/kick moves firing with no leg
    input). "sweep" now lives only under LEFT_KICK / RIGHT_KICK, so a
    sweep move requires an actual kick action in the buffer.

Known remaining risk (not silently fixed — see explicit warning below):
  - If intelligence/move_brain.py's select_move() hasn't ALSO been
    updated to accept `allowed_categories` / `move_history`, the
    `except TypeError` fallback below reverts to the old unfiltered
    random selection with NO visible error. That defeats P1 (move
    filtering) and P2 (repeat-penalty) silently. This revision now
    prints an explicit one-time [WARNING] when that fallback path is
    hit, so it's no longer invisible during testing.
"""

from intelligence.move_brain import MoveBrain
from core.heuristics import dominant_action


# ---------------------------------------------------------------------------
# Action → allowed move category mapping
# ---------------------------------------------------------------------------
# Keys are AtomicAction names.  Values are sets of move-category tags that
# MoveBrain is allowed to consider.  If a tag is absent from a move, that
# move is filtered out.
#
# IMPORTANT: "sweep" / "kick" / "leg" tags belong ONLY to actions that
# actually involve a leg (LEFT_KICK / RIGHT_KICK). Do not add them back
# to CROUCH — that was the root cause of kicks firing on punch-only input.
#
# Adjust these to match whatever tags your move database uses.
# ---------------------------------------------------------------------------

_ACTION_ALLOWED_CATEGORIES = {
    "LEFT_PUNCH":  {"punch", "jab", "pressure", "string"},
    "RIGHT_PUNCH": {"punch", "jab", "pressure", "string"},
    "LEFT_KICK":   {"kick", "leg", "pressure", "sweep"},
    "RIGHT_KICK":  {"kick", "leg", "pressure", "sweep"},
    "CROUCH":      {"low", "crouch", "pressure"},
    "JUMP":        {"jump", "aerial", "launcher"},
    "STEP_LEFT":   {"sidestep", "pressure"},
    "STEP_RIGHT":  {"sidestep", "pressure"},
}

# How many recently used moves to remember and penalise
_MOVE_HISTORY_SIZE = 6


class CombatResolver:

    def __init__(self):
        self.move_brain    = MoveBrain()
        self._move_history = []          # list of move names, most-recent last
        self._last_intent  = None        # for change-detection logging
        self._warned_no_filter_support = False   # only print the TypeError warning once

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def resolve(self, prediction, snapshot):

        # ---- extract intent ----
        try:
            intent = prediction.intent
        except Exception:
            print("[RESOLVER ERROR] invalid prediction")
            return None

        if hasattr(intent, "name"):
            intent = intent.name

        confidence = getattr(prediction, "confidence", 0.0)

        if confidence < 0.35:
            intent = "PRESSURE"

        # Only print when intent changes (reduces log spam)
        if intent != self._last_intent:
            print(f"\n[RESOLVE] {intent} | confidence: {confidence:.3f}")
            self._last_intent = intent

        # ---- get action sequence ----
        action_sequence = []
        try:
            action_sequence = list(snapshot.action_sequence or [])
        except Exception as e:
            print(f"[SNAPSHOT ERROR] {e}")
            # continue — MoveBrain can work with empty sequence

        # ---- heuristic override when ML stuck on IDLE ----
        if intent == "IDLE" and action_sequence:
            intent = self._dominant_action_intent(action_sequence) or intent

        # ---- build allowed-category filter from detected actions ----
        allowed_categories = self._allowed_categories(action_sequence)

        # ---- ask MoveBrain, with repeat-penalty ----
        try:
            move = self.move_brain.select_move(
                intent,
                action_sequence,
                allowed_categories=allowed_categories,
                move_history=list(self._move_history),
            )

            if move:
                self._push_history(move)
                print(f"[SELECTED MOVE] {move.name}")

            return move

        except TypeError:
            # MoveBrain doesn't support the new kwargs yet — fall back to
            # the original signature so nothing crashes, but make SURE
            # this is visible instead of silently dropping filtering and
            # repeat-penalty.
            if not self._warned_no_filter_support:
                print(
                    "[WARNING] MoveBrain.select_move() does not accept "
                    "allowed_categories/move_history kwargs. Falling back "
                    "to the unfiltered original call signature — move "
                    "filtering (P1) and repeat-penalty (P2) are NOT "
                    "active until intelligence/move_brain.py is updated "
                    "to accept these arguments. (This warning prints once.)"
                )
                self._warned_no_filter_support = True

            move = self.move_brain.select_move(intent, action_sequence)
            if move:
                self._push_history(move)
                print(f"[SELECTED MOVE] {move.name}")
            return move

        except Exception as e:
            print(f"[MOVE BRAIN ERROR] {e}")
            return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _dominant_action_intent(self, action_sequence, threshold=0.6):
        """
        If the buffer is ≥threshold dominated by one non-IDLE action,
        return that action name as the intent string.  Else return None.

        Delegates to core.heuristics.dominant_action so this stays in
        sync with the equivalent fallback in run_tai.py.
        """
        result = dominant_action(action_sequence, threshold=threshold)
        if result is None:
            return None

        name, ratio = result
        print(f"[HEURISTIC OVERRIDE] IDLE → {name} ({ratio:.0%} of buffer)")
        return name

    def _allowed_categories(self, action_sequence):
        """
        Return the union of allowed move categories for every distinct
        action in the buffer.  Returns None (= no filter) if the sequence
        is empty or no mapping exists.
        """
        if not action_sequence:
            return None

        categories = set()
        for event in action_sequence:
            name = event.action.name
            cats = _ACTION_ALLOWED_CATEGORIES.get(name)
            if cats:
                categories |= cats

        return categories if categories else None

    def _push_history(self, move):
        self._move_history.append(move.name)
        if len(self._move_history) > _MOVE_HISTORY_SIZE:
            self._move_history.pop(0)