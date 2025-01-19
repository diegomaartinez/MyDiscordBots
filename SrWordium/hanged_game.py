import discord
import random
import asyncio
import json

# with open('reactions.json', 'r') as file:
#     reactions = json.load(file)


def load_hanged_words(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]


def select_word(language):

    if language == 'es':
        word_list = load_hanged_words('./SrWordium/ahorcado_palabras.txt')
    elif language == 'en':
        word_list = load_hanged_words('./SrWordium/hanged_words.txt')

    word_to_guess = random.choice(word_list)

    return word_to_guess


def set_game_vocabulary(language):
    game_vocabulary = {
        "title": {"es": "Ahorcado", "en": "Hangman"},
        "tries": {"es": "Intentos restantes", "en": "Remaining tries"},
        "used": {"es": "Letras utilizadas", "en": "Used letters"},
        "win": {"es": "¡Felicidades! Adivinaste la palabra", "en": "Congratulations! You guessed the word"},
        "progress": {"es": "Tu progreso", "en": "Your progress"},
        "timeout": {"es": "¡Se acabó el tiempo! La palabra era", "en": "Time's up! The word was"},
        "lost": {"es": "¡Perdiste! La palabra era", "en": "You lost! The word was"}
    }
    return {key: value[language] for key, value in game_vocabulary.items()}

def set_game_intro(language, user):
    if language == 'es':
        return f"¡Comenzamos el juego del Ahorcado! {user.mention}\nEscribe una letra o una palabra hasta adivinar la palabra secreta. ¡Suerte!"
    if language == 'en':
        return f"Hangman game is starting! {user.mention}\nWrite letters until discovering the full word. Good luck!"


def get_display_word(word, guessed_letters):
    return ' '.join(letter.upper() if letter in guessed_letters else '_' for letter in word)


async def hanged(bot, interaction: discord.Interaction, language='es'):
    word_to_guess = select_word(language)
    texts = set_game_vocabulary(language)
    guessed_letters = []
    wrong_attempts = 0
    max_attempts = max([5, (len(word_to_guess)+1)//2])
    display_word = get_display_word(word_to_guess, guessed_letters)
    attempted_letters = []

    # Start game
    embed = discord.Embed(title=texts["title"], color=discord.Color.blue())
    embed.add_field(name=f"⏳ {texts['tries']}",
                    value=f"{'✅' * int(max_attempts - wrong_attempts)}{'❌' * int(wrong_attempts)}", inline=False)
    embed.add_field(name=f"✏️ {texts['used']}", value="-", inline=False)
    embed.description = f"{set_game_intro(language, interaction.user)}\n# `{display_word}`"

    # Send initial response and keep editing this message
    await interaction.response.send_message(embed=embed)
    game_message = await interaction.original_response()

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
                embed.description = f"{interaction.user.mention} {texts['win']}\n# `{word_to_guess.upper()}`"
                await game_message.edit(embed=embed)
                return

            if len(guess) == 1:
                if guess in guessed_letters or guess in attempted_letters:
                    pass
                else:
                    if guess in word_to_guess:
                        guessed_letters.append(guess)
                        display_word = get_display_word(word_to_guess, guessed_letters)
                        embed.description = f"{interaction.user.mention} {texts['progress']}:\n# `{display_word}`"
                    else:
                        attempted_letters.append(guess)
                        wrong_attempts += 1

                embed.set_field_at(0, name=f"⏳ {texts['tries']}",
                                   value=f"{'✅' * int(max_attempts - wrong_attempts)}{'❌' * int(wrong_attempts)}",
                                   inline=False)
                embed.set_field_at(1, name=f"✏️ {texts['used']}", value=', '.join(attempted_letters) or '-',
                                   inline=False)
                await game_message.edit(embed=embed)

        except asyncio.TimeoutError:
            embed.description = f"{interaction.user.mention} {texts['timeout']}:\n# `{word_to_guess.upper()}`"
            await game_message.edit(embed=embed)
            return

    if wrong_attempts >= max_attempts:
        embed.description = f"{interaction.user.mention} {texts['lost']}:\n# `{word_to_guess.upper()}`"
        await game_message.edit(embed=embed)