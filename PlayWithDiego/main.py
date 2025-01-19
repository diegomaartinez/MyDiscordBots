import discord
from discord.ext import commands
import random
import asyncio
import sqlite3
import os
import json

from general_commands import diegocommands, diegoping
from hunt_game import hunt, stop_hunt, active_hunts, get_active_hunts
from guess_game import guess
from hanged_game import hanged
from db_commands import setup_database, update_stats, show_stats, show_top_players

# Configura los intents del bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True

# Crea el bot
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.tree.command(name='dhanged', description='Juguemos al ahorcado!')
async def hanged_command(interaction: discord.Interaction):
    await hanged(bot, interaction)

@bot.tree.command(name='dme', description='Muestra tus estadisticas de los juegos.')
async def diegome_command(interaction: discord.Interaction, game: str):
    await show_stats(interaction, game)

@bot.tree.command(name='dlb', description='Muestra el ranking de los mejores jugadores.')
async def diegolb_command(interaction: discord.Interaction, game: str):
    await show_top_players(interaction, game)

@bot.tree.command(name='dguess', description='Adivina el numero!')
async def guess_command(interaction: discord.Interaction, limit: int = 50):
    await guess(bot, interaction, limit)

@bot.tree.command(name='dhunt', description='Persigue a un usuario con un emoticono!')
async def hunt_command(interaction: discord.Interaction, emoji: str, user: discord.Member):
    await hunt(interaction, emoji, user)  # Llama a la función hunt desde hunt_commands

@bot.tree.command(name='dstophunt', description='Detiene la caza activa sobre un usuario')
async def stop_hunt_command(interaction: discord.Interaction, user: discord.Member):
    await stop_hunt(interaction, user)  # Llama a la función stop_hunt desde hunt_commands

@bot.tree.command(name='dactivehunts', description='Muestra las cazas activas en el servidor')
async def active_hunts_command(interaction: discord.Interaction):
    await active_hunts(interaction)  # Llama a la función active_hunts desde hunt_commands

@bot.tree.command(name='dcommands', description='Muestra todos los comandos disponibles y sus descripciones.')
async def diego_commands(interaction: discord.Interaction):
    await diegocommands(interaction, bot)

@bot.tree.command(name='dping', description='Comprueba si el bot está listo.')
async def diego_ping(interaction: discord.Interaction):
    await diegoping(interaction)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    hunts = get_active_hunts()

    server, author = message.guild.id, message.author.id
    if server in hunts.keys():
        for server_active_hunt_key in hunts[server].keys():
            if server_active_hunt_key[0] == author:
                await message.add_reaction(hunts[server][server_active_hunt_key])

    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Conectado como {bot.user}')

# Lee el token del archivo
with open('./bot_token.txt', 'r') as file:
    token = file.read().strip()

with open('./reactions.json', 'r') as file:
    reactions = json.load(file)

if __name__ == '__main__':
    bot.run(token)