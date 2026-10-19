import discord
from discord.ext import commands

from utils.storage import load_guild, update_guild


class Onboarding(commands.Cog):
    """Welcome DMs for new members."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _build_dm(self, member: discord.Member) -> str:
        data = load_guild(member.guild.id)
        onboarding = data.get("onboarding", {})
        text = onboarding.get("dm_message") or "Welcome to the club!"
        rules_id = onboarding.get("rules_channel_id")
        extras: list[str] = [text.strip(), "", f"Server: **{member.guild.name}**"]
        if rules_id:
            channel = member.guild.get_channel(int(rules_id))
            if channel:
                extras.append(f"Rules: {channel.mention}")
        extras.append("Quick starts: `!resources start` · `!roles` · `!events` · `!clubhelp`")
        return "\n".join(extras)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        data = load_guild(member.guild.id)
        if not data.get("onboarding", {}).get("enabled", True):
            return
        try:
            await member.send(self._build_dm(member))
        except discord.Forbidden:
            # User has DMs closed; public greeting cog still covers them.
            return

    @commands.group(
        name="onboarding",
        invoke_without_command=True,
        help="Configure new-member welcome DMs.",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def onboarding(self, ctx: commands.Context):
        data = load_guild(ctx.guild.id)["onboarding"]
        state = "on" if data.get("enabled", True) else "off"
        await ctx.send(
            f"Onboarding DMs are **{state}**.\n"
            f"`!onboarding on|off`\n"
            f"`!onboarding message <text>`\n"
            f"`!onboarding rules #channel`\n"
            f"`!onboarding test` — DM yourself the current message"
        )

    @onboarding.command(name="on")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def onboarding_on(self, ctx: commands.Context):
        update_guild(ctx.guild.id, lambda d: d["onboarding"].__setitem__("enabled", True))
        await ctx.send("Onboarding DMs enabled.")

    @onboarding.command(name="off")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def onboarding_off(self, ctx: commands.Context):
        update_guild(ctx.guild.id, lambda d: d["onboarding"].__setitem__("enabled", False))
        await ctx.send("Onboarding DMs disabled.")

    @onboarding.command(name="message")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def onboarding_message(self, ctx: commands.Context, *, text: str):
        update_guild(
            ctx.guild.id,
            lambda d: d["onboarding"].__setitem__("dm_message", text),
        )
        await ctx.send("Updated onboarding DM message.")

    @onboarding.command(name="rules")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def onboarding_rules(self, ctx: commands.Context, channel: discord.TextChannel):
        update_guild(
            ctx.guild.id,
            lambda d: d["onboarding"].__setitem__("rules_channel_id", channel.id),
        )
        await ctx.send(f"Rules channel set to {channel.mention}.")

    @onboarding.command(name="test")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def onboarding_test(self, ctx: commands.Context):
        try:
            await ctx.author.send(self._build_dm(ctx.author))
            await ctx.send("Sent you the onboarding DM.")
        except discord.Forbidden:
            await ctx.send("Couldn't DM you — check your privacy settings.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Onboarding(bot))
