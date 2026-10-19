from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils.channels import announce_channel
from utils.storage import load_guild, update_guild


class RSVP(commands.Cog):
    """Simple RSVP / attendance for club events."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(
        name="rsvp",
        invoke_without_command=True,
        help="RSVP for a club event. Usage: !rsvp <event-key>",
    )
    @commands.guild_only()
    async def rsvp(self, ctx: commands.Context, event_key: str | None = None):
        if event_key is None:
            await ctx.send(
                "**RSVP commands**\n"
                "`!rsvp create <key> | <title> | <when>` — officers\n"
                "`!rsvp <key>` — mark yourself going\n"
                "`!rsvp maybe <key>` / `!rsvp no <key>`\n"
                "`!rsvp list <key>` — who responded\n"
                "`!rsvp close <key>` — officers\n"
                "`!rsvp upcoming` — open events"
            )
            return
        await self._set_response(ctx, event_key, "yes")

    @rsvp.command(name="create")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def rsvp_create(self, ctx: commands.Context, *, payload: str):
        parts = [p.strip() for p in payload.split("|", 2)]
        if len(parts) != 3:
            await ctx.send("Usage: `!rsvp create <key> | <title> | <when>`")
            return
        key, title, when = parts
        key = key.lower().replace(" ", "-")

        def mutate(data):
            data["rsvp"][key] = {
                "title": title,
                "when": when,
                "status": "open",
                "created_by": ctx.author.id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "responses": {},
            }

        update_guild(ctx.guild.id, mutate)
        await ctx.send(
            f"RSVP event **{title}** created as `{key}`.\n"
            f"Members can reply with `!rsvp {key}`."
        )

        channel = announce_channel(ctx.guild)
        if channel and channel != ctx.channel:
            await channel.send(
                f"📅 **{title}**\nWhen: {when}\nRSVP: `!rsvp {key}` "
                f"(or `!rsvp maybe {key}` / `!rsvp no {key}`)"
            )

    @rsvp.command(name="maybe")
    @commands.guild_only()
    async def rsvp_maybe(self, ctx: commands.Context, event_key: str):
        await self._set_response(ctx, event_key, "maybe")

    @rsvp.command(name="no")
    @commands.guild_only()
    async def rsvp_no(self, ctx: commands.Context, event_key: str):
        await self._set_response(ctx, event_key, "no")

    @rsvp.command(name="list")
    @commands.guild_only()
    async def rsvp_list(self, ctx: commands.Context, event_key: str):
        event = load_guild(ctx.guild.id)["rsvp"].get(event_key.lower())
        if event is None:
            await ctx.send("Event not found.")
            return

        buckets = {"yes": [], "maybe": [], "no": []}
        for user_id, response in (event.get("responses") or {}).items():
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else f"User {user_id}"
            buckets.setdefault(response, []).append(name)

        await ctx.send(
            f"**{event['title']}** — {event.get('when', 'TBD')} "
            f"[{event.get('status', 'open')}]\n"
            f"✅ Going ({len(buckets['yes'])}): {', '.join(buckets['yes']) or '—'}\n"
            f"🤔 Maybe ({len(buckets['maybe'])}): {', '.join(buckets['maybe']) or '—'}\n"
            f"❌ No ({len(buckets['no'])}): {', '.join(buckets['no']) or '—'}"
        )

    @rsvp.command(name="upcoming")
    @commands.guild_only()
    async def rsvp_upcoming(self, ctx: commands.Context):
        events = {
            key: event
            for key, event in load_guild(ctx.guild.id)["rsvp"].items()
            if event.get("status") == "open"
        }
        if not events:
            await ctx.send("No open RSVP events.")
            return
        lines = ["**Open RSVP events**"]
        for key, event in events.items():
            yes = sum(1 for r in event.get("responses", {}).values() if r == "yes")
            lines.append(
                f"• `{key}` — **{event['title']}** ({event.get('when', 'TBD')}) — {yes} going"
            )
        await ctx.send("\n".join(lines))

    @rsvp.command(name="close")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def rsvp_close(self, ctx: commands.Context, event_key: str):
        key = event_key.lower()
        found = {"ok": False}

        def mutate(data):
            event = data["rsvp"].get(key)
            if event is None:
                return
            event["status"] = "closed"
            found["ok"] = True

        update_guild(ctx.guild.id, mutate)
        if found["ok"]:
            await ctx.send(f"Closed RSVP `{key}`.")
        else:
            await ctx.send("Event not found.")

    async def _set_response(self, ctx: commands.Context, event_key: str, response: str):
        key = event_key.lower()
        found = {"ok": False, "title": ""}

        def mutate(data):
            event = data["rsvp"].get(key)
            if event is None or event.get("status") != "open":
                return
            event.setdefault("responses", {})[str(ctx.author.id)] = response
            found["ok"] = True
            found["title"] = event["title"]

        update_guild(ctx.guild.id, mutate)
        if not found["ok"]:
            await ctx.send("Open RSVP event not found. Try `!rsvp upcoming`.")
            return
        label = {"yes": "Going", "maybe": "Maybe", "no": "Not going"}[response]
        await ctx.send(f"{label} for **{found['title']}** (`{key}`).")


async def setup(bot: commands.Bot):
    await bot.add_cog(RSVP(bot))
