import discord
from discord.ext import commands
import random
import asyncio

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='/', intents=intents)

reactions = {
    "correct": ['✅', '🎉', '🌟'],
    "incorrect": ['❌', '😞', '👎', '🤡', '🇵🇪'],
}

async def get_reactions(msg, situation):
    num_reactions = random.randint(1, 1)
    for _ in range(num_reactions):
        reaction = random.choice(reactions[situation])
        await msg.add_reaction(reaction)

with open("./PlayWithDiego/hanged_words.txt", "r") as file:
    hanged_words = [line.strip() for line in file]

def get_display_word(word, guessed_letters):
    return " ".join([letter.upper() if letter in guessed_letters else "_" for letter in word])

# Hanged Man game
@bot.tree.command(name='diegohanged', description='Juguemos al ahorcado!')
async def hanged(interaction: discord.Interaction):
    word_to_guess = random.choice(hanged_words)
    guessed_letters = []
    wrong_attempts = 0
    max_attempts = 6
    display_word = get_display_word(word_to_guess, guessed_letters)
    attempted_letters = []

    # Start game
    await interaction.response.send_message(
        f"¡Comenzamos el juego del Ahorcado!\nEscribe una letra o una palabra hasta adivinar la palabra secreta. Suerte!"
    )

    # Using followup actions
    game_message = await interaction.followup.send(
        f"""# `{display_word}`\n⏳\tTienes {max_attempts} intentos.\n➡️\tLetras intentadas: Ninguna"""
    )

    def check(message: discord.Message):
        return message.author == interaction.user and message.content.isalpha()

    while wrong_attempts < max_attempts and "_" in display_word:
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            guess = msg.content.lower()

            # Clean chat from game related messages
            await msg.delete()

            # Right answer
            if guess == word_to_guess:
                await game_message.edit(content=f"¡Felicidades! Adivinaste la palabra\n# `{word_to_guess.upper()}`")
                await get_reactions(game_message, situation='correct')
                return

            # Correct guesses
            if len(guess) == 1:
                if guess in guessed_letters or guess in attempted_letters:
                    await game_message.edit(
                        content=f"Ya adivinaste la letra `{guess}` o la intentaste antes.\n# `{display_word}`\n⏳\tTienes {max_attempts - wrong_attempts} intentos.\n➡️\tLetras intentadas: {', '.join(attempted_letters) or 'Ninguna'}""")
                else:
                    attempted_letters.append(guess)
                    if guess in word_to_guess:
                        guessed_letters.append(guess)
                        display_word = get_display_word(word_to_guess, guessed_letters)
                        await game_message.edit(
                            content=f"""# `{display_word}`\n⏳\tTienes {max_attempts - wrong_attempts} intentos.\n➡️\tLetras intentadas: {', '.join(attempted_letters)}""")
                    else:
                        wrong_attempts += 1
                        await game_message.edit(
                            content=f"""# `{display_word}`\n⏳\tTienes {max_attempts - wrong_attempts} intentos.\n➡️\tLetras intentadas: {', '.join(attempted_letters)}""")

        except asyncio.TimeoutError:
            await interaction.channel.send('Se acabo el tiempo. ¡Intentalo de nuevo!')
            await get_reactions(game_message, situation='incorrect')
            return

    if "_" not in display_word:
        await game_message.edit(content=f"¡Felicidades! Adivinaste la palabra\n# `{word_to_guess.upper()}`")
        await get_reactions(game_message, situation='correct')
    else:
        await game_message.edit(content=f"¡Lo siento! Has perdido. La palabra era\n# `{word_to_guess.upper()}`")
        await get_reactions(game_message, situation='incorrect')


# Simple ping check
@bot.tree.command(name='diegoping', description='Comprueba si el bot está listo.')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message('¡Pong! El bot está en linea. ✅')


# Guess the number game
@bot.tree.command(name='diegoguess', description='Adivina el numero!.')
async def guess(interaction: discord.Interaction, limit: int = 50):
    if limit > 1000:
        await interaction.response.send_message('El numero máximo permitido es 1000.')
        return

    number_to_guess = random.randint(1, limit)
    attempts = max(3, limit // 100)

    await interaction.response.send_message(
        f"He pensado un numero entre 1 y {limit}. Tienes {attempts} intentos para adivinarlo.")

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    while attempts > 0:
        try:
            msg = await bot.wait_for('message', check=check, timeout=30)
            guess_number = int(msg.content)

            if guess_number == number_to_guess:
                await get_reactions(msg, situation='correct')
                await interaction.channel.send(f'¡Correcto! El numero era {number_to_guess}. ¡Felicidades!')
                return
            elif guess_number < number_to_guess:
                attempts -= 1
                await get_reactions(msg, situation='incorrect')
                await interaction.channel.send(f'Incorrecto. El numero es mayor. Te quedan {attempts} intentos.')
            else:
                attempts -= 1
                await get_reactions(msg, situation='incorrect')
                await interaction.channel.send(f'Incorrecto. El numero es menor. Te quedan {attempts} intentos.')

            if attempts == 0:
                await interaction.channel.send(
                    f'Se acabaron los intentos. El numero era {number_to_guess}. ¡Intenta de nuevo!')

        except ValueError:
            await interaction.channel.send('Por favor, ingresa un numero válido.')
        except asyncio.TimeoutError:
            await interaction.channel.send('Se acabo el tiempo. ¡Intentalo de nuevo!')
            return


# Rock, paper, scissors game
@bot.tree.command(name='diegoppt', description='Juega Piedra, Papel o Tijera contra el bot.')
async def piedra_papel_tijera(interaction: discord.Interaction):
    await interaction.response.send_message(
        "¡Escribe 'piedra', 'papel' o 'tijera', o responde con 🪨, 📄 o ✂️ para jugar!")

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=30)
        user_choice = msg.content.lower()

        # Check user input type
        if user_choice not in ['piedra', 'papel', 'tijera']:
            if str(msg.content) in ['🪨', '📄', '✂️']:
                user_choice = {
                    '🪨': 'piedra',
                    '📄': 'papel',
                    '✂️': 'tijera'
                }[str(msg.content)]
            else:
                await interaction.channel.send("Elige entre 'piedra', 'papel' o 'tijera'.")
                return

        options = ['piedra', 'papel', 'tijera']
        bot_choice = random.choice(options)

        # Game logic
        if user_choice == bot_choice:
            result = "¡Es un empate!"
        elif (user_choice == 'piedra' and bot_choice == 'tijera') or \
                (user_choice == 'papel' and bot_choice == 'piedra') or \
                (user_choice == 'tijera' and bot_choice == 'papel'):
            result = "¡Ganaste! 🎉"
        else:
            result = "¡Perdiste! 😢"

        await interaction.channel.send(f"Yo elegi: {bot_choice}. {result}")

    except asyncio.TimeoutError:
        await interaction.channel.send('Se acabo el tiempo. ¡Intentalo de nuevo!')


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Bot conectado como {bot.user}!')

# Read TOKEN from file
with open('./PlayWithDiego/bot_token.txt', 'r') as file:
    token = file.read().strip()

# Executes bot
bot.run(token)
