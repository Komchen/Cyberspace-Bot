from __future__ import annotations

import re

import discord
from discord.ext import commands

from utils.storage import load_guild, update_guild

# Patterns for common accidental secret leaks in a cyber club Discord.
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Discord bot token", re.compile(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27,}")),
    ("Discord webhook", re.compile(r"https://discord(?:app)?\.com/api/webhooks/\d+/[\w-]+")),
    (
        "AWS access key",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ),
    (
        "GitHub token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
    ),
    (
        "OpenAI-style key",
        re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    ),
    (
        "Private key block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "Slack token",
        re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
    ),
]


class Moderation(commands.Cog):
    """Slowmode helpers + accidental secret leak filter."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="slowmode",
        help="Set channel slowmode in seconds (0 to disable).",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int):
        if seconds < 0 or seconds > 21600:
            await ctx.send("Slowmode must be between 0 and 21600 seconds.")
            return
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send("Slowmode disabled.")
        else:
            await ctx.send(f"Slowmode set to **{seconds}s**.")

    @commands.command(
        name="protect",
        help="Mark/unmark this channel as protected (link spam caution).",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def protect(self, ctx: commands.Context, mode: str = "on"):
        mode = mode.lower()
        channel_id = ctx.channel.id

        def mutate(data):
            protected = data["moderation"].setdefault("protected_channel_ids", [])
            if mode in {"on", "enable", "add"}:
                if channel_id not in protected:
                    protected.append(channel_id)
            elif mode in {"off", "disable", "remove"}:
                data["moderation"]["protected_channel_ids"] = [
                    cid for cid in protected if cid != channel_id
                ]
            else:
                raise ValueError("bad mode")

        try:
            update_guild(ctx.guild.id, mutate)
        except ValueError:
            await ctx.send("Usage: `!protect on|off`")
            return
        await ctx.send(f"Protected mode **{mode}** for {ctx.channel.mention}.")

    @commands.command(
        name="secretfilter",
        help="Enable/disable secret leak auto-delete (admin).",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def secretfilter(self, ctx: commands.Context, mode: str | None = None):
        data = load_guild(ctx.guild.id)
        if mode is None:
            state = "on" if data["moderation"].get("secret_filter", True) else "off"
            await ctx.send(f"Secret filter is **{state}**.")
            return
        mode = mode.lower()
        if mode not in {"on", "off"}:
            await ctx.send("Usage: `!secretfilter on|off`")
            return

        def mutate(d):
            d["moderation"]["secret_filter"] = mode == "on"

        update_guild(ctx.guild.id, mutate)
        await ctx.send(f"Secret filter turned **{mode}**.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        if not isinstance(message.author, discord.Member):
            return

        data = load_guild(message.guild.id)
        moderation = data.get("moderation", {})

        if moderation.get("secret_filter", True):
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(message.content or ""):
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        return
                    try:
                        await message.channel.send(
                            f"{message.author.mention} possible **{label}** detected and "
                            f"removed. Rotate that credential if it was real.",
                            delete_after=20,
                        )
                    except discord.HTTPException:
                        pass
                    return

        protected_ids = set(moderation.get("protected_channel_ids") or [])
        if message.channel.id not in protected_ids:
            return
        if message.author.guild_permissions.manage_messages:
            return

        # In protected channels, block messages that are mostly untrusted links.
        urls = re.findall(r"https?://\S+", message.content or "")
        if not urls:
            return
        content_without_urls = re.sub(r"https?://\S+", "", message.content or "").strip()
        if len(content_without_urls) < 8 and len(urls) >= 1:
            try:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} link-only posts are limited in this channel. "
                    "Add context or ask an officer to post announcements.",
                    delete_after=15,
                )
            except discord.HTTPException:
                return


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
