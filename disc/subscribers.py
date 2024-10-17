import json
import os

from __init__ import LANGUAGE


def initialize() -> None:
    if not os.path.exists("data"):
        os.mkdir("data")
    if not os.path.exists("data/subscribers.json"):
        with open("data/subscribers.json", "w", encoding="utf-8") as f:
            json.dump({}, f)


def get_channels() -> dict:
    # TODO: Use a database instead of a json file
    with open("data/subscribers.json", encoding="utf-8") as f:
        data = json.load(f)
    return data


def get_settings(channel_id: str) -> dict:
    # TODO: Use a database instead of a json file
    channel_id = str(channel_id)
    with open("data/subscribers.json", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(channel_id, {"lang": LANGUAGE})


def set_lang(channel_id: str, lang: str) -> None:
    channel_id = str(channel_id)
    with open("data/subscribers.json", encoding="utf-8") as f:
        data = json.load(f)
    data[channel_id]["lang"] = lang
    with open("data/subscribers.json", "w", encoding="utf-8") as f:
        json.dump(data, f)


def toggle(channel_id: str, lang=LANGUAGE) -> bool:
    # TODO: Use a database instead of a json file
    channel_id = str(channel_id)
    new_subscriber = True
    with open("data/subscribers.json", encoding="utf-8") as f:
        data = json.load(f)

    # If the key "channel_id" exists in the dictionary, remove it
    if str(channel_id) in data.keys():
        data.pop(channel_id)
        new_subscriber = False
    else:
        data[channel_id] = dict({"lang": lang})
    with open("data/subscribers.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    return new_subscriber


def get_lang(channel_id: str) -> str:
    channel_id = str(channel_id)
    settings = get_settings(channel_id)
    return settings.get("lang", "en")


initialize()
