import discord
from discord.ext import commands
import os
import bot

BOTTOKEN = os.environ['BOTTOKEN']
#defines our cogs
cogs = [bot]

#initializes the bot
client = commands.Bot(command_prefix="-", intents = discord.Intents.all(), help_command=None)
client.remove_command('help')
      
#sets up our cogs for the client
for i in range(len(cogs)):
  cogs[i].setup(client)

client.run(BOTTOKEN)