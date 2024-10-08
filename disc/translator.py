from typing import Optional

import discord
from discord import app_commands

from manifest import COMMANDS


class DiscTranslator(app_commands.Translator):
    async def translate(
        self, string: app_commands.locale_str, locale: discord.Locale, context: app_commands.TranslationContext
    ) -> Optional[str]:
        if str(string) not in COMMANDS["en"]:
            return None
        language_commands = COMMANDS.get(str(locale), COMMANDS["en"])
        translation = language_commands.get(str(string), language_commands[str(string)])
        return translation


# TODO: Add translations for messages (currently using a dictionary handled in the DiscEmbed class)
