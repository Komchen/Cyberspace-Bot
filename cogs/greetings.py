import discord
from discord.ext import commands

from utils.channels import announce_channel


class Greetings(commands.Cog):
    """Public welcome messages when members join."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = announce_channel(member.guild)
        if channel is None:
            return
        await channel.send(
            f"Welcome to **{member.guild.name}**, {member.mention}! "
            f"Type `!clubhelp` to get started."
        )

    @commands.command(
        name="greet",
        help="Send a test welcome message in the announcement channel.",
    )
    @commands.guild_only()
    async def greet(self, ctx: commands.Context, member: discord.Member | None = None):
        target = member or ctx.author
        channel = announce_channel(ctx.guild)
        if channel is None:
            await ctx.send("No announcement channel. Use `!setchannel #channel` first.")
            return
        await channel.send(
            f"Welcome to **{ctx.guild.name}**, {target.mention}! "
            f"Type `!clubhelp` to get started."
        )
        if channel != ctx.channel:
            await ctx.send(f"Greeting sent in {channel.mention}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Greetings(bot))
