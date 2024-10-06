import json
import os
from datetime import datetime

import requests

from __init__ import (
    HOCKEYDATA_API_KEY,
    HOCKEYDATA_TEAM_NAME,
    DISPLAYED_TEAM_NAME,
    DISPLAY_TEAM_NAME_POSSESSIVE,
)
from manifest import ENDPOINTS, GLOBAL_MESSAGES
from models import DiscString, DiscException, MatchStatus


def query(endpoint: str) -> dict:
    try:
        r = requests.get(endpoint, headers={"HockeyData-API-Key": HOCKEYDATA_API_KEY})
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(e)
        return {}


def get_match_status() -> DiscString:
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

    values = {
        "team_score": r["homeGoals"] if is_home else r["awayGoals"],
        "opponent_score": r["awayGoals"] if is_home else r["homeGoals"],
        "opponent": r["awayTeam"]["fullName"] if is_home else r["homeTeam"]["fullName"],
        "team": DISPLAYED_TEAM_NAME,
        "arena": r["venue"]["name"],
    }

    discstring = DiscString(values=values, hex_color=0x00FF00)

    just_started = r["status"] == MatchStatus.InProgress.value and old_status["status"] == MatchStatus.Scheduled.value
    just_ended = r["status"] == MatchStatus.Finished.value and old_status["status"] == MatchStatus.InProgress.value

    if just_started:
        discstring.title_key = "Match started!"
        discstring.description_key = "match_start"
        discstring.hex_color = 0x00FF00
    elif just_ended:
        discstring.title_key = "Match ended!"
        discstring.description_key = "match_end"
        discstring.hex_color = 0xFF0000

    discstring.extra_data = {
        "presence_string": GLOBAL_MESSAGES["presence"].format(**values),
        "active_match": r["status"] == MatchStatus.InProgress.value,
    }

    with open("data/match.json", "w") as f:
        json.dump(r, f)
    return discstring


def get_next_match() -> DiscString:
    """Get information about the next match"""
    r = query(ENDPOINTS["status"])
    if not r or not r["status"] == MatchStatus.Scheduled.value:
        raise DiscException

    is_home = r["homeTeam"]["fullName"] in HOCKEYDATA_TEAM_NAME
    utc_date = datetime.fromisoformat(r["date"])

    values = {
        "tournament_name": r["tournament"]["fullName"],
        "team_score": r["homeGoals"] if is_home else r["awayGoals"],
        "opponent_score": r["awayGoals"] if is_home else r["homeGoals"],
        "opponent": r["awayTeam"]["fullName"] if is_home else r["homeTeam"]["fullName"],
        "team": DISPLAYED_TEAM_NAME,
        "arena": r["venue"]["name"],
        "city": r["venue"]["city"],
        "timestamp": f"<t:{int(utc_date.timestamp())}:R>",
        "long_datetime": f"<t:{int(utc_date.timestamp())}:F>",
        "team_possessive": DISPLAY_TEAM_NAME_POSSESSIVE,
    }

    return DiscString(title_key="next_match_title", description_key="next_match", values=values, hex_color=0xFFA500)


def _get_scorer_info() -> str:
    """Get information about the goalscorer and assists"""
    r = query(ENDPOINTS["goal_scorer"])
    if not r:
        return ""

    scorer = r["playerinfo"]["scorer"]
    assists = r["playerinfo"]["assists"]

    scorer_name = f"{scorer['firstName']} {scorer['lastName']}"

    output_message = GLOBAL_MESSAGES["scorer_info"].format(scorer=scorer_name)
    for assist in assists:
        assist_name = f"{assist['firstName']} {assist['lastName']}"
        output_message += f"\n{GLOBAL_MESSAGES['assist_info'].format(assist=assist_name)}"

    return output_message


def get_goal() -> DiscString:
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

    discstring = DiscString(values=values)

    if int(old_score["team"]["score"]) < int(team["score"]):
        discstring.title_key = "goal_home_title"
        discstring.description_key = "goal_home"
        discstring.hex_color = 0x00FF00
        discstring.appended_description = _get_scorer_info()
    elif int(old_score["opponent"]["score"]) < int(opponent["score"]):
        discstring.title_key = "goal_away_title"
        discstring.description_key = "goal_away"
        discstring.hex_color = 0xFF0000

    data = {"team": team, "opponent": opponent}
    with open("data/score.json", "w") as f:
        json.dump(data, f)

    return discstring
