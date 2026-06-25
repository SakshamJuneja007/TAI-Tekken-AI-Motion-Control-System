"""
TAI — Shared Heuristic Helpers
===============================

Both run_tai.py (ML/IDLE fallback at the top-level loop) and
combat/resolver.py (intent-level IDLE override) need the exact same
calculation: "if the action buffer is dominated by one non-IDLE action,
treat that as the signal instead of trusting a stuck ML model."

This was previously implemented TWICE, independently, each with its own
hard-coded 0.6 threshold. That's a latent bug: if one copy ever gets
tuned and the other doesn't, the top-level loop and the resolver start
disagreeing about what "dominant" means, and you get inconsistent
behavior that's hard to trace. This module is now the single source of
truth — both call sites import from here.
"""

DEFAULT_THRESHOLD = 0.6


def dominant_action(action_sequence, threshold=DEFAULT_THRESHOLD):
    """
    Given an iterable of ActionEvent objects (each exposing `.action.name`),
    find the action that occurs most often in the sequence.

    Returns:
        (name: str, ratio: float)
            if that action is not IDLE and makes up at least `threshold`
            fraction of the sequence.
        None
            otherwise — sequence is empty, the dominant action IS IDLE,
            or it didn't clear the threshold.
    """
    if not action_sequence:
        return None

    names = [e.action.name for e in action_sequence]
    dominant = max(set(names), key=names.count)
    ratio = names.count(dominant) / len(names)

    if dominant != "IDLE" and ratio >= threshold:
        return dominant, ratio

    return None
