"""
TAI Feature Extractor
=====================
Converts a BufferSnapshot into feature representations for ML models.

Design rationale:
  Supports two extraction modes to bridge Phase 1 and Phase 2:
  
  1. extract_histogram(): 
     Fixed-size vector using bucketed temporal distribution. Great for 
     Logistic Regression, Random Forests, or simple MLPs. Encodes rough 
     timing but loses exact input ordering.

  2. extract_sequence():
     True time-series extraction for LSTMs/Transformers. Preserves exact 
     ordering, delta times between inputs, and granular confidence/velocity.
"""

import math
from typing import List

import numpy as np

from configs.constants import AtomicAction
from core.models import BufferSnapshot


WINDOW_BUCKETS = 4
ACTIONS = list(AtomicAction)       # ordered list for consistent indexing
N_ACTIONS = len(ACTIONS)           # 8 including IDLE
FEATURE_SIZE = N_ACTIONS + (N_ACTIONS * WINDOW_BUCKETS) + 2


class FeatureExtractor:

    def extract_histogram(self, snapshot: BufferSnapshot) -> np.ndarray:
        """
        Convert a BufferSnapshot into a fixed-size float32 feature vector.
        Returns zeros if the buffer is empty.
        """
        features = np.zeros(FEATURE_SIZE, dtype=np.float32)

        if not snapshot.action_sequence:
            return features

        events = snapshot.action_sequence
        window = snapshot.window_seconds

        # --- Global action counts (normalized by window) ---
        action_index = {a: i for i, a in enumerate(ACTIONS)}
        for event in events:
            idx = action_index.get(event.action, -1)
            if idx >= 0:
                features[idx] += 1.0
        # Normalize counts
        max_count = max(features[:N_ACTIONS].max(), 1.0)
        features[:N_ACTIONS] /= max_count

        # --- Bucketed temporal distribution ---
        now = snapshot.captured_at  # Fixed: guarantees deterministic features
        bucket_duration = window / WINDOW_BUCKETS
        base_offset = N_ACTIONS

        for event in events:
            age = now - event.timestamp
            if age > window or age < 0:
                continue
            bucket = min(int(age / bucket_duration), WINDOW_BUCKETS - 1)
            # Bucket 0 = oldest, bucket 3 = most recent
            bucket = WINDOW_BUCKETS - 1 - bucket
            idx = action_index.get(event.action, -1)
            if idx >= 0:
                feat_idx = base_offset + bucket * N_ACTIONS + idx
                features[feat_idx] = 1.0

        # --- Scalar features ---
        scalar_offset = N_ACTIONS + N_ACTIONS * WINDOW_BUCKETS
        magnitudes = [e.velocity_magnitude for e in events if e.velocity_magnitude > 0]
        features[scalar_offset] = max(magnitudes) if magnitudes else 0.0
        features[scalar_offset + 1] = (
            sum(e.confidence for e in events) / len(events)
        )

        return features

    def extract_sequence(
        self, 
        snapshot: BufferSnapshot, 
        sequence_length: int = 20
    ) -> List[List[float]]:
        """
        Extracts an ordered time-series sequence for LSTMs/Transformers.
        Returns a list of length `sequence_length`, padded with zeros.
        Format per step: [action_id, delta_time, velocity, confidence]
        """
        sequence = []
        events = snapshot.action_sequence

        if not events:
            return [[0.0, 0.0, 0.0, 0.0] for _ in range(sequence_length)]

        action_index = {a: float(i) for i, a in enumerate(ACTIONS)}
        first_time = events[0].timestamp

        for event in events:
            action_id = action_index.get(event.action, 0.0)
            # Time elapsed since the first event in the sequence
            delta_time = event.timestamp - first_time 
            velocity = event.velocity_magnitude
            confidence = event.confidence
            sequence.append([action_id, delta_time, velocity, confidence])

        # Truncate if too long (keep the most recent events)
        if len(sequence) > sequence_length:
            sequence = sequence[-sequence_length:]

        # Pad if too short (pad left so recent events align at the end)
        pad_len = sequence_length - len(sequence)
        if pad_len > 0:
            pad = [[0.0, 0.0, 0.0, 0.0] for _ in range(pad_len)]
            sequence = pad + sequence

        return sequence

    @property
    def feature_size(self) -> int:
        return FEATURE_SIZE