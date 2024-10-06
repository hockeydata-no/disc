import json
import os
from datetime import datetime, UTC
from enum import Enum

import discord
import requests
from discord.ext import tasks
from dotenv import load_dotenv

import subscribers

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
HOCKEYDATA_HOST = os.getenv("HOCKEYDATA_HOST")
HOCKEYDATA_API_KEY = os.getenv("HOCKEYDATA_API_KEY")
HOCKEYDATA_TEAM_NAME = os.getenv("HOCKEYDATA_TEAM_NAME").split(",")
DISPLAYED_TEAM_NAME = os.getenv("DISPLAYED_TEAM_NAME")

ENDPOINTS = {
    "score": f"{HOCKEYDATA_HOST}/live/score?provider=fangroup",
    "goal_scorer": f"{HOCKEYDATA_HOST}/live/recent-goal-scorer-stats",
    "status": f"{HOCKEYDATA_HOST}/live/match",
}

FORMAT_MESSAGES = {
    "goal_home": "The score is now **{team} {team_score} - {opponent_score} {opponent}**",
    "goal_away": "The score is now **{team} {team_score} - {opponent_score} {opponent}**",
    "scorer_info": "Goal scorer: **{scorer}**",
    "assist_info": "Assist: **{assist}**",
    "match_start": "**{team}** vs **{opponent}** are now playing in **{arena}**",
    "match_end": "Final score **{team} {team_score} - {opponent_score} {opponent}**",
    "presence": "{team} {team_score} - {opponent_score} {opponent}",
    "next_match": "**{team}** vs **{opponent}** will play in **{venue}**\n\n{time} ({timezone})",
}


# TODO: Make a module to retrieve strings (i.e. get_goal_string, get_match_status_string) etc.
#       and use them in the code instead of hardcoding them, making the discord bot methods more readable


class MatchStatus(Enum):
    InProgress = "InProgress"
    Scheduled = "Scheduled"
    Finished = "Finished"
    Aborted = "Aborted"


intents = discord.Intents.default()


def query(endpoint: str) -> dict:
    try:
        r = requests.get(endpoint, headers={"HockeyData-API-Key": HOCKEYDATA_API_KEY})
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(e)
        return {}


class HockeyDisc(discord.Client):
    current_score = dict(
        {
            "team": {"score": 0, "team": DISPLAYED_TEAM_NAME},
            "opponent": {"score": 0, "team": "Unknown"},
        }
    )

    active_match = False

    async def _update(self):
        await self.get_match_status()
        if self.active_match:
            await self.get_score()

    async def send_embed(self, embed):
        for channel in subscribers.get_channels():
            await self.get_channel(channel).send(embed=embed)

    async def get_match_status(self):
        if os.path.exists("data/match.json"):
            with open("data/match.json") as f:
                old_status = json.load(f)
        else:
            old_status = {"status": MatchStatus.Scheduled.value}

        r = query(ENDPOINTS["status"])
        if not r:
            return

        is_home = r["homeTeam"]["fullName"] in HOCKEYDATA_TEAM_NAME
        opponent = r["awayTeam"]["fullName"] if is_home else r["homeTeam"]["fullName"]
        venue = r["venue"]["name"]
        team_score = r["homeGoals"] if is_home else r["awayGoals"]
        opponent_score = r["awayGoals"] if is_home else r["homeGoals"]

        if r["status"] == MatchStatus.InProgress.value:
            await self.change_presence(
                activity=discord.Game(
                    name=FORMAT_MESSAGES["presence"].format(
                        team=DISPLAYED_TEAM_NAME,
                        team_score=team_score,
                        opponent_score=opponent_score,
                        opponent=opponent,
                    )
                ),
            )
            self.active_match = True
        else:
            await self.change_presence(activity=None)
            self.active_match = False

        if old_status["status"] != r["status"]:
            if r["status"] == MatchStatus.InProgress.value:
                embed = discord.Embed(
                    title="Match started!",
                    description=FORMAT_MESSAGES["match_start"].format(
                        team=DISPLAYED_TEAM_NAME,
                        opponent=opponent,
                        arena=venue,
                    ),
                    color=0x00FF00,
                )
                embed.timestamp = datetime.now(tz=UTC)
                await self.send_embed(embed)
            elif (
                r["status"] == MatchStatus.Finished.value
                and old_status["status"] == MatchStatus.InProgress.value
            ):
                embed = discord.Embed(
                    title="Match ended!",
                    description=FORMAT_MESSAGES["match_end"].format(
                        team=DISPLAYED_TEAM_NAME,
                        team_score=team_score,
                        opponent_score=opponent_score,
                        opponent=opponent,
                    ),
                    color=0xFF0000,
                )
                embed.timestamp = datetime.now(tz=UTC)
                await self.send_embed(embed)

        with open("data/match.json", "w") as f:
            json.dump(r, f)

    @staticmethod
    async def _get_scorer_info() -> str:
        r = query(ENDPOINTS["goal_scorer"])
        if not r:
            raise ValueError("No data")

        scorer = r["playerinfo"]["scorer"]
        assists = r["playerinfo"]["assists"]

        scorer_name = f"{scorer['firstName']} {scorer['lastName']}"

        output_message = FORMAT_MESSAGES["scorer_info"].format(scorer=scorer_name)
        for assist in assists:
            assist_name = f"{assist['firstName']} {assist['lastName']}"
            output_message += (
                f"\n{FORMAT_MESSAGES['assist_info'].format(assist=assist_name)}"
            )

        return output_message

    async def get_score(self):
        if os.path.exists("data/score.json"):
            with open("data/score.json") as f:
                old_score = json.load(f)
        else:
            old_score = self.current_score

        r = query(ENDPOINTS["score"])
        if not r:
            return

        home_team = r["homeTeam"]
        away_team = r["awayTeam"]
        team_is_home = home_team["team"] in HOCKEYDATA_TEAM_NAME

        team = home_team if team_is_home else away_team
        opponent = away_team if team_is_home else home_team

        if int(old_score["team"]["score"]) < int(team["score"]):
            message = FORMAT_MESSAGES["goal_home"].format(
                team=DISPLAYED_TEAM_NAME,
                opponent=opponent["team"],
                team_score=team["score"],
                opponent_score=opponent["score"],
            )
            try:
                scorer_info = await self._get_scorer_info()
                message += "\n" + scorer_info
            except ValueError:
                pass
            embed = discord.Embed(
                title=f"{DISPLAYED_TEAM_NAME} scored!",
                description=message,
                color=0x00FF00,
            )
            embed.timestamp = datetime.now(tz=UTC)
            await self.send_embed(embed)

        elif int(old_score["opponent"]["score"]) < int(opponent["score"]):
            message = FORMAT_MESSAGES["goal_away"].format(
                team=DISPLAYED_TEAM_NAME,
                opponent=opponent["team"],
                team_score=team["score"],
                opponent_score=opponent["score"],
            )
            embed = discord.Embed(
                title=f"{opponent['team']} scored",
                description=message,
                color=0xFF0000,
            )
            embed.timestamp = datetime.now(tz=UTC)
            await self.send_embed(embed)

        data = {"team": team, "opponent": opponent}
        with open("data/score.json", "w") as f:
            json.dump(data, f)
        self.current_score = data

    @tasks.loop(seconds=5)
    async def _loop(self):
        await self._update()


client = HockeyDisc(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} ({client.user.id})")
    client._loop.start()
    await tree.sync()


@tree.command(name="subscribe")
async def subscribe(ctx):
    """Subscribe the current channel to live updates"""
    subscribing = subscribers.toggle(ctx.channel.id)
    if subscribing:
        await ctx.response.send_message(
            f"Channel is subscribed. Forza {DISPLAYED_TEAM_NAME}!"
        )
    else:
        await ctx.response.send_message("Channel is now unsubscribed.")


@tree.command(name="channels")
async def channels(ctx):
    """List all active channels"""
    active_channels = [
        ch for ch in subscribers.get_channels() if ctx.guild.get_channel(ch)
    ]
    if not active_channels:
        embed = discord.Embed(
            title="Active channels",
            description="No active channels",
            color=0xFF0000,
        )
        embed.timestamp = datetime.now(tz=UTC)
    else:
        embed = discord.Embed(
            title="Active channels",
            description="\n".join([f"<#{ch}>" for ch in active_channels]),
            color=0x00FF00,
        )
        embed.timestamp = datetime.now(tz=UTC)
    await ctx.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="next-match")
async def next_match(ctx):
    """Get information about the next match"""
    r = query(ENDPOINTS["status"])
    if not r:
        await ctx.response.send_message("No match data found", ephemeral=True)
        return

    if not r["status"] == MatchStatus.Scheduled.value:
        await ctx.response.send_message("No scheduled match found", ephemeral=True)
        return

    is_home = r["homeTeam"]["fullName"] in HOCKEYDATA_TEAM_NAME
    opponent = r["awayTeam"]["fullName"] if is_home else r["homeTeam"]["fullName"]
    venue = r["venue"]["name"]
    utc_date = datetime.fromisoformat(r["date"])
    time = utc_date.astimezone().strftime("%d.%m.%Y %H:%M")
    timezone = utc_date.astimezone().tzinfo

    embed = discord.Embed(
        title=f"{DISPLAYED_TEAM_NAME}'s next match",
        description=FORMAT_MESSAGES["next_match"].format(
            team=DISPLAYED_TEAM_NAME,
            opponent=opponent,
            venue=venue,
            time=time,
            timezone=timezone,
        ),
        color=0xFFA500,
    )
    embed.timestamp = datetime.now(tz=UTC)
    await ctx.response.send_message(embed=embed)


client.run(DISCORD_TOKEN)
