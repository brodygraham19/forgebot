import os
import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import ButtonStyle, Interaction

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

--- Ticket Button System ---,
class TicketView(View):
    def init(self):
        super().init(timeout=None)
        self.add_item(Button(label=" Create Ticket", custom_id="create_ticket", style=ButtonStyle.green))

@bot.event
async def on_ready():
    print(f" Logged in as {bot.user}")
    # Send ticket button in #tickets on startup
    channel = discord.utils.get(bot.get_all_channels(), name="tickets")
    if channel:
        embed = discord.Embed(
            title=" Need Help?",
            description="Click the button below to open a private support ticket. Our staff will assist you shortly.",
            color=0x1abc9c
        )
        await channel.send(embed=embed, view=TicketView())
    print(" Ticket system ready!")

@bot.event
async def on_interaction(interaction: Interaction):
    if interaction.data.get("custom_id") == "create_ticket":
        guild = interaction.guild

        # --- Adjust these role names to match your server exactly ---
        support_role = discord.utils.get(guild.roles, name="Support")
        admin_role = discord.utils.get(guild.roles, name="Admin")

        # --- Channel permissions ---
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # --- Create the ticket channel ---
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites,
            category=discord.utils.get(guild.categories, name="Support Tickets")
        )

        # --- Send welcome message in the new ticket ---
        embed = discord.Embed(
            title=" Support Ticket Created",
            description=f"{interaction.user.mention}, our staff will assist you shortly.",
            color=0x5865F2
        )
        await ticket_channel.send(embed=embed)

        await interaction.response.send_message(" Ticket created successfully!", ephemeral=True)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
