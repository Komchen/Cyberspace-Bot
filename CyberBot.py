import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

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