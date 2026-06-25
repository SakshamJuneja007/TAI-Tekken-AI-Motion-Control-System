"""
TAI Models
==========

All data contracts between pipeline layers.

Vision
 -> Detection
 -> Buffer
 -> Intent
 -> Resolver
 -> Executor
"""


from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

from configs.constants import (
    AtomicAction,
    CombatIntent
)



# =====================================
# VISION
# =====================================


@dataclass(frozen=True)
class LandmarkPoint:

    x: float
    y: float
    z: float

    visibility: float = 1.0



@dataclass(frozen=True)
class LandmarkFrame:

    landmarks: Dict[int, LandmarkPoint]

    timestamp: float = field(
        default_factory=time.time
    )

    frame_id: int = 0




# =====================================
# VELOCITY
# =====================================


@dataclass
class VelocityVector:

    landmark_id: int

    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0

    magnitude: float = 0.0

    timestamp: float = field(
        default_factory=time.time
    )




@dataclass
class VelocityState:

    landmark_id: int

    prev_x: float = 0.0
    prev_y: float = 0.0
    prev_z: float = 0.0

    ema_dx: float = 0.0
    ema_dy: float = 0.0
    ema_dz: float = 0.0





# =====================================
# ACTION DETECTION
# =====================================


@dataclass(frozen=True)
class ActionEvent:


    action: AtomicAction

    confidence: float


    timestamp: float = field(
        default_factory=time.time
    )


    source_landmark_id: Optional[int] = None


    velocity_magnitude: float = 0.0





# =====================================
# BUFFER
# =====================================


@dataclass
class BufferSnapshot:


    action_sequence: List[ActionEvent]

    window_seconds: float


    captured_at: float = field(
        default_factory=time.time
    )


    def action_types(self):

        return [
            x.action
            for x in self.action_sequence
        ]



    def has_action(self, action):

        return any(
            x.action == action
            for x in self.action_sequence
        )



    def count_action(self, action):

        return sum(
            1
            for x in self.action_sequence
            if x.action == action
        )





# =====================================
# INTENT
# =====================================


@dataclass(frozen=True)
class IntentPrediction:


    intent: CombatIntent

    confidence: float


    timestamp: float = field(
        default_factory=time.time
    )


    supporting_actions: tuple = ()


    raw_scores: Dict[str,float] = field(
        default_factory=dict
    )





# =====================================
# MOVE
# =====================================


@dataclass(frozen=True)
class SelectedMove:


    name: str


    # Executor expects:
    # ("forward","2")
    inputs: tuple[str,...]


    intent: CombatIntent


    confidence: float


    cooldown: float = 0.5


    startup_frames: int = 0


    recovery_frames: int = 0


    tags: tuple[str,...] = ()


    timestamp: float = field(
        default_factory=time.time
    )





# =====================================
# EXECUTION STATE
# =====================================


@dataclass
class ExecutionState:


    busy: bool = False


    current_move: Optional[str] = None


    started_at: float = 0.0


    expected_duration: float = 0.0



    def remaining_time(self):

        elapsed = (
            time.time()
            -
            self.started_at
        )


        return max(
            0,
            self.expected_duration
            -
            elapsed
        )





# =====================================
# DATASET
# =====================================


@dataclass
class LabelledSequence:


    snapshot: BufferSnapshot


    label: CombatIntent


    recorded_by: str = "human"


    notes: str = ""


    timestamp: float = field(
        default_factory=time.time
    )



    def to_dict(self):

        return {

            "label":
            self.label.name,


            "recorded_by":
            self.recorded_by,


            "timestamp":
            self.timestamp,


            "actions":

            [

                {

                    "action":
                    e.action.name,


                    "confidence":
                    e.confidence,


                    "velocity":
                    e.velocity_magnitude

                }

                for e in self.snapshot.action_sequence

            ]

        }