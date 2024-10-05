import json
import os


def initialize():
    if not os.path.exists("data"):
        os.mkdir("data")
    if not os.path.exists("data/subscribers.json"):
        with open("data/subscribers.json", "w") as f:
            json.dump([], f)


def get_channels():
    with open("data/subscribers.json") as f:
        data = json.load(f)
    return data


def toggle(channel_id: str) -> bool:
    new_subscriber = True
    with open("data/subscribers.json") as f:
        data = json.load(f)
    if channel_id in data:
        data.remove(channel_id)
        new_subscriber = False
    else:
        data.append(channel_id)
    with open("data/subscribers.json", "w") as f:
        json.dump(data, f)
    return new_subscriber


initialize()
