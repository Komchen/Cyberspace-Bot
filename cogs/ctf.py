from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from discord.ext import commands

from utils.storage import load_guild, update_guild


def _hash_flag(flag: str) -> str:
    return hashlib.sha256(flag.strip().encode("utf-8")).hexdigest()


class CTF(commands.Cog):
    """Club practice challenges and leaderboard."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(
        name="challenge",
        aliases=["chal"],
        invoke_without_command=True,
        help="Club CTF challenges. Try !challenge list",
    )
    @commands.guild_only()
    async def challenge(self, ctx: commands.Context):
        await ctx.send(
            "**Challenge commands**\n"
            "`!challenge list` — open challenges\n"
            "`!challenge info <name>` — details\n"
            "`!challenge submit <name> <flag>` — submit a flag\n"
            "`!challenge create <name> | <points> | <flag> | <description>` — officers\n"
            "`!challenge close <name>` — officers\n"
            "`!leaderboard` — top solvers"
        )

    @challenge.command(name="list")
    @commands.guild_only()
    async def challenge_list(self, ctx: commands.Context):
        challenges = load_guild(ctx.guild.id)["ctf"]["challenges"]
        open_chals = [
            c for c in challenges.values() if c.get("status", "open") == "open"
        ]
        if not open_chals:
            await ctx.send("No open challenges. Officers can create one with `!challenge create`.")
            return
        lines = ["**Open challenges**"]
        for chal in sorted(open_chals, key=lambda c: c["name"].lower()):
            solves = len(chal.get("solves", []))
            lines.append(
                f"• **{chal['name']}** — {chal.get('points', 0)} pts — "
                f"{solves} solve(s)"
            )
        await ctx.send("\n".join(lines))

    @challenge.command(name="info")
    @commands.guild_only()
    async def challenge_info(self, ctx: commands.Context, *, name: str):
        challenges = load_guild(ctx.guild.id)["ctf"]["challenges"]
        chal = challenges.get(name.lower())
        if chal is None:
            await ctx.send("Challenge not found.")
            return
        solves = chal.get("solves", [])
        await ctx.send(
            f"**{chal['name']}** [{chal.get('status', 'open')}]\n"
            f"Points: {chal.get('points', 0)}\n"
            f"Solves: {len(solves)}\n"
            f"{chal.get('description', '')}"
        )

    @challenge.command(name="create")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def challenge_create(self, ctx: commands.Context, *, payload: str):
        parts = [p.strip() for p in payload.split("|", 3)]
        if len(parts) != 4:
            await ctx.send(
                "Usage: `!challenge create <name> | <points> | <flag> | <description>`"
            )
            return
        name, points_raw, flag, description = parts
        try:
            points = int(points_raw)
        except ValueError:
            await ctx.send("Points must be an integer.")
            return
        if points < 0:
            await ctx.send("Points must be non-negative.")
            return

        key = name.lower()
        salt = secrets.token_hex(8)
        record = {
            "name": name,
            "points": points,
            "description": description,
            "flag_hash": _hash_flag(f"{salt}:{flag}"),
            "salt": salt,
            "status": "open",
            "solves": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": ctx.author.id,
        }

        def mutate(data):
            data["ctf"]["challenges"][key] = record

        update_guild(ctx.guild.id, mutate)
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(
            f"Challenge **{name}** created for {points} pts. "
            f"(Flag message deleted if possible — don't paste flags in public chat.)"
        )

    @challenge.command(name="close")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def challenge_close(self, ctx: commands.Context, *, name: str):
        key = name.lower()

        def mutate(data):
            chal = data["ctf"]["challenges"].get(key)
            if chal is None:
                raise KeyError(key)
            chal["status"] = "closed"

        try:
            update_guild(ctx.guild.id, mutate)
        except KeyError:
            await ctx.send("Challenge not found.")
            return
        await ctx.send(f"Closed challenge **{name}**.")

    @challenge.command(name="submit")
    @commands.guild_only()
    async def challenge_submit(self, ctx: commands.Context, name: str, *, flag: str):
        key = name.lower()
        data = load_guild(ctx.guild.id)
        chal = data["ctf"]["challenges"].get(key)
        if chal is None:
            await ctx.send("Challenge not found.")
            return
        if chal.get("status") != "open":
            await ctx.send("That challenge is closed.")
            return

        user_id = str(ctx.author.id)
        if user_id in chal.get("solves", []):
            await ctx.send("You already solved this one.")
            try:
                await ctx.message.delete()
            except Exception:
                pass
            return

        expected = chal["flag_hash"]
        candidate = _hash_flag(f"{chal['salt']}:{flag}")
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if not secrets.compare_digest(expected, candidate):
            await ctx.send("Incorrect flag.", delete_after=8)
            return

        points = int(chal.get("points", 0))

        def mutate(d):
            challenge = d["ctf"]["challenges"][key]
            if user_id not in challenge["solves"]:
                challenge["solves"].append(user_id)
                scores = d["ctf"].setdefault("scores", {})
                scores[user_id] = int(scores.get(user_id, 0)) + points

        update_guild(ctx.guild.id, mutate)
        await ctx.send(
            f"✅ {ctx.author.mention} solved **{chal['name']}** for **{points}** pts!"
        )

    @commands.command(name="leaderboard", aliases=["lb"], help="Show CTF leaderboard.")
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context):
        scores = load_guild(ctx.guild.id)["ctf"].get("scores") or {}
        if not scores:
            await ctx.send("Leaderboard is empty. Solve a challenge with `!challenge submit`.")
            return
        ranked = sorted(scores.items(), key=lambda item: int(item[1]), reverse=True)[:15]
        lines = ["**Cyberspace CTF leaderboard**"]
        for index, (user_id, points) in enumerate(ranked, start=1):
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else f"User {user_id}"
            lines.append(f"{index}. {name} — {points} pts")
        await ctx.send("\n".join(lines))


async def setup(bot: commands.Bot):
    await bot.add_cog(CTF(bot))
