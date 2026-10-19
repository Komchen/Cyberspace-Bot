from datetime import datetime, timezone

from discord.ext import commands

from utils.channels import officers_channel
from utils.storage import load_guild, update_guild


class HelpQueue(commands.Cog):
    """Office-hours style help requests for officers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="helpme",
        help="Ask for help. Usage: !helpme <topic or question>",
    )
    @commands.guild_only()
    async def helpme(self, ctx: commands.Context, *, topic: str):
        ticket_id = {"value": 0}

        def mutate(data):
            ticket_id["value"] = int(data.get("help_next_id", 1))
            data["help_next_id"] = ticket_id["value"] + 1
            data.setdefault("help_queue", []).append(
                {
                    "id": ticket_id["value"],
                    "user_id": ctx.author.id,
                    "topic": topic,
                    "status": "open",
                    "channel_id": ctx.channel.id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        update_guild(ctx.guild.id, mutate)
        tid = ticket_id["value"]

        await ctx.send(
            f"Help request **#{tid}** filed. An officer will pick it up.\n"
            f"Topic: {topic}"
        )

        channel = officers_channel(ctx.guild)
        if channel and channel != ctx.channel:
            await channel.send(
                f"🆘 Help request **#{tid}** from {ctx.author.mention} "
                f"in {ctx.channel.mention}:\n> {topic}\n"
                f"Claim with `!helpdone {tid}` when finished."
            )

    @commands.command(name="helplist", help="List open help requests.")
    @commands.guild_only()
    async def helplist(self, ctx: commands.Context):
        queue = [
            item
            for item in load_guild(ctx.guild.id).get("help_queue", [])
            if item.get("status") == "open"
        ]
        if not queue:
            await ctx.send("No open help requests.")
            return
        lines = ["**Open help queue**"]
        for item in queue[-20:]:
            member = ctx.guild.get_member(int(item["user_id"]))
            name = member.display_name if member else f"User {item['user_id']}"
            lines.append(f"#{item['id']} — {name}: {item['topic']}")
        await ctx.send("\n".join(lines))

    @commands.command(
        name="helpdone",
        help="Close a help request by id (officers).",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def helpdone(self, ctx: commands.Context, ticket_id: int):
        found = {"ok": False}

        def mutate(data):
            for item in data.get("help_queue", []):
                if int(item["id"]) == ticket_id and item.get("status") == "open":
                    item["status"] = "done"
                    item["closed_by"] = ctx.author.id
                    item["closed_at"] = datetime.now(timezone.utc).isoformat()
                    found["ok"] = True
                    break

        update_guild(ctx.guild.id, mutate)
        if found["ok"]:
            await ctx.send(f"Closed help request **#{ticket_id}**.")
        else:
            await ctx.send("Open help request not found.")


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpQueue(bot))
