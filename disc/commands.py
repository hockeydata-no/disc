import sys
from inspect import getmembers

import discord

import api_handler
import subscribers
from __init__ import LANGUAGE, DISPLAYED_TEAM_NAME
from manifest import FORMAT_MESSAGES, SUPPORTED_LANGUAGES
from models import DiscEmbed, DiscException
from translator import DiscTranslator


@discord.app_commands.command(name="subscribe", description="subscribe_description")
async def subscribe(ctx, opt_language: SUPPORTED_LANGUAGES = LANGUAGE) -> None:
    """Subscribe the current channel to live updates"""
    _lang = subscribers.get_lang(ctx.channel.id)  # TODO: Don't read the file twice
    subscribing = subscribers.toggle(ctx.channel.id, lang=opt_language)
    if subscribing:
        response = FORMAT_MESSAGES[opt_language]["subscribe"].format(team=DISPLAYED_TEAM_NAME)
        await ctx.response.send_message(response)
    else:
        response = FORMAT_MESSAGES[_lang]["unsubscribe"]
        await ctx.response.send_message(response)


@discord.app_commands.command(name="channels", description="channels_description")
async def channels(ctx) -> None:
    """List all active channels"""
    active_channels = [ch for ch in subscribers.get_channels().keys() if ctx.guild.get_channel(int(ch))]
    disc_embed = DiscEmbed(
        title_key="active_channels_title",
        description_key="no_active_channels",
        values={"active_channels": "\n".join([f"<#{ch}>" for ch in active_channels])},
        hex_color=0xFF0000,
    )
    if active_channels:
        disc_embed.description_key = "active_channels"
        disc_embed.hex_color = 0x00FF00
    await ctx.response.send_message(embed=disc_embed.embed(lang=subscribers.get_lang(ctx.channel.id)), ephemeral=True)


@discord.app_commands.command(name="set_language", description="set_language_description")
async def language(ctx, opt_language: SUPPORTED_LANGUAGES = LANGUAGE) -> None:
    """Change the language of the current channel"""
    subscribers.set_lang(ctx.channel.id, opt_language)
    await ctx.response.send_message(FORMAT_MESSAGES[opt_language]["language_set"], ephemeral=True)


@discord.app_commands.command(name="next_match", description="next_match_description")
async def next_match(ctx) -> None:
    """Get information about the next match"""
    lang = subscribers.get_lang(ctx.channel.id)
    try:
        match_string = api_handler.get_next_match()
        embed = match_string.embed(lang=lang)
        await ctx.response.send_message(embed=embed)
    except DiscException:
        if "no_next_match" not in FORMAT_MESSAGES[lang]:
            lang = "en"
        await ctx.response.send_message(FORMAT_MESSAGES[lang]["no_next_match"], ephemeral=True)


async def add_commands(tree: discord.app_commands.CommandTree) -> None:
    """Add all commands inside this file to the command tree"""
    commands = getmembers(sys.modules[__name__], lambda x: isinstance(x, discord.app_commands.Command))
    [tree.add_command(command[1]) for command in commands]
    await tree.set_translator(DiscTranslator())
