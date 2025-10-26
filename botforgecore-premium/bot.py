
# bot.py — BotForgeCore Premium
import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = False

BOT = commands.Bot(command_prefix="!", intents=INTENTS)
TREE = BOT.tree

BRAND_COLOR = discord.Color.dark_blue()
FOOTER_TEXT = "BotForge – Premium Build Edition"
PORTAL_CHANNEL_NAME = "portal"
TICKETS_CATEGORY_NAME = "Tickets"
LOG_CHANNEL_NAME = "botforge-logs"
VERIFIED_ROLE = "Verified"
SUPPORT_ROLE = "Support"

# -------------------------------
# Utilities
# -------------------------------
async def ensure_setup(guild: discord.Guild):
    # Roles
    verified = discord.utils.get(guild.roles, name=VERIFIED_ROLE)
    support = discord.utils.get(guild.roles, name=SUPPORT_ROLE)
    if not verified:
        verified = await guild.create_role(name=VERIFIED_ROLE, reason="Auto-setup")
    if not support:
        support = await guild.create_role(name=SUPPORT_ROLE, reason="Auto-setup")

    # Tickets category
    tickets_cat = discord.utils.get(guild.categories, name=TICKETS_CATEGORY_NAME)
    if not tickets_cat:
        tickets_cat = await guild.create_category(TICKETS_CATEGORY_NAME, reason="Auto-setup")

    # Portal channel
    portal = discord.utils.get(guild.text_channels, name=PORTAL_CHANNEL_NAME)
    if not portal:
        portal = await guild.create_text_channel(PORTAL_CHANNEL_NAME, topic="Verification Portal", reason="Auto-setup")

    # Logs channel
    logs = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if not logs:
        logs = await guild.create_text_channel(LOG_CHANNEL_NAME, topic="BotForge logs", reason="Auto-setup")

    return verified, support, tickets_cat, portal, logs

async def send_verify_panel(portal: discord.TextChannel, guild: discord.Guild):
    class VerifyView(discord.ui.View):
        def __init__(self, role: discord.Role, *, timeout: float | None = 1800):
            super().__init__(timeout=timeout)
            self.role = role

        @discord.ui.button(label="Verify", style=discord.ButtonStyle.primary, emoji="✅")
        async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
            member = interaction.user if isinstance(interaction.user, discord.Member) else guild.get_member(interaction.user.id)
            if not member:
                await interaction.response.send_message("Could not verify (member not found).", ephemeral=True)
                return
            if self.role in member.roles:
                await interaction.response.send_message("You're already verified ✅", ephemeral=True)
                return
            try:
                await member.add_roles(self.role, reason="Verified via button")
                await interaction.response.send_message("You're verified! Welcome to the forge ⚒️", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("I don't have permission to add roles.", ephemeral=True)

    embed = discord.Embed(
        title="⚒️ Welcome to BotForge",
        description="Press **Verify** below to unlock the forge.",
        color=BRAND_COLOR
    )
    embed.set_footer(text=FOOTER_TEXT, icon_url="https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/skull.svg")
    await portal.send(embed=embed, view=VerifyView(discord.utils.get(guild.roles, name=VERIFIED_ROLE)))

async def log(guild: discord.Guild, msg: str):
    ch = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if ch:
        embed = discord.Embed(description=msg, color=BRAND_COLOR)
        embed.set_footer(text=FOOTER_TEXT)
        await ch.send(embed=embed)

# -------------------------------
# Events
# -------------------------------
@BOT.event
async def on_ready():
    print(f"✅ Logged in as {BOT.user} (ID: {BOT.user.id})")
    # Sync slash commands
    try:
        await TREE.sync()
        print("🌐 Slash commands synced.")
    except Exception as e:
        print("Slash sync error:", e)

    # Setup per guild
    for guild in BOT.guilds:
        verified, support, tickets_cat, portal, logs = await ensure_setup(guild)
        # Send a portal panel if none exists in history
        try:
            history = [m async for m in portal.history(limit=20)]
            if not any(m.author == BOT.user and m.components for m in history):
                await send_verify_panel(portal, guild)
        except Exception:
            pass
        await log(guild, "🚀 BotForgeCore Premium is online.")

@BOT.event
async def on_member_join(member: discord.Member):
    # Welcome message (no ping)
    portal = discord.utils.get(member.guild.text_channels, name=PORTAL_CHANNEL_NAME)
    if portal:
        embed = discord.Embed(
            title="Welcome to BotForge!",
            description=f"{member.mention}, head to the panel below and verify to unlock the server.",
            color=BRAND_COLOR
        )
        embed.set_footer(text=FOOTER_TEXT)
        await portal.send(embed=embed)
    await log(member.guild, f"👤 Member joined: **{member}**")

@BOT.event
async def on_member_remove(member: discord.Member):
    await log(member.guild, f"🚪 Member left: **{member}**")

# -------------------------------
# Ticket Views
# -------------------------------
class TicketView(discord.ui.View):
    def __init__(self, opener: discord.Member, support_role: discord.Role, *, timeout: float | None = 3600):
        super().__init__(timeout=timeout)
        self.opener = opener
        self.support_role = support_role

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.secondary, emoji="🛠️")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.support_role not in interaction.user.roles and not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Only support can claim tickets.", ephemeral=True)
            return
        try:
            await interaction.channel.edit(name=f"ticket-{interaction.user.name}")
            await interaction.response.send_message(f"{interaction.user.mention} claimed this ticket.", suppress_embeds=True)
            await log(interaction.guild, f"🧰 Ticket claimed by **{interaction.user}** in {interaction.channel.mention}")
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.support_role not in interaction.user.roles and
            not interaction.user.guild_permissions.manage_channels and
            interaction.user != self.opener):
            await interaction.response.send_message("You don't have permission to close this ticket.", ephemeral=True)
            return
        await interaction.response.send_message("Closing ticket in 3 seconds…")
        await asyncio.sleep(3)
        await log(interaction.guild, f"📪 Ticket closed by **{interaction.user}** in #{interaction.channel.name}")
        await interaction.channel.delete()

# -------------------------------
# Slash Commands
# -------------------------------
@TREE.command(name="ticket", description="Open a private support ticket")
@app_commands.checks.cooldown(1, 30.0)  # one use per 30s per user
async def ticket(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild
    verified, support, tickets_cat, portal, logs = await ensure_setup(guild)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False, view_channel=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True, attach_files=True),
        support: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True, manage_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True, manage_channels=True),
    }
    ch = await guild.create_text_channel(
        name=f"ticket-{interaction.user.name}",
        category=tickets_cat,
        overwrites=overwrites,
        topic=f"Ticket opened by {interaction.user}",
        reason="Support ticket"
    )
    embed = discord.Embed(
        title="🎟️ Support Ticket",
        description="A staff member will be with you shortly.\nUse the buttons to **Claim** or **Close** the ticket.",
        color=BRAND_COLOR
    )
    embed.set_footer(text=FOOTER_TEXT)
    await ch.send(content=f"{interaction.user.mention} {support.mention}", embed=embed, view=TicketView(interaction.user, support))
    await interaction.followup.send(f"Opened {ch.mention}", ephemeral=True)
    await log(guild, f"🎫 Ticket opened by **{interaction.user}** → {ch.mention}")

@TREE.command(name="close", description="Close the current ticket")
@app_commands.checks.cooldown(1, 15.0)
async def close(interaction: discord.Interaction):
    if not isinstance(interaction.channel, discord.TextChannel) or interaction.channel.category is None or interaction.channel.category.name != TICKETS_CATEGORY_NAME:
        await interaction.response.send_message("This isn't a ticket channel.", ephemeral=True)
        return
    await interaction.response.send_message("Closing ticket…")
    await log(interaction.guild, f"📪 Ticket closed by **{interaction.user}** in #{interaction.channel.name}")
    await interaction.channel.delete()

@TREE.command(name="announce", description="Send an announcement embed to a channel")
@app_commands.describe(channel="Target channel", title="Title", message="Body text")
@app_commands.checks.cooldown(1, 30.0)
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, title: str, message: str):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("Admin only.", ephemeral=True)
        return
    embed = discord.Embed(title=title, description=message, color=BRAND_COLOR)
    embed.set_footer(text=FOOTER_TEXT)
    await channel.send(embed=embed)
    await interaction.response.send_message(f"Sent in {channel.mention}", ephemeral=True)
    await log(interaction.guild, f"📣 Announcement by **{interaction.user}** in {channel.mention}")

# -------------------------------
# Admin Commands
# -------------------------------
@TREE.command(name="ban", description="Ban a user (Admin)")
@app_commands.describe(user="User to ban", reason="Reason")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.cooldown(1, 15.0)
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    await user.ban(reason=reason, delete_message_days=0)
    await interaction.response.send_message(f"Banned **{user}**. Reason: {reason}", ephemeral=True)
    await log(interaction.guild, f"⛔ Ban: **{user}** by **{interaction.user}** — {reason}")

@TREE.command(name="kick", description="Kick a user (Admin)")
@app_commands.describe(user="User to kick", reason="Reason")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.cooldown(1, 15.0)
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    await user.kick(reason=reason)
    await interaction.response.send_message(f"Kicked **{user}**. Reason: {reason}", ephemeral=True)
    await log(interaction.guild, f"👢 Kick: **{user}** by **{interaction.user}** — {reason}")

@TREE.command(name="warn", description="Warn a user (Admin)")
@app_commands.describe(user="User to warn", reason="Reason")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.cooldown(1, 10.0)
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    embed = discord.Embed(title="⚠️ Warning", description=f"{user.mention}\nReason: {reason}", color=discord.Color.orange())
    await interaction.response.send_message(embed=embed)
    await log(interaction.guild, f"⚠️ Warn: **{user}** by **{interaction.user}** — {reason}")

@TREE.command(name="unban", description="Unban a user by ID (Admin)")
@app_commands.describe(user_id="ID of the user to unban")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.cooldown(1, 10.0)
async def unban(interaction: discord.Interaction, user_id: str):
    banned_entries = await interaction.guild.bans()
    target = None
    for entry in banned_entries:
        if str(entry.user.id) == str(user_id):
            target = entry.user
            break
    if not target:
        await interaction.response.send_message("User not found in ban list.", ephemeral=True)
        return
    await interaction.guild.unban(target)
    await interaction.response.send_message(f"Unbanned **{target}**", ephemeral=True)
    await log(interaction.guild, f"♻️ Unban: **{target}** by **{interaction.user}**")

@TREE.command(name="slowmode", description="Set channel slowmode (Admin)")
@app_commands.describe(seconds="Slowmode delay in seconds (0 to disable)")
@app_commands.default_permissions(administrator=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=max(0, seconds))
    await interaction.response.send_message(f"Slowmode set to **{seconds}s** in {interaction.channel.mention}", ephemeral=True)
    await log(interaction.guild, f"🕒 Slowmode: {seconds}s set by **{interaction.user}** in {interaction.channel.mention}")

@TREE.command(name="clear", description="Clear messages (Admin)")
@app_commands.describe(amount="Number of messages to delete (max 100)")
@app_commands.default_permissions(administrator=True)
async def clear(interaction: discord.Interaction, amount: int):
    amount = max(1, min(100, amount))
    await interaction.response.defer(ephemeral=True, thinking=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Deleted **{len(deleted)}** messages.", ephemeral=True)
    await log(interaction.guild, f"🧹 Cleared {len(deleted)} messages by **{interaction.user}** in {interaction.channel.mention}")

# -------------------------------
# Backup /verify command (optional)
# -------------------------------
@TREE.command(name="verify", description="Backup verify command (assigns Verified role)")
async def verify_cmd(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE)
    if not role:
        await interaction.response.send_message("Verified role not found.", ephemeral=True)
        return
    try:
        await interaction.user.add_roles(role, reason="Backup /verify used")
        await interaction.response.send_message("You're verified! ⚒️", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to add roles.", ephemeral=True)

# -------------------------------
# Error handling
# -------------------------------
@ticket.error
@announce.error
@ban.error
@kick.error
@warn.error
@unban.error
@slowmode.error
@clear.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"⏳ Cooldown: try again in {error.retry_after:.1f}s.", ephemeral=True)
    else:
        try:
            await interaction.response.send_message("⚠️ Error executing command.", ephemeral=True)
        except Exception:
            pass
        await log(interaction.guild, f"❗ Error: {type(error).__name__} — {error}")

# -------------------------------
# Run
# -------------------------------
def main():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing DISCORD_BOT_TOKEN in environment.")
    BOT.run(token)

if __name__ == "__main__":
    main()
