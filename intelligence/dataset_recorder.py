import json
import os
import time


class IntentDatasetRecorder:

    def __init__(self):

        os.makedirs(
            "dataset",
            exist_ok=True
        )

        self.file = "dataset/intents.jsonl"



    def record(self, snapshot, intent):

        sample = {

            "time": time.time(),

            "intent": (
                intent.name
                if hasattr(intent, "name")
                else intent
            ),

            "actions": []

        }


        for a in snapshot:

            sample["actions"].append({

                "action": a.action.name,

                "confidence": float(a.confidence),

                "velocity": float(a.velocity_magnitude)

            })


        with open(
            self.file,
            "a"
        ) as f:

            f.write(
                json.dumps(sample)
                + "\n"
            )