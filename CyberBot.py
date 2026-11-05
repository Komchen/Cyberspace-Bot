import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from google_calendar import get_next_event
import asyncio
from datetime import datetime, date
from zoneinfo import ZoneInfo
import html
import re

load_dotenv('token.env')
TOKEN = os.getenv('discord_token')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot_channel = {} #dictionary to store the bot channel for each guild


@bot.command(name="online", help="Check if the bot is online and working.")
async def online(ctx: commands.Context):
    await ctx.send("Online")


@bot.command( name= "setchannel", help= "Set which channel the bot will send messages in")
@commands.guild_only()
async def setchannel(ctx: commands.Context, channel: discord.TextChannel):

    if ctx.author.guild_permissions.administrator: #check to see if user has permission
        bot_channel[ctx.guild.id] = channel.id
        await ctx.send(f"Bot channel set to {channel.mention}")
    else:
        await ctx.send("You do not have administrator permission to use this command.")  

#~~~~~~~~~~~~~~~~~~~~~~~~~Google Calendar Commands~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@bot.command(name="event", help="Show the next CYBERSPACE event")
async def event(ctx: commands.Context):

    next_event = await asyncio.to_thread(get_next_event)

    if next_event is None:
        await ctx.send("No upcoming CYBERSPACE events found!")
        return

    # Retrieve event information
    title = next_event.get("summary", "Untitled Event")
    description = next_event.get(
        "description", "No description provided."
    )
    location = next_event.get("location", "Not specified")
    start = next_event["start"]

    # Google descriptions may contain HTML formatting
    description = re.sub(r"<[^>]+>", "", description)
    description = html.unescape(description).strip()
    if not description:
        description = "No description provided."

    # Prevent extremely long descriptions from exceeding limits
    description = description[:1000]

    # Create Discord embed
    embed = discord.Embed(
        title="📅Next CyberSpace Event:",
        description=f"**{title}**",
        color=discord.Color.blurple()
    )

    # Format the event date and time
    if "dateTime" in start:
        start_dt = datetime.fromisoformat(start["dateTime"])
        timestamp = int(start_dt.timestamp())

        embed.add_field(
            name="📆Date & Time",
            value=f"<t:{timestamp}:F>",
            inline=False
        )
    else:
        # Handle all-day calendar events
        event_date = date.fromisoformat(start["date"])

        embed.add_field(
            name="📆 Date",
            value=event_date.strftime("%A, %B %d, %Y"),
            inline=False
        )

        embed.add_field(
            name="⏰ Time",
            value="All day",
            inline=False
        )

    embed.add_field(
        name="📝Description",
        value=description,
        inline=False
    )

    
    # Include the Google Calendar event link
    event_url = next_event.get("htmlLink")

    if event_url:
        embed.add_field(
            name="Calendar Event",
            value=f"[View Event]({event_url})",
            inline=False
        )

    await ctx.send(
        embed=embed,
        allowed_mentions=discord.AllowedMentions.none()
    )

    






#killswitch command to stop the bot
@bot.command(name="exit", help="Kills the bot")
@commands.guild_only()
@commands.has_guild_permissions(administrator=True)
async def exit(ctx: commands.Context):
    if ctx.author.guild_permissions.administrator: #check to see if user has permission
        await ctx.send("Shutting down...")
        await bot.close()
    else:
        await ctx.send("You do not have administrator permission to use this command.")


bot.run(TOKEN)