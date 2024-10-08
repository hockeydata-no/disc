import discord
from discord.ext import tasks

import api_handler
import commands
import subscribers
from __init__ import DISCORD_TOKEN
from models import DiscEmbed, DiscException


class HockeyDisc(discord.Client):
    active_match = False

    async def _update(self):
        await self.get_match_status()
        if self.active_match:
            await self.get_score()

    async def send_embed(self, disc_embed: DiscEmbed) -> None:
        """Send an embed to all subscribed channels"""
        if not disc_embed.title_key:
            return
        for settings, channel in subscribers.get_channels().items():
            embed = disc_embed.embed(lang=settings.get("lang", "en"))
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
            match_status = api_handler.get_match_status()
        except DiscException:
            self.active_match = False
            return

        await self.update_status(match_status)

        # Send the embed if the embed has a title key (only happens during start/end of match)
        if match_status.title_key:
            await self.send_embed(match_status)

    async def get_score(self):
        try:
            score_string = api_handler.get_goal()
            await self.send_embed(score_string)
        except DiscException:
            pass

    @tasks.loop(seconds=5)
    async def _loop(self):
        # Every endpoint has a TTL cache, so we can safely call this every 5 seconds (though it might be a bit overkill)
        await self._update()


client = HockeyDisc(intents=discord.Intents.default())
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} ({client.user.id})")
    client._loop.start()
    await commands.add_commands(tree)
    await tree.sync()


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
