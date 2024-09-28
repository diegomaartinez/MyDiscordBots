import discord
from discord.ext import commands
import random
import asyncio
import sqlite3
import os

# Configura los intents del bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True

# Crea el bot
bot = commands.Bot(command_prefix='/', intents=intents)

# Nombre de la base de datos
DB_NAME = 'game_stats.db'


# Configura la base de datos
def setup_database():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    # Crea la tabla si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS hanged_stats (
        main_id TEXT PRIMARY KEY,
        server_id INTEGER,
        user_id INTEGER,
        user_name TEXT,
        victories INTEGER DEFAULT 0,
        games_played INTEGER DEFAULT 0
    )''')

    conexion.commit()
    conexion.close()


# Actualiza las estadísticas del usuario
def update_stats(server_id, user_id, user_name, won):
    main_id = f"{server_id}_{user_id}"

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    cursor.execute('''INSERT OR IGNORE INTO hanged_stats (main_id, server_id, user_id, user_name, victories, games_played)
                      VALUES (?, ?, ?, ?, 0, 0)''', (main_id, server_id, user_id, user_name))

    if won:
        cursor.execute('''UPDATE hanged_stats 
                          SET victories = victories + 1, games_played = games_played + 1 
                          WHERE main_id = ?''', (main_id,))
    else:
        cursor.execute('''UPDATE hanged_stats 
                          SET games_played = games_played + 1 
                          WHERE main_id = ?''', (main_id,))

    conexion.commit()
    conexion.close()


# Muestra las estadísticas del usuario
@bot.tree.command(name='diegome', description='Muestra tus estadísticas en el juego del ahorcado')
async def show_stats(interaction: discord.Interaction):
    main_id = f"{interaction.guild.id}_{interaction.user.id}"

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    cursor.execute('''SELECT victories, games_played FROM hanged_stats 
                      WHERE main_id = ?''', (main_id,))
    result = cursor.fetchone()
    conexion.close()

    if result:
        victories, games_played = result
        win_percentage = (victories / games_played) * 100 if games_played > 0 else 0
        # avg_attempts = games_played / victories if victories > 0 else 0

        embed = discord.Embed(title="Estadísticas del Ahorcado", color=discord.Color.blue())
        embed.set_author(name=interaction.user.display_name)
        embed.add_field(name="Victorias", value=victories, inline=True)
        embed.add_field(name="Partidas jugadas", value=games_played, inline=True)
        embed.add_field(name="Porcentaje de victorias", value=f"{win_percentage:.2f}%", inline=True)
        # embed.add_field(name="Promedio de intentos", value=f"{avg_attempts:.2f}", inline=True)

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Aún no has jugado ninguna partida en este servidor.")


@bot.tree.command(name='diegolb', description='Muestra el ranking de los mejores jugadores del ahorcado')
async def show_top_players(interaction: discord.Interaction):
    print('a')
    conexion = sqlite3.connect('game_stats.db')
    cursor = conexion.cursor()

    cursor.execute('''SELECT user_name, victories, games_played 
                      FROM hanged_stats 
                      ORDER BY victories DESC 
                      LIMIT 20''')
    results = cursor.fetchall()
    conexion.close()

    if results:
        embed = discord.Embed(title="Top 20 Jugadores del Ahorcado", color=discord.Color.gold())
        for index, (user_name, victories, games_played) in enumerate(results, start=1):
            win_percentage = (victories / games_played) * 100 if games_played > 0 else 0
            embed.add_field(
                name=f"{index}. {user_name}",
                value=f"Victorias: {victories}, Partidas: {games_played}, Win Rate: {win_percentage:.2f}%",
                inline=False
            )

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Aún no hay jugadores en el ranking de este servidor.")


async def get_reactions(msg, situation):
    reactions = {
        "correct": ['✅', '🎉', '🌟'],
        "incorrect": ['❌', '😞', '👎', '🤡'],
    }
    num_reactions = random.randint(1, 1)
    for _ in range(num_reactions):
        reaction = random.choice(reactions[situation])
        await msg.add_reaction(reaction)


# Configura la base de datos al inicio
database_ready = False
setup_database()


# JUEGO DEL AHORCADO
@bot.tree.command(name='diegohanged', description='Juguemos al ahorcado!')
async def hanged(interaction: discord.Interaction):
    global database_ready
    if not database_ready:
        setup_database()
        database_ready = True

    hanged_words = [
        "maravilla", "acantilado", "huracan", "tribuna", "felicidad", "aventura", "sorpresa",
        "espejo", "misterio", "desierto", "elefante", "murcielago", "relampago", "viento",
        "estrella", "arcoiris", "jardin", "universo", "sabiduria", "dinero", "amistad",
        "musica", "corazon", "inteligencia", "computadora", "programacion", "tecnologia",
        "desafio", "emociones", "creatividad", "inspiracion", "pasion", "viaje", "mariposa",
        "mariposas", "paz", "luz", "sombra", "naturaleza", "lago", "oceano", "cielo",
        "tiempo", "mundo", "espejismos", "magia", "sueños", "realidad", "palabra",
        "puente", "caminos", "destino", "anhelos", "esperanza", "recuerdos", "memorias",
        "experiencia", "cultura", "tradicion", "familia", "compasion", "solidaridad",
        "sabores", "olor", "texturas", "colores", "historias", "leyendas", "arte",
        "dibujos", "pinturas", "escultura", "fotografia", "danza", "teatro", "cine"
    ]

    word_to_guess = random.choice(hanged_words)
    guessed_letters = []
    wrong_attempts = 0
    max_attempts = 6
    display_word = get_display_word(word_to_guess, guessed_letters)
    attempted_letters = []

    # Start game
    await interaction.response.send_message(
        f"¡Comenzamos el juego del Ahorcado! {interaction.user.mention}\nEscribe una letra o una palabra hasta adivinar la palabra secreta. Suerte!"
    )

    # Creating the embed for the game
    embed = discord.Embed(title="Ahorcado", color=discord.Color.blue())
    embed.add_field(name="⏳ Intentos restantes",
                    value=f"{'✅' * int(max_attempts - wrong_attempts)}{'❌' * int(wrong_attempts)}", inline=False)
    embed.add_field(name="✏️ Letras utilizadas", value="Ninguna", inline=False)

    game_message = await interaction.followup.send(embed=embed)

    def check(message: discord.Message):
        return message.author == interaction.user and message.content.isalpha()

    while wrong_attempts < max_attempts and "_" in display_word:
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            guess = msg.content.lower()

            # Clean chat from game-related messages
            await msg.delete()

            # Right answer
            if guess == word_to_guess:
                embed.description = f"{interaction.user.mention} ¡Felicidades! Adivinaste la palabra\n# `{word_to_guess.upper()}`"
                await game_message.edit(embed=embed)
                await get_reactions(game_message, situation='correct')
                update_stats(interaction.guild.id, interaction.user.id, interaction.user.name, won=True)
                return

            if len(guess) == 1:
                if guess in guessed_letters or guess in attempted_letters:
                    # No hacer nada, ya fue intentado
                    pass
                else:
                    attempted_letters.append(guess)
                    if guess in word_to_guess:
                        guessed_letters.append(guess)
                        display_word = get_display_word(word_to_guess, guessed_letters)
                        embed.description = f"{interaction.user.mention} Tu progreso:\n# `{display_word}`"
                    else:
                        wrong_attempts += 1

                embed.set_field_at(0, name="⏳ Intentos restantes",
                                   value=f"{'✅' * int(max_attempts - wrong_attempts)}{'❌' * int(wrong_attempts)}",
                                   inline=False)
                embed.set_field_at(1, name="✏️ Letras utilizadas", value=', '.join(attempted_letters) or 'Ninguna',
                                   inline=False)
                await game_message.edit(embed=embed)

        except asyncio.TimeoutError:
            await interaction.channel.send('Se acabó el tiempo. ¡Inténtalo de nuevo!')
            await get_reactions(game_message, situation='incorrect')
            update_stats(interaction.guild.id, interaction.user.id, interaction.user.name, won=False)
            return

    if "_" not in display_word:
        embed.description = f"{interaction.user.mention} ¡Felicidades! Adivinaste la palabra\n# `{word_to_guess.upper()}`"
        await game_message.edit(embed=embed)
        await get_reactions(game_message, situation='correct')
        update_stats(interaction.guild.id, interaction.user.id, interaction.user.name, won=True)
    else:
        embed.description = f"{interaction.user.mention} ¡Lo siento! Has perdido. La palabra era\n# `{word_to_guess.upper()}`"
        await game_message.edit(embed=embed)
        await get_reactions(game_message, situation='incorrect')
        update_stats(interaction.guild.id, interaction.user.id, interaction.user.name, won=False)


# Método auxiliar para mostrar la palabra
def get_display_word(word, guessed_letters):
    return " ".join([letter.upper() if letter in guessed_letters else "_" for letter in word])


# COMPROBAR SI EL BOT ESTÁ ENCENDIDO
@bot.tree.command(name='diegoping', description='Comprueba si el bot está listo.')
async def ping(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Estado del Bot",
        description="¡Pong! El bot está en línea. ✅",
        color=discord.Color.green()  # Color verde
    )
    await interaction.response.send_message(embed=embed)


# Guess the number game
@bot.tree.command(name='diegoguess', description='Adivina el número!')
async def guess(interaction: discord.Interaction, limit: int = 50):
    if ((limit > 1000) or (limit < 10)):
        await interaction.response.send_message('Introduce un número entre 10 y 1000.')
        return

    number_to_guess = random.randint(1, limit)
    attempts = max(3, 2 + (limit // 100))

    # Responde inicialmente para cumplir con el requisito de la interacción
    await interaction.response.defer()

    # Crea el embed inicial
    embed = discord.Embed(
        title="Adivina el Número",
        description=f"🧠 He pensado un número entre 1 y {limit}. Tienes {attempts} intentos para adivinarlo.\n",
        color=discord.Color.red()  # Color rojo
    )

    # Envía el mensaje inicial usando followup y guarda el objeto del mensaje para ediciones
    msg = await interaction.followup.send(embed=embed)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    feedback = ""

    while attempts > 0:
        try:
            response = await bot.wait_for('message', check=check, timeout=30)
            guess_number = int(response.content)

            if guess_number == number_to_guess:
                feedback = f"\n\n🎉 ¡Correcto! El número era `{number_to_guess}`. ¡Felicidades!"
                await get_reactions(response, situation='correct')
                embed.description += feedback
                await msg.edit(embed=embed)
                await get_reactions(msg, situation='correct')
                return
            elif guess_number < number_to_guess:
                attempts -= 1
                feedback = f"\n➡️ El número es mayor que `{guess_number}`. Te quedan {attempts} intentos."
            else:
                attempts -= 1
                feedback = f"\n➡️ El número es menor que `{guess_number}`. Te quedan {attempts} intentos."

            await response.delete()  # Limpiar el mensaje del usuario

            # Editar el mensaje con la retroalimentación acumulada
            embed.description += feedback
            await msg.edit(embed=embed)

            if attempts == 0:
                feedback = f"\n\n❌ Se acabaron los intentos. El número era `{number_to_guess}`."
                embed.description += feedback
                await msg.edit(embed=embed)
                await get_reactions(msg, situation='incorrect')

        except ValueError:
            await interaction.channel.send('Por favor, ingresa un número válido.')
        except asyncio.TimeoutError:
            feedback = "\n⏳ Se acabó el tiempo. ¡Inténtalo de nuevo!"
            embed.description += feedback
            await msg.edit(embed=embed)
            await get_reactions(msg, situation='incorrect')
            return


hunts = {}


@bot.tree.command(name='diegohunt', description='Persigue a un usuario con un emoticono!')
async def hunt(interaction: discord.Interaction, emoji: str, user: discord.Member):
    prey, hunter, server = user, interaction.user, interaction.guild
    key = (prey.id, hunter.id)

    if server.id not in hunts.keys():
        hunts[server.id] = {}

    if hunter.id != prey.id:
        hunts[server.id][key] = emoji
        await interaction.response.send_message(
            f"La caza ha comenzado 😈. \nAhora estaré siguiendo a {prey.mention} con el emoji:\n# {emoji}")
    else:
        await interaction.response.send_message(f"¿Por qué querrías cazarte a tí mismo {user.mention}? 🤡")


@bot.tree.command(name='diegostophunt', description='Detiene la caza activa sobre un usuario')
async def stop_hunt(interaction: discord.Interaction, user: discord.Member):
    global hunts
    prey, hunter, server = user, interaction.user, interaction.guild
    key = (prey.id, hunter.id)

    # Clean all the active hunts in this server by server admins
    if prey.id == bot.user.id and hunter.guild_permissions.administrator:
        del hunts[server.id]
        await interaction.response.send_message("Todas las cazas han sido detenidas en este servidor.")
        return

    # One hunter deletes the hunt over a user in a server
    if key in hunts[server.id].keys():
        del hunts[server.id]
        await interaction.response.send_message(f"La caza sobre {user.mention} ha sido detenida en este servidor.")
    else:
        await interaction.response.send_message(
            "No hay ninguna caza activa para este usuario en este servidor o no ha sido iniciada por tí.")


@bot.tree.command(name='diegoactivehunts', description='Muestra las cazas activas en el servidor')
async def active_hunts(interaction: discord.Interaction):
    server_active_hunts = hunts[interaction.guild.id] if interaction.guild.id in hunts.keys() else None

    if server_active_hunts is None:
        await interaction.response.send_message("No hay cazas activas en este servidor.")
    else:
        hunts_list = [f"<@{key[0]}> : {emoji} por <@{key[1]}>" for key, emoji in server_active_hunts.items()]
        hunts_description = "\n".join(hunts_list)
        embed = discord.Embed(title=f"Cazas activas en {interaction.guild.name}", description=hunts_description)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='diegocommands', description='Muestra todos los comandos disponibles y sus descripciones.')
async def diegocommands(interaction: discord.Interaction):
    embed = discord.Embed(title="Comandos Disponibles", color=discord.Color.blue())

    # Agregar cada comando y su descripción al embed
    for command in bot.tree.get_commands():
        embed.add_field(name=f"/{command.name}", value=command.description or "Sin descripción", inline=False)

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

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
with open('./PlayWithDiego/bot_token.txt', 'r') as file:
    token = file.read().strip()

if __name__ == '__main__':
    bot.run(token)
