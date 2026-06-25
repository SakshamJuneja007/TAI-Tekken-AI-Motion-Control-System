import os
import json
import numpy as np

from configs.constants import CombatIntent


class MLIntentClassifier:


    def __init__(self):

        self.model = None
        self.loaded = False

        self.model_path = "ml/intent_brain2.pth"

        self.load_model()



    # =====================================
    # Load trained model later
    # =====================================

    def load_model(self):

        if os.path.exists(self.model_path):

            self.model = np.load(
                self.model_path,
                allow_pickle=True
            )

            self.loaded = True



    # =====================================
    # Convert actions -> features
    # =====================================

    def extract_features(self, snapshot):

        features = {

            "punch":0,
            "kick":0,
            "crouch":0,
            "movement":0,

            "speed":0.0,
            "count":len(snapshot)

        }


        total_speed = 0


        for action in snapshot:


            name = action.action.name


            if "PUNCH" in name:
                features["punch"] += 1


            if "KICK" in name:
                features["kick"] += 1


            if "CROUCH" in name:
                features["crouch"] += 1


            if "MOVE" in name:
                features["movement"] += 1



            if hasattr(action,"velocity_magnitude"):

                total_speed += (
                    action.velocity_magnitude
                )



        features["speed"] = total_speed



        return np.array([

            features["punch"],
            features["kick"],
            features["crouch"],
            features["movement"],
            features["speed"],
            features["count"]

        ],dtype=float)



    # =====================================
    # Predict intent
    # =====================================

    def predict(self, snapshot):


        if len(snapshot)==0:

            return None



        x = self.extract_features(
            snapshot
        )



        # ===============================
        # Temporary rule fallback
        # ===============================

        if not self.loaded:


            if x[2] > 0:

                return CombatIntent.LOW_ATTACK



            if x[0] > 0 and x[4] > 0.05:

                return CombatIntent.PRESSURE



            if x[3] > 0:

                return CombatIntent.MOVEMENT



            return CombatIntent.DEFENSIVE



        # ===============================
        # Future trained model
        # ===============================

        prediction = self.model.predict(
            [x]
        )


        return CombatIntent(
            prediction[0]
        )