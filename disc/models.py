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
class DiscEmbed:
    title_key: str = None
    description_key: str = ""
    values: dict = dict
    hex_color: int = 0x00FF00
    extra_data: dict = dict
    appended_description: str = ""

    @staticmethod
    def format_msg(msg: str, values: dict) -> str:
        """Format a message with the given values"""
        try:
            return msg.format(**values)
        # If the values are missing, return the original message
        except (KeyError, TypeError):
            return msg

    def embed(self, lang=LANGUAGE) -> discord.Embed:
        title_lang = lang if self.title_key in FORMAT_MESSAGES[lang] else "en"
        description_lang = lang if self.description_key in FORMAT_MESSAGES[lang] else "en"

        title = self.format_msg(FORMAT_MESSAGES[title_lang][self.title_key], self.values)
        description = self.format_msg(FORMAT_MESSAGES[description_lang][self.description_key], self.values)

        embed = discord.Embed(
            title=title,
            description=f"{description}\n{self.appended_description}",
            color=self.hex_color,
        )

        embed.timestamp = datetime.now(tz=UTC)
        return embed
