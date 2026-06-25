"""
TAI ML Dataset Loader
=====================

Loads combat_dataset.json
and prepares tensors for LSTM
"""


import json
import torch

from torch.utils.data import Dataset



class CombatDataset(Dataset):


    def __init__(
        self,
        path,
        max_len=20
    ):

        self.max_len = max_len


        with open(
            path,
            encoding="utf-8"
        ) as f:

            self.data = json.load(f)



        # build vocabulary

        tokens = set()


        for item in self.data:

            tokens.update(
                item["sequence"]
            )



        self.token_to_id = {

            token:i+1
            for i,token in enumerate(tokens)

        }


        self.token_to_id["PAD"] = 0



        self.intent_to_id = {

            "PRESSURE":0,
            "LAUNCHER":1,
            "LOW_ATTACK":2,
            "DEFENSIVE":3,
            "MOVEMENT":4,
            "COMBO":5

        }




    def encode_sequence(
        self,
        seq
    ):


        ids = [

            self.token_to_id[x]
            for x in seq

        ]



        ids = ids[:self.max_len]



        while len(ids) < self.max_len:

            ids.append(0)



        return ids





    def __len__(self):

        return len(
            self.data
        )





    def __getitem__(
        self,
        index
    ):


        item = self.data[index]



        sequence = torch.tensor(
            self.encode_sequence(
                item["sequence"]
            ),
            dtype=torch.long
        )



        features = torch.tensor(
            [

                item["features"]["velocity"],

                item["features"]["acceleration"],

                item["features"]["duration"],

                item["features"]["distance"],

                item["features"]["confidence"]

            ],
            dtype=torch.float
        )



        label = torch.tensor(

            self.intent_to_id[
                item["label"]
            ],

            dtype=torch.long

        )



        return (
            sequence,
            features,
            label
        )