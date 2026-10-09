import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv('token.env')
TOKEN = os.getenv('discord_token')


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.tree.command ( 
name= "setchannel"
description= "Set which channel the bot will send messages in"
)

if interaction.user.guild_permissions.administrator:
   bot_channel[interaction.guild.id] = channel.id

   await interaction.response.send_message(f"Bot channel set to {channel.mention}", ephemeral=True)
else:
    await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)  


