import os
import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import ButtonStyle, Interaction

# --- Bot Setup ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Ticket Views ---
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🎟️ Create Ticket", custom_id="create_ticket", style=ButtonStyle.green))

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🔒 Close Ticket", custom_id="close_ticket", style=ButtonStyle.red))

# --- On Bot Ready ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    channel = discord.utils.get(bot.get_all_channels(), name="🎫・tickets")  # Matches your channel name
    if channel:
        embed = discord.Embed(
            title="🎫 Need Help?",
            description="Click below to open a private support ticket. Our staff will assist you shortly.",
            color=0x1abc9c
        )
        await channel.send(embed=embed, view=TicketView())
    print("🚀 Ticket system ready!")

# --- Interaction Handling ---
@bot.event
async def on_interaction(interaction: Interaction):
    custom_id = interaction.data.get("custom_id")

    # --- Create Ticket Button ---
    if custom_id == "create_ticket":
        guild = interaction.guild

        # --- Adjust these role names to match your server exactly ---
        support_role = discord.utils.get(guild.roles, name="Ticket Support")
        admin_role = discord.utils.get(guild.roles, name="Admin")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Create or find Support Tickets category
        category = discord.utils.get(guild.categories, name="Support Tickets")
        if not category:
            category = await guild.create_category("Support Tickets")

        # --- Create the ticket channel ---
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites,
            category=category
        )

        # --- Send welcome message + close button ---
        embed = discord.Embed(
            title="🔧 Support Ticket Created",
            description=f"{interaction.user.mention}, our staff will assist you shortly.\n\nClick 🔒 to close this ticket when finished.",
            color=0x5865F2
        )
        await ticket_channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message("✅ Ticket created successfully!", ephemeral=True)

    # --- Close Ticket Button ---
    elif custom_id == "close_ticket":
        await interaction.response.send_message("🔒 Closing this ticket in 3 seconds...", ephemeral=True)
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=3))
        await interaction.channel.delete()

# --- Manual Setup Command (for admins) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def ticketsetup(ctx):
    """Manual setup command to resend the ticket embed"""
    embed = discord.Embed(
        title="🎫 Need Help?",
        description="Click below to open a private support ticket. Our staff will assist you shortly.",
        color=0x1abc9c
    )
    await ctx.send(embed=embed, view=TicketView())
    await ctx.send("✅ Ticket panel created successfully!")

# --- Run Bot ---
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
