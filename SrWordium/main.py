import discord
from discord.ext import commands

from hanged_game import hanged
from general_commands import commands as info

# Configura los intents del bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True

# Crea el bot
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.tree.command(name='ahorcado', description='Jugar al juego del Ahorcado.')
async def ahorcado_command(interaction: discord.Interaction):
    await hanged(bot, interaction, language='es')

@bot.tree.command(name='hanged', description='Play the Hangman game.')
async def hanged_command(interaction: discord.Interaction):
    await hanged(bot, interaction, language='en')

@bot.tree.command(name='info', description='Show available commands. Muestra los comandos disponibles.')
async def info_command(interaction: discord.Interaction):
    await info(interaction, bot)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Conectado como {bot.user}')

# Lee el token del archivo
with open('./bot_token.txt', 'r') as file:
    token = file.read().strip()

if __name__ == '__main__':
    bot.run(token)