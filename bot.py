import discord
from discord.ext import commands
import youtube_dl
from bs4 import BeautifulSoup
import requests
import urllib.parse, urllib.request, re
import time
import random
from datetime import datetime

currentUrl = ""
songIndex = 0
queues = {}
urls = {}
isPaused = False
            
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
    global isPaused
    #if the person calling the -join function isn't in a call
    if ctx.author.voice is None:
      errorembed=discord.Embed(title="Error",description='You are not in a VC, please connect to a VC to use bot',color=0xac45bd, timestamp=datetime.utcnow())
      errorembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
      await ctx.send(embed=errorembed)
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
    try:
      title = "Now Playing"
      if ctx.voice_client.is_playing() or isPaused:
        title = "Added To Queue"
      
      if url.startswith("file"):
        url = ctx.message.attachments[0].url
        
      if not url.startswith("https://"):
        #downloads youtube html page, looks through html content to look for video links so can add to queue
        url = url.replace(" ","_")
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query="+url)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        url = "https://www.youtube.com/watch?v="+video_ids[0]

      with youtube_dl.YoutubeDL(ydl_cfg) as ydl:
          info = ydl.extract_info(url, download=False)
          if 'entries' in info:
            for i in info['entries']:
              url2 = i['formats'][0]['url']     
              source = await discord.FFmpegOpusAudio.from_probe(url2, **ffmpeg_cfg)
              if guild_id in urls:
                urls[guild_id].append(url)
              else:
                urls[guild_id] = [url]

              if guild_id in queues:
                queues[guild_id].append(source)
              else:
                queues[guild_id] = [source]
          else:
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
          isPaused = False
      #adds reaction to message sent by user to show that the bot acknowledges their request
      await ctx.message.add_reaction("▶")
      data = scrape(urls[guild_id][len(urls[guild_id])-1])
      playembed=discord.Embed(title=title,description='[{}]({}) [<@{}>]'.format(data.get("title"),urls[guild_id][len(urls[guild_id])-1],ctx.message.author.id),color=0xac45bd, timestamp=datetime.utcnow())     
      playembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80") 
      await ctx.send(embed = playembed)  
    except:
      playerrorembed=discord.Embed(title="Error",description="Error adding song to queue",color=0xac45bd,timestamp=datetime.utcnow())
      playerrorembed.set_footer(text='guagua2', icon_url="https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
      await ctx.send(embed = playerrorembed)
      await ctx.message.add_reaction("🖕")
  
  #remove a track from a specified index in the queue
  @commands.command()
  async def remove(self,ctx,number:int):
    guild_id = ctx.message.guild.id
    #attemps to remove the song from the specified index
    try:
      await ctx.message.add_reaction("👍")
      data = scrape(urls[guild_id][songIndex+number-1])
      removeembed=discord.Embed(title="Removed",description="Removed Track:\n[{}]({})".format(data.get("title"),urls[guild_id][songIndex+number-1]), color=0xac45bd, timestamp=datetime.utcnow())
      removeembed.set_footer(text='guagua2', icon_url="https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
      await ctx.send(embed = removeembed)
      queues[guild_id].pop(songIndex+number-1)
      urls[guild_id].pop(songIndex+number-1)
    except:
      await ctx.message.add_reaction("🖕")
      invalidpageembed=discord.Embed(title="Invalid",description="Invalid track number!!",color=0xac45bd,timestamp=datetime.utcnow()) 
      invalidpageembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
      await ctx.send(embed = invalidpageembed)
  
  #view the current queue
  @commands.command()
  async def queue(self,ctx,*page):
    try:
      pageNum = 0
      if len(page)==0:
        pageNum = 0
      else:
        pageNum = (int(page[0])-1)*10
      guild_id = ctx.message.guild.id
      description = ""
      tempI = songIndex + pageNum
      showIndex = 1 + pageNum
      guild_id = ctx.message.guild.id
      if len(queues[guild_id]) != songIndex:
        data = scrape(urls[guild_id][songIndex-1])
        description+="**Now Playing:** \n[{}]({})\n\n**⬇️Up Next:⬇️**".format(data.get("title"),urls[guild_id][songIndex-1])
        await ctx.message.add_reaction("👍")
        while tempI < len(urls[guild_id]) and showIndex<11:
          data = scrape(urls[guild_id][tempI])
          description+='\n`{}.` [{}]({})'.format(showIndex,data.get("title"),urls[guild_id][tempI])
          tempI+=1
          showIndex+=1
        description+="\n\n**{} songs in queue\n**Page 1/{}".format(len(urls[guild_id])-songIndex,1+int(len(urls[guild_id])/10))
          
        queueembed=discord.Embed(title="Queue",description=description,color=0xac45bd, timestamp=datetime.utcnow()) 
        queueembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
        await ctx.send(embed = queueembed)
      else: 
        await ctx.message.add_reaction("🖕")
        queueemptyembed=discord.Embed(title="Queue Empty",description="The queue is empty! Add some tracks!",color=0xac45bd, timestamp=datetime.utcnow()) 
        queueemptyembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
        await ctx.send(embed = queueemptyembed)
    except:
      await ctx.message.add_reaction("🖕")
      invalidpageembed=discord.Embed(title="Invalid",description="Invalid page number!!",color=0xac45bd,timestamp=datetime.utcnow()) 
      invalidpageembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
      await ctx.send(embed = invalidpageembed)

  #pauses the current stream of audio and sends message alerting user
  @commands.command()
  async def pause(self,ctx):
    global isPaused
    guild_id = ctx.message.guild.id
    data = scrape(urls[guild_id][songIndex-1])
    pauseembed=discord.Embed(title="Track Paused",description='[{}]({}) [<@{}>]'.format(data.get("title"),urls[guild_id][songIndex-1],ctx.message.author.id),color=0xac45bd, timestamp=datetime.utcnow())
    pauseembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
    await ctx.message.add_reaction("⏸")
    await ctx.send(embed=pauseembed)
    isPaused = True
    ctx.voice_client.pause() 
      

  #resumes the current stream of audio and sends message alerting user
  @commands.command()
  async def resume(self,ctx):
    global isPaused
    guild_id = ctx.message.guild.id
    data = scrape(urls[guild_id][songIndex-1])
    resumeembed=discord.Embed(title="Track Resumed",description='[{}]({}) [<@{}>]'.format(data.get("title"),urls[guild_id][songIndex-1],ctx.message.author.id),color=0xac45bd, timestamp=datetime.utcnow())
    resumeembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
    await ctx.message.add_reaction("⏯")
    await ctx.send(embed=resumeembed)
    isPaused = False
    ctx.voice_client.resume()    

  #skips the current song playing
  @commands.command()
  async def skip(self,ctx):
    guild_id = ctx.message.guild.id
    if ctx.voice_client and (ctx.voice_client.is_playing() or isPaused):
      ctx.voice_client.stop()
      if songIndex==len(urls[guild_id]):
        skipembed=skipembed=discord.Embed(title="**Track Skipped**",description='No more songs are in the queue!',color=0xac45bd, timestamp=datetime.utcnow())
      else:
        time.sleep(.5)
        data = scrape(urls[guild_id][songIndex-1])
        skipembed=discord.Embed(title="**Track Skipped,** Now Playing",description='[{}]({}) [<@{}>]'.format(data.get("title"),urls[guild_id][songIndex-1],ctx.message.author.id),color=0xac45bd, timestamp=datetime.utcnow())
      await ctx.message.add_reaction("⏭")
      skipembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
      await ctx.send(embed=skipembed)
      
    else:
      await ctx.message.add_reaction("🖕")
      nosongembed=discord.Embed(title="No Song Found",description= "There are currently no songs in queue!",color=0xac45bd, timestamp=datetime.utcnow())
      nosongembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
      await ctx.send(embed=nosongembed)

  @commands.command()
  async def help(self,ctx):
    helpembed=discord.Embed(title="Command Menu",description="`-play` Play songs and add to queue, input is keywords or links \n `-pause` Pause current song \n `-resume` Resume current song \n `-skip` Skip current song \n `-queue` View queued songs \n `-remove` Remove songs from queue, input is index of queue \n `-shuffle` Shuffle queue \n `-dc` Disconnect Bot \n `-stop` Another way to Disconnect Bot \n \n Currently guagua2 only supports Soundcloud and Youtube, made by taevion#9279 and blum#0001",color=0xac45bd, timestamp=datetime.utcnow())
    helpembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
    await ctx.send(embed=helpembed)


  @commands.command()
  async def shuffle(self,ctx):
    guild_id = ctx.message.guild.id
    global queues, urls
    if len(queues[guild_id]) != songIndex:
      #creates a temp list that holds all the songs that are coming up in the queue
      tempLSources = []
      tempLUrls = []
      tempIndex = songIndex

      while tempIndex != len(queues[guild_id]):
        tempLSources.append(queues[guild_id][tempIndex])
        tempLUrls.append(urls[guild_id][tempIndex])
        tempIndex+=1
      
      #shuffles our temp lists
      i = len(tempLSources)-1
      while i>0:
        index = random.randint(0, len(tempLSources)-1)
        temp = tempLSources[index]
        tempLSources[index] = tempLSources[i]
        tempLSources[i] = temp

        temp = tempLUrls[index]
        tempLUrls[index]=tempLUrls[i]
        tempLUrls[i] = temp
        i-=1
      
      #replaces elements in our current queue playing with our now shuffled temp list of our queue
      tempIndex = songIndex
      for j in range(len(tempLSources)):
        queues[guild_id][tempIndex]=tempLSources[j]
        urls[guild_id][tempIndex]=tempLUrls[j]
        tempIndex+=1
      
      await ctx.message.add_reaction("🔀")
      shuffleembed=discord.Embed(title="Queue Shuffled",description='The queue has been shuffled!',color=0xac45bd, timestamp=datetime.utcnow())
      shuffleembed.set_footer(text='guagua2', icon_url= "https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
      await ctx.send(embed=shuffleembed)
      
    else: 
      await ctx.message.add_reaction("🖕")
      await ctx.send("The queue is empty! Add some tracks!")
      shuffleeerrorembed=discord.Embed(title="Queue Empty",description='The queue is empty! Add some tracks!',color=0xac45bd, timestamp=datetime.utcnow())
      shuffleeerrorembed.set_footer(text='guagua2', icon_url="https://cdn.discordapp.com/avatars/900794325590474753/3c28066bb4f2855bddd254d8516aa149.png?size=80")
      await ctx.send(embed=shuffleeerrorembed)

  """
  @commands.command()
  async def lyrics(self,ctx):
    data = scrape(currentUrl)
    print(data)
    search_term = data['title']
    search_term = search_term.replace(" ","_").replace("(","").replace(")","").replace(".","").replace(",","").replace("Official_Video","")
    print("https://www.genius.com/search?q="+search_term)
    #html = BeautifulSoup(requests.get("https://www.genius.com/search?q="+search_term).text, "html.parser")
    html = urllib.request.urlopen("https://www.genius.com/search?q="+search_term)
    genius_id = html.find_all("a")
    print(genius_id)
    url = "https://www.youtube.com/watch?v=" 
  """
    

#helper function that goes through the queue one song after another
def check_queue(ctx,id):
  global currentUrl, songIndex
  if queues[id]!=[]:
    try:
      if songIndex != (len(queues[id])):
        source = queues[id][songIndex]
        currentUrl = urls[id][songIndex-1]
        #streams the FFmpeg stream to the bot's current vc
        ctx.voice_client.play(source, after=lambda x=None: check_queue(ctx, id))
        songIndex+=1
    except:
      #you get an audio already playing error if you use -play function while a song is currently playing
      #this error doesn't actually affect the bot it just clogs up console so I added this try: except: statement to catch the error
      print("audio alread playing lel")


def scrape(url):
  r = BeautifulSoup(requests.get(url).text, "html.parser")
  if url.startswith("https://soundcloud"):
    title = r.select_one('meta[name="description"][content]')['content']
    title = title[7:len(title)-76]
  else:
    title = r.select_one('meta[itemprop="name"][content]')['content']
  data = {'title':title}
  return data
  
def setup(client):
  client.add_cog(bot(client))
