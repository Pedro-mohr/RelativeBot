# pip install discord.py / requests / openai==0.28 (Crear un entorno virtual, es recomendable) -- Use la version de pip 25.0

import discord
from discord.ext import commands
import requests
import Secrets  # Import the discord token and API key from the Secrets.py file
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

#Hacemos que el bot corra en local con el token del archivo secrets
bot.run(DISCORD_TOKEN)

