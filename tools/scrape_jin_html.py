"""
TAI Combat Dataset Generator
============================

Generates ML training data from jin_moves.json

Goal:
Train the combat intent model.

Input:
    action sequence
    motion features
    move context

Output:
    combat intent label


Pipeline:

jin_moves.json
        |
        v
synthetic combat samples
        |
        v
combat_dataset.json

"""


import json
import random
from pathlib import Path



# =================================================
# PATHS
# =================================================


BASE = Path(__file__).parent.parent


MOVE_DB = BASE / "tools/jin_moves.json"

OUTPUT = BASE / "tools/new_combat_dataset.json"



# =================================================
# SETTINGS
# =================================================


SAMPLES_PER_MOVE = 80



INTENTS = [
    "PRESSURE",
    "LAUNCHER",
    "LOW_ATTACK",
    "DEFENSIVE",
    "MOVEMENT",
    "COMBO"
]



# =================================================
# LOAD DATABASE
# =================================================


with open(
    MOVE_DB,
    encoding="utf-8"
) as f:

    moves = json.load(f)



dataset = []



# =================================================
# FEATURE SIMULATION
# =================================================


def generate_features(
):

    return {


        "velocity":
            round(
                random.uniform(
                    0.3,
                    1.0
                ),
                3
            ),



        "acceleration":
            round(
                random.uniform(
                    0.1,
                    1.0
                ),
                3
            ),



        "duration":
            round(
                random.uniform(
                    0.05,
                    0.6
                ),
                3
            ),



        "distance":
            round(
                random.uniform(
                    0.1,
                    1.0
                ),
                3
            ),



        "confidence":
            round(
                random.uniform(
                    0.7,
                    1.0
                ),
                3
            )

    }




# =================================================
# EXTRACT ACTION SEQUENCE
# =================================================


def extract_sequence(
        move
):

    parsed = move.get(
        "parsed",
        {}
    )


    sequence = []


    # directions first
    for d in parsed.get(
        "directions",
        []
    ):

        sequence.append(d)



    # buttons
    for b in parsed.get(
        "buttons",
        []
    ):

        sequence.append(b)



    return sequence




# =================================================
# CREATE DATASET
# =================================================


for name, move in moves.items():


    intent = move.get(
        "intent",
        "PRESSURE"
    )


    if intent not in INTENTS:
        continue



    sequence = extract_sequence(
        move
    )



    if not sequence:
        continue




    for _ in range(
        SAMPLES_PER_MOVE
    ):


        sample = {


            # what player did
            "sequence":
                sequence,



            # motion information
            "features":
                generate_features(),



            # move intelligence
            "move_context":{


                "move":
                    name,



                "priority":
                    move.get(
                        "priority",
                        1
                    ),



                "cooldown":
                    move.get(
                        "cooldown",
                        0.5
                    ),



                "type":
                    move.get(
                        "type",
                        "move"
                    ),



                "tags":
                    move.get(
                        "tags",
                        []
                    )

            },



            # target for ML
            "label":
                intent

        }


        dataset.append(
            sample
        )




# =================================================
# ADD NOISE
# =================================================

random.shuffle(
    dataset
)



# =================================================
# SAVE
# =================================================


with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:


    json.dump(
        dataset,
        f,
        indent=4,
        ensure_ascii=False
    )



print(
    "Combat dataset created"
)


print(
    "Total samples:",
    len(dataset)
)