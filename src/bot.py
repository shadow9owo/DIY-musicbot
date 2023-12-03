import discord
import asyncio
import yt_dlp
from discord.ext import commands

intents = discord.Intents(messages=True, guilds=True, message_content=True, voice_states=True)

inqueue = []

rap = open("accessrole.txt","r").read()

tokenfile = open("token.txt","r").read()
bot = commands.Bot(command_prefix='?', intents=intents)
file_contents = open("help.txt", "r").read()
credits_contents = open("Credits.txt", "r").read()

voice_clients = {}
yt_dl_opts =    ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    }
ytdl = yt_dlp.YoutubeDL(yt_dl_opts)
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 200M',
    'options': '-vn' 
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.slash_command(name="help", description="shows help", guild_ids=[1030142890300682402])
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(f"```{file_contents}```")

@bot.slash_command(name="credits", description="shows credits", guild_ids=[1030142890300682402])
async def credits(interaction: discord.Interaction):
    await interaction.response.send_message(f"```{credits_contents}```")

def hasperms(ctx):
    if any(role.id == rap for role in ctx.author.roles):
        return True
    else:
        return False

import asyncio

inqueue = []

async def after_playing(ctx, voice_clients, error):
    if ctx is None:
        return

    guild_id = ctx.guild.id
    voice_client = voice_clients.get(guild_id)

    if guild_id in voice_clients:
        del voice_clients[guild_id]

    if error:
        print(f"Error after playing: {error}")

    if inqueue:
        next_url = inqueue.pop(0)
        loop = asyncio.get_event_loop()
        next_data = await loop.run_in_executor(None, lambda: ytdl.extract_info(next_url, download=False))
        next_song = next_data["url"]
        next_player = discord.FFmpegPCMAudio(next_song, **ffmpeg_options, executable="ffmpeg.exe")
        voice_client.play(next_player, after=lambda error: loop.create_task(after_playing(ctx, voice_clients, error)))
    else:
        await voice_client.disconnect()



@bot.command(name='play')
async def play(ctx):
    if hasperms(ctx):
        try:
            url = ctx.message.content.split(" ")[1]

            channel = ctx.author.voice.channel
            voice_client = voice_clients.get(ctx.guild.id)

            if voice_client and voice_client.is_playing():
                inqueue.append(url)
                await ctx.send("The selected song has been added to the queue.")
                return

            if not voice_client:
                voice_client = await channel.connect()
                voice_clients[ctx.guild.id] = voice_client

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

            if data["duration"] > 600:
                await ctx.send("The selected song is too long (more than 10 minutes). Disconnecting.")
                await voice_client.disconnect()
                del voice_clients[ctx.guild.id]
                return

            song = data["url"]
            player = discord.FFmpegPCMAudio(song, **ffmpeg_options, executable="ffmpeg.exe")

            voice_client.play(player, after=lambda error: loop.create_task(after_playing(error, voice_client, ctx)))

        except Exception as ex:
            print(ex)
    else:
        await ctx.send("You do not have the required role.")

@bot.command(name='skip')
async def skip(ctx):
    if hasperms(ctx):
        try:
            voice_client = voice_clients.get(ctx.guild.id)

            if voice_client and voice_client.is_playing():
                voice_client.stop()

                if inqueue:
                    next_url = inqueue.pop(0)
                    loop = asyncio.get_event_loop()
                    next_data = await loop.run_in_executor(None, lambda: ytdl.extract_info(next_url, download=False))
                    next_song = next_data["url"]
                    next_player = discord.FFmpegPCMAudio(next_song, **ffmpeg_options, executable="ffmpeg.exe")
                    voice_client.play(next_player, after=lambda error: loop.create_task(after_playing(error, voice_client, ctx)))
                else:
                    await voice_client.disconnect()
                    del voice_clients[ctx.guild.id]

            else:
                await ctx.send("Not currently playing anything.")
        except Exception as ex:
            print(ex)
    else:
        await ctx.send("You do not have the required role.")


@bot.command(name='clear')
async def clear(ctx):
    if hasperms(ctx):
        try:
            inqueue.clear()
        except Exception as ex:
            print(ex)
    else:
        await ctx.send("You do not have the required role.")

@bot.command(name='pause')
async def pause(ctx):
    if hasperms(ctx):
        try:
            voice_client = voice_clients.get(ctx.guild.id)
    
            if voice_client and voice_client.is_playing():
                voice_client.pause()
            else:
                await ctx.send("Not currently playing anything.")
    
        except Exception as ex:
            print(ex)
    else:
        await ctx.send("You do not have the required role.")

@bot.command(name='resume')
async def resume(ctx):
    if hasperms(ctx):
        try:
            voice_client = voice_clients.get(ctx.guild.id)
    
            if voice_client and voice_client.is_paused():
                voice_client.resume()
            else:
                await ctx.send("Not currently paused.")
    
        except Exception as ex:
            print(ex)
    else:
        await ctx.send("You do not have the required role.")

@bot.command(name='stop')
async def stop(ctx):
    if hasperms(ctx):
        try:
            voice_client = voice_clients.get(ctx.guild.id)
    
            if voice_client:
                inqueue.clear()
                voice_client.stop()
                await voice_client.disconnect()
                del voice_clients[ctx.guild.id]
            else:
                await ctx.send("Not currently playing anything.")
    
        except Exception as ex:
            print(ex)
    else:
        await ctx.send("You do not have the required role.")

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel and not after.channel and hasattr(before, 'guild'):
        voice_client = voice_clients.get(before.guild.id)

        if bot.user == member and voice_client:
            if len(after.channel.members) == 1:
                voice_client.stop()
                await voice_client.disconnect()
                del voice_clients[before.guild.id]



bot.run("MTEyOTI5NTQ1NTM4MjE1MTIxOA.GVlrqv.PKgcnecXqW59TASLC8hNczT75eGl8-1-IIiR7Y")
