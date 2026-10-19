from discord.ext import commands

from utils.storage import load_guild, update_guild

DEFAULT_RESOURCES: dict[str, dict[str, str]] = {
    "start": {
        "title": "Getting started",
        "body": (
            "• [TryHackMe](https://tryhackme.com/) — guided rooms\n"
            "• [Hack The Box Academy](https://academy.hackthebox.com/) — structured paths\n"
            "• [OverTheWire](https://overthewire.org/wargames/) — classic wargames\n"
            "• Ask an officer or use `!helpme getting started`"
        ),
    },
    "nmap": {
        "title": "Nmap",
        "body": (
            "• [Official docs](https://nmap.org/book/man.html)\n"
            "• [Nmap Network Scanning book](https://nmap.org/book/)\n"
            "• Practice: scan only hosts you own or club labs"
        ),
    },
    "wireshark": {
        "title": "Wireshark",
        "body": (
            "• [Wireshark User Guide](https://www.wireshark.org/docs/)\n"
            "• [SharkFest / sample captures](https://wiki.wireshark.org/SampleCaptures)"
        ),
    },
    "linux": {
        "title": "Linux fundamentals",
        "body": (
            "• [Linux Journey](https://linuxjourney.com/)\n"
            "• [OverTheWire Bandit](https://overthewire.org/wargames/bandit/)"
        ),
    },
    "web": {
        "title": "Web security",
        "body": (
            "• [OWASP Top 10](https://owasp.org/www-project-top-ten/)\n"
            "• [PortSwigger Web Security Academy](https://portswigger.net/web-security)\n"
            "• Burp Suite Community for intercepting traffic"
        ),
    },
    "forensics": {
        "title": "Digital forensics",
        "body": (
            "• [DFIR resources](https://github.com/meirwah/awesome-incident-response)\n"
            "• Autopsy / Volatility for disk & memory analysis"
        ),
    },
    "crypto": {
        "title": "Crypto / CTF crypto",
        "body": (
            "• [CryptoHack](https://cryptohack.org/)\n"
            "• [Practical Cryptography for Developers](https://cryptobook.nakov.com/)"
        ),
    },
    "oscp": {
        "title": "OSCP-oriented practice",
        "body": (
            "• [TJ Null's OSCP prep](https://www.reddit.com/r/oscp/)\n"
            "• HTB / Proving Grounds practice boxes\n"
            "• Focus: enumeration notes + privilege escalation"
        ),
    },
    "blue": {
        "title": "Blue team",
        "body": (
            "• [MITRE ATT&CK](https://attack.mitre.org/)\n"
            "• [Detection Engineering](https://github.com/0x4D31/awesome-threat-detection)\n"
            "• Sigma rules + basic SIEM concepts"
        ),
    },
    "red": {
        "title": "Red team / offensive",
        "body": (
            "• [HackTricks](https://book.hacktricks.xyz/)\n"
            "• [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings)\n"
            "• Always stay in-scope on club / legal targets only"
        ),
    },
}


class Resources(commands.Cog):
    """Curated cybersecurity learning resources."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _all_resources(self, guild_id: int) -> dict[str, dict[str, str]]:
        custom = load_guild(guild_id).get("resources") or {}
        merged = dict(DEFAULT_RESOURCES)
        merged.update(custom)
        return merged

    @commands.command(
        name="resources",
        aliases=["resource", "res"],
        help="Show learning resources. Usage: !resources [topic]",
    )
    @commands.guild_only()
    async def resources(self, ctx: commands.Context, topic: str | None = None):
        catalog = self._all_resources(ctx.guild.id)
        if topic is None:
            keys = ", ".join(f"`{k}`" for k in sorted(catalog))
            await ctx.send(
                "**Cyberspace resource library**\n"
                f"Topics: {keys}\n"
                "Example: `!resources nmap`\n"
                "Officers can add entries with `!resourceadd`."
            )
            return

        key = topic.lower().strip()
        entry = catalog.get(key)
        if entry is None:
            await ctx.send(
                f"No resource named `{key}`. Try `!resources` for the full list."
            )
            return
        await ctx.send(f"**{entry['title']}**\n{entry['body']}")

    @commands.command(
        name="resourceadd",
        help="Add/update a resource. Usage: !resourceadd <key> | <title> | <body>",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def resourceadd(self, ctx: commands.Context, *, payload: str):
        parts = [p.strip() for p in payload.split("|", 2)]
        if len(parts) != 3:
            await ctx.send("Usage: `!resourceadd <key> | <title> | <body/markdown>`")
            return
        key, title, body = parts
        key = key.lower().replace(" ", "-")

        def mutate(data):
            data["resources"][key] = {"title": title, "body": body}

        update_guild(ctx.guild.id, mutate)
        await ctx.send(f"Saved resource `{key}`. View with `!resources {key}`.")

    @commands.command(name="resourceremove", help="Remove a custom resource (officers).")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def resourceremove(self, ctx: commands.Context, key: str):
        key = key.lower()

        def mutate(data):
            data["resources"].pop(key, None)

        update_guild(ctx.guild.id, mutate)
        await ctx.send(f"Removed custom resource `{key}` (built-ins remain).")


async def setup(bot: commands.Bot):
    await bot.add_cog(Resources(bot))
