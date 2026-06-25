import time


class CombatMemory:

    def __init__(self):

        self.moves = []
        self.intents = []


    def remember_move(self, move):

        self.moves.append(
            move.name
        )

        self.moves = self.moves[-10:]


    def remember_intent(self, intent):

        self.intents.append(
            intent.name
        )

        self.intents = self.intents[-10:]



    def is_repeating(self):

        if len(self.intents)<3:
            return False

        return (
            len(set(self.intents[-3:])) == 1
        )