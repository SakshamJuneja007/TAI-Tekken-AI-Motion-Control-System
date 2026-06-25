"""
TAI Move Brain
==============

Database driven move selector.

Flow:

CombatIntent
      |
      v
MoveBrain
      |
      v
jin_moves.json
      |
      v
SelectedMove
"""


import json
import random
from pathlib import Path


from configs.constants import CombatIntent
from core.models import SelectedMove



class MoveBrain:


    def __init__(self):

        self.moves = []

        self.load_moves()



    # -------------------------------------------------
    # LOAD DATABASE
    # -------------------------------------------------

    def load_moves(self):


        path = (
            Path(__file__)
            .resolve()
            .parent
            /
            "jin_moves.json"
        )


        if not path.exists():

            print(
                "[MOVE BRAIN] jin_moves.json missing"
            )

            return



        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)



        if isinstance(data, dict):

            self.moves = list(
                data.values()
            )

        else:

            self.moves = data



        print(
            f"[MOVE BRAIN] Loaded {len(self.moves)} moves"
        )



    # -------------------------------------------------
    # INTENT MAPPING
    # -------------------------------------------------

    def normalize_intent(self, intent):

        if isinstance(intent, CombatIntent):

            return intent


        if isinstance(intent, str):

            try:
                return CombatIntent[intent.upper()]
            except:
                return CombatIntent.PRESSURE


        return CombatIntent.PRESSURE



    # -------------------------------------------------
    # SELECT MOVE
    # -------------------------------------------------

    def select_move(
        self,
        intent,
        actions=None
    ):


        intent = self.normalize_intent(
            intent
        )


        intent_name = intent.name



        print(
            f"[MOVE BRAIN] intent: {intent_name}"
        )



        candidates = []



        # ---------------------------------------------
        # Direct intent match
        # ---------------------------------------------

        for move in self.moves:


            move_intent = (
                move
                .get(
                    "intent",
                    ""
                )
                .upper()
            )


            if move_intent == intent_name:

                candidates.append(move)




        print(
            "[CANDIDATES]",
            len(candidates)
        )



        # ---------------------------------------------
        # Launcher fallback
        # Dataset uses COMBO
        # ---------------------------------------------

        if (
            not candidates
            and
            intent == CombatIntent.COMBO
        ):


            print(
                "[LAUNCHER -> COMBO FALLBACK]"
            )


            for move in self.moves:


                if (
                    move
                    .get(
                        "intent",
                        ""
                    )
                    .upper()
                    ==
                    "COMBO"
                ):

                    candidates.append(move)




        # ---------------------------------------------
        # Grab fallback
        # ---------------------------------------------

        if (
            not candidates
            and
            intent == CombatIntent.GRAB
        ):


            print(
                "[GRAB -> PRESSURE FALLBACK]"
            )


            for move in self.moves:


                if (
                    move
                    .get(
                        "tags",
                        []
                    )
                    and
                    "Throws"
                    in
                    move["tags"]
                ):

                    candidates.append(move)




        # ---------------------------------------------
        # Aggressive fallback
        # ---------------------------------------------

        if (
            not candidates
            and
            intent == CombatIntent.AGGRESSIVE
        ):

            intent = CombatIntent.PRESSURE



        # ---------------------------------------------
        # Final pressure fallback
        # ---------------------------------------------

        if not candidates:


            print(
                "[FALLBACK PRESSURE]"
            )


            for move in self.moves:


                if (
                    move
                    .get(
                        "intent",
                        ""
                    )
                    .upper()
                    ==
                    "PRESSURE"
                ):

                    candidates.append(move)




        if not candidates:

            print(
                "[NO MOVE FOUND]"
            )

            return None




        # ---------------------------------------------
        # Priority sorting
        # ---------------------------------------------

        candidates.sort(
            key=lambda x:
            x.get(
                "priority",
                0
            ),
            reverse=True
        )



        chosen = random.choice(
            candidates[
                :
                min(
                    5,
                    len(candidates)
                )
            ]
        )



        print(
            "[CHOSEN]",
            chosen.get("name")
        )



        # ---------------------------------------------
        # Notation -> Executor Inputs
        # ---------------------------------------------

        notation = chosen.get(
            "notation",
            ""
        )


        inputs = tuple(
            x.strip()
            for x in
            notation
            .replace("+"," ")
            .replace(","," ")
            .split()
        )



        # ---------------------------------------------
        # Return SelectedMove
        # ---------------------------------------------

        return SelectedMove(


            name = chosen.get(
                "name",
                "UNKNOWN"
            ),


            inputs = inputs,


            intent = intent,


            confidence = 1.0,


            cooldown = chosen.get(
                "cooldown",
                0.5
            ),


            startup_frames = chosen.get(
                "startup_frames",
                0
            ),


            recovery_frames = chosen.get(
                "recovery_frames",
                0
            ),


            tags = tuple(
                chosen.get(
                    "tags",
                    []
                )
            )

        )