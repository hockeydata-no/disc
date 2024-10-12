from typing import Literal

from __init__ import HOCKEYDATA_HOST

ENDPOINTS = {
    "score": f"{HOCKEYDATA_HOST}/live/score",
    "goal_scorer": f"{HOCKEYDATA_HOST}/live/recent-goal-scorer-stats",
    "status": f"{HOCKEYDATA_HOST}/live/match",
}

# Global messsages cannot be translated
GLOBAL_MESSAGES = {
    "scorer_info": "Scorer: **#{jersey} {scorer}**",
    "assist_info": "Assist: **#{jersey} {assist}**",
    "presence": "{team} {team_score} - {opponent_score} {opponent}",
}

# TODO: Setup something more scalable than a dictionary
FORMAT_MESSAGES = {
    "en": {
        "subscribe": "Channel is now subscribed. Forza {team}! 🏒🥳",
        "unsubscribe": "Channel is now unsubscribed.",
        "active_channels_title": "Active channels",
        "active_channels": "{active_channels}",
        "no_active_channels": "No active channels",
        "goal_home_title": "{team} scored! 🥳",
        "goal_away_title": "{opponent} scored 😓",
        "goal_home": "The score is now **{team} {team_score} - {opponent_score} {opponent}**",
        "goal_away": "The score is now **{team} {team_score} - {opponent_score} {opponent}**",
        "match_start": "**{team}** vs **{opponent}** are now playing in **{arena}**",
        "match_end": "Final score **{team} {team_score} - {opponent_score} {opponent}**",
        "match_win": "Final score **{team} {team_score} - {opponent_score} {opponent}**\n\nCongratulations to **{team}** for winning the match! 🏒🥳",
        "match_loss": "Final score **{team} {team_score} - {opponent_score} {opponent}**\n\nBetter luck next time **{team}** 😓",
        "match_start_title": "Match started 🏒",
        "match_end_title": "Match ended 🏒",
        "next_match_title": "[{tournament_name}] {team_possessive} next match",
        "next_match": "**{team}** vs **{opponent}** will play in **{arena}** {timestamp}\n\n{long_datetime}",
        "no_next_match": "No scheduled match found",
        "language_set": "Language has been set to English",
    },
    "no": {
        "subscribe": "Kanalen er nå abonnert. Forza {team}! 🏒🥳",
        "unsubscribe": "Kanalen er nå avabonnert.",
        "active_channels_title": "Aktive kanaler",
        "no_active_channels": "Ingen aktive kanaler",
        "goal_home_title": "{team} scoret! 🥳",
        "goal_away_title": "{opponent} scoret 😓",
        "goal_home": "Stillingen er nå **{team} {team_score} - {opponent_score} {opponent}**",
        "goal_away": "Stillingen er nå **{team} {team_score} - {opponent_score} {opponent}**",
        "match_start": "**{team}** vs **{opponent}** spiller nå i **{arena}**",
        "match_end": "Sluttresultat **{team} {team_score} - {opponent_score} {opponent}**",
        "match_win": "Sluttresultat **{team} {team_score} - {opponent_score} {opponent}**\n\nGratulerer til **{team}** med seieren! 🏒🥳",
        "match_loss": "Sluttresultat **{team} {team_score} - {opponent_score} {opponent}**\n\nBedre lykke neste gang **{team}** 😓",
        "match_start_title": "Kampen har startet 🏒",
        "match_end_title": "Kampen er over 🏒",
        "next_match_title": "[{tournament_name}] {team_possessive} neste kamp",
        "next_match": "**{team}** spiller mot **{opponent}** i **{arena}** {timestamp}\n\n{long_datetime}",
        "no_next_match": "Ingen planlagte kamper funnet",
        "language_set": "Språket er endret til Norsk",
    },
}

COMMANDS = {
    "en": {
        "next_match": "next-match",
        "next_match_description": "Get information about the next match",
        "subscribe": "subscribe",
        "subscribe_description": "Subscribe the current channel to live updates in the specified language",
        "channels": "channels",
        "channels_description": "List all active channels in the server",
        "set_language": "set-language",
        "set_language_description": "Change the language of the current channel",
        "opt_language": "language",
    },
    "no": {
        "next_match": "neste-kamp",
        "next_match_description": "Få informasjon om neste kamp",
        "subscribe": "abonner",
        "subscribe_description": "Abonner på direkteoppdateringer for den gjeldende kanalen i angitt språk",
        "channels": "kanaler",
        "channels_description": "Vis alle aktive kanaler i serveren",
        "set_language": "endre-språk",
        "set_language_description": "Endre språket for den gjeldende kanalen",
        "opt_language": "språk",
    },
}

SUPPORTED_LANGUAGES = Literal["en", "no"]
