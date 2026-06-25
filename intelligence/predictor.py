"""
TAI Intent Predictor
===================

ML brain:
Buffer action sequence
        |
        v
IntentBrain (LSTM)
        |
        v
CombatIntent
"""

import torch

from intelligence.intent_model import IntentBrain
from configs.constants import CombatIntent


class IntentPrediction:

    def __init__(
        self,
        intent,
        confidence
    ):
        self.intent = intent
        self.confidence = confidence

    def __repr__(self):
        return (
            f"IntentPrediction("
            f"{self.intent.name}, "
            f"{self.confidence:.3f})"
        )



class IntentPredictor:

    def __init__(
        self,
        model_path="models/intent_brain.pth"
    ):

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        print(
            f"[ML] Using device: {self.device}"
        )


        checkpoint = torch.load(
            model_path,
            map_location=self.device
        )


        self.action_to_id = (
            checkpoint["action_to_id"]
        )

        self.label_to_id = (
            checkpoint["label_to_id"]
        )


        self.id_to_label = {
            v:k
            for k,v in self.label_to_id.items()
        }

        print("\n===== LABELS =====")
        print(self.label_to_id)

        print("\n===== ACTION VOCAB =====")
        print(self.action_to_id)

        print("========================")


        self.model = IntentBrain(
            vocab=len(
                self.action_to_id
            ),
            classes=len(
                self.label_to_id
            )
        ).to(
            self.device
        )


        self.model.load_state_dict(
            checkpoint["model"]
        )

        self.model.eval()



        # Ignore noisy actions for now
        self.ignore_actions = {

            "STANCE",
            

        }


        print(
            "🔥 ML Intent Brain Loaded"
        )



    def predict(
        self,
        sequence
    ):

        MAX_LEN = 8


        if sequence is None:
            sequence = []



        ids = []


        print(
            "\n[RAW SEQUENCE]"
        )


        print(
            [
                a.name
                if hasattr(a,"name")
                else str(a)
                for a in sequence
            ]
        )



        for action in sequence:

            # ActionEvent
            if hasattr(action, "action"):
                name = action.action.name

            # AtomicAction
            elif hasattr(action, "name"):
                name = action.name

            else:
                name = str(action)

            ACTION_ALIASES = {
                "MOVE_FORWARD": "FORWARD",
                "MOVE_BACK": "BACK",
                "MOVE_LEFT": "BACK",
                "MOVE_RIGHT": "FORWARD",
                "CROUCH": "DOWN",
            }

            name = ACTION_ALIASES.get(name, name)

            if name in self.ignore_actions:
                print(
                    "[IGNORED ACTION]",
                    name
                )
                continue

            if name not in self.action_to_id:
                print(
                    "[UNKNOWN ACTION]",
                    name
                )
                continue

            print(
                "[ACTION MAP]",
                name,
                "=>",
                self.action_to_id[name]
            )

            ids.append(
                self.action_to_id[name]
            )




        # keep latest actions
        ids = ids[-MAX_LEN:]



        # padding
        ids += [
            0
        ] * (
            MAX_LEN - len(ids)
        )



        print(
            "[ML IDS]",
            ids
        )




        x = torch.tensor(
            [ids],
            dtype=torch.long
        ).to(
            self.device
        )



        with torch.no_grad():

            out = self.model(x)


            probs = torch.softmax(
                out,
                dim=1
            )



        idx = probs.argmax(
            dim=1
        ).item()



        label = self.id_to_label[idx]



        confidence = (
            probs[0][idx]
            .item()
        )



        print(
            "\n===== ML RESULT ====="
        )


        print(
            "LABEL:",
            label
        )


        print(
            "CONFIDENCE:",
            round(
                confidence,
                3
            )
        )


        print(
            "===================="
        )




        intent = self._convert(
            label
        )



        result = IntentPrediction(
            intent,
            confidence
        )


        print(
            "[ML INTENT]",
            result
        )


        return result




    def _convert(
        self,
        name
    ):


        name = name.upper()



        if name in CombatIntent.__members__:

            return CombatIntent[name]




        mapping = {


            "AGGRESSIVE":
            "PRESSURE",


            "PRESSURE":
            "PRESSURE",


            "MOVEMENT":
            "MOVEMENT",


            "LOW_ATTACK":
            "LOW_ATTACK",


            "LAUNCHER":
            "LAUNCHER",


            "DEFENSIVE":
            "DEFENSIVE",


            "IDLE":
            "IDLE"

        }



        if name in mapping:

            return CombatIntent[
                mapping[name]
            ]




        print(
            "[UNKNOWN INTENT]",
            name
        )



        return CombatIntent.MOVEMENT