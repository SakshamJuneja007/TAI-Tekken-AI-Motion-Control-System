import time


class ComboAnalyzer:

    def __init__(self):
        self.sequence = []
        self.last_time = 0

        self.combo_window = 0.8


    def update(self, actions):

        now = time.time()

        if now - self.last_time > self.combo_window:
            self.sequence.clear()


        for action in actions:

            self.sequence.append(
                action.action
            )


        self.last_time = now


        return self.get_combo()



    def get_combo(self):

        if len(self.sequence) < 2:
            return None


        return [
            a.name 
            for a in self.sequence
        ]