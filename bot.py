import os
import discord
from discord.ext import commands
from discord import app_commands, Interaction, ButtonStyle
from discord.ui import View, Button

# --- Bot Setup ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Ticket System Views ---
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🎟️ Create Ticket", custom_id="create_ticket", style=ButtonStyle.green))

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🔒 Close Ticket", custom_id="close_ticket", style=ButtonStyle.red))

# --- On Ready ---
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")
    print(f"🤖 Logged in as {bot.user}")

# -----------------------------
# ⚙️ TICKET SYSTEM COMMANDS
# -----------------------------

@bot.tree.command(name="ticketsetup", description="Set up the ticket creation panel (admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def ticketsetup(interaction: Interaction):
    embed = discord.Embed(
        title="🎫 Need Help?",
        description="Click below to open a private support ticket.\nOur staff will assist you shortly.",
        color=0x1abc9c
    )
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ Ticket panel created successfully!", ephemeral=True)

@bot.event
async def on_interaction(interaction: Interaction):
    custom_id = interaction.data.get("custom_id")

    # --- Create Ticket ---
    if custom_id == "create_ticket":
        guild = interaction.guild
        user = interaction.user

        support_role = discord.utils.get(guild.roles, name="Support")
        admin_role = discord.utils.get(guild.roles, name="Admin")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = discord.utils.get(guild.categories, name="Support Tickets")
        if not category:
            category = await guild.create_category("Support Tickets")

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            category=category
        )

        embed = discord.Embed(
            title="🔧 Support Ticket Created",
            description=f"{user.mention}, our staff will assist you shortly.\n\nClick 🔒 to close this ticket when finished.",
            color=0x5865F2
        )
        await ticket_channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message("✅ Ticket created successfully!", ephemeral=True)

    # --- Close Ticket ---
    elif custom_id == "close_ticket":
        transcript_channel = discord.utils.get(interaction.guild.text_channels, name="ticket-transcripts")

        if transcript_channel:
            messages = [f"{msg.author}: {msg.content}" async for msg in interaction.channel.history(limit=None, oldest_first=True)]
            transcript_text = "\n".join(messages) if messages else "(No messages in this ticket.)"

            transcript_file = f"{interaction.channel.name}_transcript.txt"
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(transcript_text)

            await transcript_channel.send(
                content=f"🗂 Transcript from {interaction.channel.name}",
                file=discord.File(transcript_file)
            )
            os.remove(transcript_file)

        await interaction.response.send_message("🔒 Closing this ticket in 3 seconds...", ephemeral=True)
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=3))
        await interaction.channel.delete()

# -----------------------------
# ⚡ GENERAL SLASH COMMANDS
# -----------------------------

@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"🏓 Pong! Latency: `{round(bot.latency * 1000)}ms`", ephemeral=True)

@bot.tree.command(name="rules", description="Display server rules")
async def rules(interaction: Interaction):
    embed = discord.Embed(
        title="📜 Server Rules",
        description="1️⃣ Be respectful\n2️⃣ No spam or NSFW content\n3️⃣ Follow Discord ToS\n4️⃣ Use channels properly\n5️⃣ Listen to staff",
        color=0x3498db
    )
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="verify", description="Verify yourself to access the server")
async def verify(interaction: Interaction):
    verified_role = discord.utils.get(interaction.guild.roles, name="Verified")
    if verified_role:
        await interaction.user.add_roles(verified_role)
        await interaction.response.send_message("✅ You are now verified!", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ No 'Verified' role found. Please contact an admin.", ephemeral=True)

@bot.tree.command(name="help", description="Show list of bot commands")
async def help(interaction: Interaction):
    embed = discord.Embed(
        title="🤖 ForgeBot Command List",
        description="Here’s what I can do:",
        color=0xffc300
    )
    embed.add_field(name="/ticketsetup", value="Set up the ticket panel (Admin only)", inline=False)
    embed.add_field(name="/verify", value="Assign yourself the Verified role", inline=False)
    embed.add_field(name="/rules", value="View the server rules", inline=False)
    embed.add_field(name="/ping", value="Check if the bot is online", inline=False)
    embed.add_field(name="/help", value="Show this command list", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="announce", description="Send an announcement (Admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def announce(interaction: Interaction, title: str, message: str):
    embed = discord.Embed(
        title=f"📢 {title}",
        description=message,
        color=0x2ecc71
    )
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✅ Announcement sent!", ephemeral=True)

# -----------------------------
# 🚀 Run Bot
# -----------------------------
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
