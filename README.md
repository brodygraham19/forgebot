# BotForgeCore Premium

Features:
- Button-based verification in **#portal**
- Auto-creates roles: `Verified`, `Support`
- Ticket system with **Claim** and **Close** buttons
- Logging channel `#botforge-logs`
- Admin slash commands: `/ban`, `/kick`, `/warn`, `/unban`, `/slowmode`, `/clear`, `/announce`
- Cooldowns to prevent spam
- Midnight blue brand embeds with skull footer

## Run locally
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
copy env.example .env     # or rename
# put your token into .env
python bot.py
```

## Railway
- Add a new service from repo or upload these files.
- Set an environment variable: `DISCORD_BOT_TOKEN`.
- Start command: `python bot.py`

## Replit
- Upload files, create a `.env` secret `DISCORD_BOT_TOKEN`, run `python bot.py`.
