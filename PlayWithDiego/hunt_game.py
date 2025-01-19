import discord
from discord.ext import commands

hunts = {}

def get_active_hunts():
    return hunts

async def hunt(interaction: discord.Interaction, emoji: str, user: discord.Member):
    prey, hunter, server = user, interaction.user, interaction.guild
    key = (prey.id, hunter.id)

    if server.id not in hunts.keys():
        hunts[server.id] = {}

    hunts[server.id][key] = emoji
    await interaction.response.send_message(
        f"La caza ha comenzado 😈. \nAhora estaré siguiendo a {prey.mention} con el emoji:\n# {emoji}"
    )

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
                await interaction.response.send_message(f"Dejaré de perseguir a {prey.mention}.")
                return

    # One hunter deletes the hunt over a user in a server
    else: 
        if key in hunts[server.id].keys():
            del hunts[server.id][key]
            await interaction.response.send_message(f"La caza sobre {user.mention} ha sido detenida en este servidor.")
        else:
            await interaction.response.send_message("No hay ninguna caza activa para este usuario en este servidor o no ha sido iniciada por ti.")

async def active_hunts(interaction: discord.Interaction):
    server_active_hunts = hunts[interaction.guild.id] if interaction.guild.id in hunts.keys() else None

    if server_active_hunts is None:
        await interaction.response.send_message("No hay cazas activas en este servidor.")
    else:
        hunts_list = [f"<@{key[0]}> : {emoji} por <@{key[1]}>" for key, emoji in server_active_hunts.items()]
        hunts_description = "\n".join(hunts_list)
        embed = discord.Embed(title=f"Cazas activas en {interaction.guild.name}", description=hunts_description)
        await interaction.response.send_message(embed=embed)
