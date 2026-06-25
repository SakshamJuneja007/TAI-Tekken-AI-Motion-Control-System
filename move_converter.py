import json
from core.notation import TekkenParser



class MoveConverter:


    def __init__(self):

        self.parser = TekkenParser()



    def classify_intent(
        self,
        name,
        properties,
        hit_range=""
    ):

        text = (
            name +
            " " +
            properties +
            " " +
            hit_range
        ).lower()



        if any(x in text for x in [
            "launcher",
            "upper",
            "piston",
            "electric",
            "ewgf",
            "hopkick",
            "knd"
        ]):
            return "LAUNCHER"



        if any(x in text for x in [
            "low",
            "sweep",
            "hell",
            "crouch"
        ]):
            return "LOW_ATTACK"



        if any(x in text for x in [
            "counter",
            "parry",
            "reversal"
        ]):
            return "DEFENSIVE"



        if any(x in text for x in [
            "dash",
            "step"
        ]):
            return "MOVEMENT"



        return "PRESSURE"





    def convert_move(
        self,
        name,
        command,
        damage,
        hit_range,
        properties
    ):


        return {

            "name": name,

            "notation": command,

            "parsed":
            self.parser.parse(
                command
            ),

            "damage": damage,

            "range": hit_range,

            "intent":
            self.classify_intent(
                name,
                properties,
                hit_range
            ),

            "priority": 1,

            "cooldown": 0.5,

            "tags":
            properties.split()

        }







    def save(
        self,
        moves,
        path
    ):


        grouped = {}


        for move in moves.values():

            intent = move["intent"]


            if intent not in grouped:

                grouped[intent] = []


            grouped[intent].append(
                move
            )



        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                grouped,
                f,
                indent=4,
                ensure_ascii=False
            )








if __name__ == "__main__":


    converter = MoveConverter()


    moves = {}


    with open(
        "combat/jin_raw.json",
        encoding="utf-8"
    ) as f:

        raw = json.load(f)




    for category, rows in raw.items():


        print(
            "Processing:",
            category
        )


        if not rows:
            continue



        headers = rows[0]



        for row in rows[1:]:


            if len(row) < 2:
                continue



            name = row[0]


            command = row[1]


            damage = (
                row[2]
                if len(row) > 2
                else ""
            )


            hit_range = (
                row[3]
                if len(row) > 3
                else ""
            )


            properties = (
                row[4]
                if len(row) > 4
                else ""
            )



            data = converter.convert_move(
                name,
                command,
                damage,
                hit_range,
                properties
            )


            moves[name] = data
            # Add movement actions manually

movement_moves = [

    {
        "name": "Back Dash",
        "notation": "b,b",
        "parsed": converter.parser.parse("b,b"),
        "damage": "",
        "range": "",
        "intent": "MOVEMENT",
        "priority": 1,
        "cooldown": 0.2,
        "tags": ["movement"]
    },

    {
        "name": "Forward Dash",
        "notation": "f,f",
        "parsed": converter.parser.parse("f,f"),
        "damage": "",
        "range": "",
        "intent": "MOVEMENT",
        "priority": 1,
        "cooldown": 0.2,
        "tags": ["movement"]
    },


    {
        "name": "Side Step",
        "notation": "ss",
        "parsed": {
            "directions": [
                "SIDE_STEP"
            ],
            "buttons": [],
            "states": []
        },
        "damage": "",
        "range": "",
        "intent": "MOVEMENT",
        "priority": 1,
        "cooldown": 0.2,
        "tags": ["movement"]
    }
]


for move in movement_moves:

    moves[move["name"]] = move





    converter.save(
        moves,
        "combat/jin_moves.json"
    )



    print("\nConversion complete")

    print(
        "Moves converted:",
        len(moves)
    )


    print(
        "Intents:"
    )


    intents = set()

    for m in moves.values():
        intents.add(
            m["intent"]
        )

    print(intents)