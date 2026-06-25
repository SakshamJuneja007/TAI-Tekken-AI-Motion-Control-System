"""
TAI Combat State
================
Maintains short-term fight memory.

This is not game state.
It is the AI's memory of what the player is trying to do.
"""
print("STATE FILE LOADED")
from dataclasses import dataclass, field
from typing import List

from configs.constants import CombatIntent


@dataclass
class CombatState:

    # Recent executed moves
    move_history: List[str] = field(default_factory=list)

    # Recent intents
    intent_history: List[CombatIntent] = field(default_factory=list)

    # Style variables
    aggression: float = 0.0
    pressure: float = 0.0
    combo_count: int = 0


    def update_move(self, move_name: str):
        """
        Store executed move.
        """

        self.move_history.append(move_name)

        # keep memory small
        if len(self.move_history) > 20:
            self.move_history.pop(0)


    def update_intent(self, intent: CombatIntent):
        """
        Track player intention.
        """

        self.intent_history.append(intent)

        if len(self.intent_history) > 20:
            self.intent_history.pop(0)


        self._update_style(intent)



    def _update_style(self, intent):

        if intent == CombatIntent.PRESSURE:

            self.aggression += 0.1
            self.pressure += 0.2


        elif intent == CombatIntent.DEFENSIVE:

            self.pressure -= 0.2
            self.aggression -= 0.1


        else:

            self.pressure *= 0.9
            self.aggression *= 0.95



    def reset(self):

        self.move_history.clear()
        self.intent_history.clear()

        self.aggression = 0
        self.pressure = 0
        self.combo_count = 0