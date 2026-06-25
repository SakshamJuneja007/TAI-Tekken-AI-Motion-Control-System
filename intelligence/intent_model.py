import torch
import torch.nn as nn


class IntentBrain(nn.Module):

    def __init__(
        self,
        vocab,
        classes
    ):

        super().__init__()


        self.embed = nn.Embedding(
            vocab + 1,
            32,
            padding_idx=0
        )


        self.lstm = nn.LSTM(
            32,
            64,
            batch_first=True,
            bidirectional=True
        )


        self.fc = nn.Sequential(

            nn.Linear(
                128,
                64
            ),

            nn.ReLU(),

            nn.Dropout(
                0.2
            ),

            nn.Linear(
                64,
                classes
            )
        )



    def forward(
        self,
        x
    ):


        x = self.embed(x)


        _,(h,_) = self.lstm(x)


        h = torch.cat(
            (
                h[0],
                h[1]
            ),
            dim=1
        )


        return self.fc(h)