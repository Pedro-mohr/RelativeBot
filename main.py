# pip install -Requirements.txt

import discord
from discord.ext import commands
import requests
from discord import app_commands
import os
import webserver
from dotenv import load_dotenv
from discord import FFmpegPCMAudio
from collections import deque
import yt_dlp as youtube_dl
import asyncio
import traceback

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

with open('cookies.txt', 'w', newline='\n') as f:
    f.write(os.environ.get('COOKIES_CONTENT', ''))
    os.chmod('cookies.txt', 0o600)
    
# Import the OpenAI API
import openai
openai.api_key = OPENAI_API_KEY

# Configuración de intents
intents = discord.Intents.default()
intents.message_content = True

# Creando la instancia del bot (única instancia)
bot = commands.Bot(command_prefix='!', intents=intents)

# ara que nos diga cuando esta activo y cuantos comandos tiene logeado (Si algun comando no inicia bien el bot no va a iniciar).
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# Comando de prueba: /hello
@bot.tree.command(name="hello", description="Say hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

# Comando /info que muestra un Embed con información del bot (Esto es super modificable y personalizable)
@bot.tree.command(name="info", description="Get information on how to use the bot")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Bot Information",
        description="Welcome to the translation bot! Here's how to use it:",
        color=0x00ff00
    )
    embed.add_field(name="/tran [language] [text]", value="Translates the given text to the specified language.", inline=False)
    embed.add_field(name="/info", value="Shows this information message.", inline=False)
    embed.set_author(name="Relative", icon_url="")
    embed.set_thumbnail(url="")
    embed.set_footer(text="Powered by Relative")
    #Todos estos parametros son para modificar distintos aspectos del Embed, pero a mi me da paja.
    
    await interaction.response.send_message(embed=embed)

# Comando /shutdown para apagar el bot (solo administradores)
@bot.tree.command(name="shutdown", description="Shut down the bot (admin only)")
@app_commands.default_permissions(administrator=True)  # Solo administradores pueden usar este comando
async def shutdown(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Shutting down the bot...")
        await bot.close()  # Cierra la conexión del bot
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

# Lista de idiomas (Pueden ser mas, pero me dio paja)
LANGUAGES = [
    "English",
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Chinese",
    "Japanese",
    "Russian",
    "Arabic"
]

# Función para traducir texto usando la API de OpenAI. Le decimos al modelo que actue como traductor.
async def translate_text(text, target_language):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", #Escogemos el modelo de lenguaje
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates text."},
                {"role": "user", "content": f"Translate the following text to {target_language}: {text}"}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

# Comando /tran que traduce el texto al idioma seleccionado
@bot.tree.command(name="tran", description="Translate text to a specified language")
@app_commands.describe(
    language="The language to translate to",
    text="The text to translate"
)
@app_commands.choices(language=[app_commands.Choice(name=lang, value=lang) for lang in LANGUAGES])
async def tran(interaction: discord.Interaction, language: app_commands.Choice[str], text: str):
    target_language = language.value
    translated_text = await translate_text(text, target_language)
    await interaction.response.send_message(f"{translated_text}")

 

# ------------------------- Música -------------------------
class MusicQueue:
    def __init__(self):
        self.queue = deque()
        self.now_playing = None

    def add_to_queue(self, song):
        self.queue.append(song)
    
    def next_song(self):
        if self.queue:
            self.now_playing = self.queue.popleft()
            return self.now_playing
        return None

music_queues = {}

def get_queue(guild_id):
    if guild_id not in music_queues:
        music_queues[guild_id] = MusicQueue()
    return music_queues[guild_id]

# ytdl
# En ytdl_format_options, REEMPLAZAR CON:
ytdl_format_options = {
    'format': 'bestaudio/best',
    'cookiefile': 'cookies.txt',
    'extractor_args': {
        'youtube': {
            'player_client': ['web'],
            'skip': ['dash', 'hls'],
            'data_sync_id': secrets.token_hex(8)  # ID único por ejecución
        }
    },
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-Origin': 'https://www.youtube.com',
        'Referer': 'https://www.youtube.com/'
    },
    'throttled_rate': '512K',  # Limitar ancho de banda
    'retries': 15,
    'fragment_retries': 15,
    'socket_timeout': 25,
    'force-ipv4': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

ffmpeg_options = {'options': '-vn'}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        
        if "entries" in data:
            data = data["entries"][0]
        
        # Configuración de FFmpeg con reconexión
        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -loglevel error"
        }
        
        return cls(
            discord.FFmpegPCMAudio(data["url"], **ffmpeg_options),
            data=data
        )

# Comandos de música (Slash Commands)
@bot.tree.command(name="play")
@app_commands.describe(busqueda="URL o nombre de la canción")
async def play(interaction: discord.Interaction, busqueda: str):
    await interaction.response.defer()
    
    try:
        # Delay anti-bot (1.5-4 segundos)
        await asyncio.sleep(random.uniform(1.5, 4))
        
        # Limita la descarga a 10 segundos
        song = await asyncio.wait_for(YTDLSource.from_url(busqueda), timeout=10)
        queue = get_queue(interaction.guild.id)
        queue.add_to_queue(song)
        
        voice_client = interaction.guild.voice_client
        if not voice_client.is_playing():
            await play_next(interaction.guild)
            await interaction.followup.send(f"🎶 **Now playing:** {song.title}")
        else:
            await interaction.followup.send(f"🎵 **Adding to queue:** {song.title}")
            
    except asyncio.TimeoutError:
        await interaction.followup.send("❌ **Timeout.** Try again with other link.")
    except Exception as e:
        await interaction.followup.send("❌ **Serious error:** " + str(e))
        print(f"[ERROR] {traceback.format_exc()}")  # Log detallado

async def play_next(guild):
    queue = get_queue(guild.id)
    voice_client = guild.voice_client
    
    if voice_client and not voice_client.is_playing():
        next_song = queue.next_song()
        if next_song:
            voice_client.play(next_song, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild), bot.loop))
            await guild.system_channel.send(f"🎶 **Now is playing:** {next_song.title}")
        else:
            await voice_client.disconnect()

@bot.tree.command(name="stop", description="Detiene la música y desconecta al bot")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client:
        music_queues.pop(interaction.guild.id, None)
        await voice_client.disconnect()
        await interaction.response.send_message("⏹ **Música detenida.**")
    else:
        await interaction.response.send_message(" Relative has to be in a voice channel.", ephemeral=True)

@bot.tree.command(name="skip", description="Salta la canción actual")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("⏭ **Canción saltada.**")
    else:
        await interaction.response.send_message("❌ No music.", ephemeral=True)



webserver.keep_alive()
bot.run(DISCORD_TOKEN)
