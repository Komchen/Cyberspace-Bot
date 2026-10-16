import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv('token.env')
TOKEN = os.getenv('discord_token')


bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
bot_channel = {} #dictionary to store the bot channel for each guild

@bot.command ( 
name= "setchannel",
description= "Set which channel the bot will send messages in")

@bot.command() # "!online" checks if bot is online and working.
async def online(ctx: commands.Context):
    await ctx.send("Online")

@discord.app_commands.guild_only()
async def setchannel(interaction: commands.Context, channel: discord.TextChannel):

    if interaction.user.guild_permissions.administrator: #check to see if user has permission
        bot_channel[interaction.guild.id] = channel.id
        await interaction.response.send_message(f"Bot channel set to {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)  












bot.run(TOKEN)