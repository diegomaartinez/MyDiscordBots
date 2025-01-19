# guess_game.py
import discord
import random
import json
import asyncio

with open('./reactions.json', 'r') as file:
    reactions = json.load(file)

async def guess(bot, interaction: discord.Interaction, limit: int = 50):
    if (limit > 1000) or (limit < 10):
        await interaction.response.send_message('Introduce un numero entre 10 y 1000.')
        return

    number_to_guess = random.randint(1, limit)
    attempts = max(3, 2 + (limit // 100))

    # Responde inicialmente para cumplir con el requisito de la interacción
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
                await response.add_reaction(random.choice(reactions['correct']))
                embed.description += feedback
                await msg.edit(embed=embed)
                await response.add_reaction(msg.choice(reactions['correct']))
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
                await msg.add_reaction(random.choice(reactions['incorrect']))

        except ValueError:
            await interaction.channel.send('Por favor, ingresa un numero válido.')
        except asyncio.TimeoutError:
            feedback = "\n⏳ Se acabo el tiempo. ¡Inténtalo de nuevo!"
            embed.description += feedback
            await msg.edit(embed=embed)
            await msg.add_reaction(random.choice(reactions['incorrect']))
            return