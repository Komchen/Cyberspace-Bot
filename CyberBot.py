import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from google_calendar import get_next_event
import asyncio

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

@bot.command(name="nextevent", help="Show the next Cyberspace Calendar event")
async def event(ctx: commands.Context):

    next_event = await asyncio.to_thread(get_next_event)

    if next_event is None:
        await ctx.send("📅 No upcoming Cyberspace events yet!")
        return

    title = next_event.get("summary", "Untitled Event")
    start = next_event["start"].get(
        "dateTime",
        next_event["start"].get("date")
    )

    await ctx.send(
        f"📅 **Next CYBERSPACE Event**\n"
        f"**Event:** {title}\n"
        f"**Starts:** {start}",
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