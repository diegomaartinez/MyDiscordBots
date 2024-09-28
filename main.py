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


# Actualiza las estadisticas del usuario
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


# Muestra las estadisticas del usuario
@bot.tree.command(name='diegome', description='Muestra tus estadisticas en el juego del ahorcado')
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

        embed = discord.Embed(title="Estadisticas del Ahorcado", color=discord.Color.blue())
        embed.set_author(name=interaction.user.display_name)
        embed.add_field(name="Victorias", value=victories, inline=True)
        embed.add_field(name="Partidas jugadas", value=games_played, inline=True)
        embed.add_field(name="Porcentaje de victorias", value=f"{win_percentage:.2f}%", inline=True)
        # embed.add_field(name="Promedio de intentos", value=f"{avg_attempts:.2f}", inline=True)

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Aun no has jugado ninguna partida en este servidor.")


@bot.tree.command(name='diegolb', description='Muestra el ranking de los mejores jugadores del ahorcado')
async def show_top_players(interaction: discord.Interaction):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    # Obtener el top 10 de jugadores
    cursor.execute('''SELECT user_name, victories, games_played, ((victories*1.0)/games_played) AS win_ratio
                      FROM hanged_stats
                      WHERE server_id == ?
                      ORDER BY victories DESC, win_ratio DESC
                      LIMIT 10''', (interaction.guild.id,))
    top_10_results = cursor.fetchall()

    # Obtener la posicion del usuario en el ranking
    cursor.execute('''SELECT COUNT(*) + 1 AS rank 
                      FROM hanged_stats
                      WHERE server_id = ? AND victories > (SELECT victories FROM hanged_stats WHERE main_id = ?)''',
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
      "acantilado", "amistad", "anhelos", "arcoiris", "arte", "aventura", "almohadilla", "altramuz", "angelical", "arqueologo", 
      "abierto", "abogado", "abundancia", "abuelita", "acacia", "aceituna", "acero", "admiracion", "adversidad", "aficion", 
      "agujero", "aguila", "aguijon", "aguacate", "albahaca", "alegria", "alfa", "algodon", "aliado", "almendra", 
      "alquimia", "altura", "anemona", "animo", "aniversario", "antorcha", "aroma", "articulo", "asombro", "asistente",
    
      "barca", "bronquios", "brocoli", "bifurcacion", "burrito", "bruxismo", "boliche", "barracuda", "betun", "bacteriologia",
      "bailar", "bajo", "baldosa", "banda", "barco", "bazar", "beber", "biografia", "blanco", "brindis",
      
      "caminos", "cine", "colores", "compasion", "computadora", "creatividad", "cultura", "ciudadela", "concurrido", "ciencia",
      "caballo", "cabeza", "cabina", "cactus", "calor", "camara", "caminata", "camiseta", "campana", "canasta", 
      "cancion", "cangrejo", "canto", "cariño", "carne", "carta", "casita", "castillo", "cereza", "cerveza",
      "chicle", "chino", "cielo", "ciencia", "circulo", "cobijo", "colorido", "cometa", "compra", "computo",
    
      "danza", "desafio", "destino", "desierto", "dibujos", "dinero", "divino", "dentadura", "dolores", "doctorado",
      "despertar", "destello", "diamente", "dinosaurio", "divertido", "doblaje", "dinastia", "diligencia", "destrozo",
      
      "elefante", "emociones", "esperanza", "espejismos", "espejo", "estrella", "escultura", "experiencia", "españa", "exito",
      "exaltado", "entusiasmo", "elaboracion",
      
      "familia", "felicidad", "fotografia", "fuego", "fuerza", "fruta", "futuro", "festival", "flor", "forma", 
      "ferreteria", "feo", "feroz", "favor", "folio", "fresa", "fiesta", "fracaso", "fuente", "florero",
      
      "gato", "guitarra", "globo", "gente", "gigante", "goloso", "gloria", "guapo", "granja", "guerrero",      
      "galleta", "gimnasio", "goma", "gusto", "guirnalda", "galaxia", "guitarra", "grito", "gorra", "golpe",
    
      "historias", "huracan", "hermosa", "horizonte", "hogar", "helado", "heroe", "hongo", "hoja", "hambre", 
      "humo", "historia", "himno", "huella", "habilidad", "hospital", "hoja", "heroico", "horario", "helio", 
      
      "inspiracion", "inteligencia", "isla", "ilusion", "infinito", "idea", "imagen", "iman", "invierno", "iglesia", 
      "interes", "ingrediente", "intriga", "impacto", "instante", "ignorancia", "ilusion", "indice", "imprenta", "insecto",
      
      "jardin", "juego", "joya", "jirafa", "jabon", "jamon", "jaula", "jota", "joven", "justicia", 
      "jengibre", "jornada", "juguete", "jurado", "jubilo", "jarabe", "jabali", "juramento", "jalapeño", "jolgorio",
      
      "koala", "kilometro", "kilogramo", "kilobyte", "kiwi",
      
      "lago", "leyendas", "luz", "luna", "libro", "lapiz", "leon", "lente", "lampara", "lengua", 
      "leche", "lavabo", "lago", "lima", "lucha", "lapiz", "laboratorio", "lago", "lagrima", "largo", 
      "linea", "local", "libertad", "libreria", "limon", "lider", "loto", "limpieza", "loja", "lienzo", "loro",

      "magia", "maravilla", "mariposa", "maternidad", "memorias", "misterio", "murcielago", "musica", "mundo",
      "mar", "madera", "mesa", "mundo", "mujer", "magia", "musica", "mama", "misterio", "memoria", 
      "montaña", "murcielago", "mirada", "mariposa", "motivo", "moneda", "mosaico", "melodia", "movil", "mito", 
      "manzana", "maestro", "medicina", "mantener", "mascota", "muralla", "miel", "movil", "marcha", "modelo", "movimiento",
      
      "naturaleza", "nube", "naranja", "nave", "nido", "negro", "nuevo", "nieve", "nota", "nacido", 
      "navegar", "narrar", "necesidad", "nicho", "novela", "nombre", "nube", "naranja", "nacional", "nave",
      
      "oceano", "olor", "ola", "oro", "orquidea", "olla", "ocaso", "octavo", "ojo", "otono", 
      "origen", "oracion", "organizacion", "opinion", "oasis", "oscuro", "obvio", "oferta", "omito", "orquesta",
      
      "pasion", "paz", "palabra", "pinturas", "programacion", "puente", "piedra", "pluma", "planeta",
      "pelota", "piano", "pajaros", "prueba", "plato", "perro", "pescado", "puerta", "playa", "pueblo", "polvo",
      
      "queso", "quimica", "quijote", "quimera", "quebrada", "quinto", "quijada", "quijote", "quimera", "quimica",
      "quiosco", "quinto", "quedarse", "quebradizo", "quimicamente",
      
      "realidad", "recuerdos", "relampago", "rayo", "risa", "reunion", "reptil", "rojo", "reflejo", "reina",
      "resiliencia", "regalo", "respeto", "ruido", "romance", "rodar", "rueda", "rincon", "rayo", "remolino",
      
      "sabiduria", "sabores", "sombra", "solidaridad", "sorpresa", "sueños", "silencio", "sonido", "sueño", 
      "salud", "sabana", "sal", "secreto", "sabana", "salto", "sopa", "silla", "sociedad", "sello", "sabor",
      
      "teatro", "tecnologia", "texturas", "tiempo", "tribuna", "tradicion", "tierra", "talento", "tesoro", 
      "tarde", "tambor", "taza", "talento", "tapiz", "tierra", "tigre", "tiza", "titulo", "tipo", 
      "tabla", "tarta", "telarana", "telefono", "tren", "tranquilo", "traje", "tornillo", "test", "tornado", 
      "trampa", "trueno", "tenedor", "tarea", "trato", "tristeza", "tunel", "tradicion", "trigo", "teclado", "tablero",
      
      "universo", "unicornio", "utopia", "uvas", "usuario", "usurpar", "usualmente", "uncion", "ubicacion", "ultrasonico",
      
      "viaje", "viento", "vacaciones", "valor", "vulcano", "vacuna", "victoria", "velocidad", "verificacion", "variabilidad",
      
      "xilofono", "xenofobia", "xerografia", "xenon", "xilema",
      "yate", "yogur", "yunque", "yema", "yoga", "yodada", "yelmo", "yerma", "yuxtaposicion", "yacimiento",
      "zorro", "zapato", "zafiro", "zumo", "zona", "zen", "zapatear", "zebra"
    ]

    word_to_guess = random.choice(hanged_words)
    guessed_letters = []
    wrong_attempts = 0
    max_attempts = max([5, (len(word_to_guess)+1)//2])
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
            await interaction.channel.send('Se acabo el tiempo. ¡Intentalo de nuevo!')
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


# Metodo auxiliar para mostrar la palabra
def get_display_word(word, guessed_letters):
    return " ".join([letter.upper() if letter in guessed_letters else "_" for letter in word])


# COMPROBAR SI EL BOT ESTa ENCENDIDO
@bot.tree.command(name='diegoping', description='Comprueba si el bot esta listo.')
async def ping(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Estado del Bot",
        description="¡Pong! El bot esta en linea. ✅",
        color=discord.Color.green()  # Color verde
    )
    await interaction.response.send_message(embed=embed)


# Guess the number game
@bot.tree.command(name='diegoguess', description='Adivina el numero!')
async def guess(interaction: discord.Interaction, limit: int = 50):
    if ((limit > 1000) or (limit < 10)):
        await interaction.response.send_message('Introduce un numero entre 10 y 1000.')
        return

    number_to_guess = random.randint(1, limit)
    attempts = max(3, 2 + (limit // 100))

    # Responde inicialmente para cumplir con el requisito de la interaccion
    await interaction.response.defer()

    # Crea el embed inicial
    embed = discord.Embed(
        title="Adivina el Numero",
        description=f"🧠 He pensado un numero entre 1 y {limit}. Tienes {attempts} intentos para adivinarlo.\n",
        color=discord.Color.red()  # Color rojo
    )

    # Envia el mensaje inicial usando followup y guarda el objeto del mensaje para ediciones
    msg = await interaction.followup.send(embed=embed)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    feedback = ""

    while attempts > 0:
        try:
            response = await bot.wait_for('message', check=check, timeout=30)
            guess_number = int(response.content)

            if guess_number == number_to_guess:
                feedback = f"\n\n🎉 ¡Correcto! El numero era `{number_to_guess}`. ¡Felicidades!"
                await get_reactions(response, situation='correct')
                embed.description += feedback
                await msg.edit(embed=embed)
                await get_reactions(msg, situation='correct')
                return
            elif guess_number < number_to_guess:
                attempts -= 1
                feedback = f"\n➡️ El numero es mayor que `{guess_number}`. Te quedan {attempts} intentos."
            else:
                attempts -= 1
                feedback = f"\n➡️ El numero es menor que `{guess_number}`. Te quedan {attempts} intentos."

            await response.delete()  # Limpiar el mensaje del usuario

            # Editar el mensaje con la retroalimentacion acumulada
            embed.description += feedback
            await msg.edit(embed=embed)

            if attempts == 0:
                feedback = f"\n\n❌ Se acabaron los intentos. El numero era `{number_to_guess}`."
                embed.description += feedback
                await msg.edit(embed=embed)
                await get_reactions(msg, situation='incorrect')

        except ValueError:
            await interaction.channel.send('Por favor, ingresa un numero valido.')
        except asyncio.TimeoutError:
            feedback = "\n⏳ Se acabo el tiempo. ¡Intentalo de nuevo!"
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

    hunts[server.id][key] = emoji
    await interaction.response.send_message(
        f"La caza ha comenzado 😈. \nAhora estare siguiendo a {prey.mention} con el emoji:\n# {emoji}"
    )

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

    if user.guild_permissions.administrator:
        for k in hunts[server.id].keys():
            if k[0] == prey.id:
              del hunts[server.id][k]
              await interaction.response.send_message(f"Dejare de perseguir a {prey.mention}.")
              return
              
    # One hunter deletes the hunt over a user in a server
    else: 
        if key in hunts[server.id].keys():
            del hunts[server.id][key]
            await interaction.response.send_message(f"La caza sobre {user.mention} ha sido detenida en este servidor.")
        else:
            await interaction.response.send_message("No hay ninguna caza activa para este usuario en este servidor o no ha sido iniciada por ti.")


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

    # Agregar cada comando y su descripcion al embed
    for command in bot.tree.get_commands():
        embed.add_field(name=f"/{command.name}", value=command.description or "Sin descripcion", inline=False)

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
