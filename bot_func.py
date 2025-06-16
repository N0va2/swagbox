import discord
from discord.ext import commands
import yt_dlp
import asyncio
import database as db

opus_path = "/opt/homebrew/opt/opus/lib/libopus.0.dylib"

if not discord.opus.is_loaded():
    print(f"Attempting to load Opus from: {opus_path}")
    try:
        discord.opus.load_opus(opus_path)
        print("Opus library loaded successfully.")
    except Exception as e:
        print(f"!!! FAILED to load opus library from custom path: {e}")

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- FFMPEG and YTDL Options ---
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'extract_flat': True # Faster for getting info
}

# --- Helper function for fetching song info ---
def get_song_info(url):
    with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown Title'),
                'url': info.get('webpage_url', url)
            }
        except yt_dlp.utils.DownloadError:
            return None

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # These playback-related attributes remain the same
        self.voice_clients = {}
        self.queues = {}
    
    # --- CORE PLAYBACK LOGIC (Identical to before) ---
    def play_next(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.queues and self.queues[guild_id]:
            url = self.queues[guild_id].pop(0)
            self.play_song(ctx, url)
        else:
            asyncio.run_coroutine_threadsafe(self.check_disconnect(ctx), self.bot.loop)

    def play_song(self, ctx, url):
        guild_id = ctx.guild.id
        if guild_id not in self.voice_clients: return
        voice_client = self.voice_clients[guild_id]
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        player = discord.PCMVolumeTransformer(source)
        voice_client.play(player, after=lambda e: self.play_next(ctx) if e is None else print(f'Player error: {e}'))

    async def check_disconnect(self, ctx):
        if ctx.voice_client is not None:
            await asyncio.sleep(120)
            if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                await ctx.voice_client.disconnect()
                del self.voice_clients[ctx.guild.id]
                await ctx.send("Disconnected due to inactivity.")
                
    async def join_vc(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You are not in a voice channel!")
            return None
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            vc = await voice_channel.connect()
            self.voice_clients[ctx.guild.id] = vc
        else:
            await ctx.voice_client.move_to(voice_channel)
            vc = ctx.voice_client
        return vc

    # --- NEW PLAYLIST MANAGEMENT COMMANDS ---

    # --- Personal Playlist Commands (p- prefix) ---
    @commands.group(name="p", invoke_without_command=True, help="Manage your personal playlists. Use `!p list` to see them.")
    async def p(self, ctx):
        await ctx.send("Invalid personal playlist command. Use `!help p` for more info.")

    @p.command(name="create", help="Creates a new personal playlist. Usage: !p create <playlist_name>")
    async def p_create(self, ctx, *, name: str):
        if db.create_playlist(ctx.guild.id, name, owner_id=ctx.author.id):
            await ctx.send(f"✅ Personal playlist `{name}` created!")
        else:
            await ctx.send(f"⚠️ You already have a playlist named `{name}`.")

    @p.command(name="add", help="Adds a song to your personal playlist. Usage: !p add <playlist_name> <url>")
    async def p_add(self, ctx, playlist_name: str, *, url: str):
        playlist = db.get_playlist(ctx.guild.id, playlist_name, owner_id=ctx.author.id)
        if not playlist:
            await ctx.send(f"You don't have a personal playlist named `{playlist_name}`.")
            return

        song_info = get_song_info(url)
        if not song_info:
            await ctx.send("Could not fetch song info. Please check the URL.")
            return

        song_id = db.add_or_get_song(song_info['title'], song_info['url'], ctx.author.name)
        if db.add_song_to_playlist(playlist[0], song_id):
            await ctx.send(f"Added **{song_info['title']}** to your playlist `{playlist_name}`.")
        else:
            await ctx.send(f"That song is already in your playlist `{playlist_name}`.")

    @p.command(name="show", help="Shows the songs in one of your playlists. Usage: !p show <playlist_name>")
    async def p_show(self, ctx, *, name: str):
        playlist = db.get_playlist(ctx.guild.id, name, owner_id=ctx.author.id)
        if not playlist:
            await ctx.send(f"You don't have a personal playlist named `{name}`.")
            return
        
        songs = db.get_songs_from_playlist(playlist[0])
        if not songs:
            await ctx.send(f"Playlist `{name}` is empty.")
            return

        description = ""
        for song_id, title, url in songs:
            description += f"`{song_id}`. **{title}**\n"
        
        embed = discord.Embed(title=f"🎵 {ctx.author.display_name}'s Playlist: {name}", description=description, color=discord.Color.green())
        await ctx.send(embed=embed)

    @p.command(name="list", help="Lists all of your personal playlists in this server.")
    async def p_list(self, ctx):
        playlists = db.get_user_playlists(ctx.guild.id, ctx.author.id)
        if not playlists:
            await ctx.send("You have no personal playlists in this server. Use `!p create <name>` to make one!")
            return
        
        description = "\n".join([f"• {name[0]}" for name in playlists])
        embed = discord.Embed(title=f"Your Playlists in {ctx.guild.name}", description=description, color=discord.Color.green())
        await ctx.send(embed=embed)


    # --- Server Playlist Commands (s- prefix) - Admin-only ---
    @commands.group(name="s", invoke_without_command=True, help="Manage server-wide playlists (Admin only).")
    @commands.has_permissions(manage_guild=True)
    async def s(self, ctx):
        await ctx.send("Invalid server playlist command. Use `!help s` for more info.")

    @s.command(name="create", help="Creates a new server playlist. Usage: !s create <playlist_name>")
    @commands.has_permissions(manage_guild=True)
    async def s_create(self, ctx, *, name: str):
        if db.create_playlist(ctx.guild.id, name, owner_id=None):
            await ctx.send(f"✅ Server playlist `{name}` created!")
        else:
            await ctx.send(f"⚠️ A server playlist named `{name}` already exists.")
            
    @s.command(name="add", help="Adds a song to a server playlist. Usage: !s add <playlist_name> <url>")
    @commands.has_permissions(manage_guild=True)
    async def s_add(self, ctx, playlist_name: str, *, url: str):
        playlist = db.get_playlist(ctx.guild.id, playlist_name, owner_id=None)
        if not playlist:
            await ctx.send(f"There is no server playlist named `{playlist_name}`.")
            return

        song_info = get_song_info(url)
        if not song_info:
            await ctx.send("Could not fetch song info. Please check the URL.")
            return

        song_id = db.add_or_get_song(song_info['title'], song_info['url'], ctx.author.name)
        if db.add_song_to_playlist(playlist[0], song_id):
            await ctx.send(f"Added **{song_info['title']}** to server playlist `{playlist_name}`.")
        else:
            await ctx.send(f"That song is already in the server playlist `{playlist_name}`.")

    @s.command(name="show", help="Shows the songs in a server playlist. Usage: !s show <playlist_name>")
    async def s_show(self, ctx, *, name: str):
        playlist = db.get_playlist(ctx.guild.id, name, owner_id=None)
        if not playlist:
            await ctx.send(f"There is no server playlist named `{name}`.")
            return
        
        songs = db.get_songs_from_playlist(playlist[0])
        if not songs:
            await ctx.send(f"Server playlist `{name}` is empty.")
            return

        description = ""
        for song_id, title, url in songs:
            description += f"`{song_id}`. **{title}**\n"
        
        embed = discord.Embed(title=f"🎵 Server Playlist: {name}", description=description, color=discord.Color.blue())
        await ctx.send(embed=embed)
        
    @s.command(name="list", help="Lists all server-wide playlists.")
    async def s_list(self, ctx):
        playlists = db.get_server_playlists(ctx.guild.id)
        if not playlists:
            await ctx.send("This server has no playlists. Use `!s create <name>` to make one!")
            return
        
        description = "\n".join([f"• {name[0]}" for name in playlists])
        embed = discord.Embed(title=f"Server Playlists in {ctx.guild.name}", description=description, color=discord.Color.blue())
        await ctx.send(embed=embed)
        
    # --- UNIVERSAL PLAYBACK AND CONTROL COMMANDS ---
    @commands.command(name="play", help="Plays a song from a URL or an entire playlist. Usage: !play <playlist_name> or !play <url>")
    async def play(self, ctx, *, query: str):
        voice_client = await self.join_vc(ctx)
        if voice_client is None: return

        guild_id = ctx.guild.id
        songs_to_queue = []

        # Try to find a personal playlist first
        playlist = db.get_playlist(guild_id, query, owner_id=ctx.author.id)
        if not playlist:
            # If not found, try to find a server playlist
            playlist = db.get_playlist(guild_id, query, owner_id=None)

        if playlist:
            # It's a playlist
            playlist_id, playlist_name = playlist
            songs = db.get_songs_from_playlist(playlist_id)
            if not songs:
                await ctx.send(f"Playlist `{playlist_name}` is empty!")
                return
            songs_to_queue = [s[2] for s in songs] # s[2] is the url
            await ctx.send(f"▶️ Queuing up **{len(songs_to_queue)}** songs from playlist `{playlist_name}`.")
        elif "http" in query:
            # It's a URL
            song_info = get_song_info(query)
            if song_info:
                songs_to_queue.append(song_info['url'])
                await ctx.send(f"▶️ Queuing **{song_info['title']}**.")
            else:
                await ctx.send("Could not find a song at that URL.")
                return
        else:
            await ctx.send(f"Could not find a playlist or a valid URL for `{query}`.")
            return
            
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        
        self.queues[guild_id].extend(songs_to_queue)

        if not voice_client.is_playing() and not voice_client.is_paused():
            self.play_next(ctx)

    @commands.command(name="skip", help="Skips the current song.")
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped the current song.")
        else:
            await ctx.send("Not playing any music right now.")

    @commands.command(name="stop", aliases=["leave"], help="Stops the music, clears the queue, and leaves the channel.")
    async def stop(self, ctx):
        if ctx.guild.id in self.queues:
            self.queues[ctx.guild.id].clear()
        
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            if ctx.guild.id in self.voice_clients:
                del self.voice_clients[ctx.guild.id]
            await ctx.send("Stopped the music and left the channel.")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    db.setup_database()
    await bot.add_cog(Music(bot))
    print("Music cog loaded and database is ready.")

bot.run()