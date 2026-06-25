"""
TAI Constants
=============
Single source of truth for all enums, thresholds, and config.
"""

from enum import Enum, auto


# ---------------------------------------------------------------------------
# Atomic Actions
# ---------------------------------------------------------------------------

class AtomicAction(Enum):

    IDLE = auto()

    LEFT_PUNCH = auto()
    RIGHT_PUNCH = auto()

    LEFT_KICK = auto()
    RIGHT_KICK = auto()

    BLOCK = auto()
    CROUCH = auto()
    JUMP = auto()

    MOVE_FORWARD = auto()
    MOVE_BACKWARD = auto()



# ---------------------------------------------------------------------------
# Combat Intents
# Must match jin_moves.json exactly
# ---------------------------------------------------------------------------

class CombatIntent(Enum):

    IDLE = auto()

    # Exists in jin_moves.json
    PRESSURE = auto()

    # Exists in jin_moves.json
    LOW_ATTACK = auto()

    # Replaces old LAUNCHER
    # because move database uses COMBO
    COMBO = auto()

    DEFENSIVE = auto()

    MOVEMENT = auto()

    AGGRESSIVE = auto()

    GRAB = auto()



# ---------------------------------------------------------------------------
# MediaPipe Landmark Indices
# ---------------------------------------------------------------------------

class MP:

    NOSE = 0


    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12

    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14

    LEFT_WRIST = 15
    RIGHT_WRIST = 16


    LEFT_HIP = 23
    RIGHT_HIP = 24


    LEFT_KNEE = 25
    RIGHT_KNEE = 26


    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28



    WRISTS = [
        LEFT_WRIST,
        RIGHT_WRIST
    ]


    ANKLES = [
        LEFT_ANKLE,
        RIGHT_ANKLE
    ]


    SHOULDERS = [
        LEFT_SHOULDER,
        RIGHT_SHOULDER
    ]


    HIPS = [
        LEFT_HIP,
        RIGHT_HIP
    ]




# ---------------------------------------------------------------------------
# Detection Thresholds
# ---------------------------------------------------------------------------

class Thresholds:


    # -----------------------------
    # Velocity
    # -----------------------------

    PUNCH_VELOCITY = 0.015

    KICK_VELOCITY = 0.020



    # -----------------------------
    # Position
    # -----------------------------

    CROUCH_HIP_Y = 0.99

    JUMP_HIP_Y = 0.01

    BLOCK_WRIST_Y = 0.45




    # -----------------------------
    # Temporal
    # -----------------------------

    ACTION_COOLDOWN = 0.12

    BUFFER_WINDOW = 0.75

    INTENT_COOLDOWN = 1.0


    MAX_EVENTS = int(
        BUFFER_WINDOW * 30
    )




    # -----------------------------
    # Smoothing
    # -----------------------------

    EMA_ALPHA = 0.4




    # -----------------------------
    # Intent
    # -----------------------------

    MIN_INTENT_CONFIDENCE = 0.55




    # -----------------------------
    # Executor
    # -----------------------------

    MOVE_COOLDOWN = 0.5





# ---------------------------------------------------------------------------
# App Config
# ---------------------------------------------------------------------------

class Config:


    APP_TITLE = (
        "TAI — Motion-to-Intent Combat Engine"
    )


    CAMERA_WIDTH = 640

    CAMERA_HEIGHT = 480


    FPS_TARGET = 30


    LOG_LEVEL = "INFO"