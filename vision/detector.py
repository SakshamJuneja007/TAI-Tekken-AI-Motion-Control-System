"""
TAI Atomic Action Detector
==========================
Converts a LandmarkFrame + velocity map into zero or more ActionEvents.
"""

import time
from typing import Dict, List, Optional

from configs.constants import AtomicAction, MP, Thresholds
from core.models import ActionEvent, LandmarkFrame, VelocityVector


class AtomicActionDetector:

    def __init__(self):
        # Per-action last-fired timestamp for cooldown enforcement
        self._last_fired: Dict[AtomicAction, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(
        self,
        frame: LandmarkFrame,
        velocities: Dict[int, VelocityVector],
    ) -> List[ActionEvent]:
        """
        Run all detectors against the current frame.
        Returns a list of ActionEvents (may be empty, may have multiple).
        """
        events: List[ActionEvent] = []

        lm = frame.landmarks  # shorthand

        # Order matters: positional states first, then velocity-based
        result = self._detect_crouch(lm)
        if result:
            events.append(result)

        result = self._detect_jump(lm)
        if result:
            events.append(result)

        result = self._detect_block(lm)
        if result:
            events.append(result)

        result = self._detect_punch(lm, velocities)
        if result:
            events.append(result)

        result = self._detect_kick(lm, velocities)
        if result:
            events.append(result)

        result = self._detect_move_forward(lm, velocities)
        if result:
            events.append(result)

        result = self._detect_move_backward(lm, velocities)
        if result:
            events.append(result)

        # Update cooldown timers for fired actions
        for event in events:
            self._last_fired[event.action] = event.timestamp

        return events

    # ------------------------------------------------------------------
    # Individual Detectors
    # ------------------------------------------------------------------

    def _on_cooldown(self, action: AtomicAction, now: float) -> bool:
        last = self._last_fired.get(action, 0.0)
        return (now - last) < Thresholds.ACTION_COOLDOWN

    def _detect_punch(
        self,
        lm: dict,
        velocities: Dict[int, VelocityVector],
    ) -> Optional[ActionEvent]:
        
        now = time.time()
        best_vel = 0.0
        best_lm_id = None

        for wrist_id in MP.WRISTS:
            v = velocities.get(wrist_id)
            if v and v.magnitude > best_vel:
                best_vel = v.magnitude
                best_lm_id = wrist_id

        if best_vel < Thresholds.PUNCH_VELOCITY:
            return None

        # Action Identification
        if best_lm_id == MP.LEFT_WRIST:
            action = AtomicAction.LEFT_PUNCH
        elif best_lm_id == MP.RIGHT_WRIST:
            action = AtomicAction.RIGHT_PUNCH
        else:
            return None

        if self._on_cooldown(action, now):
            return None

        confidence = min(
            (best_vel - Thresholds.PUNCH_VELOCITY)
            / (Thresholds.PUNCH_VELOCITY * 2)
            + 0.5,
            1.0,
        )

        return ActionEvent(
            action=action,
            confidence=confidence,
            timestamp=now,
            source_landmark_id=best_lm_id,
            velocity_magnitude=best_vel,
        )

    def _detect_kick(
        self,
        lm: dict,
        velocities: Dict[int, VelocityVector],
    ) -> Optional[ActionEvent]:
        now = time.time()
        best_vel = 0.0
        best_lm_id = None
        for ankle_id in MP.ANKLES:
            v = velocities.get(ankle_id)
            if v and v.magnitude > best_vel:
                best_vel = v.magnitude
                best_lm_id = ankle_id

        if best_vel < Thresholds.KICK_VELOCITY:
            return None

        if best_lm_id == MP.LEFT_ANKLE:
            action = AtomicAction.LEFT_KICK
        elif best_lm_id == MP.RIGHT_ANKLE:
            action = AtomicAction.RIGHT_KICK
        else:
            return None

        if self._on_cooldown(action, now):
            return None

        confidence = min(
            (best_vel - Thresholds.KICK_VELOCITY) /
            (Thresholds.KICK_VELOCITY * 2) + 0.5,
            1.0,
        )

        return ActionEvent(
            action=action,
            confidence=confidence,
            timestamp=now,
            source_landmark_id=best_lm_id,
            velocity_magnitude=best_vel,
        )

    def _detect_crouch(self, lm: dict) -> Optional[ActionEvent]:
        now = time.time()
        if self._on_cooldown(AtomicAction.CROUCH, now):
            return None

        left = lm.get(MP.LEFT_HIP)
        right = lm.get(MP.RIGHT_HIP)
        if not (left and right):
            return None

        avg_hip_y = (left.y + right.y) / 2.0
        
        # DEBUG: Print this value to see why crouch is spamming
        print(f"[DEBUG] Hip Y: {avg_hip_y:.4f} | Threshold: {Thresholds.CROUCH_HIP_Y}")

        if avg_hip_y < Thresholds.CROUCH_HIP_Y:
            return None

        confidence = min(
            (avg_hip_y - Thresholds.CROUCH_HIP_Y) / 0.2 + 0.6,
            1.0,
        )

        return ActionEvent(
            action=AtomicAction.CROUCH,
            confidence=confidence,
            timestamp=now,
        )

    def _detect_jump(self, lm: dict) -> Optional[ActionEvent]:
        now = time.time()
        if self._on_cooldown(AtomicAction.JUMP, now):
            return None

        left = lm.get(MP.LEFT_HIP)
        right = lm.get(MP.RIGHT_HIP)
        if not (left and right):
            return None

        avg_hip_y = (left.y + right.y) / 2.0
        if avg_hip_y > Thresholds.JUMP_HIP_Y:
            return None

        confidence = min(
            (Thresholds.JUMP_HIP_Y - avg_hip_y) / 0.2 + 0.6,
            1.0,
        )

        return ActionEvent(
            action=AtomicAction.JUMP,
            confidence=confidence,
            timestamp=now,
        )

    def _detect_block(self, lm: dict) -> Optional[ActionEvent]:
        now = time.time()
        if self._on_cooldown(AtomicAction.BLOCK, now):
            return None

        lw = lm.get(MP.LEFT_WRIST)
        rw = lm.get(MP.RIGHT_WRIST)
        if not (lw and rw):
            return None

        both_raised = (lw.y < Thresholds.BLOCK_WRIST_Y and
                       rw.y < Thresholds.BLOCK_WRIST_Y)
        close_x = abs(lw.x - rw.x) < 0.25

        if not (both_raised and close_x):
            return None

        avg_wrist_y = (lw.y + rw.y) / 2.0
        confidence = min(
            (Thresholds.BLOCK_WRIST_Y - avg_wrist_y) / 0.15 + 0.6,
            1.0,
        )

        return ActionEvent(
            action=AtomicAction.BLOCK,
            confidence=confidence,
            timestamp=now,
        )

    def _detect_move_forward(
        self,
        lm: dict,
        velocities: Dict[int, VelocityVector],
    ) -> Optional[ActionEvent]:
        now = time.time()
        if self._on_cooldown(AtomicAction.MOVE_FORWARD, now):
            return None

        vl = velocities.get(MP.LEFT_SHOULDER)
        vr = velocities.get(MP.RIGHT_SHOULDER)
        if not (vl and vr):
            return None

        avg_dx = (vl.dx + vr.dx) / 2.0
        threshold = 0.015

        if avg_dx > -threshold:
            return None

        confidence = min(abs(avg_dx) / (threshold * 3) + 0.5, 1.0)

        return ActionEvent(
            action=AtomicAction.MOVE_FORWARD,
            confidence=confidence,
            timestamp=now,
            velocity_magnitude=abs(avg_dx),
        )

    def _detect_move_backward(
        self,
        lm: dict,
        velocities: Dict[int, VelocityVector],
    ) -> Optional[ActionEvent]:
        now = time.time()
        if self._on_cooldown(AtomicAction.MOVE_BACKWARD, now):
            return None

        vl = velocities.get(MP.LEFT_SHOULDER)
        vr = velocities.get(MP.RIGHT_SHOULDER)
        if not (vl and vr):
            return None

        avg_dx = (vl.dx + vr.dx) / 2.0
        threshold = 0.015

        if avg_dx < threshold:
            return None

        confidence = min(avg_dx / (threshold * 3) + 0.5, 1.0)

        return ActionEvent(
            action=AtomicAction.MOVE_BACKWARD,
            confidence=confidence,
            timestamp=now,
            velocity_magnitude=avg_dx,
        )

    def reset(self) -> None:
        self._last_fired.clear()