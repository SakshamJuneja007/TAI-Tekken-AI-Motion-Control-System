import json
from collections import Counter

with open("intent_dataset2.json") as f:
    data = json.load(f)

labels = [x["label"] for x in data]

print(Counter(labels))