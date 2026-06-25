"""
TAI Move Loader
===============
Loads Tekken move database
"""


import json
from pathlib import Path

from core.notation import TekkenParser



class MoveLoader:


    def __init__(self):

        self.parser = TekkenParser()



    def load_moves(self, path):

        path = Path(path)


        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            raw_moves = json.load(f)



        moves = {}



        for key, value in raw_moves.items():


            # metadata
            if key.startswith("_"):
                continue



            # FIX:
            # ignore non move entries

            if not isinstance(value, dict):
                continue



            move = value.copy()



            notation = move.get(
                "notation",
                ""
            )



            if notation:

                try:

                    move["parsed"] = self.parser.parse(
                        notation
                    )

                except Exception:

                    move["parsed"] = {
                        "directions": [],
                        "buttons": [],
                        "states": []
                    }

            else:

                move["parsed"] = {
                    "directions": [],
                    "buttons": [],
                    "states": []
                }



            move.setdefault(
                "name",
                key
            )


            move.setdefault(
                "priority",
                99
            )


            move.setdefault(
                "cooldown",
                0.5
            )


            move.setdefault(
                "tags",
                []
            )



            moves[key] = move



        print(
            f"[MOVE LOADER] Loaded {len(moves)} moves"
        )


        return moves





    def get_move(
        self,
        moves,
        name
    ):

        return moves.get(name)