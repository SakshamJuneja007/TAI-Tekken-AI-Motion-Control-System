"""
TAI Combat Brain
================

High level move scoring layer.

Input:
    move database dictionaries

Output:
    selected move dictionary

This layer does not execute.
"""



from configs.constants import CombatIntent






class CombatBrain:



    def __init__(
        self,
        moves
    ):

        # JSON/database moves
        self.moves = moves







    def choose_move(
        self,
        intent,
        state
    ):



        candidates=[]





        for key, move in self.moves.items():



            score=0




            # -------------------------
            # safe dictionary access
            # -------------------------


            move_intent = move.get(
                "intent",
                None
            )



            ai = move.get(
                "ai",
                {}
            )



            move_name = move.get(
                "name",
                key
            )






            # -------------------------
            # intent matching
            # -------------------------


            if (
                move_intent
                ==
                intent.name
            ):

                score += 50






            # -------------------------
            # aggression
            # -------------------------


            score += (

                ai.get(
                    "aggression",
                    0
                )
                *
                getattr(
                    state,
                    "aggression",
                    0
                )

            )







            # -------------------------
            # pressure
            # -------------------------


            if getattr(
                state,
                "pressure",
                0
            ) > 0.5:


                score += ai.get(
                    "coolness",
                    0
                )








            # -------------------------
            # combo
            # -------------------------


            if getattr(
                state,
                "combo_count",
                0
            ) > 0:


                score += ai.get(
                    "combo",
                    0
                )








            score += move.get(
                "priority",
                0
            )






            candidates.append(
                (
                    score,
                    move
                )
            )








        if not candidates:

            return None







        candidates.sort(
            key=lambda x:x[0],
            reverse=True
        )




        # returns dictionary

        return candidates[0][1]