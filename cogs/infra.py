from discord.ext import commands

from utils.channels import announce_channel
from utils.storage import load_guild, update_guild

VALID_SERVICES = ("lab", "vpn", "vms")
VALID_STATUSES = ("up", "down", "degraded", "maintenance", "unknown")

STATUS_EMOJI = {
    "up": "🟢",
    "down": "🔴",
    "degraded": "🟡",
    "maintenance": "🔧",
    "unknown": "⚪",
}


class Infra(commands.Cog):
    """Club lab / VPN / VM status board."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(
        name="status",
        invoke_without_command=True,
        help="Show lab / VPN / VM status.",
    )
    @commands.guild_only()
    async def status(self, ctx: commands.Context):
        infra = load_guild(ctx.guild.id).get("infra", {})
        lines = ["**Cyberspace infra status**"]
        for service in VALID_SERVICES:
            entry = infra.get(service, {"status": "unknown", "note": ""})
            emoji = STATUS_EMOJI.get(entry.get("status", "unknown"), "⚪")
            note = entry.get("note") or ""
            suffix = f" — {note}" if note else ""
            lines.append(
                f"{emoji} **{service.upper()}**: {entry.get('status', 'unknown')}{suffix}"
            )
        await ctx.send("\n".join(lines))

    @status.command(name="set", help="Set status: !status set lab up [note...]")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def status_set(
        self,
        ctx: commands.Context,
        service: str,
        state: str,
        *,
        note: str = "",
    ):
        service = service.lower()
        state = state.lower()
        if service not in VALID_SERVICES:
            await ctx.send(f"Service must be one of: {', '.join(VALID_SERVICES)}")
            return
        if state not in VALID_STATUSES:
            await ctx.send(f"Status must be one of: {', '.join(VALID_STATUSES)}")
            return

        def mutate(data):
            data["infra"][service] = {"status": state, "note": note}

        update_guild(ctx.guild.id, mutate)
        emoji = STATUS_EMOJI.get(state, "⚪")
        message = f"{emoji} **{service.upper()}** is now **{state}**"
        if note:
            message += f" — {note}"
        await ctx.send(message)

        channel = announce_channel(ctx.guild)
        if channel and channel != ctx.channel and state in {"down", "degraded", "up"}:
            await channel.send(f"Infra update: {message}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Infra(bot))
