from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum

import discord

from __init__ import LANGUAGE
from manifest import FORMAT_MESSAGES


class MatchStatus(Enum):
    InProgress = "InProgress"
    Scheduled = "Scheduled"
    Finished = "Finished"
    Aborted = "Aborted"


class DiscException(Exception):
    pass


@dataclass
class BaseEmbed:
    title: str = None  # Used by DiscEmbedSimple
    description: str = ""  # Used by DiscEmbedSimple
    title_key: str = None  # Used by DiscEmbed
    description_key: str = ""  # Used by DiscEmbed
    appended_description: str = ""

    hex_color: int = 0x00FF00
    thumbnail: discord.File = None
    values: dict = dict
    extra_data: dict = dict

    def _handle_images(self, embed: discord.Embed) -> discord.Embed:
        if self.thumbnail:
            self.thumbnail.fp.seek(0)
            embed.set_thumbnail(url=f"attachment://{self.thumbnail.filename}")
        return embed

    @property
    def files(self):
        return [self.thumbnail] if self.thumbnail else []

    @staticmethod
    def format_msg(msg: str, values: dict) -> str:
        """Format a message with the given values"""
        try:
            return msg.format(**values)
        # If the values are missing, return the original message
        except (KeyError, TypeError):
            return msg

    def create_embed(self, lang=LANGUAGE) -> discord.Embed:
        raise NotImplementedError

    def embed(self, lang=LANGUAGE):
        embed_object = self.create_embed(lang)
        embed_object = self._handle_images(embed_object)
        embed_object.timestamp = datetime.now(tz=UTC)
        return embed_object


@dataclass
class DiscEmbed(BaseEmbed):
    def create_embed(self, lang=LANGUAGE) -> discord.Embed:
        # TODO: Use a more sophisticated way to translate the messages than just using a dictionary
        title_lang = lang if self.title_key in FORMAT_MESSAGES[lang] else "en"
        description_lang = lang if self.description_key in FORMAT_MESSAGES[lang] else "en"

        title = self.format_msg(FORMAT_MESSAGES[title_lang][self.title_key], self.values)
        description = self.format_msg(FORMAT_MESSAGES[description_lang][self.description_key], self.values)

        return discord.Embed(
            title=title,
            description=f"{description}\n{self.appended_description}",
            color=self.hex_color,
        )


@dataclass
class DiscEmbedSimple(BaseEmbed):
    def create_embed(self, lang=LANGUAGE) -> discord.Embed:
        return discord.Embed(
            title=self.title,
            description=f"{self.description}\n{self.appended_description}",
            color=self.hex_color,
        )
