import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv('token.env')
TOKEN = os.getenv('discord_token')


bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
bot_channel = {} #dictionary to store the bot channel for each guild

@bot.command( 
name= "setchannel",
help= "Set which channel the bot will send messages in")

@bot.command(name="online", help="Check if the bot is online and working.")
async def online(ctx: commands.Context):
    await ctx.send("Online")

@commands.guild_only()
async def setchannel(ctx: commands.Context, channel: discord.TextChannel):

    if ctx.author.guild_permissions.administrator: #check to see if user has permission
        bot_channel[ctx.guild.id] = channel.id
        await ctx.send(f"Bot channel set to {channel.mention}")
    else:
        await ctx.send("You do not have permission to use this command.")  












bot.run(TOKEN)