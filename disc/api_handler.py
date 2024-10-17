import json
import os
import tempfile
from datetime import datetime
from typing import Union

import cachetools.func
import discord
import requests

from __init__ import (
    HOCKEYDATA_API_KEY,
    HOCKEYDATA_TEAM_NAME,
    DISPLAYED_TEAM_NAME,
    DISPLAY_TEAM_NAME_POSSESSIVE,
)
from manifest import ENDPOINTS, GLOBAL_MESSAGES
from models import DiscEmbed, DiscException, MatchStatus


@cachetools.func.ttl_cache(ttl=15)
def query(endpoint: str, as_json: bool = True) -> Union[dict, requests.Response]:
    try:
        r = requests.get(endpoint, headers={"HockeyData-API-Key": HOCKEYDATA_API_KEY})
        r.raise_for_status()
        if as_json:
            return r.json()
        return r
    except requests.exceptions.RequestException as e:
        print(e)
        return {}


def get_team_image(team_name: str = DISPLAYED_TEAM_NAME) -> discord.File:
    """Get the image of the team"""
    r = query(ENDPOINTS["team_image"].format(team_name=team_name), as_json=False)
    if not r:
        raise DiscException("No image found")

    # TODO: We should probably delete temp files on a regular basis, or store them a different way
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(r.content)
        return discord.File(temp_file.name, "team_image.png")


def get_player_image(player_id: int, image_type: str = "") -> discord.File:
    """Get the image URL of a player"""
    r = query(ENDPOINTS["player_image"].format(player_id=player_id, image_type=image_type), as_json=False)
    if not r:
        raise DiscException("No image found")

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(r.content)
        return discord.File(temp_file.name, "player_image.png")


def get_match_status() -> DiscEmbed:
    # TODO: Remove json file and use a database
    if os.path.exists("data/match.json"):
        with open("data/match.json") as f:
            old_status = json.load(f)
    else:
        old_status = {"status": MatchStatus.Scheduled.value}

    r = query(ENDPOINTS["status"])
    if not r:
        raise DiscException("No data")

    is_home = r["homeTeam"]["fullName"] in HOCKEYDATA_TEAM_NAME

    just_started = r["status"] == MatchStatus.InProgress.value and old_status["status"] == MatchStatus.Scheduled.value
    just_ended = r["status"] == MatchStatus.Finished.value and old_status["status"] == MatchStatus.InProgress.value

    values = {
        "opponent": r["awayTeam"]["fullName"] if is_home else r["homeTeam"]["fullName"],
        "team": DISPLAYED_TEAM_NAME,
        "arena": r["venue"]["name"],
        "team_score": "Error",
        "opponent_score": "Error",
    }

    disc_embed = DiscEmbed(values=values, hex_color=0x00FF00)

    if just_started:
        disc_embed.title_key = "match_start_title"
        disc_embed.description_key = "match_start"
        disc_embed.hex_color = 0x00FF00
    elif just_ended:
        disc_embed.title_key = "match_end_title"
        disc_embed.description_key = "match_end"
        disc_embed.hex_color = 0xFFA500
        score = query(ENDPOINTS["score"])

        if score:
            disc_embed.values["team_score"] = score["homeTeam"]["score"] if is_home else score["awayTeam"]["score"]
            disc_embed.values["opponent_score"] = score["awayTeam"]["score"] if is_home else score["homeTeam"]["score"]
            winner = disc_embed.values["team_score"] > disc_embed.values["opponent_score"]
            if winner:
                disc_embed.hex_color = 0x00FF00
                disc_embed.description_key = "match_win"
                disc_embed.thumbnail = get_team_image(values["team"])
            else:
                disc_embed.hex_color = 0xFF0000
                disc_embed.description_key = "match_loss"
                disc_embed.thumbnail = get_team_image(values["opponent"])

    disc_embed.extra_data = {
        "active_match": r["status"] == MatchStatus.InProgress.value,
    }

    with open("data/match.json", "w") as f:
        json.dump(r, f)
    return disc_embed


def get_next_match() -> DiscEmbed:
    """Get information about the next match"""
    r = query(ENDPOINTS["status"])
    if not r or not r["status"] == MatchStatus.Scheduled.value:
        raise DiscException

    is_home = r["homeTeam"]["fullName"] in HOCKEYDATA_TEAM_NAME
    utc_date = datetime.fromisoformat(r["date"])

    values = {
        "tournament_name": r["tournament"]["name"],
        "opponent": r["awayTeam"]["fullName"] if is_home else r["homeTeam"]["fullName"],
        "team": DISPLAYED_TEAM_NAME,
        "arena": r["venue"]["name"],
        "timestamp": f"<t:{int(utc_date.timestamp())}:R>",
        "long_datetime": f"<t:{int(utc_date.timestamp())}:F>",
        "team_possessive": DISPLAY_TEAM_NAME_POSSESSIVE,
    }

    return DiscEmbed(title_key="next_match_title", description_key="next_match", values=values, hex_color=0xFFA500)


def _get_scorer_info() -> dict:
    """Get information about the goalscorer and assists"""
    r = query(ENDPOINTS["goal_scorer"])
    if not r:
        return {}

    scorer = r["playerinfo"]["scorer"]
    assists = r["playerinfo"]["assists"]

    output_message = (
        f"\n{GLOBAL_MESSAGES['scorer_info'].format(scorer=scorer['fullName'], jersey=scorer['jerseyNumber'])}"
    )
    for assist in assists:
        output_message += (
            f"\n{GLOBAL_MESSAGES['assist_info'].format(assist=assist["fullName"], jersey=assist['jerseyNumber'])}"
        )

    return {
        "appended_description": output_message,
        "player_id": scorer["id"],
    }


def get_presence_string() -> str:
    """Get the presence string for the bot"""
    r = query(ENDPOINTS["score"])
    if not r:
        raise DiscException("No data")

    is_home = r["homeTeam"]["team"] in HOCKEYDATA_TEAM_NAME

    values = {
        "team_score": r["homeTeam"]["score"] if is_home else r["awayTeam"]["score"],
        "opponent_score": r["awayTeam"]["score"] if is_home else r["homeTeam"]["score"],
        "opponent": r["awayTeam"]["team"] if is_home else r["homeTeam"]["team"],
        "team": DISPLAYED_TEAM_NAME,
    }

    return GLOBAL_MESSAGES["presence"].format(**values)


def get_goal() -> DiscEmbed:
    """Get information about the goal and the scorer (if there was a goal)"""
    # TODO: Remove json file and use a database
    if os.path.exists("data/score.json"):
        with open("data/score.json") as f:
            old_score = json.load(f)
    else:
        old_score = dict(
            {
                "team": {"score": 0, "team": DISPLAYED_TEAM_NAME},
                "opponent": {"score": 0, "team": "Unknown"},
            }
        )

    r = query(ENDPOINTS["score"])
    if not r:
        raise DiscException("No data")

    home_team = r["homeTeam"]
    away_team = r["awayTeam"]
    team_is_home = home_team["team"] in HOCKEYDATA_TEAM_NAME
    team = home_team if team_is_home else away_team
    opponent = away_team if team_is_home else home_team

    values = {
        "home_team": r["homeTeam"],
        "away_team": r["awayTeam"],
        "team": DISPLAYED_TEAM_NAME,
        "opponent": opponent["team"],
        "team_score": team["score"],
        "opponent_score": opponent["score"],
    }

    data = {"team": team, "opponent": opponent}
    with open("data/score.json", "w") as f:
        json.dump(data, f)

    disc_embed = DiscEmbed(values=values)

    if int(old_score["team"]["score"]) < int(team["score"]):
        disc_embed.title_key = "goal_home_title"
        disc_embed.description_key = "goal_home"
        disc_embed.hex_color = 0x00FF00
        disc_embed.thumbnail = get_team_image(values["team"])
        scorer_info = _get_scorer_info()
        if scorer_info:
            disc_embed.appended_description = scorer_info["appended_description"]
            # Overwrite the thumbnail with the player image if there is one
            disc_embed.thumbnail = get_player_image(scorer_info["player_id"], image_type="goal")
    elif int(old_score["opponent"]["score"]) < int(opponent["score"]):
        disc_embed.title_key = "goal_away_title"
        disc_embed.description_key = "goal_away"
        disc_embed.thumbnail = get_team_image(values["opponent"])
        disc_embed.hex_color = 0xFF0000

    return disc_embed
