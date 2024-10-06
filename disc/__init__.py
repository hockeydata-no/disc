import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
HOCKEYDATA_HOST = os.getenv("HOCKEYDATA_HOST")
HOCKEYDATA_API_KEY = os.getenv("HOCKEYDATA_API_KEY")
HOCKEYDATA_TEAM_NAME = os.getenv("HOCKEYDATA_TEAM_NAME").split(",")
DISPLAYED_TEAM_NAME = os.getenv("DISPLAYED_TEAM_NAME")
DISPLAY_TEAM_NAME_POSSESSIVE = (
    f"{DISPLAYED_TEAM_NAME}'s" if DISPLAYED_TEAM_NAME[-1] != "s" else f"{DISPLAYED_TEAM_NAME}'"
)
LANGUAGE = os.getenv("LANGUAGE", "en")
