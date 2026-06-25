import json
import random


class CombatBrain:


    def __init__(
        self,
        move_file
    ):

        with open(
            move_file,
            encoding="utf-8"
        ) as f:

            self.moves=json.load(f)



    def score_move(
        self,
        move,
        intent,
        distance
    ):

        score=0



        # intent match

        if move["intent"] == intent:

            score += 50

        else:

            score -= 20



        # priority

        score += (
            move.get(
                "priority",
                1
            )
            *10
        )



        # distance logic

        tags=" ".join(
            move.get(
                "tags",
                []
            )
        ).lower()



        if distance < 0.4:

            if "mid" in tags:
                score+=10


        if distance >0.7:

            if "throw" not in tags:
                score+=5



        # randomness
        # avoids same move forever

        score += random.randint(
            -5,
            5
        )


        return score




    def choose_move(
        self,
        intent,
        distance=0.5
    ):


        best=None
        best_score=-999


        for name,move in self.moves.items():


            s=self.score_move(
                move,
                intent,
                distance
            )


            if s>best_score:

                best_score=s
                best=name



        return {

            "move":best,

            "score":best_score

        }