"""
TAI MediaPipe Processor
=======================
MediaPipe Pose -> LandmarkFrame
Also draws skeleton overlay.
"""

import time
import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False


from core.models import LandmarkFrame, LandmarkPoint


class MediaPipeProcessor:

    def __init__(
        self,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    ):

        self._frame_counter = 0
        self._pose = None

        if MP_AVAILABLE:

            self.mp_pose = mp.solutions.pose
            self.mp_draw = mp.solutions.drawing_utils

            self._pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=0,  # <--- CHANGED FROM 1 TO 0 FOR REAL-TIME SPEED
                enable_segmentation=False,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )


    def process(self, frame_bgr):

        if not self._pose:
            return None, frame_bgr

        rgb = cv2.cvtColor(
            frame_bgr,
            cv2.COLOR_BGR2RGB
        )

        result = self._pose.process(rgb)

        if not result.pose_landmarks:
            return None, frame_bgr

        self._frame_counter += 1

        landmarks={}

        for idx,lm in enumerate(result.pose_landmarks.landmark):

            landmarks[idx] = LandmarkPoint(
                x=lm.x,
                y=lm.y,
                z=lm.z,
                visibility=lm.visibility
            )


        # skeleton overlay
        self.mp_draw.draw_landmarks(
            frame_bgr,
            result.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS
        )

        landmark_frame = LandmarkFrame(
            landmarks=landmarks,
            timestamp=time.time(),
            frame_id=self._frame_counter
        )

        return landmark_frame, frame_bgr

    def close(self):

        if self._pose:
            self._pose.close()