import discord

async def diegocommands(interaction: discord.Interaction, bot):
    embed = discord.Embed(title="Comandos Disponibles", color=discord.Color.blue())

    # Agregar cada comando y su descripcion al embed
    for command in bot.tree.get_commands():
        embed.add_field(name=f"/{command.name}", value=command.description or "", inline=False)

    await interaction.response.send_message(embed=embed)

async def diegoping(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Estado del Bot",
        description="¡Pong! El bot está en linea. ✅",
        color=discord.Color.green()  # Color verde
    )
    await interaction.response.send_message(embed=embed)
