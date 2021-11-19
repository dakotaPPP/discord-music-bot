import discord
from discord.ext import commands
import youtube_dl
from bs4 import BeautifulSoup
import requests
import urllib.parse, urllib.request, re
import random
#guaTOKEN = os.environ['guaguaTOKEN']


currentUrl = ""
songIndex = 0
queues = {}
urls = {}
          
    
class bot(commands.Cog):
  def __init__(self, client): 
    self.client = client
  
  #disconnects bot from queue and clears queue
  @commands.command()
  async def dc(self,ctx):
    global songIndex
    guild_id = ctx.message.guild.id
    queues[guild_id].clear()
    urls[guild_id].clear()
    songIndex = 0
    await ctx.message.add_reaction("👋")
    await ctx.voice_client.disconnect()

  #another way to call the dc command
  @commands.command()  
  async def stop(self,ctx):
    global songIndex
    guild_id = ctx.message.guild.id
    queues[guild_id].clear()
    urls[guild_id].clear()
    songIndex = 0
    await ctx.message.add_reaction("👋")
    await ctx.voice_client.disconnect()

    #adds songs to the queue 
  @commands.command()
  async def play(self,ctx,url:str):
    #if the person calling the -join function isn't in a call
    if ctx.author.voice is None:
      await ctx.send("You are not in a VC, please connect to a VC to use bot")
    vc = ctx.author.voice.channel
    #if bot is not in a vc
    if ctx.voice_client is None:
      await vc.connect()
    #if bot is currently in a vc and needs to switch vc
    else:
      await ctx.voice_client.move_to(vc)

    #standard FFMPEG configuration
    ffmpeg_cfg = {"before_options":"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5","options":"-vn"}
    #youtube dl config that gets the best audio to stream
    ydl_cfg = {"format":"bestaudio"}

    guild_id = ctx.message.guild.id

    if not url.startswith("https://"):
      #downloads youtube html page, looks through html content to look for video links so can add to queue
      url = url.replace(" ","_")
      html = urllib.request.urlopen("https://www.youtube.com/results?search_query="+url)
      video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
      url = "https://www.youtube.com/watch?v="+video_ids[0]

    #adds reaction to message sent by user to show that the bot acknowledges their request
       
    await ctx.message.add_reaction("▶")
    await ctx.send(f"`{url}` added to queue!")
    
    with youtube_dl.YoutubeDL(ydl_cfg) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info["formats"][0]["url"]
        #creates FFmpeg stream for the audio
        source = await discord.FFmpegOpusAudio.from_probe(url2, **ffmpeg_cfg)

        #adds our url into urls dictionary corresponding to guild_id
        if guild_id in urls:
          urls[guild_id].append(url)
        else:
          urls[guild_id] = [url]

        #adds our FFmpeg stream of audio into queues dictionary corresponding to guild_id
        if guild_id in queues:
          queues[guild_id].append(source)
        else:
          queues[guild_id] = [source]
        check_queue(ctx, guild_id)    
  
  #remove a track from a specified index in the queue
  @commands.command()
  async def remove(self,ctx,number:int):
    guild_id = ctx.message.guild.id
    #attemps to remove the song from the specified index
    try:
      queues[guild_id].pop(songIndex+number-1)
      await ctx.message.add_reaction("👍")
      await ctx.send(f"Your queue is now `{queues[guild_id]}`")
    except:
      await ctx.message.add_reaction("🖕")
      await ctx.send("**Invalid track number**")
  
  #view the current queue
  @commands.command()
  async def queue(self,ctx):
    guild_id = ctx.message.guild.id
    if len(queues[guild_id]) != songIndex:
      await ctx.message.add_reaction("👍")
      await ctx.send(f"Your queue is now `{queues[guild_id]}`")
    else: 
      await ctx.message.add_reaction("🖕")
      await ctx.send("The queue is empty! Add some tracks!")

  #pauses the current stream of audio and sends message alerting user
  @commands.command()
  async def pause(self,ctx):
    data = scrape(currentUrl)
    pauseembed=discord.Embed(title="Track Paused",description=data.get["title"])
    await ctx.message.add_reaction("⏸")
    await ctx.send(embed=pauseembed)  
    ctx.voice_client.pause() 
      

  #resumes the current stream of audio and sends message alerting user
  @commands.command()
  async def resume(self,ctx):
    data = scrape(currentUrl)
    resumeembed=discord.Embed(title="Track Resumed",description= data.get["title"])
    await ctx.message.add_reaction("⏯")
    await ctx.send(embed=resumeembed)
    ctx.voice_client.resume()    

  #skips the current song playing
  @commands.command()
  async def skip(self,ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
      ctx.voice_client.stop()
      await ctx.message.add_reaction("⏭")
      skipembed=discord.Embed(title="Track Skipped",description= "")
      await ctx.send(embed=skipembed)
    else:
      await ctx.message.add_reaction("🖕")
      nosongembed=discord.Embed(title="No Song Found",description= "There are currently no songs in queue!")
      await ctx.send(embed=nosongembed)

  @commands.command()
  async def shuffle(self,ctx):
    guild_id = ctx.message.guild.id
    if len(queues[guild_id]) != songIndex:
      #creates a temp list that holds all the songs that are coming up in the queue
      tempLSources = []
      tempLUrls = []
      tempIndex = songIndex
      print(queues[guild_id])
      while tempIndex != len(queues[guild_id]):
        tempLSources.append(queues[guild_id][tempIndex])
        tempLUrls.append(urls[guild_id][tempIndex])
        tempIndex+=1
      #shuffles our temp lists
      i = tempLSources.lenght-1
      while i>0:
        index = random.nextInt(i+1)
        temp = tempLSources[index]
        tempLSources[index] = tempLSources[i]
        tempLSources[i] = temp

        temp = tempLUrls[index]
        tempLUrls[index]=tempLUrls[i]
        tempLUrls[i] = temp
        i-=1
      #replaces elements in our current queue playing with our now shuffled temp list of our queue
      tempIndex = songIndex
      for j in tempLSources:
        queues[guild_id][tempIndex]=j
        tempIndex+=1

      tempIndex = songIndex
      for k in tempLUrls:
        urls[guild_id][tempIndex]=k
        tempIndex+=1
      await ctx.message.add_reaction("🔀")
      await ctx.send("The queue has been shuffled!")
      print(queues[guild_id])
    else: 
      await ctx.message.add_reaction("🖕")
      await ctx.send("The queue is empty! Add some tracks!")

  @commands.command()
  async def lyrics(self,ctx):
    data = scrape(currentUrl)
    print(data)
    search_term = data['title']
    search_term = search_term.replace(" ","_").replace("(","").replace(")","").replace(".","").replace(",","").replace("Official_Video","")
    print("https://www.genius.com/search?q="+search_term)
    html = BeautifulSoup(requests.get("https://www.genius.com/search?q="+search_term).text, "html.parser")
    genius_id = html.find_all("td",{"class":"tal qx"})
    print(genius_id[0])
    url = "https://www.youtube.com/watch?v="
    

#helper function that goes through the queue one song after another
def check_queue(ctx,id):
  global currentUrl, songIndex
  if queues[id]!=[]:
    try:
      if songIndex != (len(queues[id])):
        source = queues[id][songIndex]
        currentUrl = urls[id][songIndex]
        #streams the FFmpeg stream to the bot's current vc
        ctx.voice_client.play(source, after=lambda x=None: check_queue(ctx, id))
        songIndex+=1
    except:
      #you get an audio already playing error if you use -play function while a song is currently playing
      #this error doesn't actually affect the bot it just clogs up console so I added this try: except: statement to catch the error
      print("audio alread playing lel")


def scrape(url):
  r = BeautifulSoup(requests.get(url).text, "html.parser")
  title = r.select_one('meta[itemprop="name"][content]')['content']
  data = {'title':title}
  return data
  



def setup(client):
  client.add_cog(bot(client))