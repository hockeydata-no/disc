import asyncio
from asyncio import Future

import discord
from discord.ext import tasks

import api_handler
import commands
import subscribers
from __init__ import DISCORD_TOKEN, DISPLAYED_TEAM_NAME
from models import DiscEmbed, DiscException, BaseEmbed


class HockeyDisc(discord.Client):
    active_match = False

    async def _update(self):
        await self.get_match_status()
        if self.active_match:
            await self.get_score()

    @staticmethod
    async def _get_first_embed_urls(first_message: Future[discord.Message]) -> dict:
        embedded_data = dict()
        embeds = await asyncio.gather(first_message)
        for embed in embeds[0].embeds:
            if embed.thumbnail:
                embedded_data["thumbnail"] = embed.thumbnail.url
            if embed.image:
                embedded_data["image"] = embed.image.url
        return embedded_data

    @staticmethod
    def _replace_embed_files_with_urls(embed: discord.Embed, first_embed_data: dict) -> discord.Embed:
        if "thumbnail" in first_embed_data:
            embed.set_thumbnail(url=first_embed_data["thumbnail"])
        if "image" in first_embed_data:
            embed.set_image(url=first_embed_data["image"])
        return embed

    async def send_embed(self, disc_embed: BaseEmbed) -> None:
        """Send an embed to all subscribed channels"""
        # If we use a DiscEmbed (uses title keys), we don't want to send the embed if the title key is missing
        if isinstance(type(disc_embed), DiscEmbed) and not disc_embed.title_key:
            return

        # If the embed has files, we need to send the files first
        files = list([discord.File(image.fp, image.filename) for image in disc_embed.files if image])
        # Embedded data will be replaced with values from the first sent embed
        embedded_data = dict()

        for channel, settings in subscribers.get_channels().items():
            # Generate the embed with the language of the channel
            embed = disc_embed.embed(lang=settings.get("lang", "en"))
            ch = self.get_channel(int(channel))

            # If we have files, we need to send them
            if files and not embedded_data:
                # TODO: Make sure we have control over the first channel we send the embed to, since if the message gets deleted the URLs will be lost
                first_msg = ch.send(embed=embed, files=files)
                embedded_data = await self._get_first_embed_urls(first_msg)
                continue
            elif embedded_data:
                embed = self._replace_embed_files_with_urls(embed, embedded_data)
            await ch.send(embed=embed)

    async def update_status(self, match_status):
        """Update the presence of the bot"""
        if match_status.extra_data.get("active_match"):
            await self.change_presence(
                activity=discord.CustomActivity(name=f"{api_handler.get_presence_string()} 🎉🏒", emoji="🏒")
            )
            self.active_match = True
        else:
            await self.change_presence(
                activity=discord.CustomActivity(name=f"Forza {DISPLAYED_TEAM_NAME}! 🥅🏒", emoji="🏒")
            )
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
