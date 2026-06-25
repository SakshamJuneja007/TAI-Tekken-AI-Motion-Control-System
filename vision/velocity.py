"""
TAI Velocity Estimator
======================
Converts sequential LandmarkFrames into per-landmark velocity vectors.

Design rationale:
  Raw frame-to-frame displacement is noisy (camera jitter, MediaPipe
  sub-pixel variance). Exponential Moving Average (EMA) smoothing damps
  high-frequency noise while preserving the leading edge of real motion.

  Alpha=0.4 means: new_ema = 0.4 * raw + 0.6 * previous
  Higher alpha -> faster response, more noise.
  Lower alpha -> smoother, more lag.

  We track only 2D (xy) magnitude because z from a monocular webcam is
  reconstruction noise, not real depth. Detectors should not use dz.
"""

import math
import time
from typing import Dict, List

from configs.constants import MP, Thresholds
from core.models import LandmarkFrame, LandmarkPoint, VelocityState, VelocityVector


class VelocityEstimator:
    """
    Stateful estimator: call update() once per frame.
    Maintains one VelocityState per tracked landmark across frames.
    """

    # Only estimate velocity for landmarks the detector actually needs.
    # Tracking all 33 pose landmarks wastes cycles.
    TRACKED_LANDMARKS = MP.WRISTS + MP.ANKLES + MP.SHOULDERS + MP.HIPS

    def __init__(self, alpha: float = Thresholds.EMA_ALPHA):
        self.alpha = alpha
        self._states: Dict[int, VelocityState] = {}
        self._last_frame: Dict[int, LandmarkPoint] = {}

    def update(self, frame: LandmarkFrame) -> Dict[int, VelocityVector]:
        """
        Consume one LandmarkFrame, return velocity vectors for all
        tracked landmarks that appear in this frame.
        """
        velocities: Dict[int, VelocityVector] = {}

        for lm_id in self.TRACKED_LANDMARKS:
            point = frame.landmarks.get(lm_id)
            if point is None or point.visibility < 0.5:
                # Landmark not visible — don't corrupt the EMA state
                continue

            if lm_id not in self._states:
                # First time seeing this landmark — initialize state, skip velocity
                self._states[lm_id] = VelocityState(
                    landmark_id=lm_id,
                    prev_x=point.x,
                    prev_y=point.y,
                    prev_z=point.z,
                )
                continue

            state = self._states[lm_id]

            # Raw frame displacement
            raw_dx = point.x - state.prev_x
            raw_dy = point.y - state.prev_y
            raw_dz = point.z - state.prev_z

            # EMA smoothing
            state.ema_dx = self.alpha * raw_dx + (1 - self.alpha) * state.ema_dx
            state.ema_dy = self.alpha * raw_dy + (1 - self.alpha) * state.ema_dy
            state.ema_dz = self.alpha * raw_dz + (1 - self.alpha) * state.ema_dz

            # Update prev position
            state.prev_x = point.x
            state.prev_y = point.y
            state.prev_z = point.z

            magnitude = math.sqrt(state.ema_dx**2 + state.ema_dy**2)

            velocities[lm_id] = VelocityVector(
                landmark_id=lm_id,
                dx=state.ema_dx,
                dy=state.ema_dy,
                dz=state.ema_dz,
                magnitude=magnitude,
                timestamp=frame.timestamp,
            )

        return velocities

    def reset(self) -> None:
        """Clear all state — call when the subject leaves the frame."""
        self._states.clear()
