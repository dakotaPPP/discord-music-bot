import discord
from discord.ext import commands
import os
import youtube_dl
import bot


#defines our cogs
cogs = [bot]

#initializes the bot
client = commands.Bot(command_prefix="-", intents = discord.Intents.all())

#sets up our cogs for the client
for i in range(len(cogs)):
  cogs[i].setup(client)


#testing embeds
@client.command()
async def embed(ctx):
  embed=discord.Embed(title="Test")

  await ctx.send(embed=embed)



client.run("OTAwNzk0MzI1NTkwNDc0NzUz.YXGgFw._3O-vsdfQkZkj2A5gQLoyMDVkDk")
