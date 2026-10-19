import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv("token.env")
TOKEN = os.getenv("discord_token")

EXTENSIONS = (
    "cogs.basic",
    "cogs.greetings",
    "cogs.music",
    "cogs.calendar_events",
    "cogs.resources",
    "cogs.roles",
    "cogs.ctf",
    "cogs.help_queue",
    "cogs.infra",
    "cogs.moderation",
    "cogs.onboarding",
    "cogs.rsvp",
)


class CyberBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        for extension in EXTENSIONS:
            await self.load_extension(extension)
            print(f"Loaded {extension}")

    async def on_ready(self):
        print(f"Logged in as {self.user} (id={self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="!clubhelp",
            )
        )

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use that command.")
            return
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("That command only works in a server.")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument. Try `!help {ctx.command}`.")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"Bad argument. Try `!help {ctx.command}`.")
            return
        message = str(error) or "Something went wrong running that command."
        await ctx.send(message)


def main() -> None:
    if not TOKEN:
        raise SystemExit(
            "Missing discord_token. Create token.env with: discord_token=YOUR_BOT_TOKEN"
        )
    bot = CyberBot()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
