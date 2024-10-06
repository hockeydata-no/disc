import discord
from discord.ext import tasks

import api_handler as data
import subscribers
from __init__ import DISPLAYED_TEAM_NAME, DISCORD_TOKEN
from manifest import FORMAT_MESSAGES, SUPPORTED_LANGUAGES
from models import DiscString, DiscException

intents = discord.Intents.default()


class HockeyDisc(discord.Client):
    active_match = False

    async def _update(self):
        await self.get_match_status()
        if self.active_match:
            await self.get_score()

    async def send_embed(self, discstring: DiscString) -> None:
        """Send an embed to all subscribed channels"""
        if not discstring.title_key:
            return
        for settings, channel in subscribers.get_channels().items():
            embed = discstring.embed(lang=settings.get("lang", "en"))
            await self.get_channel(channel).send(embed=embed)

    async def update_status(self, match_status):
        """Update the presence of the bot"""
        if match_status.extra_data.get("active_match"):
            await self.change_presence(activity=discord.Game(name=match_status.extra_data["presence_string"]))
            self.active_match = True
        else:
            await self.change_presence(activity=None)
            self.active_match = False

    async def get_match_status(self):
        """Get the current match status and update the presence"""
        try:
            match_status = data.get_match_status()
        except DiscException:
            self.active_match = False
            return

        await self.update_status(match_status)

        # Send the embed if the embed has a title key (only happens during start/end of match)
        if match_status.title_key:
            await self.send_embed(match_status)

    async def get_score(self):
        try:
            score_string = data.get_goal()
            await self.send_embed(score_string)
        except DiscException:
            pass

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
async def subscribe(ctx, language: SUPPORTED_LANGUAGES = "en"):
    """Subscribe the current channel to live updates"""
    _lang = subscribers.get_lang(ctx.channel.id)  # TODO: Don't read the file twice
    subscribing = subscribers.toggle(ctx.channel.id, lang=language)
    if subscribing:
        response = FORMAT_MESSAGES[language]["subscribe"].format(team=DISPLAYED_TEAM_NAME)
        await ctx.response.send_message(response)
    else:
        response = FORMAT_MESSAGES[_lang]["unsubscribe"]
        await ctx.response.send_message(response)


@tree.command(name="channels")
async def channels(ctx):
    """List all active channels"""
    active_channels = [ch for ch in subscribers.get_channels().keys() if ctx.guild.get_channel(int(ch))]
    discstring = DiscString(
        title_key="active_channels_title",
        description_key="no_active_channels",
        values={"active_channels": "\n".join([f"<#{ch}>" for ch in active_channels])},
        hex_color=0xFF0000,
    )
    if active_channels:
        discstring.description_key = "active_channels"
        discstring.hex_color = 0x00FF00
    await ctx.response.send_message(embed=discstring.embed(lang=subscribers.get_lang(ctx.channel.id)), ephemeral=True)


@tree.command(name="next")
async def next_match(ctx):
    """Get information about the next match"""
    lang = subscribers.get_lang(ctx.channel.id)
    try:
        match_string = data.get_next_match()
        embed = match_string.embed(lang=lang)
        await ctx.response.send_message(embed=embed)
    except DiscException:
        if "no_next_match" not in FORMAT_MESSAGES[lang]:
            lang = "en"
        await ctx.response.send_message(FORMAT_MESSAGES[lang]["no_next_match"], ephemeral=True)
        return


client.run(DISCORD_TOKEN)
