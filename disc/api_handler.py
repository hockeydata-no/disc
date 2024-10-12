import json
import os
from datetime import datetime

import cachetools.func
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
def query(endpoint: str) -> dict:
    try:
        r = requests.get(endpoint, headers={"HockeyData-API-Key": HOCKEYDATA_API_KEY})
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(e)
        return {}


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
            else:
                disc_embed.hex_color = 0xFF0000
                disc_embed.description_key = "match_loss"

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
        "city": r["venue"]["city"],
        "timestamp": f"<t:{int(utc_date.timestamp())}:R>",
        "long_datetime": f"<t:{int(utc_date.timestamp())}:F>",
        "team_possessive": DISPLAY_TEAM_NAME_POSSESSIVE,
    }

    return DiscEmbed(title_key="next_match_title", description_key="next_match", values=values, hex_color=0xFFA500)


def _get_scorer_info() -> str:
    """Get information about the goalscorer and assists"""
    r = query(ENDPOINTS["goal_scorer"])
    if not r:
        return ""

    scorer = r["playerinfo"]["scorer"]
    assists = r["playerinfo"]["assists"]

    output_message = GLOBAL_MESSAGES["scorer_info"].format(scorer=scorer["fullName"], jersey=scorer["jerseyNumber"])
    for assist in assists:
        output_message += (
            f"\n{GLOBAL_MESSAGES['assist_info'].format(assist=assist["fullName"], jersey=assist['jerseyNumber'])}"
        )

    return output_message


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

    disc_embed = DiscEmbed(values=values)

    if int(old_score["team"]["score"]) < int(team["score"]):
        disc_embed.title_key = "goal_home_title"
        disc_embed.description_key = "goal_home"
        disc_embed.hex_color = 0x00FF00
        disc_embed.appended_description = _get_scorer_info()
    elif int(old_score["opponent"]["score"]) < int(opponent["score"]):
        disc_embed.title_key = "goal_away_title"
        disc_embed.description_key = "goal_away"
        disc_embed.hex_color = 0xFF0000

    data = {"team": team, "opponent": opponent}
    with open("data/score.json", "w") as f:
        json.dump(data, f)

    return disc_embed
