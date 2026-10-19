import discord
from discord.ext import commands

from utils.storage import update_guild


class Basic(commands.Cog):
    """Core utility commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="online", help="Check if the bot is online and working.")
    async def online(self, ctx: commands.Context):
        await ctx.send("Online")

    @commands.command(name="ping", help="Show bot latency.")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"Pong! `{round(self.bot.latency * 1000)}ms`")

    @commands.command(name="info", help="Show basic bot info.")
    async def info(self, ctx: commands.Context):
        await ctx.send(
            f"**Cyberspace Bot** — SRU Cybersecurity Club\n"
            f"Servers: {len(self.bot.guilds)}\n"
            f"Prefix: `!`\n"
            f"Try `!clubhelp` for club features."
        )

    @commands.command(
        name="clubhelp",
        help="Show cybersecurity club feature commands.",
    )
    async def clubhelp(self, ctx: commands.Context):
        await ctx.send(
            "**Cyberspace club commands**\n"
            "`!events` / `!reminders` — upcoming meetings\n"
            "`!resources [topic]` — curated learning links\n"
            "`!roles` — self-assign interest roles\n"
            "`!helpme <topic>` — ask officers for help\n"
            "`!status` — lab / VPN / VM status\n"
            "`!challenge` / `!leaderboard` — club CTF practice\n"
            "`!rsvp` — RSVP for club events\n"
            "`!setchannel` / `!setofficers` — configure announce channels"
        )

    @commands.command(
        name="setchannel",
        help="Set the greeting / announcement channel (admin).",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def setchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        update_guild(
            ctx.guild.id,
            lambda data: data.__setitem__("announce_channel_id", channel.id),
        )
        await ctx.send(f"Announcement channel set to {channel.mention}")

    @commands.command(
        name="setofficers",
        help="Set the officers channel for help-queue alerts (admin).",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def setofficers(self, ctx: commands.Context, channel: discord.TextChannel):
        update_guild(
            ctx.guild.id,
            lambda data: data.__setitem__("officers_channel_id", channel.id),
        )
        await ctx.send(f"Officers channel set to {channel.mention}")

    @commands.command(name="exit", help="Shut down the bot (admin only).")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def exit_bot(self, ctx: commands.Context):
        await ctx.send("Shutting down...")
        music = self.bot.get_cog("Music")
        if music is not None:
            await music.shutdown()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        await self.bot.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(Basic(bot))
