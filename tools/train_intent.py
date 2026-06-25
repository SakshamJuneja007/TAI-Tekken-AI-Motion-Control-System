import json
from pathlib import Path


path = Path("intelligence/jin_moves.json")


with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)


print("TOTAL MOVES:", len(data))


intents = {}


for name, move in data.items():

    intent = move.get("intent")

    if intent not in intents:
        intents[intent] = 0

    intents[intent] += 1


print("\nINTENTS:")
for k,v in intents.items():
    print(k, "=", v)



print("\nSAMPLE MOVE:")
for k,v in list(data.items())[:5]:

    print("\nNAME:", k)
    print(v)