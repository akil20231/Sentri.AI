1) Discord Developer Portal setup

Go to the Discord Developer Portal → create/select your Application → Bot

Click Reset Token (if needed) and copy your bot token

Turn on these toggles under Privileged Gateway Intents:

✅ Message Content Intent (required)

✅ Server Members Intent (recommended for role/quarantine)

Invite the bot to your server:

OAuth2 → URL Generator

Scopes: bot

Bot permissions (minimum):

Read Messages/View Channels

Send Messages

Read Message History

Manage Roles (only if you want quarantine role)

Manage Messages (optional)

Open the generated URL and add to your server

2) Create channels in your server

Create (or choose) these channels:

#demo-chat (or whatever you’ll monitor)

#mod-logs (where AgentGuard posts decisions)

#quarantine (optional, for quarantined users)

You’ll need their IDs next.

Get Discord channel IDs

In Discord: Settings → Advanced → enable Developer Mode
Then right-click channel → Copy ID

3) Fill in .env (this is the main thing)

Create a .env file in the same folder as bot.py (NOT .env.example) and set:

DISCORD_BOT_TOKEN=PASTE_YOUR_TOKEN
GUILD_ID=YOUR_SERVER_ID
MONITORED_CHANNEL_IDS=CHANNEL_ID_1,CHANNEL_ID_2
MOD_LOG_CHANNEL_ID=MOD_LOG_CHANNEL_ID
QUARANTINE_ROLE_NAME=Quarantined

WARN_THRESHOLD=0.35
THROTTLE_THRESHOLD=0.55
QUARANTINE_THRESHOLD=0.75
THROTTLE_SECONDS=20

Get your GUILD_ID (server ID)

Right-click your server icon → Copy ID

4) Role + permissions for quarantine (optional but best demo)

The bot can auto-create the role Quarantined, but you need permissions set so quarantine actually “does something”.

Recommended permission setup

Create/verify channel #quarantine

Server Settings → Roles:

@everyone: ❌ Send Messages in most channels

Quarantined role:

❌ Send Messages everywhere

✅ Send Messages in #quarantine only

Important: Discord role hierarchy matters.

Put the bot’s role above Quarantined in the roles list, or it can’t assign it.
