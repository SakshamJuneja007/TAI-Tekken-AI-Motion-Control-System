"""
TAI Combat Intents — Rule-Based Classifier
==========================================
Translates a BufferSnapshot into a CombatIntent.

Design rationale:
  This serves as the Phase 1 brain and weak-labeller for the future ML model.
  It implements the same interface (BufferSnapshot -> IntentPrediction) 
  that the ML predictor will use, allowing zero-friction swaps later.

  Upgrades over previous baseline:
  - Velocity Weighting: Heavy/fast physical executions score significantly higher.
  - Strict Chronology: Inputs are checked sequentially (e.g., Forward -> Punch)
    via timestamps to match fighting game command syntax.
  - Neutral Fallback: Returns an explicit IDLE intent instead of None when 
    actions fall below thresholds.
"""

import time
from typing import Callable, Dict, Tuple

from configs.constants import AtomicAction, CombatIntent, Thresholds
from core.models import BufferSnapshot, IntentPrediction

# Action group definitions for backward compatibility with split inputs
PUNCH_ACTIONS = {
    AtomicAction.LEFT_PUNCH,
    AtomicAction.RIGHT_PUNCH,
}

KICK_ACTIONS = {
    AtomicAction.LEFT_KICK,
    AtomicAction.RIGHT_KICK,
}

ATTACK_ACTIONS = PUNCH_ACTIONS | KICK_ACTIONS

# Heuristic thresholds for input evaluation
FAST_ATTACK_VELOCITY = 0.025  # Normalized velocity floor for "fast" actions


# ---------------------------------------------------------------------------
# Scoring Functions
# Each receives the BufferSnapshot and returns a raw score in [0, 1].
# ---------------------------------------------------------------------------

def _score_pressure(snap: BufferSnapshot) -> float:
    """
    PRESSURE: Rapid or high-velocity punches, OR punch + forward movement.
    Velocity weighting ensures lazy movements don't register as pressure.
    """
    events = snap.action_sequence
    punches = [e for e in events if e.action in PUNCH_ACTIONS]
    forward = snap.count_action(AtomicAction.MOVE_FORWARD)

    if not punches:
        return 0.0

    # Calculate velocity bonus from intense/fast punches
    fast_punches = [p for p in punches if p.velocity_magnitude >= FAST_ATTACK_VELOCITY]
    
    if len(punches) >= 2:
        # Stronger signal if the strikes were executed with high velocity
        velocity_bonus = 0.2 if len(fast_punches) >= 2 else 0.0
        return min(0.6 + (len(punches) - 2) * 0.1 + forward * 0.1 + velocity_bonus, 1.0)
        
    if len(punches) >= 1 and forward >= 1:
        # Execution velocity determines the confidence of advancing pressure
        return 0.75 if fast_punches else 0.60
        
    if len(punches) == 1:
        # Allow a single strike to register as baseline pressure
        return 0.60 if fast_punches else 0.45
        
    return 0.0


def _score_launcher(snap: BufferSnapshot) -> float:
    """
    LAUNCHER: Jump -> Attack, or Forward -> Punch sequence.
    Strict timing verification prevents unrelated concurrent inputs from triggering.
    """
    events = snap.action_sequence
    
    # Track latest timestamps for clean sequence checking
    last_forward_t = max((e.timestamp for e in events if e.action == AtomicAction.MOVE_FORWARD), default=0.0)
    last_jump_t = max((e.timestamp for e in events if e.action == AtomicAction.JUMP), default=0.0)
    
    punches = [e for e in events if e.action in PUNCH_ACTIONS]
    kicks = [e for e in events if e.action in KICK_ACTIONS]
    
    # 1. Check Jump-Ins (Jump must precede the attack)
    if last_jump_t > 0.0:
        air_attack_t = max(
            [e.timestamp for e in punches + kicks if e.timestamp > last_jump_t], 
            default=0.0
        )
        if air_attack_t > last_jump_t:
            return 0.85

    # 2. Check Command Launchers (Forward must precede the punch attack)
    if last_forward_t > 0.0 and punches:
        launcher_punch_t = max([p.timestamp for p in punches if p.timestamp > last_forward_t], default=0.0)
        if launcher_punch_t > last_forward_t:
            # Velocity validation: real command attacks are delivered fast
            launcher_punch = [p for p in punches if p.timestamp == launcher_punch_t][0]
            return 0.80 if launcher_punch.velocity_magnitude >= FAST_ATTACK_VELOCITY else 0.65

    return 0.0


def _score_low_attack(snap: BufferSnapshot) -> float:
    """
    LOW_ATTACK: Crouching cleanly followed by a kick or punch.
    """
    events = snap.action_sequence
    crouches = [e for e in events if e.action == AtomicAction.CROUCH]
    attacks = [e for e in events if e.action in ATTACK_ACTIONS]

    if crouches and attacks:
        last_crouch_t = max(c.timestamp for c in crouches)
        # Check ordering: attack must execute *after* entering crouch state
        valid_low_attacks = [a for a in attacks if a.timestamp > last_crouch_t]
        
        if valid_low_attacks:
            # Check if execution velocity was high
            max_low_vel = max(a.velocity_magnitude for a in valid_low_attacks)
            return 0.90 if max_low_vel >= FAST_ATTACK_VELOCITY else 0.75
            
        return 0.40  # Out of order/simultaneous but still plausible
    return 0.0


def _score_defensive(snap: BufferSnapshot) -> float:
    """
    DEFENSIVE: Blocking or moving backward with low offense output.
    """
    blocks = snap.count_action(AtomicAction.BLOCK)
    backward = snap.count_action(AtomicAction.MOVE_BACKWARD)
    attacks = sum(1 for e in snap.action_sequence if e.action in ATTACK_ACTIONS)

    if attacks >= 2:
        return 0.0  # High offense cancels defensive posture evaluations

    if blocks >= 1 and backward >= 1:
        return 0.90
    if blocks >= 1:
        return 0.80
    if backward >= 2:
        return 0.65
    return 0.0


def _score_movement(snap: BufferSnapshot) -> float:
    """
    MOVEMENT: Clean directional positioning without combat execution metrics.
    """
    forward = snap.count_action(AtomicAction.MOVE_FORWARD)
    backward = snap.count_action(AtomicAction.MOVE_BACKWARD)
    jumps = snap.count_action(AtomicAction.JUMP)
    attacks = sum(1 for e in snap.action_sequence if e.action in ATTACK_ACTIONS)

    if attacks >= 1:
        return 0.0

    total_movement = forward + backward + jumps
    if total_movement >= 3:
        return 0.85
    if total_movement >= 1:
        return 0.60
    return 0.0


# ---------------------------------------------------------------------------
# Intent → scoring function registry
# ---------------------------------------------------------------------------

RULE_MAP: Dict[CombatIntent, Callable[[BufferSnapshot], float]] = {
    CombatIntent.PRESSURE:   _score_pressure,
    CombatIntent.LAUNCHER:   _score_launcher,
    CombatIntent.LOW_ATTACK: _score_low_attack,
    CombatIntent.DEFENSIVE:  _score_defensive,
    CombatIntent.MOVEMENT:   _score_movement,
}


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class RuleBasedIntentClassifier:
    """
    Stateless classifier. Call predict() with any BufferSnapshot.
    No side effects — the same snapshot always returns the same result.
    """

    def predict(self, snapshot: BufferSnapshot) -> IntentPrediction:
        """
        Score all intents and return the winner. Falls back to IDLE
        if no evaluation satisfies the confidence floor.
        """
        raw_scores: Dict[str, float] = {intent.name: 0.0 for intent in CombatIntent}
        
        # Populate operational scores from registry
        for intent, scorer in RULE_MAP.items():
            raw_scores[intent.name] = scorer(snapshot)

        best_name = max(raw_scores, key=lambda k: raw_scores[k])
        best_score = raw_scores[best_name]

        print("\n===== INTENT SCORES =====")
        for k, v in raw_scores.items():
            print(k, v)
        print("BEST:", best_name, best_score)
        print("========================\n")

        # Neutral Fallback: Verify against minimum threshold
        if best_score < Thresholds.MIN_INTENT_CONFIDENCE or not snapshot.action_sequence:
            raw_scores[CombatIntent.IDLE.name] = 1.0
            return IntentPrediction(
                intent=CombatIntent.IDLE,
                confidence=1.0,
                timestamp=time.time(),
                supporting_actions=(),
                raw_scores=raw_scores,
            )

        best_intent = CombatIntent[best_name]
        supporting = _find_supporting_actions(best_intent, snapshot)

        return IntentPrediction(
            intent=best_intent,
            confidence=best_score,
            timestamp=time.time(),
            supporting_actions=supporting,
            raw_scores=raw_scores,
        )

    def score_all(self, snapshot: BufferSnapshot) -> Dict[str, float]:
        """Debug helper: return all scores without filtering."""
        scores = {intent.name: 0.0 for intent in CombatIntent}
        for intent, scorer in RULE_MAP.items():
            scores[intent.name] = scorer(snapshot)
        return scores


def _find_supporting_actions(
    intent: CombatIntent,
    snap: BufferSnapshot,
) -> Tuple[AtomicAction, ...]:
    """Return which actions in the buffer match the selected intent signature."""
    relevant_map = {
        CombatIntent.PRESSURE:   {AtomicAction.LEFT_PUNCH, AtomicAction.RIGHT_PUNCH, AtomicAction.MOVE_FORWARD},
        CombatIntent.LAUNCHER:   {AtomicAction.JUMP, AtomicAction.LEFT_PUNCH, AtomicAction.RIGHT_PUNCH, AtomicAction.LEFT_KICK, AtomicAction.RIGHT_KICK, AtomicAction.MOVE_FORWARD},
        CombatIntent.LOW_ATTACK: {AtomicAction.CROUCH, AtomicAction.LEFT_PUNCH, AtomicAction.RIGHT_PUNCH, AtomicAction.LEFT_KICK, AtomicAction.RIGHT_KICK},
        CombatIntent.DEFENSIVE:  {AtomicAction.BLOCK, AtomicAction.MOVE_BACKWARD},
        CombatIntent.MOVEMENT:   {AtomicAction.MOVE_FORWARD, AtomicAction.MOVE_BACKWARD, AtomicAction.JUMP},
    }
    relevant = relevant_map.get(intent, set())
    seen = set()
    result = []
    for e in snap.action_sequence:
        if e.action in relevant and e.action not in seen:
            result.append(e.action)
            seen.add(e.action)
    return tuple(result)