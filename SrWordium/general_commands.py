import discord

async def commands(interaction: discord.Interaction, bot):
    embed = discord.Embed(title="Comandos disponibles. Available commands.", color=discord.Color.blue())

    # Agregar cada comando y su descripcion al embed
    for command in bot.tree.get_commands():
        embed.add_field(name=f"/{command.name}", value=command.description or "", inline=False)

    await interaction.response.send_message(embed=embed)

async def ping(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Estado del Bot",
        description="¡Pong! El bot está en linea. ✅",
        color=discord.Color.green()  # Color verde
    )
    await interaction.response.send_message(embed=embed)
