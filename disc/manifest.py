from typing import Literal

from __init__ import HOCKEYDATA_HOST

ENDPOINTS = {
    "score": f"{HOCKEYDATA_HOST}/live/score?provider=fangroup",
    "goal_scorer": f"{HOCKEYDATA_HOST}/live/recent-goal-scorer-stats",
    "status": f"{HOCKEYDATA_HOST}/live/match",
}

# Global messsages cannot be translated
GLOBAL_MESSAGES = {
    "scorer_info": "Scorer: **{scorer}**",
    "assist_info": "Assist: **{assist}**",
    "presence": "{team} {team_score} - {opponent_score} {opponent}",
}

FORMAT_MESSAGES = {
    "en": {
        "subscribe": "Channel is now subscribed. Forza {team}!",
        "unsubscribe": "Channel is now unsubscribed.",
        "active_channels_title": "Active channels",
        "active_channels": "{active_channels}",
        "no_active_channels": "No active channels",
        "goal_home_title": "{team} scored!",
        "goal_away_title": "{opponent} scored",
        "goal_home": "The score is now **{team} {team_score} - {opponent_score} {opponent}**",
        "goal_away": "The score is now **{team} {team_score} - {opponent_score} {opponent}**",
        "match_start": "**{team}** vs **{opponent}** are now playing in **{arena}**",
        "match_end": "Final score **{team} {team_score} - {opponent_score} {opponent}**",
        "next_match_title": "[{tournament_name}] {team_possessive} next match",
        "next_match": "**{team}** vs **{opponent}** will play in **{arena}, {city}** {timestamp}\n\n{long_datetime}",
        "no_next_match": "No scheduled match found",
    },
    "no": {
        "subscribe": "Kanalen er nå abonnert. Forza {team}!",
        "unsubscribe": "Kanalen er nå avabonnert.",
        "active_channels_title": "Aktive kanaler",
        "no_active_channels": "Ingen aktive kanaler",
        "goal_home_title": "{team} scoret!",
        "goal_away_title": "{opponent} scoret",
        "goal_home": "Stillingen er nå **{team} {team_score} - {opponent_score} {opponent}**",
        "goal_away": "Stillingen er nå **{team} {team_score} - {opponent_score} {opponent}**",
        "match_start": "**{team}** vs **{opponent}** spiller nå i **{arena}**",
        "match_end": "Sluttresultat **{team} {team_score} - {opponent_score} {opponent}**",
        "next_match_title": "[{tournament_name}] {team_possessive} neste kamp",
        "next_match": "**{team}** spiller mot **{opponent}** i **{arena}, {city}** {timestamp}\n\n{long_datetime}",
        "no_next_match": "Ingen planlagte kamper funnet",
    },
}

SUPPORTED_LANGUAGES = Literal["en", "no"]
