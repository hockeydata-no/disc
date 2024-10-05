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
HOCKEYLIVE_TEAM_NAME = os.getenv("HOCKEYLIVE_TEAM_NAME")
DISPLAYED_TEAM_NAME = os.getenv("DISPLAYED_TEAM_NAME")

ENDPOINTS = {
    "score": f"{HOCKEYDATA_HOST}/live/score?provider=fangroup",
    "goal_scorer": f"{HOCKEYDATA_HOST}/live/recent-goal-scorer-stats",
    "status": f"{HOCKEYDATA_HOST}/live/match",
}

FORMAT_MESSAGES = {
    "goal_home": "{team} scores against {opponent}!\nThe score is now {team} **{team_score} - {opponent_score}** {opponent}",
    "goal_away": "{opponent} scores against {team}.\nThe score is now {team} **{team_score} - {opponent_score}** {opponent}",
    "scorer_info": "**{scorer}** scored the goal!",
    "assist_info": "**{assist}** assisted the goal!",
    "match_start": "{team} vs {opponent} in arena {arena}",
    "match_end": "Match ended! Final score is {team} {team_score} - {opponent_score} {opponent}",
}


class MatchStatus(Enum):
    InProgress = "InProgress"
    Scheduled = "Scheduled"
    Finished = "Finished"
    Aborted = "Aborted"


intents = discord.Intents.default()


class HockeyDisc(discord.Client):
    current_score = dict(
        {
            "team": {"score": 0, "team": HOCKEYLIVE_TEAM_NAME},
            "opponent": {"score": 0, "team": "Unknown"},
        }
    )

    async def _update(self):
        await self.get_score()
        await self.get_match_status()

    async def send_embed(self, embed):
        for channel in subscribers.get_channels():
            await self.get_channel(channel).send(embed=embed)

    async def get_match_status(self):
        if os.path.exists("data/match.json"):
            with open("data/match.json") as f:
                old_status = json.load(f)
        else:
            old_status = {"status": MatchStatus.Scheduled}

        try:
            r = requests.get(ENDPOINTS["status"])
            r.raise_for_status()
            r = r.json()
        except requests.exceptions.RequestException as e:
            print(e)
            return

        if old_status["status"] != r["status"]:
            if r["status"] == MatchStatus.InProgress:
                embed = discord.Embed(
                    title="Match started!",
                    description=FORMAT_MESSAGES["match_start"].format(
                        team=r["homeTeam"]["team"],
                        opponent=r["awayTeam"]["team"],
                        arena=r["arena"],
                    ),
                    color=0x00FF00,
                )
                embed.timestamp = datetime.now(tz=UTC)
                await self.send_embed(embed)
            elif r["status"] == MatchStatus.Finished:
                embed = discord.Embed(
                    title="Match ended!",
                    description=FORMAT_MESSAGES["match_end"].format(
                        team=r["homeTeam"]["team"],
                        team_score=r["homeTeam"]["score"],
                        opponent_score=r["awayTeam"]["score"],
                        opponent=r["awayTeam"]["team"],
                    ),
                    color=0xFF0000,
                )
                embed.timestamp = datetime.now(tz=UTC)
                await self.send_embed(embed)

        with open("data/match.json", "w") as f:
            json.dump(r, f)

    @staticmethod
    async def _get_scorer_info() -> str:
        r = requests.get(ENDPOINTS["goal_scorer"])
        r.raise_for_status()
        r = r.json()

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

        try:
            r = requests.get(ENDPOINTS["score"])
            r.raise_for_status()
            r = r.json()
        except requests.exceptions.RequestException as e:
            print(e)
            return

        home_team = r["homeTeam"]
        away_team = r["awayTeam"]
        team_is_home = home_team["team"] == HOCKEYLIVE_TEAM_NAME

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
            except requests.exceptions.RequestException as e:
                print(e)
                return
            embed = discord.Embed(
                title="Goal!",
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
                title="Oh no!",
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
    await tree.sync()
    client._loop.start()


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


client.run(DISCORD_TOKEN)
