import discord
from discord.ext import commands

from utils.storage import load_guild, update_guild

DEFAULT_TRACKS = [
    ("Red Team", "🔴", discord.ButtonStyle.danger),
    ("Blue Team", "🔵", discord.ButtonStyle.primary),
    ("Hardware", "🛠️", discord.ButtonStyle.secondary),
    ("Cloud", "☁️", discord.ButtonStyle.secondary),
    ("Competing", "🏆", discord.ButtonStyle.success),
]


class RoleToggleButton(discord.ui.Button):
    def __init__(self, label: str, emoji: str, style: discord.ButtonStyle, role_id: int):
        super().__init__(
            label=label,
            emoji=emoji,
            style=style,
            custom_id=f"cyberspace:role:{role_id}",
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "This only works inside the server.", ephemeral=True
            )
            return

        role = interaction.guild.get_role(self.role_id)
        if role is None:
            await interaction.response.send_message(
                "That role no longer exists. Ask an officer to run `!roles setup`.",
                ephemeral=True,
            )
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role, reason="Self-removed interest role")
            await interaction.response.send_message(
                f"Removed **{role.name}**.", ephemeral=True
            )
        else:
            await member.add_roles(role, reason="Self-assigned interest role")
            await interaction.response.send_message(
                f"Added **{role.name}**.", ephemeral=True
            )


class RolePanel(discord.ui.View):
    def __init__(self, options: dict[str, int]):
        super().__init__(timeout=None)
        style_by_name = {name: style for name, _emoji, style in DEFAULT_TRACKS}
        emoji_by_name = {name: emoji for name, emoji, _style in DEFAULT_TRACKS}
        for name, role_id in options.items():
            self.add_item(
                RoleToggleButton(
                    label=name,
                    emoji=emoji_by_name.get(name, "📌"),
                    style=style_by_name.get(name, discord.ButtonStyle.secondary),
                    role_id=int(role_id),
                )
            )


class Roles(commands.Cog):
    """Self-assign interest roles for club tracks."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Re-register persistent views for guilds that already posted a panel.
        # Actual buttons are rebuilt when setup runs; custom_id handlers need the view.
        for guild in self.bot.guilds:
            data = load_guild(guild.id)
            options = data.get("roles", {}).get("options") or {}
            if options:
                self.bot.add_view(RolePanel(options))

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            data = load_guild(guild.id)
            options = data.get("roles", {}).get("options") or {}
            if options:
                self.bot.add_view(RolePanel(options))

    @commands.group(
        name="roles",
        invoke_without_command=True,
        help="Show or set up self-assign interest roles.",
    )
    @commands.guild_only()
    async def roles(self, ctx: commands.Context):
        data = load_guild(ctx.guild.id)
        options = data.get("roles", {}).get("options") or {}
        if not options:
            await ctx.send(
                "Interest roles are not set up yet. An officer can run `!roles setup`."
            )
            return

        lines = ["**Interest roles** (toggle with the panel buttons, or ask an officer):"]
        for name, role_id in options.items():
            role = ctx.guild.get_role(int(role_id))
            lines.append(f"• {name}: {role.mention if role else '`missing`'}")
        channel_id = data["roles"].get("channel_id")
        if channel_id:
            channel = ctx.guild.get_channel(int(channel_id))
            if channel:
                lines.append(f"\nPanel: {channel.mention}")
        await ctx.send("\n".join(lines))

    @roles.command(name="setup", help="Create interest roles and post a button panel.")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True, manage_guild=True)
    async def roles_setup(self, ctx: commands.Context):
        me = ctx.guild.me
        if me is None or not me.guild_permissions.manage_roles:
            await ctx.send("I need the **Manage Roles** permission.")
            return

        options: dict[str, int] = {}
        for name, _emoji, _style in DEFAULT_TRACKS:
            role = discord.utils.get(ctx.guild.roles, name=name)
            if role is None:
                role = await ctx.guild.create_role(
                    name=name,
                    reason="Cyberspace interest role setup",
                    mentionable=True,
                )
            if role >= me.top_role:
                await ctx.send(
                    f"My role must be **above** `{name}` so I can assign it. "
                    "Move my bot role higher, then rerun `!roles setup`."
                )
                return
            options[name] = role.id

        view = RolePanel(options)
        embed = discord.Embed(
            title="Choose your Cyberspace tracks",
            description=(
                "Click a button to join or leave a track.\n"
                "You can pick more than one."
            ),
            color=discord.Color.dark_green(),
        )
        message = await ctx.send(embed=embed, view=view)
        self.bot.add_view(view)

        def mutate(data):
            data["roles"]["options"] = options
            data["roles"]["message_id"] = message.id
            data["roles"]["channel_id"] = ctx.channel.id

        update_guild(ctx.guild.id, mutate)
        await ctx.send("Interest role panel is live.", delete_after=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
