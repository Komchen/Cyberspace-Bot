from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks

from google_calendar import (
    calendar_configured,
    events_needing_reminder,
    format_event_line,
    list_upcoming_events,
    parse_event_start,
)
from utils.channels import announce_channel
from utils.storage import load_guild, update_guild


class CalendarEvents(commands.Cog):
    """Google Calendar meeting list + automatic reminders."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminder_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()

    @commands.command(
        name="events",
        aliases=["meetings", "calendar"],
        help="List upcoming club calendar events.",
    )
    @commands.guild_only()
    async def events(self, ctx: commands.Context):
        if not calendar_configured():
            await ctx.send(
                "Google Calendar is not configured yet.\n"
                "Add `credentials.json`, run the bot once to authorize, "
                "and optionally set `google_calendar_id` in `token.env`."
            )
            return

        try:
            events = await self.bot.loop.run_in_executor(None, list_upcoming_events, 8)
        except Exception as exc:
            await ctx.send(f"Couldn't fetch calendar events: {exc}")
            return

        if not events:
            await ctx.send("No upcoming events on the club calendar.")
            return

        lines = ["**Upcoming Cyberspace events**"]
        for event in events:
            lines.append(format_event_line(event))
            lines.append("")
        await ctx.send("\n".join(lines).strip())

    @commands.command(
        name="reminders",
        help="Enable or disable calendar reminders for this server (admin).",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def reminders(self, ctx: commands.Context, mode: str | None = None):
        data = load_guild(ctx.guild.id)
        if mode is None:
            state = "on" if data["calendar"].get("enabled", True) else "off"
            await ctx.send(f"Calendar reminders are **{state}**.")
            return

        mode = mode.lower()
        if mode not in {"on", "off", "enable", "disable"}:
            await ctx.send("Usage: `!reminders on|off`")
            return

        enabled = mode in {"on", "enable"}

        def mutate(d):
            d["calendar"]["enabled"] = enabled

        update_guild(ctx.guild.id, mutate)
        await ctx.send(f"Calendar reminders turned **{'on' if enabled else 'off'}**.")

    @tasks.loop(minutes=10)
    async def reminder_loop(self):
        if not calendar_configured():
            return

        try:
            events = await self.bot.loop.run_in_executor(None, list_upcoming_events, 15)
        except Exception as exc:
            print(f"[calendar] fetch failed: {exc}")
            return

        now = datetime.now(timezone.utc)
        for guild in self.bot.guilds:
            data = load_guild(guild.id)
            if not data["calendar"].get("enabled", True):
                continue

            channel = announce_channel(guild)
            if channel is None:
                continue

            reminded = data["calendar"].setdefault("reminded", {})
            due = events_needing_reminder(events, reminded, now=now)
            if not due:
                continue

            for event, kind in due:
                label = "in about 24 hours" if kind == "24h" else "in about 1 hour"
                start = parse_event_start(event)
                title = event.get("summary") or "Club event"
                embed = discord.Embed(
                    title=f"Reminder: {title}",
                    description=f"Starts {label}.\n\n{format_event_line(event)}",
                    color=discord.Color.dark_teal(),
                    timestamp=start or now,
                )
                try:
                    await channel.send(embed=embed)
                except discord.HTTPException as exc:
                    print(f"[calendar] announce failed in {guild.id}: {exc}")
                    continue

                event_id = event["id"]

                def mark(d, eid=event_id, k=kind):
                    d["calendar"].setdefault("reminded", {}).setdefault(eid, [])
                    if k not in d["calendar"]["reminded"][eid]:
                        d["calendar"]["reminded"][eid].append(k)

                update_guild(guild.id, mark)

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(CalendarEvents(bot))
