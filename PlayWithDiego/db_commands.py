import discord
from discord.ext import commands
import random
import asyncio
import sqlite3
import os

# Nombre de la base de datos
DB_NAME = 'diego_games_stats.db'

available_games = ['hanged', 'guess']

# Configura la base de datos
def setup_database(game):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    # Crea la tabla si no existe
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {game}_stats (
        main_id TEXT PRIMARY KEY,
        server_id INTEGER,
        user_id INTEGER,
        user_name TEXT,
        victories INTEGER DEFAULT 0,
        games_played INTEGER DEFAULT 0
    )''')

    conexion.commit()
    conexion.close()

# Actualiza las estadisticas del usuario
def update_stats(server_id, user_id, user_name, won, game):
    main_id = f"{server_id}_{user_id}"

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    cursor.execute(f'''INSERT OR IGNORE INTO {game}_stats (main_id, server_id, user_id, user_name, victories, games_played)
                      VALUES (?, ?, ?, ?, 0, 0)''', (main_id, server_id, user_id, user_name))

    if won:
        cursor.execute(f'''UPDATE {game}_stats 
                          SET victories = victories + 1, games_played = games_played + 1 
                          WHERE main_id = ?''', (main_id,))
    else:
        cursor.execute(f'''UPDATE {game}_stats 
                          SET games_played = games_played + 1 
                          WHERE main_id = ?''', (main_id,))

    conexion.commit()
    conexion.close()

# Muestra las estadisticas del usuario
async def show_stats(interaction, game):
    main_id = f"{interaction.guild.id}_{interaction.user.id}"

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    cursor.execute(f'''SELECT victories, games_played FROM {game}_stats 
                      WHERE main_id = ?''', (main_id,))
    result = cursor.fetchone()
    conexion.close()

    if result:
        victories, games_played = result
        win_percentage = (victories / games_played) * 100 if games_played > 0 else 0

        embed = discord.Embed(title="Estadisticas del Ahorcado", color=discord.Color.blue())
        embed.set_author(name=interaction.user.display_name)
        embed.add_field(name="Victorias", value=victories, inline=True)
        embed.add_field(name="Partidas jugadas", value=games_played, inline=True)
        embed.add_field(name="Porcentaje de victorias", value=f"{win_percentage:.2f}%", inline=True)

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Aun no has jugado ninguna partida en este servidor.")

# Muestra el ranking de los mejores jugadores
async def show_top_players(interaction, game):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    if game not in available_games:
        await interaction.response.send_message(f"Juego no válido. Por favor elige alguno de estos:\n# {', '.join(available_games)}.")
        return

    # Obtener el top 10 de jugadores
    cursor.execute(f'''SELECT user_name, victories, games_played, ((victories*1.0)/games_played) AS win_ratio
                      FROM {game}_stats
                      WHERE server_id == ?
                      ORDER BY victories DESC, win_ratio DESC
                      LIMIT 10''', (interaction.guild.id,))
    top_10_results = cursor.fetchall()

    # Obtener la posicion del usuario en el ranking
    cursor.execute(f'''SELECT COUNT(*) + 1 AS rank 
                      FROM {game}_stats
                      WHERE server_id = ? AND victories > (SELECT victories FROM {game}_stats WHERE main_id = ?)''',
                   (interaction.guild.id, f"{interaction.guild.id}_{interaction.user.id}"))
    user_rank = cursor.fetchone()[0]

    # Cerrar la conexion a la base de datos
    conexion.close()

    if top_10_results:
        embed = discord.Embed(title="Top 10 Jugadores del Ahorcado\nen este servidor", color=discord.Color.gold())
        for index, (user_name, victories, games_played, win_ratio) in enumerate(top_10_results, start=1):
            win_percentage = win_ratio * 100 if games_played > 0 else 0
            embed.add_field(
                name=f"{index}. {user_name}",
                value=f"Victorias: {victories}, Partidas: {games_played}, Win Rate: {win_percentage:.2f}%",
                inline=False
            )

        # Añadir la posicion del usuario
        embed.add_field(
            name="Tu posicion en el ranking:",
            value=f"{user_rank}",
            inline=False
        )

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Aun no hay jugadores en el ranking de este servidor.")
