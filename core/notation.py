"""
TAI Tekken Notation Parser
==========================

Converts Tekken notation:

    f+2
    df+1
    ws+4
    EWGF style inputs
    qcf+2

into structured input data.

Output is later consumed by MoveExecutor.
"""


import re

from enum import Enum, auto



# --------------------------------------------------
# Input Types
# --------------------------------------------------

class InputAction(Enum):

    FORWARD = auto()
    BACK = auto()

    DOWN = auto()
    UP = auto()

    DOWN_FORWARD = auto()
    DOWN_BACK = auto()

    UP_FORWARD = auto()
    UP_BACK = auto()


    LEFT_PUNCH = auto()
    RIGHT_PUNCH = auto()

    LEFT_KICK = auto()
    RIGHT_KICK = auto()



# --------------------------------------------------
# Tekken Symbols
# --------------------------------------------------

DIRECTIONS = {

    "f": InputAction.FORWARD,
    "b": InputAction.BACK,

    "d": InputAction.DOWN,
    "u": InputAction.UP,


    "df": InputAction.DOWN_FORWARD,
    "db": InputAction.DOWN_BACK,

    "uf": InputAction.UP_FORWARD,
    "ub": InputAction.UP_BACK,

}



BUTTONS = {

    "1": InputAction.LEFT_PUNCH,
    "2": InputAction.RIGHT_PUNCH,

    "3": InputAction.LEFT_KICK,
    "4": InputAction.RIGHT_KICK

}





# --------------------------------------------------
# AtomicAction -> ML Encoder
# --------------------------------------------------

try:

    from configs.constants import AtomicAction


    ACTION_TO_ID = {

        AtomicAction.LEFT_PUNCH: 2,

        AtomicAction.RIGHT_PUNCH: 3,

        AtomicAction.LEFT_KICK: 4,

        AtomicAction.RIGHT_KICK: 5,

        AtomicAction.BLOCK: 6,

        AtomicAction.CROUCH: 7,

    }


except Exception:


    ACTION_TO_ID = {}





# --------------------------------------------------
# Parser
# --------------------------------------------------

class TekkenParser:


    def normalize(self, command):


        command = (
            command
            .lower()
            .replace(" ", "")
        )



        replacements = {


            "d/f": "df",
            "d/b": "db",

            "u/f": "uf",
            "u/b": "ub",


            "qcf": "df",
            "qcb": "db",


            "n": "",

            "~": ""

        }



        for old,new in replacements.items():

            command = command.replace(
                old,
                new
            )



        return command





    def parse(self, command):


        result = {


            "directions": [],

            "buttons": [],

            "states": []

        }



        command = self.normalize(command)





        # stance

        if "ws+" in command:


            result["states"].append(
                "WHILE_STANDING"
            )


            command = command.replace(
                "ws+",
                ""
            )




        if "ss+" in command:


            result["states"].append(
                "SIDESTEP"
            )


            command = command.replace(
                "ss+",
                ""
            )






        command = (
            command
            .replace("[","")
            .replace("]","")
        )





        parts = command.split(",")




        for part in parts:


            tokens = part.split("+")



            for token in tokens:


                if token == "":
                    continue



                token = re.sub(
                    r"\(.*?\)",
                    "",
                    token
                )





                if token in DIRECTIONS:


                    result["directions"].append(

                        DIRECTIONS[token].name

                    )




                elif token in BUTTONS:


                    result["buttons"].append(

                        BUTTONS[token].name

                    )





                else:


                    result["states"].append(
                        token
                    )



        return result





# --------------------------------------------------
# helper for ML
# --------------------------------------------------

def action_to_id(action):


    """
    Converts AtomicAction into ML integer.
    """

    return ACTION_TO_ID.get(
        action,
        0
    )